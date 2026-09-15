# ADR-0012: Package the MVP as a single application container

- Status: Superseded
- Date: 2026-09-14
- Decision makers: Repository owner
- Technical owner: Project team
- Consulted: None
- Informed: Project team
- Supersedes: None
- Superseded by: [ADR-0014](0014-run-local-mvp-with-postgresql.md)

## Context and problem statement

The MVP repository is organized into web, API, worker, and shared package boundaries, but currently only has a minimal API runtime. The deployment needs one reproducible Docker unit while Supabase and OpenAI remain managed external services. Vietnamese embedding and reranker model artifacts are stored in the host Hugging Face cache and total more than 4 GB when complete.

The decision must keep local development simple, avoid copying credentials into image layers, and avoid rebuilding a multi-gigabyte image whenever model weights or application code change.

## Decision drivers

- One-command local startup;
- no secrets in the build context or image;
- reuse of existing CPU model weights;
- small and replaceable application image;
- clear path from scaffold to MVP without introducing an orchestrator.

## Considered options

1. One application container with a read-only host model-cache mount.
2. One fully self-contained image containing application code and model weights.
3. Separate API, web, worker, and model-serving containers.

## Evidence

- The current host has CPU-only PyTorch and no available CUDA device.
- Complete embedding and reranker model artifacts total more than 4 GB; the initially observed reranker cache was incomplete.
- Supabase and OpenAI are external dependencies and do not require local containers.
- Docker excludes files matched by `.dockerignore` from the build context, and Compose supports runtime environment files and bind mounts.

## Decision outcome

Chosen option: **one application container with a read-only host model-cache mount**.

The image contains the repository, Python runtime, CPU PyTorch, API dependencies and the deployable API entrypoint. Compose defines exactly one service. The host Hugging Face directory is mounted at `/opt/huggingface`; Supabase and OpenAI credentials are injected at runtime through the ignored `.env` file.

The web and worker module boundaries remain in the repository. They are not started as extra services until their runtime behavior and independent scaling requirements exist.

## Consequences

### Positive

- Application rebuilds do not copy the model weights.
- A single container is sufficient for the current MVP runtime.
- The same model cache can be reused by host development and Docker.
- Secrets remain outside image layers.

### Negative

- The container is not fully portable without providing the model-cache mount.
- CPU inference can increase request latency.
- Combining future web, API and worker execution into one process may stop being appropriate as the product grows.

### Risks and mitigations

- Risk: the host cache path is missing or not shared with Docker Desktop.
  - Mitigation: fail Compose interpolation when `HF_CACHE_HOST_PATH` is absent and expose cache checks through `/health/ready`.
- Risk: a credential is accidentally copied into the image.
  - Mitigation: exclude `.env*` except examples through `.dockerignore` and inject `.env` only at runtime.
- Risk: local model inference exhausts memory.
  - Mitigation: load models once, precompute catalog embeddings, and rerank only a bounded candidate set.

## Confirmation

- `docker compose config` parses successfully without exposing runtime values in logs.
- The image builds on a working Docker daemon.
- `/health/live` returns `200`.
- `/health/ready` reports Supabase, OpenAI and both model caches independently.
- Image history and exported filesystem do not contain `.env`.

## Revisit triggers

- Web or worker requires independent availability or scaling;
- GPU inference is introduced;
- deployment platform cannot provide a host bind mount;
- model startup time or image portability becomes a release blocker;
- production secrets move to a dedicated secret manager.

## Links

- [System architecture](../architecture/system-architecture.md)
- [Operations runbook](../operations/operations-runbook.md)
- [Repository README](../../README.md)
