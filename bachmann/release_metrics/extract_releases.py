import json
import re
from urllib.parse import urlparse

JENKINS_BOT_ID = "BNJDGC42C"


def extract_tag(release_message):
    if not release_message.startswith('Production'):
        return None, None
    match = re.search(r"<(.*)>", release_message)
    url = match.group(1)
    parsed = urlparse(url)
    tag_parts = urlparse(url).path.split("/")[-1].split(":")
    try:
        return tag_parts[0], tag_parts[1]
    except IndexError:
        return None, None


def process_history(history):
    releases = []
    for message in history:
        if (
            message.get("bot_id") == JENKINS_BOT_ID
            and message["subtype"] == "bot_message"
        ):
            timestamp = message["ts"]
            project, tag = extract_tag(message["attachments"][0]["fields"][0]["value"])
            if project and tag:
                releases.append(
                    {"timestamp": timestamp, "project": project, "tag": tag}
                )
    return releases


def main():
    with open("../slack_exporter/channel_history.json") as infile:
        history = json.loads(infile.read())
    with open("releases.json", "w") as outfile:
        outfile.write(json.dumps(process_history(history), indent=4))


if __name__ == "__main__":
    main()
