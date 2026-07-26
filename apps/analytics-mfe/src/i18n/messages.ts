export type TranslateFn = (key: string, params?: Record<string, string | number>) => string

type Catalog = Record<string, string>

/**
 * Minimal shared message catalog. Keys mirror the Blazor shell catalog so both
 * surfaces stay consistent (UX §18). Locales cover LU/DE/BE/ES operations:
 * English, French, German, Dutch, Spanish. Unknown keys fall back to English
 * and then to the raw key, so partial translations degrade gracefully.
 */
const EN: Catalog = {
  'app.synthetic': 'Synthetic demo data — not for operational control',
  'state.loading': 'Loading…',
  'state.empty.title': 'Nothing to show',
  'state.empty.filters': 'No rows match the current filters.',
  'state.empty.reset': 'Clear filters',
  'state.error.title': 'Something went wrong',
  'state.error.retry': 'Retry',
  'state.stale': 'Data as of {time} — refreshing',
  'source.fixture': 'Cached offline data',
  'source.bff': 'Live BFF data',
  'kpi.why': 'Why?',
  'kpi.target': 'target {value}',
  'kpi.asOf': 'as of {time}',
  'kpi.confidence': 'Confidence',
  'table.search': 'Search all columns',
  'table.columnSearch': 'Search {column}',
  'table.export': 'Export CSV',
  'table.columns': 'Columns',
  'table.density': 'Density',
  'table.refresh': 'Refresh',
  'table.rows': 'Rows {from}–{to} of {total}',
  'table.page': 'Page {page}',
  'table.viewAsTable': 'View as table',
  'table.viewAsChart': 'View as chart',
  'table.clearFilters': 'Clear filters',
  'table.noExport': 'This view is not exportable.',
  'chart.summary': 'Chart summary',
  'nav.commandCenter': 'Command Center',
  'capacity.request.start': 'Request start',
  'capacity.request.pause': 'Request pause',
  'demo.badge': 'DEMO',
  'demo.tour.start': 'Start guided demo',
  'demo.tour.stop': 'Stop guided demo',
  'demo.tour.next': 'Next',
  'demo.tour.prev': 'Back',
  'demo.tour.auto': 'Auto-advance',
}

const FR: Catalog = {
  'app.synthetic': 'Données de démonstration synthétiques — pas pour le contrôle opérationnel',
  'state.loading': 'Chargement…',
  'state.empty.title': 'Rien à afficher',
  'state.empty.filters': 'Aucune ligne ne correspond aux filtres actuels.',
  'state.empty.reset': 'Effacer les filtres',
  'state.error.title': 'Une erreur est survenue',
  'state.error.retry': 'Réessayer',
  'state.stale': 'Données au {time} — actualisation',
  'source.fixture': 'Données hors ligne en cache',
  'source.bff': 'Données BFF en direct',
  'kpi.why': 'Pourquoi ?',
  'kpi.target': 'objectif {value}',
  'kpi.asOf': 'au {time}',
  'kpi.confidence': 'Confiance',
  'table.search': 'Rechercher dans toutes les colonnes',
  'table.columnSearch': 'Rechercher {column}',
  'table.export': 'Exporter CSV',
  'table.columns': 'Colonnes',
  'table.density': 'Densité',
  'table.refresh': 'Actualiser',
  'table.rows': 'Lignes {from}–{to} sur {total}',
  'table.page': 'Page {page}',
  'table.viewAsTable': 'Voir en tableau',
  'table.viewAsChart': 'Voir en graphique',
  'table.clearFilters': 'Effacer les filtres',
  'table.noExport': 'Cette vue n’est pas exportable.',
  'chart.summary': 'Résumé du graphique',
  'nav.commandCenter': 'Centre de commande',
  'capacity.request.start': 'Demander le démarrage',
  'capacity.request.pause': 'Demander la pause',
  'demo.badge': 'DÉMO',
  'demo.tour.start': 'Démarrer la visite guidée',
  'demo.tour.stop': 'Arrêter la visite guidée',
  'demo.tour.next': 'Suivant',
  'demo.tour.prev': 'Retour',
  'demo.tour.auto': 'Avance automatique',
}

const DE: Catalog = {
  'app.synthetic': 'Synthetische Demodaten — nicht für die Betriebssteuerung',
  'state.loading': 'Wird geladen…',
  'state.empty.title': 'Nichts anzuzeigen',
  'state.empty.filters': 'Keine Zeilen entsprechen den aktuellen Filtern.',
  'state.empty.reset': 'Filter löschen',
  'state.error.title': 'Etwas ist schiefgelaufen',
  'state.error.retry': 'Erneut versuchen',
  'state.stale': 'Daten vom {time} — wird aktualisiert',
  'source.fixture': 'Zwischengespeicherte Offline-Daten',
  'source.bff': 'Live-BFF-Daten',
  'kpi.why': 'Warum?',
  'kpi.target': 'Ziel {value}',
  'kpi.asOf': 'Stand {time}',
  'kpi.confidence': 'Konfidenz',
  'table.search': 'Alle Spalten durchsuchen',
  'table.columnSearch': '{column} durchsuchen',
  'table.export': 'CSV exportieren',
  'table.columns': 'Spalten',
  'table.density': 'Dichte',
  'table.refresh': 'Aktualisieren',
  'table.rows': 'Zeilen {from}–{to} von {total}',
  'table.page': 'Seite {page}',
  'table.viewAsTable': 'Als Tabelle anzeigen',
  'table.viewAsChart': 'Als Diagramm anzeigen',
  'table.clearFilters': 'Filter löschen',
  'table.noExport': 'Diese Ansicht ist nicht exportierbar.',
  'chart.summary': 'Diagrammzusammenfassung',
  'nav.commandCenter': 'Kommandozentrale',
  'capacity.request.start': 'Start anfordern',
  'capacity.request.pause': 'Pause anfordern',
  'demo.badge': 'DEMO',
  'demo.tour.start': 'Geführte Demo starten',
  'demo.tour.stop': 'Geführte Demo beenden',
  'demo.tour.next': 'Weiter',
  'demo.tour.prev': 'Zurück',
  'demo.tour.auto': 'Automatisch weiter',
}

