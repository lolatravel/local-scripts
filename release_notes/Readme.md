# Release Notes Script

** This is a python 3 project **

This script will query for the release notes for the last run release. 

It does this by querying K8 for the current commit and the previous commit. Then it queries github for the diff
extracts jira info from PR titles and queries Jira for ticket details.

If a ticket does not exist for a PR we grabbed we will display those separately.

This script currently runs over Lola-Server, Travel Service, and Lola Desktop.

To work you need the following environment variables defined

`JIRA_API_TOKEN` An api token from jira
`JIRA_API_USER_EMAIL` The email for the jira user who owns the api token
`GITHUB_TOKEN` The token for the github apis. I has this as a personal access token that has the `repo` checkbox checked

The script assumes you have authenticated to aws before calling it. Generally this means 
you should make sure you have ran `aws-mfa` before calling this.


```
python query_release_notes.py -h
usage: query_release_notes.py [-h] [--previous PREVIOUS_COMMIT] [--current CURRENT_COMMIT] [repos [repos ...]]

Generate notes for the release

positional arguments:
  repos                 repos to query for. If undefined ill run them all

optional arguments:
  -h, --help            show this help message and exit
  --previous PREVIOUS_COMMIT
                        previous commit
  --current CURRENT_COMMIT
                        current commit
```

## Creating your tokens
To make a github token follow these instructions. This script requires `repo` permissions
https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line#creating-a-token

To make a jira api token follow these instructions
https://confluence.atlassian.com/cloud/api-tokens-938839638.html

the email should be the email associated with your jira account

# There is now a simple server to wrap this script functionality. 

`uvicorn release_notes.release_notes_server:app`

## Running the server in a docker container

Just build it, pass in the environment vars and the args

`docker build -t bachmann/releasenotes .`

`docker run --rm -p 8000:8000 -e JIRA_API_USER_EMAIL -e GITHUB_TOKEN -e JIRA_API_TOKEN  bachmann/releasenotes`