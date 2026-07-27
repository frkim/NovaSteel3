import type { HelpCatalog } from '../components/help/helpTypes'

/**
 * Help topics for the illustrated process diagrams on the AxelorMetal
 * corporate website.
 *
 * Kept in a satellite file rather than inline in the five `helpMessages.*`
 * catalogs so that a whole-file rewrite of any locale catalog cannot silently
 * drop these entries. Spread into `HELP_CATALOGS` in `helpCatalogs.ts`.
 */
export const HELP_DIAGRAM: Record<string, HelpCatalog> = {
  en: {
    'website.processDiagram': {
      title: 'Steelmaking diagram',
      what: 'An illustrated map of how raw materials become finished steel products, stage by stage.',
      steel:
        'Steel is not made in one machine. It is a chain of steps — melt the metal, remove what should not be in it, cast it into a solid shape, then roll it thinner. Each numbered stage on the picture is one of those steps, in the order it happens.',
      useIt:
        'Click the picture to enlarge it, then use the zoom buttons to read the small labels. The stages shown here are the same ones the operating screens of this portal monitor.',
    },
  },
  fr: {
    'website.processDiagram': {
      title: 'Sch\u00e9ma de fabrication de l\u2019acier',
      what: 'Une carte illustr\u00e9e de la transformation des mati\u00e8res premi\u00e8res en produits finis en acier, \u00e9tape par \u00e9tape.',
      steel:
        'L\u2019acier ne se fabrique pas dans une seule machine. C\u2019est une cha\u00eene d\u2019\u00e9tapes : fondre le m\u00e9tal, en retirer ce qui ne doit pas s\u2019y trouver, le couler en une forme solide, puis le laminer plus fin. Chaque \u00e9tape num\u00e9rot\u00e9e de l\u2019image correspond \u00e0 l\u2019une de ces op\u00e9rations, dans l\u2019ordre o\u00f9 elle se produit.',
      useIt:
        'Cliquez sur l\u2019image pour l\u2019agrandir, puis utilisez les boutons de zoom pour lire les petites \u00e9tiquettes. Les \u00e9tapes montr\u00e9es ici sont celles que surveillent les \u00e9crans d\u2019exploitation de ce portail.',
    },
  },
  de: {
    'website.processDiagram': {
      title: 'Schema der Stahlherstellung',
      what: 'Eine bebilderte \u00dcbersicht, wie aus Rohstoffen Schritt f\u00fcr Schritt fertige Stahlprodukte werden.',
      steel:
        'Stahl entsteht nicht in einer einzigen Maschine. Es ist eine Kette von Schritten: das Metall schmelzen, unerw\u00fcnschte Bestandteile entfernen, es zu einer festen Form gie\u00dfen und anschlie\u00dfend d\u00fcnner walzen. Jede nummerierte Stufe im Bild ist einer dieser Schritte, in der Reihenfolge des Ablaufs.',
      useIt:
        'Klicken Sie auf das Bild, um es zu vergr\u00f6\u00dfern, und lesen Sie die kleinen Beschriftungen mit den Zoom-Schaltfl\u00e4chen. Die hier gezeigten Stufen sind dieselben, die die Betriebsbildschirme dieses Portals \u00fcberwachen.',
    },
  },
  nl: {
    'website.processDiagram': {
      title: 'Schema van de staalproductie',
      what: 'Een ge\u00efllustreerd overzicht van hoe grondstoffen stap voor stap afgewerkte staalproducten worden.',
      steel:
        'Staal wordt niet in \u00e9\u00e9n machine gemaakt. Het is een keten van stappen: het metaal smelten, verwijderen wat er niet in hoort, het tot een vaste vorm gieten en het daarna dunner walsen. Elke genummerde fase op de afbeelding is een van die stappen, in de volgorde waarin ze plaatsvindt.',
      useIt:
        'Klik op de afbeelding om ze te vergroten en gebruik de zoomknoppen om de kleine labels te lezen. De hier getoonde fasen zijn dezelfde die de bedieningsschermen van dit portaal bewaken.',
    },
  },
  es: {
    'website.processDiagram': {
      title: 'Esquema de fabricaci\u00f3n del acero',
      what: 'Un mapa ilustrado de c\u00f3mo las materias primas se convierten en productos de acero acabados, etapa por etapa.',
      steel:
        'El acero no se fabrica en una sola m\u00e1quina. Es una cadena de pasos: fundir el metal, retirar lo que no debe contener, colarlo en una forma s\u00f3lida y despu\u00e9s laminarlo m\u00e1s fino. Cada etapa numerada de la imagen es uno de esos pasos, en el orden en que ocurre.',
      useIt:
        'Haga clic en la imagen para ampliarla y use los botones de zoom para leer las etiquetas peque\u00f1as. Las etapas que se muestran aqu\u00ed son las mismas que vigilan las pantallas de explotaci\u00f3n de este portal.',
    },
  },
}
