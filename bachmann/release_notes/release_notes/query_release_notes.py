#!/usr/bin/env python
import argparse
import os
import sys

# TypeDict not being accepted by the current version of mypy
from typing import List, NamedTuple, Tuple, TypedDict, Optional, Dict  # type: ignore

import aiohttp  # type: ignore
import asyncio

from aiohttp import BasicAuth, ClientResponseError
from async_lru import alru_cache  # type: ignore
from kubernetes.config import ConfigException  # type: ignore
import re
from kubernetes import config, client  # type: ignore

LOLA_SERVER = "lola-server"
TRAVEL_SERVICE = "lola-travel-service"
LOLA_DESKTOP = "lola-desktop"

SEPARATOR = "-" * 20

JIRA_AUTH = BasicAuth(os.environ["JIRA_API_USER_EMAIL"], os.environ["JIRA_API_TOKEN"])
GITHUB_AUTH_HEADER = {"Authorization": f"token {os.environ['GITHUB_TOKEN']}"}


class PRInfo(NamedTuple):
    id: str
    title: str
    author: str


class JiraTicketInfo(NamedTuple):
    id: str
    title: str
    ticket_assignee: str
    pr_id: str
    pr_title: str
    pr_author: str


class PrTicketDescription(TypedDict):
    pr_title: str
    pr_number: str
    pr_author: str
    jira_id: Optional[str]
    jira_title: Optional[str]
    jira_assignee: Optional[str]


class ReleaseNotesResult(TypedDict):
    repo: str
    from_commit: str
    to_commit: str
    prs: List[PrTicketDescription]


async def _call_github_for_diff(
    repo: str, current_commit: str, previous_commit: str
) -> Dict:
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.get(
            f"https://api.github.com/repos/lolatravel/{repo}/compare/{previous_commit}...{current_commit}",
            headers=GITHUB_AUTH_HEADER,
        ) as response:
            return await response.json()


async def query_for_diff(
    repo: str, current_commit: str, previous_commit: str
) -> List[str]:
    response = await _call_github_for_diff(repo, current_commit, previous_commit)
    return [commit["commit"]["message"] for commit in response["commits"]]


async def get_head_commit(repo: str) -> str:
    response = await _call_github_for_diff(repo, "HEAD", "HEAD~")
    return response["commits"][0]["sha"]


async def get_pr_title_and_author(repo: str, pr_number: str) -> PRInfo:
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.get(
            f"https://api.github.com/repos/lolatravel/{repo}/pulls/{pr_number}",
            headers=GITHUB_AUTH_HEADER,
        ) as response:
            response_json = await response.json()
    return PRInfo(
        id=pr_number,
        title=response_json["title"],
        author=response_json["user"]["login"],
    )


async def get_commits_between(
    repo: str, current_commit: str, previous_commit: str
) -> List[PRInfo]:
    messages = await query_for_diff(repo, current_commit, previous_commit)

    pr_futures = []
    for message in messages:
        first_line = message.split("\n")[0]
        if "Merge pull request" in first_line:
            pr_futures.append(
                get_pr_title_and_author(
                    repo, re.findall(r"Merge pull request #(\d+) from", message)[0]
                )
            )
        elif re.findall(r"\(#\d+\)$", first_line):
            pr_futures.append(
                get_pr_title_and_author(repo, first_line.split()[-1][2:-1])
            )
        # Final case means there was no pr number or PR title
        # This likely means the commit is just part of the merge
        # and can be safely ignored for the purposes of finding tickets

    return await asyncio.gather(*pr_futures)


