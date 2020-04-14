import asyncio

import pytest
import vcr

from release_notes import query_release_notes
from release_notes.query_release_notes import (
    query_for_diff,
    get_commits_between,
    query_ticket_info,
    JiraTicketInfo,
    get_notes_for_repo_with_commits,
    PRInfo,
    get_notes_for_repo,
    parse_args,
    extract_commit_from_docker_tag,
    get_current_and_previous_commit,
)

from release_notes.query_release_notes import format_release_notes

DESKTOP_NOTES_EXAMPLE = {
    "repo": "lola-desktop",
    "from_commit": "2919e85",
    "to_commit": "2f65240",
    "prs": [
        {
            "pr_title": "[HOT-68] Add mixpanel tracking for hotel search rank and sort type for book hotel event",
            "pr_number": "3138",
            "pr_author": "nbond211",
            "jira_id": "HOT-68",
            "jira_title": "Track - What's the hotel rank of hotels booked by each sort? (w/o filters used)",
            "jira_assignee": "Nick Bond",
        },
        {
            "pr_title": "TMV-653 update multiselect bug fixes",
            "pr_number": "3160",
            "pr_author": "jwaters627",
            "jira_id": None,
            "jira_title": None,
            "jira_assignee": None,
        },
        {
            "pr_title": "NOTIX-1 Document and make it easier to run production build locally",
            "pr_number": "3163",
            "pr_author": "emroussel",
            "jira_id": None,
            "jira_title": None,
            "jira_assignee": None,
        },
        {
            "pr_title": "TVM-554: Remove CSV Update flag",
            "pr_number": "3165",
            "pr_author": "ramselgonzalez",
            "jira_id": "TVM-554",
            "jira_title": "Remove feature flag/code clean up",
            "jira_assignee": "Ramsel Gonzalez",
        },
        {
            "pr_title": "[HOT-238] Change order of items in negotiated rates tooltip",
            "pr_number": "3166",
            "pr_author": "nbond211",
            "jira_id": "HOT-238",
            "jira_title": "Negotiated Rates: Tooltip - swap item 2 with item 3.",
            "jira_assignee": "Nick Bond",
        },
        {
            "pr_title": "ST-532 Adding Delete Credit Modal",
            "pr_number": "3167",
            "pr_author": "chaz9127",
            "jira_id": "ST-532",
            "jira_title": "[UI] Add ability to delete travel credit",
            "jira_assignee": "CJ Douglas",
        },
    ],
}


@vcr.use_cassette(
    "tests/fixtures/vcr_cassettes/query_for_diff.yaml", filter_headers=["authorization"]
)
def test_query_for_diff():
    result = asyncio.run(
        query_for_diff(
            "lola-server",
            "3cb7e431258000ddfd648e650787e51ffe87760e",
            "c0c43ba0c86d876cbd881e1242965116753b2702",
        )
    )
    assert [
        "[FLY-342] Add birthmonth node on traveler profile (#6126)\n\n* added birthmonth field\n\n* blackened files\n\n* added tests for new queries\n\n* blackened files",
        "[ST-671] post waiver to slack not task (#6128)",
        "PLAT-337 bugsnag logconfig fix\n\nIf bugsnag was turned on, the log config would crash\n\nblack formatting",
        "Merge pull request #6130 from lolatravel/feature/20200218/PLAT-337-bugsnag_config_error\n\nPLAT-337 bugsnag logconfig fix",
        "[PLAT-338] Use the current timestamp for random id values (#6132)\n\n* Use the current timestamp for random id values\n\n* Use current timestamp and random id list to prevent milli-collisions",
    ] == result


@vcr.use_cassette(
    "tests/fixtures/vcr_cassettes/get_commits_between.yaml",
    filter_headers=["authorization"],
)
def test_get_commits_between():
    result = asyncio.run(
        get_commits_between(
            "lola-server",
            "3cb7e431258000ddfd648e650787e51ffe87760e",
            "c0c43ba0c86d876cbd881e1242965116753b2702",
        )
    )
    assert [
        PRInfo(
            id="6126",
            title="[FLY-342] Add birthmonth node on traveler profile",
            author="JKThanassi",
        ),
        PRInfo(
            id="6128",
            title="[ST-671] post waiver to slack not task",
            author="maxvoltage",
        ),
        PRInfo(id="6130", title="PLAT-337 bugsnag logconfig fix", author="mmcmahon"),
        PRInfo(
            id="6132",
            title="[PLAT-338] Use the current timestamp for random id values",
            author="jdormit",
        ),
    ] == result


