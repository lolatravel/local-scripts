import pytest
from starlette.testclient import TestClient

from release_notes import release_notes_server
from release_notes.release_notes_server import app


@pytest.fixture
def test_client():
    return TestClient(app)


def test_ping(test_client):
    response = test_client.get("/")
    assert response.status_code == 200


def test_released_no_repos(test_client):
    response = test_client.get("/released")
    assert response.status_code == 400


@pytest.mark.parametrize(
    "repos_input,current_commit_input,previous_commit_input,staged_input",
    [
        (["lola-desktop"], "a", "b", False),
        (["lola-desktop"], "a", "b", True),
        (["lola-desktop", "lola-server"], "a", "b", True),
        (["lola-desktop", "lola-server"], None, None, False),
    ],
)
def test_server(
    test_client,
    monkeypatch,
    repos_input,
    current_commit_input,
    previous_commit_input,
    staged_input,
):
    # The goal of these tests is to ensure the parameters make it over to the script logic
    # correctly. The logic of the script is tested elsewhere
    async def mocked_query_for_release_notes(
        repos, current_commit, previous_commit, staged
    ):
        assert repos_input == repos
        assert current_commit_input == current_commit
        assert previous_commit == previous_commit_input
        assert staged is staged_input
        return {"a": "ok"}

    monkeypatch.setattr(
        release_notes_server, "query_for_release_notes", mocked_query_for_release_notes,
    )
    url = f"/{'staged' if staged_input else 'released'}?repos={','.join(repos_input)}"
    if current_commit_input:
        url += f"&current_commit={current_commit_input}"
    if previous_commit_input:
        url += f"&previous_commit={previous_commit_input}"

    response = test_client.get(url)
    assert response.status_code == 200
