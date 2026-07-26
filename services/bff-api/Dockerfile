# NovaSteel v3 BFF (FastAPI) production image.
#
# The BFF resolves its sibling deterministic packages and demo fixtures with
# repo-relative paths (Path(__file__).resolve().parents[4]), so the image must
# reproduce the `services/` layout. Because those siblings live outside this
# folder, the image is built with BuildKit named build contexts:
#
#   Main build context : services/bff-api  (honours ./.dockerignore)
#   optimizer-worker   : services/optimizer-worker
#   scoring-worker     : services/scoring-worker
#   knowledge          : services/knowledge-orchestrator
#
# Build (see .azure/scripts/build-images.ps1 or .azure/docker/docker-bake.hcl):
#   docker buildx build `
#     --build-context optimizer-worker=../optimizer-worker `
#     --build-context scoring-worker=../scoring-worker `
#     --build-context knowledge=../knowledge-orchestrator `
#     -t novasteelv3/bff:<immutable-tag> --load services/bff-api
#
# Python/NuGet restores use ONLY the Microsoft protected feed with no public
# fallback (requirement); pip is pinned to packagefeedproxy.microsoft.io below.

ARG PYTHON_IMAGE=python:3.13-slim

FROM ${PYTHON_IMAGE} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=https://packagefeedproxy.microsoft.io/pypi/simple

# Protected feed only. Setting index-url (and no extra-index-url) removes the
# public PyPI fallback for every pip invocation in this image.
RUN printf '[global]\nindex-url = https://packagefeedproxy.microsoft.io/pypi/simple\ndisable-pip-version-check = true\n' > /etc/pip.conf

# Install the fully pinned dependency set before copying app code so the layer
# is cached across code-only changes.
WORKDIR /app/services/bff-api
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application code (from the main build context = services/bff-api).
COPY src ./src
COPY fixtures ./fixtures

# Sibling deterministic packages + knowledge fixtures (named build contexts).
# The BFF adds these src trees to sys.path at runtime; the knowledge speech
# adapter reads services/knowledge-orchestrator/fixtures at demo seed time.
COPY --from=optimizer-worker src /app/services/optimizer-worker/src
COPY --from=scoring-worker src /app/services/scoring-worker/src
COPY --from=knowledge src /app/services/knowledge-orchestrator/src
COPY --from=knowledge fixtures /app/services/knowledge-orchestrator/fixtures

# Deterministic cloud demo defaults. Container Apps overrides BFF_CORS_ORIGINS
# with the deployed portal origin and may set additional Azure env vars; demo
# mode stays enabled (DEMO_MODE=local) unless explicitly changed.
ENV PYTHONPATH=/app/services/bff-api/src \
    DEMO_MODE=local \
    BFF_ENVIRONMENT=demo \
    BFF_DATA_NAMESPACE=NS-DEMO-LUX-01 \
    BFF_AUTH_MODE=demo \
    BFF_CAPACITY_MODE=local \
    BFF_CORS_ORIGINS="http://localhost:5266,https://localhost:7075,http://localhost:5000,http://localhost:5173"

# Run as an unprivileged user.
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app --no-create-home app \
    && chown -R app:app /app
USER app

EXPOSE 8080

# Container Apps uses its own HTTP probes (/health/live, /health/ready); this
# HEALTHCHECK covers local `docker run` validation without adding a curl dep.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health/live', timeout=4).status==200 else 1)"]

CMD ["uvicorn", "bff_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