@vcr.use_cassette(
    "tests/fixtures/vcr_cassettes/get_commits_between_multiline_commit_messages.yaml",
    filter_headers=["authorization"],
)
def test_get_commits_between_multiline_commit_messages():
    result = asyncio.run(get_commits_between("lola-server", "8fb51f8", "74d5a0d",))
    assert [
        PRInfo(
            id="6155",
            title="HIIT-70 Post savings to #savings channel",
            author="ddoughty",
        ),
        PRInfo(
            id="6140", title="TVM-610 Make group policy editable", author="mpnovikova"
        ),
    ] == result


@vcr.use_cassette(
    "tests/fixtures/vcr_cassettes/query_ticket_info.yaml",
    filter_headers=["authorization"],
)
def test_query_ticket_info():
    result = asyncio.run(
        query_ticket_info(
            "PLAT-337 bugsnag logconfig fix", "PLAT-337", "mmcmahon", "1234"
        )
    )
    assert (
        JiraTicketInfo(
            id="PLAT-337",
            title="Bugsnag logging configuration fails",
            ticket_assignee="unassigned",
            pr_title="PLAT-337 bugsnag logconfig fix",
            pr_author="mmcmahon",
            pr_id="1234",
        )
        == result
    )


@vcr.use_cassette(
    "tests/fixtures/vcr_cassettes/query_ticket_info_invalid.yaml",
    filter_headers=["authorization"],
)
def test_query_ticket_info_invalid():
    result = asyncio.run(
        query_ticket_info(
            "NOTIK-1234 I am too cool for tickets", "NOTIK-1234", "batman", "1234"
        )
    )
    assert (
        JiraTicketInfo(
            id="NOTIK-1234",
            title="Failed",
            ticket_assignee="n/a",
            pr_title="NOTIK-1234 I am too cool for tickets",
            pr_author="batman",
            pr_id="1234",
        )
        == result
    )


def test_get_notes_for_repo(monkeypatch):
    async def mock_get_current_and_previous_commit(pod, app):
        assert pod == "travel-service-api"
        assert app == "travel-service"
        return "a", "b"

    async def assert_standard_release(repo, current_commit, previous_commit):
        assert repo == "lola-travel-service"
        assert current_commit == "a"
        assert previous_commit == "b"

    monkeypatch.setattr(
        query_release_notes,
        "get_current_and_previous_commit",
        mock_get_current_and_previous_commit,
    )
    monkeypatch.setattr(
        query_release_notes, "get_notes_for_repo_with_commits", assert_standard_release
    )
    asyncio.run(get_notes_for_repo("lola-travel-service", None, None, False))


def test_get_notes_for_standard_repo(monkeypatch):
    async def mock_get_current_and_previous_commit(pod, app):
        assert pod == "lola-desktop"
        assert app == "lola-desktop"
        return "a", "b"

    async def assert_standard_release(repo, current_commit, previous_commit):
        assert repo == "lola-desktop"
        assert current_commit == "a"
        assert previous_commit == "b"

    monkeypatch.setattr(
        query_release_notes,
        "get_current_and_previous_commit",
        mock_get_current_and_previous_commit,
    )

    monkeypatch.setattr(
        query_release_notes, "get_notes_for_repo_with_commits", assert_standard_release
    )
    asyncio.run(get_notes_for_repo("lola-desktop", None, None, False))


