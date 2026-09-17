# Analytics engine

`wren_workflow.py` implements the Wren-first query path: load MDL and
`knowledge/`, recall relevant Memory, ask the LLM for SQL written against
logical Wren models, run Wren `dry_plan`, validate the expanded SQL, and
optionally execute it through Wren's connector with a bounded response.

The module has a bounded repair loop and never gives the LLM direct database
execution authority. `wren_runtime.py` is the native Wren adapter for
`dry_plan`, `dry_run`, CubeQuery translation and optional execution;
`wren_memory.py` keeps `knowledge/sql/*.md` as source of truth and falls back
to dependency-free grep when the optional Wren memory extra is absent.
