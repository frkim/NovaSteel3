/**
 * Cross-component dock commands.
 *
 * KPI tiles drill down by calling `revealPanel(id)`, which historically scrolled
 * the target card into view. Inside a dock a target panel is often on a
 * background tab, where scrolling does nothing, so the dock registers a
 * resolver here and the call becomes "activate that tab". The scroll path stays
 * as the fallback for screens that are not docked.
 */

type RevealHandler = (panelId: string) => boolean

const revealHandlers = new Set<RevealHandler>()
const resetHandlers = new Set<() => void>()

export function registerDockReveal(handler: RevealHandler): () => void {
  revealHandlers.add(handler)
  return () => {
    revealHandlers.delete(handler)
  }
}

/** Returns true when a mounted dock owns and activated the panel. */
export function revealDockPanel(panelId: string): boolean {
  for (const handler of revealHandlers) {
    if (handler(panelId)) {
      return true
    }
  }
  return false
}

export function registerDockReset(handler: () => void): () => void {
  resetHandlers.add(handler)
  notifyPresence()
  return () => {
    resetHandlers.delete(handler)
    notifyPresence()
  }
}

/** Discards persisted arrangements and restores every dock to its defaults. */
export function resetDockLayouts(): void {
  for (const handler of [...resetHandlers]) {
    handler()
  }
}

export function hasDockLayouts(): boolean {
  return resetHandlers.size > 0
}

const presenceListeners = new Set<() => void>()

function notifyPresence(): void {
  for (const listener of [...presenceListeners]) {
    listener()
  }
}

/**
 * Lets the dashboard chrome hide dock-only controls on screens that render no
 * dock at all — the corporate website page, for instance.
 */
export function subscribeDockPresence(listener: () => void): () => void {
  presenceListeners.add(listener)
  return () => {
    presenceListeners.delete(listener)
  }
}
