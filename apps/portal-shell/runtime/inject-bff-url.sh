#!/bin/sh
# Runtime injection of the deployed BFF base URL into the Blazor WebAssembly
# configuration. Container Apps passes PORTAL_BFF_BASE_URL (and/or BFF_BASE_URL).
# The Blazor shell reads Bff:BaseUrl from appsettings.json and forwards it to the
# React analytics MFE through the bridge context, so this single rewrite wires
# both the shell HttpClient and the microfrontend. Runs from the stock nginx
# /docker-entrypoint.d before nginx starts.
set -eu

APPSETTINGS="/usr/share/nginx/html/appsettings.json"
BFF_URL="${PORTAL_BFF_BASE_URL:-${BFF_BASE_URL:-}}"

if [ -z "$BFF_URL" ]; then
    echo "[novasteel] No PORTAL_BFF_BASE_URL/BFF_BASE_URL set; keeping appsettings default."
    exit 0
fi

if [ ! -f "$APPSETTINGS" ]; then
    echo "[novasteel] WARNING: $APPSETTINGS not found; cannot inject BFF URL." >&2
    exit 0
fi

# Normalise: drop any trailing slash so the SPA builds clean request URLs.
BFF_URL="${BFF_URL%/}"

tmp="${APPSETTINGS}.tmp"
sed -E "s#(\"BaseUrl\"[[:space:]]*:[[:space:]]*\")[^\"]*(\")#\1${BFF_URL}\2#" "$APPSETTINGS" > "$tmp"
mv -f "$tmp" "$APPSETTINGS"
echo "[novasteel] Injected BFF base URL into appsettings.json: ${BFF_URL}"
