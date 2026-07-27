/**
 * Corporate website message catalogs (AxelorMetal public site).
 *
 * Only short UI chrome — nav labels, button labels, footer — is translated.
 * Long-form editorial body copy stays English-only (realistic for a corporate
 * site and keeps the diff sane). All five locales expose the identical key set
 * so the catalog parity check in catalogs.test.ts stays green.
 */
type Catalog = Record<string, string>

const EN: Catalog = {
  'website.nav.home': 'Home',
  'website.nav.company': 'Company',
  'website.nav.products': 'Products & Markets',
  'website.nav.steelKnowledge': 'Steel Knowledge',
  'website.nav.contact': 'Contact',
  'website.hero.cta.discover': 'Discover AxelorMetal',
  'website.hero.cta.products': 'Explore our products',
  'website.footer.copyright': '© 2026 AxelorMetal S.A. All rights reserved.',
  'website.footer.disclaimer':
    'Synthetic demo — all data and content are fictitious and for demonstration purposes only.',
  'website.cta.learnMore': 'Learn more',
  'website.cta.getInTouch': 'Get in touch',
}

const FR: Catalog = {
  'website.nav.home': 'Accueil',
  'website.nav.company': 'Société',
  'website.nav.products': 'Produits & Marchés',
  'website.nav.steelKnowledge': "Connaissance de l'acier",
  'website.nav.contact': 'Contact',
  'website.hero.cta.discover': 'Découvrir AxelorMetal',
  'website.hero.cta.products': 'Explorer nos produits',
  'website.footer.copyright': '© 2026 AxelorMetal S.A. Tous droits réservés.',
  'website.footer.disclaimer':
    'Démo synthétique — toutes les données et contenus sont fictifs et à des fins de démonstration uniquement.',
  'website.cta.learnMore': 'En savoir plus',
  'website.cta.getInTouch': 'Nous contacter',
}

const DE: Catalog = {
  'website.nav.home': 'Startseite',
  'website.nav.company': 'Unternehmen',
  'website.nav.products': 'Produkte & Märkte',
  'website.nav.steelKnowledge': 'Stahlwissen',
  'website.nav.contact': 'Kontakt',
  'website.hero.cta.discover': 'AxelorMetal entdecken',
  'website.hero.cta.products': 'Unsere Produkte erkunden',
  'website.footer.copyright': '© 2026 AxelorMetal S.A. Alle Rechte vorbehalten.',
  'website.footer.disclaimer':
    'Synthetische Demo — alle Daten und Inhalte sind fiktiv und dienen nur Demonstrationszwecken.',
  'website.cta.learnMore': 'Mehr erfahren',
  'website.cta.getInTouch': 'Kontakt aufnehmen',
}

const NL: Catalog = {
  'website.nav.home': 'Home',
  'website.nav.company': 'Bedrijf',
  'website.nav.products': 'Producten & Markten',
  'website.nav.steelKnowledge': 'Staalkennis',
  'website.nav.contact': 'Contact',
  'website.hero.cta.discover': 'AxelorMetal ontdekken',
  'website.hero.cta.products': 'Onze producten verkennen',
  'website.footer.copyright': '© 2026 AxelorMetal S.A. Alle rechten voorbehouden.',
  'website.footer.disclaimer':
    'Synthetische demo — alle gegevens en inhoud zijn fictief en uitsluitend voor demonstratiedoeleinden.',
  'website.cta.learnMore': 'Meer informatie',
  'website.cta.getInTouch': 'Neem contact op',
}

const ES: Catalog = {
  'website.nav.home': 'Inicio',
  'website.nav.company': 'Empresa',
  'website.nav.products': 'Productos y Mercados',
  'website.nav.steelKnowledge': 'Conocimiento del acero',
  'website.nav.contact': 'Contacto',
  'website.hero.cta.discover': 'Descubrir AxelorMetal',
  'website.hero.cta.products': 'Explorar nuestros productos',
  'website.footer.copyright': '© 2026 AxelorMetal S.A. Todos los derechos reservados.',
  'website.footer.disclaimer':
    'Demo sintética — todos los datos y el contenido son ficticios y solo para fines de demostración.',
  'website.cta.learnMore': 'Saber más',
  'website.cta.getInTouch': 'Ponerse en contacto',
}

export const WEBSITE_CATALOGS: Record<string, Catalog> = { en: EN, fr: FR, de: DE, nl: NL, es: ES }
