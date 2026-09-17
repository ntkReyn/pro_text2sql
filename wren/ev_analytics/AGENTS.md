# EV Analytics Wren Project

This project uses Wren MDL schema version 5. The YAML files under `models/`,
`views/`, `cubes/`, and `relationships.yml` are the semantic source of truth;
`target/mdl.json` is generated output.

## Query contract

- Write SQL against logical Wren model names, never against physical
  `analytics.*` tables or views.
- Respect each model's documented grain and column descriptions.
- Do not invent relationships between the denormalized marts. The empty
  `relationships.yml` is intentional until a grain/cardinality review approves
  a join.
- Treat `knowledge/rules/` as business guidance that must be applied together
  with the MDL.
- Treat `knowledge/sql/*.md` as curated NL-to-SQL memory source files. Store a
  pair only after a user confirms the answer or an approved curation step; do
  not store failed, exploratory, or unverified SQL.
- When no database is connected, use `wren dry-plan` only; do not claim that a
  result was executed or verified against data.

## Runtime contract

- `dry_plan` expands logical model SQL through Wren without a database.
- `dry_run` expands and asks the connected Wren connector to validate the SQL
  without returning rows; it is disabled until execution and database settings
  are explicitly enabled.
- Cube queries must use the structured CubeQuery contract and Wren core
  translation; do not hand-write cube `GROUP BY` or time-granularity SQL.

## Change lifecycle

After changing MDL source files, run:

```text
wren context validate --path wren/ev_analytics
wren context build --path wren/ev_analytics
```

Review the generated plan for representative queries before enabling execution.
