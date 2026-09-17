# Wren-first Analytics API

FastAPI entrypoint: `apps.api.main:app`.

The API follows Wren's operating model:

1. Load the project's MDL and `knowledge/` files.
2. Ask the OpenAI-compatible LLM to write SQL against logical Wren models.
3. Validate the logical SQL with an AST policy.
4. Run Wren Engine `dry_plan` to expand it into PostgreSQL SQL.
5. Validate the expanded SQL again.
6. Optionally execute it through the local PostgreSQL read-only executor.

Endpoints:

- `GET /health/live`
- `GET /health/ready`
- `GET /api/v1/wren/models`
- `POST /api/v1/query/wren` — body: `{"question": "...", "execute": false}`
- `GET /api/v1/wren/cubes` and `GET /api/v1/wren/cubes/{name}`
- `POST /api/v1/wren/query/cube` — structured Wren CubeQuery; plan-only by default
- `POST /api/v1/wren/dry-plan` — Wren MDL expansion without a database
- `POST /api/v1/wren/dry-run` — Wren connector validation without returning rows
- `GET /api/v1/wren/memory/status`
- `GET /api/v1/wren/memory/describe` and `/queries`
- `POST /api/v1/wren/memory/index`, `/fetch`, `/recall`, `/store`, `/reset`
- `GET /docs`

`execute=false` is the default. Execution requires both
`ANALYTICS_EXECUTION_ENABLED=true` and a configured read-only PostgreSQL URL.
`dry-run` has the same explicit gate because it contacts the database. `dry-plan`
and Memory fetch/recall work without data; Memory uses `knowledge/sql/*.md` as
the source of truth and auto-falls back to grep when the optional memory extra
is not installed. No second planner or local semantic catalog is started by
this API.
