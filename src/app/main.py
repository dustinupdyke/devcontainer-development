"""FastAPI application exposing a minimal URL shortener.

Endpoints:
    * ``POST /shorten``      - create a short link
    * ``GET  /{code}``       - resolve a short link (307 redirect)
    * ``GET  /stats/{code}`` - inspect a short link's usage
    * ``GET  /health``       - liveness probe
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Path, Request, status
from fastapi.responses import RedirectResponse

from app import __version__
from app.models import HealthResponse, ShortenRequest, ShortenResponse, StatsResponse
from app.store import LinkStore

app = FastAPI(
    title="URL Shortener",
    version=__version__,
    summary="A tiny base62 URL shortener used to demo GitHub Actions CI/CD.",
    description=(
        "Create short links, follow them via HTTP redirects, and inspect "
        "per-link hit statistics. State is held in memory for the lifetime of "
        "the process."
    ),
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "links", "description": "Create, resolve, and inspect short links."},
        {"name": "system", "description": "Operational endpoints."},
    ],
)

store = LinkStore()


def _short_url(request: Request, code: str) -> str:
    """Build the absolute short URL for ``code`` from the incoming request."""
    base = str(request.base_url).rstrip("/")
    return f"{base}/{code}"


@app.post(
    "/shorten",
    response_model=ShortenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["links"],
    summary="Create a short link",
    description=(
        "Accepts an absolute http(s) URL and returns a short code plus the "
        "fully qualified short URL. Invalid or non-http(s) URLs are rejected "
        "with a 422 validation error. Submitting the same URL twice returns "
        "the existing short link."
    ),
    responses={
        201: {"description": "Short link created (or an existing one reused)."},
        422: {"description": "The request body failed URL validation."},
    },
)
def shorten(payload: ShortenRequest, request: Request) -> ShortenResponse:
    link = store.shorten(str(payload.url))
    return ShortenResponse(
        code=link.code,
        short_url=_short_url(request, link.code),
        target_url=link.target_url,
    )


@app.get(
    "/stats/{code}",
    response_model=StatsResponse,
    tags=["links"],
    summary="Get link statistics",
    description="Return the target URL, creation time, and hit count for a short code.",
    responses={
        200: {"description": "Statistics for the requested short code."},
        404: {"description": "No link exists for the given code."},
    },
)
def stats(
    code: str = Path(..., description="The short code to inspect.", examples=["3"]),
) -> StatsResponse:
    link = store.get(code)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown short code")
    return StatsResponse(
        code=link.code,
        target_url=link.target_url,
        hits=link.hits,
        created_at=link.created_at,
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Liveness probe",
    description="Lightweight health check used by the container HEALTHCHECK and CI smoke test.",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", links=store.count())


@app.get(
    "/{code}",
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    tags=["links"],
    summary="Resolve a short link",
    description=(
        "Look up a short code and issue a 307 redirect to its target URL, "
        "incrementing the link's hit counter. Unknown codes return 404."
    ),
    responses={
        307: {"description": "Redirect to the target URL via the Location header."},
        404: {"description": "No link exists for the given code."},
    },
)
def resolve(
    code: str = Path(..., description="The short code to resolve.", examples=["3"]),
) -> RedirectResponse:
    link = store.resolve(code)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown short code")
    return RedirectResponse(url=link.target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
