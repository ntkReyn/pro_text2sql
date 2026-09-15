# ADR-0014: Run the local MVP with PostgreSQL in Compose

- Status: Accepted
- Date: 2026-09-15
- Decision makers: Repository owner
- Technical owner: Project team
- Consulted: None
- Informed: Project team
- Supersedes: [ADR-0012](0012-package-mvp-as-single-application-container.md)
- Superseded by: None

## Context and problem statement

ADR-0012 selected one application container and treated Supabase and OpenAI as
external services. The project does not yet have a remote analytics database,
while the semantic compiler, schema migration and EV-customer fixture
already target PostgreSQL. Requiring a remote Supabase project now prevents a
new developer from exercising the database path with a one-command local setup.

This decision covers local development only. It does not select the managed
database, topology or high-availability model for staging and production; those
questions remain in ADR-0006.

## Decision drivers

- One-command startup from a clean development machine;
- exact PostgreSQL dialect compatibility for migrations and generated SQL;
- repeatable schema and seed application;
- a least-privilege runtime credential distinct from the migration owner;
- persistent local data without committing database files;
- no additional application deployable units before independent scaling exists.

## Considered options

1. Keep PostgreSQL or Supabase entirely external to Compose.
2. Add PostgreSQL and a migration runner to the main local Compose project.
3. Run the complete local Supabase stack.
4. Substitute SQLite or DuckDB during early development.

## Evidence

- The repository compiler and migration already use PostgreSQL semantics.
- The repository has no remote database dependency available for local work.
- The current vertical slice has a versioned migration and deterministic seed.
- Docker Compose supports dependency health conditions, one-shot services and
  named volumes.
- PostgreSQL supports role-level read-only defaults and object-level grants;
  both controls are needed for defense in depth.

## Decision outcome

Chosen option: **add PostgreSQL and a migration runner to the main local Compose
project**.

`compose.yaml` contains three services:

- `app`: the only long-running application service;
- `db`: PostgreSQL pinned to the `17-bookworm` image and backed by a named
  volume;
- `migrate`: a one-shot process using the application image, which applies
  ordered migrations and local seed files before `app` starts.

The migration runner records the SHA-256 checksum of every applied migration
and seed file. An applied file must not be edited; a new migration/seed file is
required. A mismatch fails startup explicitly. Resetting the named volume is
allowed only for disposable local data.

The PostgreSQL bootstrap owner applies schema changes. The application connects
as a separate role with `USAGE` on the `analytics` schema and `SELECT` on its
tables and views. The runtime role has `NOINHERIT`, a statement timeout and
`default_transaction_read_only=on`. It is not granted create, write, temporary
object or administrative privileges.

OpenAI remains an external dependency. Supabase remains an option for staging
or production but is no longer required for local database development.

## Consequences

### Positive

- A clean environment can create schema and fixture data with
  `docker compose up --build`.
- Generated SQL and migrations are exercised against the target dialect.
- The application credential cannot mutate analytics tables through ordinary
  grants, even if a higher application layer fails.
- Local data persists across ordinary container recreation.
- There is still only one application service; `db` and `migrate` are local
  backing infrastructure.

### Negative

- Local startup now downloads and runs PostgreSQL in addition to the
  application image.
- Port `5432` can conflict with another local PostgreSQL instance and may need
  a different `POSTGRES_PORT`.
- The local PostgreSQL service is not a production database design and does not
  provide managed backups, high availability or production secret management.
- Changing an already-applied migration or seed requires a new file or an
  explicit reset of disposable local data.

### Risks and mitigations

- Risk: example passwords are reused outside local development.
  - Mitigation: label them local-only, keep `.env` ignored and require managed
    secrets plus rotated credentials in non-local environments.
- Risk: application SQL executes with owner privileges.
  - Mitigation: Compose overrides the application URL with the dedicated
    read-only role and migration credentials are only passed to `migrate`.
- Risk: a migration runs before PostgreSQL accepts connections.
  - Mitigation: `migrate` depends on the database health check and `app`
    depends on successful migration completion.
- Risk: local fixture data is mistaken for business truth.
  - Mitigation: keep fixtures under `data/seeds`, document their synthetic
    purpose and prohibit production data in the local environment.

## Confirmation

- `docker compose config --quiet` validates the Compose model.
- `docker compose up --build` starts a healthy database, completes `migrate`
  and then starts `app`.
- The migration history contains the expected migration and seed versions.
- The runtime role can select from
  `analytics.charging_session_analytics_v1` and cannot insert into an
  analytics table.
- Unit and API integration tests continue to pass.

## Revisit triggers

- A managed staging or production database is selected in ADR-0006;
- CI needs isolated ephemeral databases or parallel migration execution;
- migrations require rollback, locking or online schema-change features beyond
  the lightweight runner;
- PostgreSQL major-version support changes;
- local Supabase Auth, Storage or Realtime becomes necessary.

## Links

- [Superseded ADR-0012](0012-package-mvp-as-single-application-container.md)
- [Repository README](../../README.md)
- [Operations runbook](../operations/operations-runbook.md)
