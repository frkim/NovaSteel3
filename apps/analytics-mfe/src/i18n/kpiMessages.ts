/**
 * KPI tile message catalogs.
 *
 * Status labels are shared by every KPI card so semantic colour is paired with
 * a text cue for assistive technology and hover/tooltips.
 */
type Catalog = Record<string, string>

const EN: Catalog = {
  'kpi.status.ok': 'OK',
  'kpi.status.warning': 'At risk',
  'kpi.status.critical': 'Alert',
  'kpi.status.neutral': 'Not available',
  'kpi.status.aria': 'status: {status}',
}

const FR: Catalog = {
  'kpi.status.ok': 'OK',
  'kpi.status.warning': '\u00c0 risque',
  'kpi.status.critical': 'Alerte',
  'kpi.status.neutral': 'Non disponible',
  'kpi.status.aria': 'statut\u00a0: {status}',
}

const DE: Catalog = {
  'kpi.status.ok': 'OK',
  'kpi.status.warning': 'Gef\u00e4hrdet',
  'kpi.status.critical': 'Alarm',
  'kpi.status.neutral': 'Nicht verf\u00fcgbar',
  'kpi.status.aria': 'Status: {status}',
}

const NL: Catalog = {
  'kpi.status.ok': 'OK',
  'kpi.status.warning': 'Risico',
  'kpi.status.critical': 'Alarm',
  'kpi.status.neutral': 'Niet beschikbaar',
  'kpi.status.aria': 'status: {status}',
}

const ES: Catalog = {
  'kpi.status.ok': 'Correcto',
  'kpi.status.warning': 'En riesgo',
  'kpi.status.critical': 'Alerta',
  'kpi.status.neutral': 'No disponible',
  'kpi.status.aria': 'estado: {status}',
}

export const KPI_CATALOGS: Record<string, Catalog> = { en: EN, fr: FR, de: DE, nl: NL, es: ES }
