#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

export SPEND_DATABASE_URL=postgres://spend:spend@127.0.0.1/spend
cd ~/code/models
source .env
git pull
./all_migrations.sh
deactivate
cd ~/code/python-services
git pull
source $(pipenv --venv)/bin/activate
source spend/.env
alembic -c spend/db/spend/alembic.ini upgrade head
alembic -c spend/db/stripe/alembic.ini upgrade head
deactivate