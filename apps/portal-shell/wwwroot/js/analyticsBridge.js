const mounted = new Map();
const bridgeVersion = "1.0";

function resolvedTheme(themeMode) {
  if (themeMode === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  return themeMode;
}

function renderFallback(host, error) {
  const message = document.createElement("div");
  message.setAttribute("role", "alert");
  message.className = "analytics-fallback";
  message.textContent = "Analytics bundle is unavailable. Run the root build to generate it.";
  host.replaceChildren(message);
  console.error("NovaSteel analytics bridge failed to mount.", error);
}

export async function mount(elementId, context, dotNetReference) {
  const host = document.getElementById(elementId);
  if (!host) {
    return;
  }

  document.documentElement.dataset.theme = resolvedTheme(context.themeMode);
  if (context.bridgeVersion !== bridgeVersion) {
    renderFallback(host, new Error(`Unsupported bridge version: ${context.bridgeVersion}`));
    return;
  }

  try {
    const module = await import("/analytics-mfe/analytics-mfe.js");
    const instance = module.mountAnalyticsMicrofrontend(host, context, (eventType, payload) =>
      dotNetReference.invokeMethodAsync("ReceiveEvent", eventType, payload));
    mounted.set(elementId, { instance, dotNetReference });
  } catch (error) {
    renderFallback(host, error);
  }
}

export function update(context) {
  document.documentElement.dataset.theme = resolvedTheme(context.themeMode);
  for (const entry of mounted.values()) {
    entry.instance.update(context);
  }
}

export function dispose(elementId) {
  const entry = mounted.get(elementId);
  if (!entry) {
    return;
  }

  entry.instance.unmount();
  mounted.delete(elementId);
}
