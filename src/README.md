# URL Shortener — GitHub Actions CI/CD demo

[![CI](https://github.com/dustinupdyke/CMU-95-731-development/actions/workflows/ci.yml/badge.svg)](https://github.com/dustinupdyke/CMU-95-731-development/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A deliberately small FastAPI URL shortener whose real purpose is to showcase a
production-shaped **GitHub Actions CI/CD pipeline**: matrix testing, linting,
type-checking, a coverage gate, a multi-stage container build with a smoke
test, image + dependency security scanning, an SBOM, and a tagged-release
workflow.

> **Repository layout note.** GitHub only runs workflows found in
> `.github/workflows/` **at the repository root**. This project is
> self-contained under `src/`, so treat `src/` as the repo root — either push
> `src/` as its own repository, or move `src/.github/` up to the repo root and
> set the build `context:` to `src` in each workflow. The badge/URLs above
> assume `src/` is the root; adjust `OWNER/REPO` if yours differs.

## API

| Method | Path            | Description                                             |
| ------ | --------------- | ------------------------------------------------------- |
| `POST` | `/shorten`      | Create a short link. Rejects invalid URLs with **422**. |
| `GET`  | `/{code}`       | **307** redirect to the target; increments hit counter. |
| `GET`  | `/stats/{code}` | Target URL, creation time, and hit count. **404** if unknown. |
| `GET`  | `/health`       | Liveness probe used by the container + CI smoke test.   |

Short codes are produced by **base62-encoding** a monotonic counter, so they
stay short and collision-free (`1`, `2`, ... `z`, `10`, ...). Submitting the
same URL twice returns the existing link. Interactive Swagger UI lives at
[`/docs`](http://localhost:8000/docs) and ReDoc at `/redoc`.

### Example

```bash
curl -s -X POST http://localhost:8000/shorten \
  -H 'content-type: application/json' \
  -d '{"url": "https://www.example.com/a/very/long/path"}'
# {"code":"1","short_url":"http://localhost:8000/1","target_url":"https://www.example.com/a/very/long/path"}

curl -i http://localhost:8000/1          # -> 307, Location: https://www.example.com/...
curl -s http://localhost:8000/stats/1    # -> {"code":"1", "hits":1, ...}
```

## Project structure

```
src/
├── app/
│   ├── base62.py      # encode/decode short codes
│   ├── models.py      # Pydantic request/response models
│   ├── store.py       # thread-safe in-memory link store
│   └── main.py        # FastAPI app + endpoints
├── tests/
│   ├── test_base62.py # unit tests for the codec + validation
│   └── test_api.py    # integration tests for every endpoint
├── Dockerfile         # multi-stage, non-root, HEALTHCHECK
├── pyproject.toml     # deps + ruff / mypy / pytest / coverage config
└── .github/workflows/
    ├── ci.yml         # test → build → security → deploy
    └── release.yml    # semver image + GitHub Release on v* tags
```

## Local development

Requires Python **3.11+**.

```bash
cd src
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Run

```bash
uvicorn app.main:app --reload
# open http://localhost:8000/docs
```

### Test, lint, type-check

```bash
pytest                 # runs the suite with the ≥90% coverage gate
ruff check .           # lint
ruff format --check .  # formatting check (drop --check to auto-format)
mypy app tests         # strict type-checking
```

## Docker

```bash
cd src
docker build -t url-shortener .
docker run --rm -p 8000:8000 url-shortener
curl http://localhost:8000/health   # {"status":"ok","links":0}
```

The image is multi-stage: a **builder** stage installs the app into a virtualenv,
and the **final** `python:3.12-slim` stage copies only that venv, runs as a
non-root `app` user, exposes port 8000, and ships a `HEALTHCHECK` that probes
`/health` from the Python stdlib (the slim image has no `curl`).

## CI/CD

### `ci.yml` — runs on pushes/PRs to `main` and via manual dispatch

A `concurrency` group cancels superseded runs on the same ref so only the
latest commit's pipeline keeps running.

- **`test`** — matrix across Python **3.11 / 3.12 / 3.13**. Installs with a
  cached `pip`, runs `ruff check`, `ruff format --check`, strict `mypy`, then
  `pytest` with a **≥90% coverage gate**, and uploads each run's `coverage.xml`
  as an artifact.
- **`build`** (needs `test`) — sets up **Buildx** with a **GHA layer cache**,
  builds the image, boots a container and **curls `/health`** as a smoke test,
  then logs in and **pushes to GHCR** tagged with the commit **SHA** and
  `latest` (skipped on pull requests, where GHCR pushes aren't available).
- **`security`** (needs `test`) — **Trivy** scans the image and **fails on
  HIGH/CRITICAL** vulnerabilities, **pip-audit** checks dependencies for known
  CVEs, and **syft** generates an **SBOM** (SPDX JSON) uploaded as an artifact.
- **`deploy`** (needs `build` + `security`) — runs only on pushes to the
  default branch, targets a `production` environment (so you can require manual
  approval), and contains a **placeholder** deploy step to wire up your real
  target.

### `release.yml` — runs on `v*` tags

Builds the image tagged with the full **semver** (`1.2.3`, `1.2`, `1`) plus
`latest`, pushes to GHCR, and creates a **GitHub Release** with auto-generated
notes.

```bash
git tag v0.1.0 && git push origin v0.1.0
```

### Required permissions / setup

- GHCR pushes use the built-in `GITHUB_TOKEN` (`packages: write`) — no extra
  secrets needed for the same-repo package.
- The pinned action versions (Trivy `0.28.0`, etc.) are safe starting points;
  bump them with Dependabot as you like.

## License

MIT.
