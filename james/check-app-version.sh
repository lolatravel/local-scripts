#!/bin/bash
#
# check what version of the mobile app is the latest in the app store

set -e

curl -s "http://itunes.apple.com/lookup?id=1248039795" | jq -r '.results[0] | .version + " on " + .currentVersionReleaseDate'
