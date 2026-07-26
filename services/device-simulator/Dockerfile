# NovaSteel v3 device-simulator production image.
#
# Self-contained service. The BFF image may copy the src/ tree for direct
# library import (same pattern as optimizer-worker, scoring-worker, knowledge).
#
# Build:
#   docker buildx build -t novasteelv3/device-simulator:<tag> --load services/device-simulator
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
WORKDIR /app/services/device-simulator
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY src ./src

ENV PYTHONPATH=/app/services/device-simulator/src \
    DEVICE_SIMULATOR_MODE=local

# Run as an unprivileged user.
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app --no-create-home app \
    && chown -R app:app /app
USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import device_simulator; print('ok')"]

CMD ["uvicorn", "device_simulator.app:app", "--host", "0.0.0.0", "--port", "8080"]
