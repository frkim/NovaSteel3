// Placeholder runtime configuration. In a container this file is overwritten on
// startup by runtime/inject-config.sh with the deployed BFF origin. Locally it
// stays empty so src/config.ts falls through to VITE_BFF_BASE_URL (or demo mode).
window.NOVASTEEL_CAPTURE_CONFIG = window.NOVASTEEL_CAPTURE_CONFIG || {};
