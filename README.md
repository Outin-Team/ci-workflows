# Reusable Coolify CI/CD & Approval Gate Workflows

Generic GitHub Actions reusable workflows for Docker/GHCR build-and-gate pipelines paired with a centralized CI Hub:

- `.github/workflows/reusable-build-and-gate.yml` (Stage 1): builds immutable `sha-<7>` container images, collects GitHub PR/commit/diff context, and delegates summarization, optional auto-deploy, or manual approval card delivery to a centralized CI Hub.
- `.github/workflows/reusable-deploy-approved.yml` (Stage 2): promotes an approved `sha-<7>` image tag to `:latest` via `docker buildx imagetools create` (no rebuild) and notifies the CI Hub to trigger Coolify restart and update the approval card.

## Minimal Caller Secrets
- `CI_HUB_URL`
- `CI_HUB_TOKEN`
- `COOLIFY_SERVICE_UUID` (or pass `coolify_service_uuid_override` for monorepos)
