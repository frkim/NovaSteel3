#!/bin/sh
# Runtime injection of the deployed BFF base URL into the Operator Capture PWA.
# Container Apps passes CAPTURE_BFF_BASE_URL (or BFF_BASE_URL). index.html loads
# /config.js before the app bundle, and src/config.ts reads the resulting
# window.NOVASTEEL_CAPTURE_CONFIG global ahead of any build-time value. Writing
# it here (instead of baking it in) keeps one image promotable across
# environments. Runs from the stock nginx /docker-entrypoint.d before nginx starts.
set -eu

CONFIG_JS="/usr/share/nginx/html/config.js"
BFF_URL="${CAPTURE_BFF_BASE_URL:-${BFF_BASE_URL:-}}"
# The BFF rejects demo identities whose plant claim is not an NS-DEMO-* value.
DEMO_PLANT="${CAPTURE_DEMO_PLANT:-NS-DEMO-LUX-01}"

# Normalise: drop any trailing slash so the SPA builds clean request URLs.
BFF_URL="${BFF_URL%/}"

if [ -z "$BFF_URL" ]; then
    # No backend wired up: run the synthetic demo experience rather than firing
    # requests at our own static origin, which would only ever 404.
    cat > "$CONFIG_JS" <<EOF
window.NOVASTEEL_CAPTURE_CONFIG = { bffBaseUrl: '', demoMode: true, plant: '${DEMO_PLANT}' };
EOF
    echo "[novasteel] No CAPTURE_BFF_BASE_URL/BFF_BASE_URL set; capture PWA starts in demo mode."
    exit 0
fi

cat > "$CONFIG_JS" <<EOF
window.NOVASTEEL_CAPTURE_CONFIG = { bffBaseUrl: '${BFF_URL}', demoMode: false, plant: '${DEMO_PLANT}' };
EOF
echo "[novasteel] Injected BFF base URL into capture PWA config.js: ${BFF_URL}"
