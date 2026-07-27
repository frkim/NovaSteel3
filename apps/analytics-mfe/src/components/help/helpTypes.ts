/** One explanation, written for somebody with no steel-industry background. */
export interface HelpTopic {
  /** Short name of the thing, used when the element has no accessible name. */
  title: string
  /** Plain-language answer to "what am I looking at?". */
  what: string
  /**
   * Why the number or visual matters to a steel plant. This is the part that
   * teaches the process, not the software.
   */
  steel?: string
  /** What the reader can do with it on this screen. */
  useIt?: string
}

export type HelpCatalog = Record<string, HelpTopic>

/** What the pointer landed on, resolved from the DOM. */
export interface HelpTarget {
  /** The element that gets the selection frame. */
  element: HTMLElement
  /** Ordered topic ids to try, most specific first. */
  keys: string[]
  /**
   * Name taken from the page itself - a KPI label, a chart caption, a column
   * header. Always more specific than the catalog title, so it wins.
   */
  label?: string
  /** Extra sentence the page already shows, such as a chart summary. */
  detail?: string
}
