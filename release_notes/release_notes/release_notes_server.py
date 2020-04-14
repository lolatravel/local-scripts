from starlette.applications import Starlette  # type: ignore
from starlette.requests import Request  # type: ignore
from starlette.responses import JSONResponse, Response  # type: ignore
from starlette.routing import Route  # type: ignore

from release_notes.query_release_notes import (
    query_for_release_notes,
    get_notes_for_repo,
)


async def _get_notes(request: Request, query_for_staged: bool) -> Response:
    try:
        repos = request.query_params["repos"].split(",")
    except KeyError:
        return JSONResponse(
            {
                "error": "Repos must be specified in a comma delimited string in query parameter 'repos'"
            },
            status_code=400,
        )
    result = await query_for_release_notes(
        repos,
        request.query_params.get("current_commit"),
        request.query_params.get("previous_commit"),
        staged=query_for_staged,
    )
    return JSONResponse(result)


async def released(request: Request) -> Response:
    return await _get_notes(request, query_for_staged=False)


async def staged(request: Request) -> Response:
    return await _get_notes(request, query_for_staged=True)


async def ping(_) -> Response:
    return JSONResponse({"ping": "pong"})


async def clear_cache(_) -> Response:
    get_notes_for_repo.cache_clear()
    return JSONResponse({"result": "cache_cleared"})


app = Starlette(
    debug=True,
    routes=[
        Route("/", ping),
        Route("/released", released),
        Route("/staged", staged),
        Route("/clearcache", clear_cache),
    ],
)
