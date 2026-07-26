# NovaSteel v3 portal image: Blazor WebAssembly shell + React/MUI/D3 analytics
# microfrontend, published as one static artifact and served (SPA fallback) on
# port 8080.
#
# The React MFE is a member of the repo npm workspace and Vite emits it into the
# Blazor wwwroot (apps/portal-shell/wwwroot/analytics-mfe). The Blazor publish
# then packages that bundle. Because the workspace root files and the MFE live
# outside this folder, the image is built with BuildKit named build contexts:
#
#   Main build context : apps/portal-shell  (honours ./.dockerignore)
#   analytics-mfe      : apps/analytics-mfe
#   contracts          : contracts (shared UI design tokens imported by the MFE)
#   reporoot           : repository root (package.json, package-lock.json,
#                        .npmrc, NuGet.Config)
#
# NuGet restores use ONLY the Microsoft protected feed (NuGet.Config clears
# sources); no public nuget.org fallback.

ARG NODE_IMAGE=node:22-bookworm-slim
ARG DOTNET_SDK_IMAGE=mcr.microsoft.com/dotnet/sdk:10.0
ARG NGINX_IMAGE=nginx:1.27-alpine

# ---- Stage 1: build the React analytics MFE into the Blazor wwwroot ----------
FROM ${NODE_IMAGE} AS mfe
WORKDIR /src
# Workspace manifests first so `npm ci` layer caches across source-only changes.
COPY --from=reporoot package.json package-lock.json .npmrc ./
COPY --from=analytics-mfe package.json ./apps/analytics-mfe/package.json
RUN npm ci
# MFE sources, then build. Vite outDir = ../portal-shell/wwwroot/analytics-mfe.
COPY --from=analytics-mfe . ./apps/analytics-mfe
# Shared UI contracts imported by the MFE (design-tokens.v1.json).
COPY --from=contracts . ./contracts
# Optional build-time BFF URL. The shell still injects the runtime value via the
# bridge context (appsettings.json Bff:BaseUrl), which takes precedence, so this
# defaults to empty and same-origin/runtime resolution is used.
ARG VITE_BFF_BASE_URL=""
ENV VITE_BFF_BASE_URL=${VITE_BFF_BASE_URL}
RUN npm run build:analytics

# ---- Stage 2: publish the Blazor WebAssembly portal --------------------------
FROM ${DOTNET_SDK_IMAGE} AS publish
WORKDIR /src
COPY --from=reporoot NuGet.Config ./NuGet.Config
COPY . ./apps/portal-shell
# Overlay the freshly built MFE bundle (authoritative over any committed copy).
COPY --from=mfe /src/apps/portal-shell/wwwroot/analytics-mfe ./apps/portal-shell/wwwroot/analytics-mfe
RUN dotnet restore apps/portal-shell/PortalShell.csproj --configfile NuGet.Config
RUN dotnet publish apps/portal-shell/PortalShell.csproj \
        -c Release \
        -o /app/publish \
        --no-restore

# ---- Stage 3: static runtime (nginx) on 8080 with SPA fallback ---------------
FROM ${NGINX_IMAGE} AS runtime
# Portal runtime server config + runtime BFF-URL injection.
COPY runtime/nginx.conf /etc/nginx/nginx.conf
COPY runtime/inject-bff-url.sh /docker-entrypoint.d/20-novasteel-inject-bff-url.sh
COPY --from=publish /app/publish/wwwroot /usr/share/nginx/html
# Normalise CRLF -> LF (in case of a Windows checkout) and make executable.
RUN sed -i 's/\r$//' /docker-entrypoint.d/20-novasteel-inject-bff-url.sh \
    && chmod +x /docker-entrypoint.d/20-novasteel-inject-bff-url.sh

EXPOSE 8080
STOPSIGNAL SIGQUIT

# The stock nginx entrypoint runs /docker-entrypoint.d/*.sh (our BFF-URL
# injection) and then execs nginx with the config above.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["sh", "-c", "wget -q -O /dev/null http://localhost:8080/healthz || exit 1"]