def test_get_notes_for_repo_staged(monkeypatch):
    async def mock_get_current_and_previous_commit(pod, app):
        assert pod == "lola-server-web"
        assert app == "lola-server"
        return "a", "b"

    async def mock_get_head_commit(repo):
        assert repo == "lola-server"
        return "imacommit"

    async def assert_staged_release(repo, current_commit, previous_commit):
        # Basically, compare head to what is currently released
        # So despite the current released commit being "a" consider it
        # to be the previous commit
        assert repo == "lola-server"
        assert current_commit == "imacommit"
        assert previous_commit == "a"

    monkeypatch.setattr(
        query_release_notes,
        "get_current_and_previous_commit",
        mock_get_current_and_previous_commit,
    )
    monkeypatch.setattr(
        query_release_notes, "get_head_commit", mock_get_head_commit,
    )
    monkeypatch.setattr(
        query_release_notes, "get_notes_for_repo_with_commits", assert_staged_release
    )
    asyncio.run(get_notes_for_repo("lola-server", None, None, True))


@vcr.use_cassette(
    "tests/fixtures/vcr_cassettes/test_get_notes_for_repo_with_commits.yaml",
    filter_headers=["authorization"],
)
@pytest.mark.skip(
    reason="For some reason the tape is not recording the expected 404 on NOTIX"
)
def test_get_notes_for_repo_with_commits():
    result = asyncio.run(
        get_notes_for_repo_with_commits("lola-desktop", "2f65240", "2919e85")
    )
    assert DESKTOP_NOTES_EXAMPLE == result


@vcr.use_cassette(
    "tests/fixtures/vcr_cassettes/get_current_and_previous_commit.yaml",
    filter_headers=["authorization"],
)
def test_get_current_and_previous_commit():
    # This test is inherently unstable since if the tape is cleared
    # the commits will change. But at least it gives me the freedom to refactor
    # the parsing if I need to
    assert ("5427252", "8bb1c4a") == asyncio.run(
        get_current_and_previous_commit("lola-server-web", "lola-server")
    )


@vcr.use_cassette(
    "tests/fixtures/vcr_cassettes/get_current_and_previous_commit_invalid.yaml",
    filter_headers=["authorization"],
)
def test_get_current_and_previous_commit_invalid():
    # This test is inherently unstable since if the tape is cleared
    # the commits will change. But at least it gives me the freedom to refactor
    # the parsing if I need to
    with pytest.raises(ValueError):
        asyncio.run(get_current_and_previous_commit("nonsense-31212312", "batman"))


def test_args():
    no_args = parse_args([])
    assert not no_args.current_commit
    assert not no_args.previous_commit
    assert ["lola-server", "lola-travel-service", "lola-desktop"] == no_args.repos

    commits = parse_args(["--current", "b", "--previous", "a"])
    assert "b" == commits.current_commit
    assert "a" == commits.previous_commit
    assert ["lola-server", "lola-travel-service", "lola-desktop"] == commits.repos

    repo_specified = parse_args(["lola-server", "--previous", "a"])
    assert "a" == repo_specified.previous_commit
    assert ["lola-server"] == repo_specified.repos


def test_extract_commit_from_docker_tag():
    assert "5db1461" == extract_commit_from_docker_tag("Cool:test.5db1461")
    assert "5db1461" == extract_commit_from_docker_tag("cool:pypy-5db1461")
    assert "5db1461" == extract_commit_from_docker_tag("woah:5db1461")


def test_format_notes_for_people():
    result = format_release_notes([DESKTOP_NOTES_EXAMPLE], False)
    assert (
        """lola-desktop
Commits 2919e85..2f65240
--------------------
The following tickets were released
--------------------
HOT-238 Negotiated Rates: Tooltip - swap item 2 with item 3.
	Assigned to: Nick Bond
	Pr #3166 by: nbond211
HOT-68 Track - What's the hotel rank of hotels booked by each sort? (w/o filters used)
	Assigned to: Nick Bond
	Pr #3138 by: nbond211
ST-532 [UI] Add ability to delete travel credit
	Assigned to: CJ Douglas
	Pr #3167 by: chaz9127
TVM-554 Remove feature flag/code clean up
	Assigned to: Ramsel Gonzalez
	Pr #3165 by: ramselgonzalez
--------------------
The following PRs were released as well but did not have valid ticket info
--------------------
NOTIX-1 Document and make it easier to run production build locally
	Pr #3163 by: emroussel
TMV-653 update multiselect bug fixes
	Pr #3160 by: jwaters627
--------------------"""
        == result
    )
