# NovaSteel v3 Knowledge Orchestrator production image.
#
# Self-contained service. Ships both src/ and fixtures/ — the BFF image
# copies fixtures via a named build context for demo data, and the
# orchestrator itself uses fixtures for offline/deterministic mode.
#
# Build:
#   docker buildx build -t novasteelv3/knowledge-orchestrator:<tag> --load services/knowledge-orchestrator
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
WORKDIR /app/services/knowledge-orchestrator
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application code and fixtures (used by both the service and the BFF image).
COPY src ./src
COPY fixtures ./fixtures

ENV PYTHONPATH=/app/services/knowledge-orchestrator/src \
    KNOWLEDGE_AGENT_MODE=local

# Run as an unprivileged user.
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app --no-create-home app \
    && chown -R app:app /app
USER app

EXPOSE 8080

# HEALTHCHECK uses only the standard library (no curl dependency).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import knowledge_orchestrator; print('ok')"]

CMD ["python", "-m", "knowledge_orchestrator"]
