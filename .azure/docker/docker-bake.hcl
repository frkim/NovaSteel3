# Declarative build definition for the NovaSteel v3 application images.
#
# Run from the repository root:
#   docker buildx bake -f .azure/docker/docker-bake.hcl                 # both (local --load)
#   docker buildx bake -f .azure/docker/docker-bake.hcl bff             # a single target
#   TAG=1.2.3 REGISTRY=novasteelv3acrXXXX.azurecr.io `
#     docker buildx bake -f .azure/docker/docker-bake.hcl --push        # tag + push
#
# Both apps depend on sibling source trees, supplied here as BuildKit named
# contexts. The main context stays the app folder so each app's own
# .dockerignore is honoured.
#
# The "reporoot" context supplies the npm workspace root files (package.json,
# package-lock.json, .npmrc) and NuGet.Config. It defaults to the repository
# root; build-images.ps1 overrides REPOROOT_CONTEXT with a minimal staged
# directory so the large root node_modules is never transferred.
#
# pip and NuGet restores resolve ONLY from the Microsoft protected feeds (no
# public fallback) as enforced by the Dockerfiles, pip.conf and NuGet.Config.

variable "TAG" { default = "local" }
variable "REGISTRY" { default = "" }
variable "REPO_NS" { default = "novasteelv3" }
variable "VITE_BFF_BASE_URL" { default = "" }
variable "REPOROOT_CONTEXT" { default = "." }

function "ref" {
  params = [name]
  result = REGISTRY == "" ? "${REPO_NS}/${name}:${TAG}" : "${REGISTRY}/${REPO_NS}/${name}:${TAG}"
}

group "default" {
  targets = ["bff", "portal", "capture"]
}

target "bff" {
  context    = "services/bff-api"
  dockerfile = "Dockerfile"
  contexts = {
    optimizer-worker = "services/optimizer-worker"
    scoring-worker   = "services/scoring-worker"
    knowledge        = "services/knowledge-orchestrator"
    device-simulator = "services/device-simulator"
  }
  tags      = [ref("bff")]
  platforms = ["linux/amd64"]
}

target "portal" {
  context    = "apps/portal-shell"
  dockerfile = "Dockerfile"
  contexts = {
    analytics-mfe = "apps/analytics-mfe"
    contracts     = "contracts"
    reporoot      = REPOROOT_CONTEXT
  }
  args = {
    VITE_BFF_BASE_URL = VITE_BFF_BASE_URL
  }
  tags      = [ref("portal")]
  platforms = ["linux/amd64"]
}

# Standalone installable PWA for shop-floor operators (voice procedure capture).
# The BFF origin is injected at container start, so no build arg is needed here.
target "capture" {
  context    = "apps/operator-capture-mfe"
  dockerfile = "Dockerfile"
  contexts = {
    contracts = "contracts"
    reporoot  = REPOROOT_CONTEXT
  }
  tags      = [ref("capture")]
  platforms = ["linux/amd64"]
}
