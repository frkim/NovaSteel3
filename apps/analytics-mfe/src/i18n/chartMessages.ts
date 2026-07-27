import type { Catalog } from './messages'

/**
 * Chart chrome strings that live outside the core catalog so a chart-level
 * change touches one file instead of five interleaved locale blocks.
 * `chart.zoomLevel` carries a `{level}` placeholder in every locale.
 */
export const CHART_CATALOGS: Record<string, Catalog> = {
  en: {
    'chart.zoomIn': 'Zoom in',
    'chart.zoomOut': 'Zoom out',
    'chart.zoomReset': 'Reset zoom to 100%',
    'chart.zoomLevel': 'Zoom level {level}%',
  },
  fr: {
    'chart.zoomIn': 'Agrandir',
    'chart.zoomOut': 'R\u00e9duire',
    'chart.zoomReset': 'R\u00e9tablir le zoom \u00e0 100 %',
    'chart.zoomLevel': 'Niveau de zoom {level} %',
  },
  de: {
    'chart.zoomIn': 'Vergr\u00f6\u00dfern',
    'chart.zoomOut': 'Verkleinern',
    'chart.zoomReset': 'Zoom auf 100 % zur\u00fccksetzen',
    'chart.zoomLevel': 'Zoomstufe {level} %',
  },
  nl: {
    'chart.zoomIn': 'Inzoomen',
    'chart.zoomOut': 'Uitzoomen',
    'chart.zoomReset': 'Zoom terugzetten naar 100%',
    'chart.zoomLevel': 'Zoomniveau {level}%',
  },
  es: {
    'chart.zoomIn': 'Acercar',
    'chart.zoomOut': 'Alejar',
    'chart.zoomReset': 'Restablecer el zoom al 100 %',
    'chart.zoomLevel': 'Nivel de zoom {level} %',
  },
}
