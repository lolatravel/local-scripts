import argparse
import datetime
import os
import uuid
import time
import json
import urllib.parse
import webbrowser
import requests
from requests import HTTPError

AUTHORIZE_ENDPOINT = "https://slack.com/oauth/authorize"
CHANNEL_HISTORY_ENDPOINT = "https://slack.com/api/channels.history"
OAUTH_ACCESS_ENDPOINT = "https://slack.com/api/oauth.access"
REDIRECT_URL = "http://localhost:8080"

CHANNELS_IDS = {
    "release": "CLNNTBBB3",
    "booking_failures": "CFCURFPFB",
    "lola_desktop": "C8PPP3U2Y",
    "production_errors": "CJYBRAP5X",
}


def authorize_app():
    state = str(uuid.uuid4())
    params = {
        "client_id": os.environ["RELEASE_METRICS_CLIENT_ID"],
        "scope": "channels:history",
        "redirect_url": REDIRECT_URL,
        "state": state,
        "team": "lola_travel",
    }
    webbrowser.open_new(f"{AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(params)}")
    resulting_url = input("Copy URL in your browser after accepting app: ")
    raw_params = urllib.parse.urlparse(resulting_url).query.strip()
    parsed_params = urllib.parse.parse_qs(raw_params)
    if parsed_params["state"][0] != state:
        raise ValueError(
            f"INVALID STATE PARAM got {parsed_params['state']} but got {state}"
        )
    code = parsed_params["code"][0]
    result = requests.post(
        OAUTH_ACCESS_ENDPOINT,
        data={
            "client_id": os.environ["RELEASE_METRICS_CLIENT_ID"],
            "client_secret": os.environ["RELEASE_METRICS_CLIENT_SECRET"],
            "code": code,
            "redirect_url": REDIRECT_URL,
        },
    )
    return result.json()["access_token"]


def get_page_history(access_token, latest, oldest, channel):
    return requests.get(
        CHANNEL_HISTORY_ENDPOINT,
        params={
            "token": access_token,
            "channel": channel,
            "count": 1000,
            "inclusive": False,
            "latest": latest,
            "oldest": oldest,
            "unreads": False,
        },
    )


def download_data(access_token, channel):
    messages = []
    oldest = 0
    latest = str(time.time())
    has_more = True
    while has_more:
        utc_timestamp = datetime.datetime.utcfromtimestamp(
            float(latest)
        ) + datetime.timedelta(hours=-5)
        print(utc_timestamp)
        result = get_page_history(access_token, latest, oldest, channel)
        try:
            result.raise_for_status()
        except HTTPError:
            print("Request failed. Retrying")
        response_data = result.json()
        messages += response_data["messages"]
        latest = messages[-1]["ts"]
        has_more = response_data["has_more"]
        time.sleep(2)
    return messages


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "channel", choices=CHANNELS_IDS.keys(), help="Which slack channel?"
    )
    return parser.parse_args()


def main():
    args = _get_args()
    access_token = authorize_app()
    messages = download_data(access_token, CHANNELS_IDS[args.channel])
    with open(f"{args.channel}_channel_history.json", "w") as outfile:
        outfile.write(json.dumps(messages, indent=4))


if __name__ == "__main__":
    main()