async def query_ticket_info(
    pr_title: str, ticket_id: str, author: str, pr_id: str
) -> JiraTicketInfo:
    async with aiohttp.ClientSession(auth=JIRA_AUTH, raise_for_status=True) as session:
        try:
            async with session.get(
                f"https://lola.atlassian.net/rest/api/3/issue/{ticket_id.upper()}",
                headers={"Content-Type": "application/json"},
            ) as response:
                response_json = await response.json()
                ticket_fields = response_json["fields"]
                assignee = (ticket_fields["assignee"] or {}).get(
                    "displayName", "unassigned"
                )
                return JiraTicketInfo(
                    id=ticket_id,
                    title=ticket_fields["summary"],
                    ticket_assignee=assignee,
                    pr_title=pr_title,
                    pr_author=author,
                    pr_id=pr_id,
                )
        except ClientResponseError:
            return JiraTicketInfo(
                id=ticket_id,
                title="Failed",
                ticket_assignee="n/a",
                pr_title=pr_title,
                pr_author=author,
                pr_id=pr_id,
            )


async def get_notes_for_repo_with_commits(
    repo: str, current_commit: str, previous_commit: str
) -> ReleaseNotesResult:
    prs = await get_commits_between(repo, current_commit, previous_commit)
    tickets = set()
    for pr_info in prs:
        ticket_id = (
            pr_info.title.replace(
                "[", " "
            )  # I am using space here to split up people who put in multiple tickets
            .replace("]", " ")  # Right now I only support the first
            .replace(":", " ")
            .split()[0]
            .strip()
        )
        tickets.add((pr_info.title, ticket_id, pr_info.author, pr_info.id))

    jira_ticket_infos = await asyncio.gather(
        *[query_ticket_info(*ticket_info) for ticket_info in tickets]
    )
    return _structure_release_notes(
        repo, current_commit, previous_commit, jira_ticket_infos
    )


def _structure_release_notes(
    repo: str,
    current_commit: str,
    previous_commit: str,
    jira_ticket_infos: List[JiraTicketInfo],
) -> ReleaseNotesResult:
    prs = []
    for jira_ticket_info in jira_ticket_infos:
        if jira_ticket_info.title == "Failed":
            prs.append(
                PrTicketDescription(
                    pr_title=jira_ticket_info.pr_title,
                    pr_number=jira_ticket_info.pr_id,
                    pr_author=jira_ticket_info.pr_author,
                    jira_id=None,
                    jira_title=None,
                    jira_assignee=None,
                )
            )

        else:
            prs.append(
                PrTicketDescription(
                    pr_title=jira_ticket_info.pr_title,
                    pr_number=jira_ticket_info.pr_id,
                    pr_author=jira_ticket_info.pr_author,
                    jira_id=jira_ticket_info.id,
                    jira_title=jira_ticket_info.title,
                    jira_assignee=jira_ticket_info.ticket_assignee,
                )
            )
    prs.sort(key=lambda pr: pr["pr_number"])
    return ReleaseNotesResult(
        repo=repo, from_commit=previous_commit, to_commit=current_commit, prs=prs
    )


# This is here to benefit the server. If this script is long running this seemed like the most valuable place to cache
@alru_cache
async def get_notes_for_repo(
    repo: str,
    arg_current_commit: Optional[str],
    arg_previous_commit: Optional[str],
    staged: bool,
) -> ReleaseNotesResult:
    if repo == LOLA_SERVER:
        pod = "lola-server-web"
        app = "lola-server"
    elif repo == TRAVEL_SERVICE:
        pod = "travel-service-api"
        app = "travel-service"
    else:
        pod = repo
        app = repo
    current_commit, previous_commit = "", ""
    if not arg_current_commit or not arg_previous_commit:
        current_commit, previous_commit = await get_current_and_previous_commit(
            pod, app
        )
    current_commit = arg_current_commit or current_commit
    previous_commit = arg_previous_commit or previous_commit

    if staged:
        # Prepare notes for whats *staged* for release. That means, compare
        # the currently released commit to the head of the repo
        previous_commit = current_commit
        current_commit = await get_head_commit(repo)

    return await get_notes_for_repo_with_commits(repo, current_commit, previous_commit)


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate notes for the release")

    parser.add_argument(
        "--previous", action="store", dest="previous_commit", help="previous commit"
    )
    parser.add_argument(
        "--current", action="store", dest="current_commit", help="current commit"
    )
    parser.add_argument(
        "--staged",
        dest="staged",
        const=True,
        action="store_const",
        default=False,
        help="Prepare notes between whats currently released and what has not been released yet",
    )
    parser.add_argument(
        "repos",
        metavar="repos",
        type=str,
        nargs="*",
        default=[LOLA_SERVER, TRAVEL_SERVICE, LOLA_DESKTOP],
        help="repos to query for. If undefined ill run them all",
    )

    return parser.parse_args(args)


