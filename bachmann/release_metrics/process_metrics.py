import datetime
import json


def group_by_project(releases):
    projects = {}
    for release in releases:
        try:
            project = projects[release['project']]
        except KeyError:
            projects[release['project']] = []
            project = projects[release['project']]
        project.append(release)

    return projects


def reverse_project_messages(messages_by_project):
    for project in messages_by_project.keys():
        messages_by_project[project].reverse()


def compute_metrics(messages):
    seen_tags = set()
    fresh_releases = 0
    repeated_releases = 0
    for message in messages:
        tag = message['tag']
        if tag in seen_tags:
            repeated_releases += 1
        else:
            fresh_releases += 1
        seen_tags.add(tag)
    return {
        'fresh_releases': fresh_releases,
        'repeated_releases': repeated_releases,
        'rollback_percentage': round(repeated_releases / (fresh_releases + repeated_releases), 2)
    }


def process_metrics(releases):
    start = datetime.datetime.utcfromtimestamp(float(releases[-1]['timestamp'])) + datetime.timedelta(hours=-5)
    end = datetime.datetime.utcfromtimestamp(float(releases[0]['timestamp'])) + datetime.timedelta(hours=-5)
    messages_by_project = group_by_project(releases)
    reverse_project_messages(messages_by_project)
    metrics_by_project = {}
    for project, messages in messages_by_project.items():
        metrics_by_project[project] = compute_metrics(messages)
    return start, end, metrics_by_project


def main():
    with open('releases.json') as infile:
        releases = json.loads(infile.read())
        start, end, metrics = process_metrics(releases)
        print(f"Processed from {start} to {end}")
        print(json.dumps(metrics, indent=4))


if __name__  == '__main__':
    main()