const NL: Catalog = {
  'app.synthetic': 'Synthetische demogegevens — niet voor operationele besturing',
  'state.loading': 'Laden…',
  'state.empty.title': 'Niets om te tonen',
  'state.empty.filters': 'Geen rijen komen overeen met de huidige filters.',
  'state.empty.reset': 'Filters wissen',
  'state.error.title': 'Er is iets misgegaan',
  'state.error.retry': 'Opnieuw',
  'state.stale': 'Gegevens van {time} — vernieuwen',
  'source.fixture': 'Gecachte offline gegevens',
  'source.bff': 'Live BFF-gegevens',
  'kpi.why': 'Waarom?',
  'kpi.target': 'doel {value}',
  'kpi.asOf': 'per {time}',
  'kpi.confidence': 'Betrouwbaarheid',
  'table.search': 'Alle kolommen doorzoeken',
  'table.columnSearch': '{column} doorzoeken',
  'table.export': 'CSV exporteren',
  'table.columns': 'Kolommen',
  'table.density': 'Dichtheid',
  'table.refresh': 'Vernieuwen',
  'table.rows': 'Rijen {from}–{to} van {total}',
  'table.page': 'Pagina {page}',
  'table.viewAsTable': 'Als tabel weergeven',
  'table.viewAsChart': 'Als grafiek weergeven',
  'table.clearFilters': 'Filters wissen',
  'table.noExport': 'Deze weergave kan niet worden geëxporteerd.',
  'chart.summary': 'Grafiekoverzicht',
  'nav.commandCenter': 'Commandocentrum',
  'capacity.request.start': 'Start aanvragen',
  'capacity.request.pause': 'Pauze aanvragen',
  'demo.badge': 'DEMO',
  'demo.tour.start': 'Begeleide demo starten',
  'demo.tour.stop': 'Begeleide demo stoppen',
  'demo.tour.next': 'Volgende',
  'demo.tour.prev': 'Terug',
  'demo.tour.auto': 'Automatisch verdergaan',
}

const ES: Catalog = {
  'app.synthetic': 'Datos de demostración sintéticos — no para control operativo',
  'state.loading': 'Cargando…',
  'state.empty.title': 'Nada que mostrar',
  'state.empty.filters': 'Ninguna fila coincide con los filtros actuales.',
  'state.empty.reset': 'Borrar filtros',
  'state.error.title': 'Algo salió mal',
  'state.error.retry': 'Reintentar',
  'state.stale': 'Datos a las {time} — actualizando',
  'source.fixture': 'Datos sin conexión en caché',
  'source.bff': 'Datos en vivo del BFF',
  'kpi.why': '¿Por qué?',
  'kpi.target': 'objetivo {value}',
  'kpi.asOf': 'a las {time}',
  'kpi.confidence': 'Confianza',
  'table.search': 'Buscar en todas las columnas',
  'table.columnSearch': 'Buscar {column}',
  'table.export': 'Exportar CSV',
  'table.columns': 'Columnas',
  'table.density': 'Densidad',
  'table.refresh': 'Actualizar',
  'table.rows': 'Filas {from}–{to} de {total}',
  'table.page': 'Página {page}',
  'table.viewAsTable': 'Ver como tabla',
  'table.viewAsChart': 'Ver como gráfico',
  'table.clearFilters': 'Borrar filtros',
  'table.noExport': 'Esta vista no se puede exportar.',
  'chart.summary': 'Resumen del gráfico',
  'nav.commandCenter': 'Centro de mando',
  'capacity.request.start': 'Solicitar inicio',
  'capacity.request.pause': 'Solicitar pausa',
  'demo.badge': 'DEMO',
  'demo.tour.start': 'Iniciar demo guiada',
  'demo.tour.stop': 'Detener demo guiada',
  'demo.tour.next': 'Siguiente',
  'demo.tour.prev': 'Atrás',
  'demo.tour.auto': 'Avance automático',
}

const CATALOGS: Record<string, Catalog> = {
  en: EN,
  fr: FR,
  de: DE,
  nl: NL,
  es: ES,
}

export const SUPPORTED_LANGUAGES = ['en', 'fr', 'de', 'nl', 'es'] as const

export function languageOf(locale: string): string {
  const language = (locale || 'en').slice(0, 2).toLowerCase()
  return language in CATALOGS ? language : 'en'
}

function interpolate(template: string, params?: Record<string, string | number>): string {
  if (!params) {
    return template
  }
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match,
  )
}

export function createTranslator(locale: string): TranslateFn {
  const language = languageOf(locale)
  const catalog = CATALOGS[language]
  return (key, params) => {
    const template = catalog[key] ?? EN[key] ?? key
    return interpolate(template, params)
  }
}