def extract_commit_from_docker_tag(tag: str) -> str:
    tag = tag.split(":")[1]
    if len(tag.split("-")) > 1:
        tag = tag.split("-")[1]
    if len(tag.split(".")) > 1:
        tag = tag.split(".")[1]
    return tag


async def get_current_and_previous_commit(pod: str, app: str) -> Tuple[str, str]:
    try:
        config.load_incluster_config()
    except ConfigException:
        config.load_kube_config()
    v1 = client.AppsV1Api()
    current_commit = None
    ret = v1.list_namespaced_replica_set(
        "core-services", label_selector=f"app={app}", watch=False
    )
    for i in sorted(
        ret.items, key=lambda x: x.metadata.creation_timestamp, reverse=True
    ):
        if i.metadata.name.startswith(pod):
            commit = i.spec.template.spec.containers[0].image.split(":")[1]
            if len(commit.split("-")) > 1:
                commit = commit.split("-")[1]
            if len(commit.split(".")) > 1:
                commit = commit.split(".")[1]
            if not current_commit:
                current_commit = commit
            elif commit != current_commit:
                return current_commit, commit
    raise ValueError(
        "Could not find commits! Verify you have your k8 context set correctly."
        " (You likely want kubectx prod; kubens core-services)"
    )


async def query_for_release_notes(
    repos: List[str],
    current_commit: Optional[str],
    previous_commit: Optional[str],
    staged: bool,
) -> List[ReleaseNotesResult]:
    return await asyncio.gather(
        *[
            get_notes_for_repo(repo, current_commit, previous_commit, staged)
            for repo in repos
        ]
    )


def format_release_notes(release_notes: List[ReleaseNotesResult], staged: bool) -> str:
    tense = "will be" if staged else "were"
    results: List[str] = []
    for release_note_result in release_notes:
        formatted_release_notes = [
            release_note_result["repo"],
            f"Commits {release_note_result['from_commit']}..{release_note_result['to_commit']}",
            SEPARATOR,
            f"The following tickets {tense} released",
            SEPARATOR,
        ]
        valid = []
        invalid = []
        for pr_ticket_description in release_note_result["prs"]:
            if not pr_ticket_description["jira_title"]:
                invalid.append(
                    f"{pr_ticket_description['pr_title']}\n\t"
                    f"Pr #{pr_ticket_description['pr_number']} "
                    f"by: {pr_ticket_description['pr_author']}"
                )
            else:
                valid.append(
                    "".join(
                        [
                            f"{pr_ticket_description['jira_id']} {pr_ticket_description['jira_title']}",
                            f"\n\tAssigned to: {pr_ticket_description['jira_assignee']}",
                            f"\n\tPr #{pr_ticket_description['pr_number']} by: {pr_ticket_description['pr_author']}",
                        ]
                    )
                )
        results += formatted_release_notes + sorted(valid)
        results.append(SEPARATOR)
        if invalid:
            results.append(
                f"The following PRs {tense} released as well but did not have valid ticket info"
            )
            results.append(SEPARATOR)
            results += sorted(invalid)
        results.append(SEPARATOR)
    return "\n".join(results)


async def main() -> str:
    args = parse_args(sys.argv[1:])
    results = await query_for_release_notes(
        args.repos, args.current_commit, args.previous_commit, args.staged
    )
    return format_release_notes(results, args.staged)


if __name__ == "__main__":
    print(asyncio.run(main()))
