FROM python:3.8
ARG GITHUB_TOKEN
ARG JIRA_TOKEN

RUN set -ex && mkdir /workspace
WORKDIR /workspace
COPY ./requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
COPY release_notes release_notes

EXPOSE 8000
ENTRYPOINT ["uvicorn", "release_notes.release_notes_server:app", "--host", "0.0.0.0"]