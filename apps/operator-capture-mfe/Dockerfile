# NovaSteel v3 Operator Capture PWA: React/MUI/Vite installable web app that
# records shop-floor procedures by voice and files them into the Knowledge Hub.
# Published as a static bundle and served (SPA fallback) on port 8080.
#
# This app is a member of the repo npm workspace and imports the shared UI design
# tokens from `contracts/`, so the workspace root files and the contracts tree
# live outside this folder. The image is therefore built with BuildKit named
# build contexts (same convention as apps/portal-shell/Dockerfile):
#
#   Main build context : apps/operator-capture-mfe  (honours ./.dockerignore)
#   contracts          : contracts (design-tokens.v1.json imported by the app)
#   reporoot           : repository root (package.json, package-lock.json, .npmrc)
#
# npm installs resolve ONLY through the Microsoft protected feed configured in
# the repo-root .npmrc; no public registry fallback.

ARG NODE_IMAGE=node:22-bookworm-slim
ARG NGINX_IMAGE=nginx:1.27-alpine

# ---- Stage 1: build the PWA bundle ------------------------------------------
FROM ${NODE_IMAGE} AS build
WORKDIR /src
# Workspace manifests first so `npm ci` layer caches across source-only changes.
COPY --from=reporoot package.json package-lock.json .npmrc ./
COPY package.json ./apps/operator-capture-mfe/package.json
RUN npm ci --workspace @novasteel/operator-capture-mfe --include-workspace-root
# Shared UI contracts imported by the app (design-tokens.v1.json).
COPY --from=contracts . ./contracts
# App sources, then build. Vite outDir = apps/operator-capture-mfe/dist.
COPY . ./apps/operator-capture-mfe
# The deployed BFF origin is injected at container start (runtime/inject-config.sh)
# so one image can be promoted across environments. This build-time value stays
# empty, which makes the app fall back to same-origin/demo resolution locally.
ARG VITE_BFF_BASE_URL=""
ENV VITE_BFF_BASE_URL=${VITE_BFF_BASE_URL}
RUN npm run build --workspace @novasteel/operator-capture-mfe

# ---- Stage 2: static runtime (nginx) on 8080 with SPA fallback ---------------
FROM ${NGINX_IMAGE} AS runtime
COPY runtime/nginx.conf /etc/nginx/nginx.conf
COPY runtime/inject-config.sh /docker-entrypoint.d/20-novasteel-inject-config.sh
COPY --from=build /src/apps/operator-capture-mfe/dist /usr/share/nginx/html
# Normalise CRLF -> LF (in case of a Windows checkout) and make executable.
RUN sed -i 's/\r$//' /docker-entrypoint.d/20-novasteel-inject-config.sh \
    && chmod +x /docker-entrypoint.d/20-novasteel-inject-config.sh

EXPOSE 8080
STOPSIGNAL SIGQUIT

# The stock nginx entrypoint runs /docker-entrypoint.d/*.sh (our runtime config
# injection) and then execs nginx with the config above.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["sh", "-c", "wget -q -O /dev/null http://localhost:8080/healthz || exit 1"]
