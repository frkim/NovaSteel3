import type { HelpTarget } from './helpTypes'

const MAX_WALK = 24
const MAX_LABEL = 90

function text(node: Element | null | undefined): string | undefined {
  const raw = node?.textContent?.replace(/\s+/g, ' ').trim()
  if (!raw) return undefined
  return raw.length > MAX_LABEL ? `${raw.slice(0, MAX_LABEL - 1)}\u2026` : raw
}

function attr(el: Element, name: string): string | undefined {
  const value = el.getAttribute(name)
  return value && value.trim() ? value.trim() : undefined
}

/** Prefer a name the page already shows over anything the catalog invents. */
function labelOf(el: Element): string | undefined {
  return (
    attr(el, 'data-help-label') ??
    attr(el, 'aria-label') ??
    text(el.querySelector('figcaption, h1, h2, h3, h4, h5, h6, [data-help-label-source]'))
  )
}

/**
 * Table cells sit inside a table that carries its own `data-help`, so the cell
 * has to win even though the table attribute is closer to the document root.
 */
function structuralKeys(el: Element): { keys: string[]; label?: string } | null {
  const tag = el.tagName.toLowerCase()
  if (el.classList.contains('dv-tab') || el.getAttribute('role') === 'tab') {
    return { keys: ['generic.dockTab'], label: text(el) }
  }
  if (tag === 'th') {
    return { keys: ['generic.tableHeader'], label: text(el) }
  }
  if (tag === 'tr' && el.closest('tbody')) {
    return { keys: ['generic.tableRow'], label: text(el.querySelector('th, td')) }
  }
  return null
}

/** Last-resort shapes, used only when nothing declared a topic. */
function looseKeys(el: Element): { keys: string[]; label?: string } | null {
  const tag = el.tagName.toLowerCase()
  if (tag === 'table') return { keys: ['generic.table'], label: labelOf(el) }
  if (tag === 'figure') return { keys: ['generic.chart'], label: labelOf(el) }
  if (tag === 'article') return { keys: ['generic.kpi'], label: labelOf(el) }
  if (tag === 'button' || el.getAttribute('role') === 'button') {
    return { keys: ['generic.button'], label: attr(el, 'aria-label') ?? text(el) }
  }
  if (el.hasAttribute('data-dock-panel')) {
    return { keys: ['generic.panel'], label: attr(el, 'data-dock-title') }
  }
  return null
}

/**
 * Turns the element under the pointer into an ordered list of catalog keys.
 *
 * `scope` is the current `section/subView`, which lets one metric id such as
 * `peak` mean furnace shell temperature on one screen and grid demand on
 * another without renaming anything in the screens.
 */
export function resolveHelpTarget(from: Element | null, scope?: string): HelpTarget | null {
  let node: Element | null = from
  let declared: { element: HTMLElement; keys: string[]; label?: string; detail?: string } | null = null
  let structural: { element: HTMLElement; keys: string[]; label?: string } | null = null
  let loose: { element: HTMLElement; keys: string[]; label?: string } | null = null

  for (let depth = 0; node && depth < MAX_WALK; depth += 1, node = node.parentElement) {
    if (!(node instanceof HTMLElement) && !(node instanceof SVGElement)) continue
    const element = (node instanceof SVGElement ? node.closest('div, section, article, figure') : node) as
      | HTMLElement
      | null
    if (!element) continue

    if (!structural) {
      const match = structuralKeys(node)
      if (match) structural = { element, ...match }
    }
    if (!declared) {
      const topic = attr(node, 'data-help')
      if (topic) {
        declared = {
          element,
          keys: scope ? [`${scope}:${topic}`, topic] : [topic],
          label: labelOf(node),
          detail: attr(node, 'data-help-detail'),
        }
      }
    }
    if (!loose) {
      const match = looseKeys(node)
      if (match) loose = { element, ...match }
    }
  }

  if (structural) {
    // Keep the declared topic as a fallback so a row inside a known table can
    // still borrow that table's explanation when no row topic is written.
    const keys = declared ? [...structural.keys, ...declared.keys] : structural.keys
    return { ...structural, keys }
  }
  if (declared) return declared
  if (loose) return loose
  return null
}

/** First key that the catalog actually knows about. */
export function pickHelpKey(keys: string[], catalog: Record<string, unknown>): string | undefined {
  return keys.find((key) => key in catalog)
}
