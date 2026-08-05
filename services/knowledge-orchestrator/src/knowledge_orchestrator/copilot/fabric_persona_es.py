"""Spanish answers served for the Copilot's per-persona predefined questions.

Every figure below is synthetic demo data: it is the value already shown on the
matching screen, emitted by the device simulator, or recorded in the verified
July-2026 gold scorecard. Keep prose and numbers in sync with the fixture pack --
the whole point of these answers is that an operator can check them against the
screens.

Formatting note: the Copilot panel renders paragraphs, ``**bold**`` and
``_italic_`` only. Do not use tables, headings or code spans.
"""

from __future__ import annotations

from typing import Final

ANSWERS: Final[dict[str, str]] = {
    # -- plant-manager -------------------------------------------------------
    "persona-plant-manager-q1": """**No hay un KPI diario único a nivel de línea en este paquete demo.** El proxy en vivo más cercano es **LUX-RHF-01**, la línea de recalentamiento que más se aleja del plan durante la ventana de escasez.

- El rendimiento de planta es **128.4 t/h** frente a un objetivo de **130 t/h**, con OEE **84.1%** frente a 85%
- Entre **17:00 y 20:00** el perfil de recalentamiento cae a aproximadamente **114-122 t/h**
- Esa ventana coincide con el pico vespertino de **€280/MWh**, por lo que la caída es un desplazamiento de carga deliberado y no una parada no planificada
- La calidad aguas abajo aún requiere atención porque **COIL-LUX-260725-017** arrastra un sesgo de bobinado de **+11.4 °C**

Si quiere la línea más rezagada en términos operativos, priorice primero la ventana del horno de recalentamiento. La consecuencia es comercial, no catastrófica: está intercambiando una breve caída de rendimiento por energía más barata y una menor exposición de Alcance 2.""",
    "persona-plant-manager-q2": """**El paquete no contiene un registro de rendimiento etiquetado por cuadrilla para el turno de noche.** La evidencia más cercana apunta a una deriva local de calidad, no a una oscilación metalúrgica de toda la planta.

- El lote actual con FAIL es **COIL-LUX-260725-017** en **LUX-HSM-01**, con un sesgo de bobinado de **+11.4 °C**
- El límite elástico es **452.4 MPa** frente a una especificación de **380-520 MPa**, así que el acero sigue dentro de banda, pero el resultado de laboratorio está en **REVIEW**
- El SPC sitúa el subgrupo **20** en **11.4**, por encima del **8.5** del límite de control superior (LCS)
- En julio de 2026 hay **86 defectos**, y la deriva de temperatura de bobinado explica **34 (39.5%)**, por delante de grieta en borde 21 y cascarilla superficial 14

Empiece la mañana con el control de bobinado del tren de laminación en caliente, la disciplina de liberación de la bobina DP780 y la confirmación de que la deriva fue asignable y no sistémica. Esa es la causa de mayor probabilidad sobre la que puede actuar primero.""",
    "persona-plant-manager-q3": """**Empiece por el crisol, luego por el despacho y después por la deriva de calidad DP780.** Ese es el orden de triaje más limpio esta mañana.

- **1. Horno** - **ALERT-HEARTH-SECTOR-07-260725** es la única alerta crítica: riesgo **0.8995**, **P50 19.65 días**, revestimiento **363 mm** frente a un mínimo de **300 mm**
- **2. Energía** - **REC-DEMO-LUX-240725** sigue pendiente de aprobación y vale **€2,688.70** o **7.25%**, con la demanda máxima bajando de **56.0 MW** a **51.58 MW**
- **3. Calidad** - **COIL-LUX-260725-017** arrastra un sesgo de bobinado de **+11.4 °C** y la infracción SPC del subgrupo 20
- El estado del tablero es de **16 alertas abiertas**: **1 critical, 8 warning, 7 info, 2 acknowledged**

Ese orden protege primero la seguridad y la disponibilidad, captura en segundo lugar la mayor palanca controlable de coste y carbono de hoy, y después aborda el riesgo de calidad más visible de cara al cliente.""",
    "persona-plant-manager-q4": """**84.1%** ahora mismo, frente a un objetivo del **85%**.

- El rendimiento es **128.4 t/h** frente a **130 t/h**
- La entrega a tiempo es **96.4%** frente a 97%
- La intensidad energética es **€312/t** frente a **€300/t**
- El lastre visible del rendimiento se concentra en la ventana de escasez de **17:00-20:00**, donde la salida del recalentamiento funciona aproximadamente a **114-122 t/h**

Así que la planta está cerca del objetivo de OEE, pero no en él. La lectura importante es que la desviación se está comprando de forma controlada para evitar la electricidad a **€280/MWh**, no porque la línea haya caído en funcionamiento inestable. La consecuencia operativa es mantener explícita la compensación energética en lugar de tratarla como una pérdida oculta de rendimiento.""",
    # -- furnace-operator ----------------------------------------------------
    "persona-furnace-operator-q1": """**El perfil del crisol de BF-01 es asimétrico, no uniformemente caliente.** El punto a vigilar es **SECTOR-07**.

- **SECTOR-07** está subiendo a **3.4 °C/h** desde aproximadamente **652 °C**
- Los otros sectores solo se mueven alrededor de **0.4 °C/h**, así que el problema es la divergencia, no un desplazamiento de todo el crisol
- El flujo de calor local es **118 kW/m²**
- La refrigeración sigue pareciendo nominal a **198 m³/h** con un **ΔT del agua de 9.4 °C**
- La estimación del refractario cae de **372 mm** a **363 mm** en 24 horas

Esa combinación es la razón por la que el modelo pondera **heat_flux_6h_slope** en **29%**, **sector_to_ring_temp_delta** en **24%** y **cooling_efficiency_residual** en **18%**. La consecuencia es que debe tratar esto como una señal real de desgaste localizado, no como un calentamiento inocuo de todo el horno.""",
    "persona-furnace-operator-q2": """**La demo no incluye un sensor etiquetado T12-North.** La evidencia en vivo más cercana es la deriva de **TC-114** y la carcasa en **SECTOR-07** despegándose de sus sectores vecinos.

- **TC-114** deriva a **1.8 °C/h**
- **SECTOR-07** está subiendo a **3.4 °C/h** desde **652 °C**, mientras que los sectores vecinos se mantienen cerca de **0.4 °C/h**
- El flujo de calor ya es de **118 kW/m²**
- El agua de refrigeración sigue en **198 m³/h** con **ΔT 9.4 °C**, así que una explicación simple de pérdida de agua no encaja con el patrón

Así que la explicación mejor sustentada no es 'un único sensor norte defectuoso', sino un cambio térmico local auténtico que también es visible en la puntuación basada en física. La consecuencia operativa es verificar TC-114 frente a los termopares adyacentes, pero seguir actuando como si la señal del crisol fuera real hasta que esa comprobación la descarte.""",
    "persona-furnace-operator-q3": """**No hay una tabla en vivo de parámetros de vaciado en esta plataforma.** La evidencia gobernada más cercana es **PROC-DEMO-0002**, además del hecho de que la anomalía de hoy está en el comportamiento térmico del crisol y no en una ventana química de una colada vaciada.

- **PROC-DEMO-0002** es el procedimiento aprobado: estado **APPROVED**, versión **3**
- **PROC-DEMO-0001** sigue en **IN_REVIEW**, así que puede orientar comprobaciones, pero no debe tratarse como autoridad operativa
- El contexto actual es térmico: flujo de calor **118 kW/m²**, refrigeración **198 m³/h**, **ΔT 9.4 °C**, y el sector 07 subiendo a **3.4 °C/h**
- La cadena de proceso sigue siendo alto horno a acería a máquina de colada continua; nada en la evidencia dice que haya que improvisar la próxima colada

Así que no invente un ajuste de vaciado desde esta pantalla. La consecuencia es procedimental: ejecute primero los pasos aprobados de inspección y confirmación, y cambie la práctica de colada solo si una instrucción gobernada de BOF o de la máquina de colada continua se lo indica explícitamente.""",
    "persona-furnace-operator-q4": """**La plataforma no cuantifica una curva independiente de tasa de coque frente a desgaste.** Lo que sí muestra es que la señal de desgaste de hoy está dominada por el estrés térmico.

- El principal factor determinante del modelo es **heat_flux_6h_slope en 29%**
- El siguiente es **sector_to_ring_temp_delta en 24%**
- Después viene **cooling_efficiency_residual en 18%**
- El estado térmico en vivo detrás de eso es un flujo de calor de **118 kW/m²**, un caudal de refrigeración de **198 m³/h** y un **ΔT del agua de 9.4 °C**
- La estimación ya ha bajado a **363 mm** de espesor de revestimiento frente a un mínimo seguro de **300 mm**

Así que la respuesta honesta es que la tasa de coque puede importar como covariable, pero la puntuación actual no está siendo impulsada por una elasticidad de la tasa de coque demostrada. La consecuencia operativa es controlar lo que ahora está evidenciado directamente - carga térmica, desequilibrio sectorial y eficacia de la refrigeración - en lugar de perseguir una explicación solo de coque que no está respaldada.""",
    # -- maintenance-engineer ------------------------------------------------
    "persona-maintenance-engineer-q1": """**LUX-BF-01 / HEARTH-SECTOR-07** es claramente el mayor riesgo de esta semana.

- Puntuación de riesgo **0.8995** con **P50 19.65 días**, **P10 18.69**, **P90 20.61**
- Espesor estimado **363 mm** frente a un mínimo de **300 mm**
- La degradación avanza a aproximadamente **3.0 mm/día**
- El siguiente activo con nombre en el paquete, **LUX-RHF-01**, está solo en torno al **34%** de riesgo con aproximadamente **120 días** restantes
- La orden de trabajo **WO-DEMO-LUX-1042** ya existe para una inspección planificada

No hay un segundo puesto cercano dentro de la misma banda de urgencia. La consecuencia es asegurar primero la inspección y la ventana de planificación de reparación del revestimiento alrededor de BF-01; todo lo demás es trabajo de lista de vigilancia, no una intervención de esta semana.""",
    "persona-maintenance-engineer-q2": """**Porque la imagen térmica en vivo es más pronunciada que los episodios históricos de alerta.** El modelo está viendo una señal más rápida de deterioro local, no solo repitiendo la trayectoria media anterior.

- La estimación del refractario pasa de **372 mm** a **363 mm** en 24 horas
- **SECTOR-07** está subiendo a **3.4 °C/h** mientras los sectores vecinos se mantienen cerca de **0.4 °C/h**
- La puntuación sigue anclada por la misma pila de factores: **29%** pendiente de flujo de calor, **24%** delta sector-anillo, **18%** residual de eficiencia de refrigeración
- La refrigeración permanece nominal a **198 m³/h** y **ΔT 9.4 °C**, lo que hace más difícil descartar la divergencia del sector como ruido de instrumentación

Históricamente, los episodios de alerta de julio demuestran que el sistema puede sostener una reparación del revestimiento planificada con **21.0 días** de antelación. La caída de hoy a **P50 19.65 días** significa que la firma de desgaste actual ya está dentro de ese margen de confianza. La consecuencia es comprimir la planificación y la cadencia de inspección, no esperar a que el histórico la diluya.""",
    "persona-maintenance-engineer-q3": """**Programe ahora la secuencia de inspección de BF-01 y mantenga la ventana de reparación del revestimiento dentro de los días 18-24.** Ese es el plan gobernado respaldado por la evidencia actual.

- **WO-DEMO-LUX-1042** es el objeto de mantenimiento en vivo
- Días de inspección **1-4**: confirmar termopares, temperaturas de entrada y salida de la refrigeración y el histórico local
- Ultrasonidos y confirmación de espesor días **5-8**
- Ventana de reparación del revestimiento planificada **días 18-24**
- Las cifras de referencia son riesgo **0.8995**, **P50 19.65 días** y revestimiento **363 mm** frente a **300 mm** de mínimo

Use **PROC-DEMO-0002** como procedimiento operativo aprobado; **PROC-DEMO-0001** sigue en revisión y debe mantenerse como asesor. La consecuencia es que todavía tiene tiempo de convertir esto en una parada planificada, pero solo si la secuencia de inspección empieza de inmediato.""",
    "persona-maintenance-engineer-q4": """**P50 es 19.65 días; P90 es 20.61 días.** No son dos futuros distintos, sino dos puntos de confianza distintos sobre la misma distribución pronosticada de vida útil restante.

- **P10 18.69 días** - un límite inferior conservador
- **P50 19.65 días** - la estimación mediana, el valor que la mayoría usa para la planificación diaria
- **P90 20.61 días** - un límite superior optimista con más vida útil restante que la mediana
- La dispersión es estrecha: solo **0.96 días** de P50 a P90

Frente a un objetivo del programa de **21 días** de antelación, las tres cifras cuentan la misma historia: en la práctica ya está dentro de la ventana de actuación. La consecuencia operativa es planificar con P50, hacer pruebas de tensión con P10 y usar P90 solo para entender el potencial al alza - no para justificar esperar.""",
    # -- energy-manager ------------------------------------------------------
    "persona-energy-manager-q1": """**02:00-05:00** es la próxima ventana de bajo carbono incluida en la demo, ayudada por el bloque de PPA eólico de **12 MWh**.

- La ventana cara y más sucia es **17:00-20:00**, con precios de hasta **€280/MWh**
- La recomendación de despacho aparta el recalentamiento flexible de ese período de escasez
- Un movimiento visible es **REHEAT-BATCH-06** de la franja **75** a las **18:45** a la franja **67** a las **16:45**
- El impacto a nivel diario es de **€37,109.10** en línea base a **€34,420.40** optimizado, ahorrando **€2,688.70** o **7.25%**

Así que la próxima ventana limpia no es solo electricidad más barata; es la parte del día en la que el programa puede absorber carga sin pagar la prima de carbono del pico vespertino. La consecuencia es adelantar o retrasar la calefacción y la fusión flexibles, no dejarlas dentro de la banda de 17:00-20:00.""",
    "persona-energy-manager-q2": """**Porque las toneladas bajaron mientras la carga fija no lo hizo.** El pico de intensidad energética del último turno se explica mejor por el desplazamiento deliberado de carga de recalentamiento a través de la ventana de escasez.

- La intensidad energética es **€312/t** frente a un objetivo de **€300/t**
- El rendimiento es **128.4 t/h** frente a **130 t/h**, pero en la ventana de **17:00-20:00** cae a aproximadamente **114-122 t/h**
- Ahí es exactamente donde el precio spot alcanza el máximo de **€280/MWh**
- El despacho mantiene el tonelaje total sin cambios en **960 t**, así que el programa compra alivio de coste y carbono con una breve caída de cadencia

En otras palabras, el pico es un efecto aritmético de una menor producción instantánea frente a una carga de planta en gran medida fija, no una prueba de que la planta se haya vuelto de repente intrínsecamente ineficiente. La consecuencia operativa es juzgar €/t junto con el objetivo del despacho, no de forma aislada.""",
    "persona-energy-manager-q3": """**REC-DEMO-LUX-240725** es el mayor ahorro visible del paquete, y el movimiento clave es el lote de recalentamiento que abandona la franja de las 18:45.

- Línea base **€37,109.10** a optimizado **€34,420.40** - ahorro de **€2,688.70** o **7.25%**
- La demanda máxima baja de **56.0 MW** a **51.58 MW**
- **REHEAT-BATCH-06** pasa de la franja **75** a las **18:45** y **€280/MWh** a la franja **67** a las **16:45** y **€97.24/MWh**
- Ese único movimiento reduce el coste del lote de **€3,920.00** a **€1,361.36**
- En julio de 2026, se aceptaron **100 de 116** recomendaciones, adopción **0.862** frente a un objetivo de 0.70

Así que las oportunidades de mayor valor son las cargas térmicas flexibles que todavía tocan la banda de escasez. La consecuencia es aprobar el despacho rápidamente y seguir buscando movimientos de recalentamiento o fusión en la ventana vespertina con el mismo patrón.""",
    "persona-energy-manager-q4": """**La plataforma no incluye en esta tarjeta un what-if específico de horas valle para EAF.** La evidencia medida más cercana es el despacho ya modelado sobre carga térmica flexible.

- Ese despacho reduce CO₂ en **3.29%** con el tonelaje sin cambios
- El caso de optimización del plan completo en el resumen de sostenibilidad es **8.7%**
- El carbono de la red promedia aproximadamente **244 gCO₂/kWh**, así que mover carga a horas más limpias reduce el Alcance 2 sin cambiar la producción de acero
- El mismo despacho también reduce la demanda máxima de **56.0 MW** a **51.58 MW**

Así que no citaría una cifra independiente de coladas EAF que el paquete no demuestra. Lo que la plataforma sí demuestra es el mecanismo: el movimiento a horas valle recorta directamente las emisiones de electricidad comprada. La consecuencia operativa es tratar el desplazamiento de carga como una palanca real de Alcance 2 incluso cuando el rendimiento y el tonelaje se mantienen planos.""",
    # -- quality-engineer ----------------------------------------------------
    "persona-quality-engineer-q1": """**COIL-LUX-260725-017** es el único **FAIL** actual en el tablero en vivo de Luxemburgo, y es la primera que hay que apartar.

- Grado **NS-AUTO-DP780**
- Puntuación de riesgo **0.429**
- Sesgo de temperatura de bobinado **+11.4 °C**, la mayor desviación visible
- Límite elástico medido **452.4 MPa** frente a una especificación de **380-520 MPa**
- Estado de laboratorio **REVIEW**, y la alerta de calidad sigue reconocida pero abierta

La plataforma no muestra en esta pantalla una lista separada de fallos de 'solo superficie' para múltiples bobinas, así que esta es la respuesta veraz más cercana a una llamada por fallo en la comprobación de calidad. La consecuencia operativa es poner esta bobina en cuarentena o revisarla antes de liberarla, y después rastrear la deriva hacia atrás por recalentamiento y bobinado en lugar de asumir un problema general de laboratorio.""",
    "persona-quality-engineer-q2": """**No existe un activo llamado Line 3 en el modelo demo.** La evidencia de línea real más cercana es **LUX-HSM-01**, y la deriva está liderada por la temperatura de bobinado más que por un cambio amplio del mix de producto.

- Julio de 2026 registra **86 defectos** en alcance
- **34 defectos (39.5%)** son deriva de temperatura de bobinado, por delante de grieta en borde **21**, cascarilla superficial **14**, variación de espesor **9**, recubrimiento **5** y otros **3**
- El punto actual de causa especial es el subgrupo **20** en **11.4**, por encima del **8.5** del LCS
- La bobina afectada es **COIL-LUX-260725-017** con un sesgo de **+11.4 °C** en **LUX-HSM-01**

Así que la tendencia no se interpreta mejor como 'Line 3 está empeorando'; se interpreta mejor como un modo de fallo dominante en la ruta de laminación en caliente. La consecuencia operativa es estabilizar primero el control de bobinado, porque es ahí donde apuntan tanto la infracción en vivo como la mezcla mensual de defectos.""",
    "persona-quality-engineer-q3": """**La plataforma no puntúa la segregación central como un KPI propio.** La evidencia real más cercana está en las entradas de la máquina de colada continua y en la genealogía detrás de la bobina afectada.

- Las variables en vivo de la máquina de colada continua disponibles para este tipo de triaje son **superheat**, **casting_speed** y **secondary_cooling_flow** en **LUX-CC-01**
- La genealogía está completa: **LOT-FE-017 → H-LUX-260725-0040 → LADLE-017 → SLAB-017 → REHEAT-017 → COIL-LUX-260725-017 → SMP-017 → SHIP-DEMO-017**
- El límite elástico medido de la bobina es **452.4 MPa**, todavía dentro de la banda de **380-520 MPa**, con estado de laboratorio **REVIEW**

Así que usaría el trío de la máquina de colada continua como conjunto de correlación y mantendría abierta la genealogía a través del recalentamiento y el bobinado. La consecuencia operativa es investigar el riesgo tipo segregación como un problema de ruta que abarca la práctica térmica de la máquina de colada continua y el recalentamiento aguas abajo, no como un número aislado de laboratorio que aparece de la nada.""",
    "persona-quality-engineer-q4": """**El SPC de esta pantalla no es directamente de espesor; es de sesgo de temperatura de bobinado.** Aun así, lo que le dice es importante desde el punto de vista operativo.

- Media **1.9**, sigma **2.2**, límite de control superior (LCS) **8.5**, límite de control inferior (LCI) **-4.7**
- El subgrupo **20** marca **11.4**, así que está fuera de control por el lado alto
- La capacidad del proceso Cpk es **1.18** frente a un objetivo de **1.33**
- El mismo valor **11.4** coincide con el sesgo de bobinado en **COIL-LUX-260725-017**

Así que el SPC le está diciendo que hay una causa especial reciente en el manejo térmico, no que todo el centro de proceso haya derivado gradualmente. La consecuencia es investigar primero la causa asignable de la temperatura de bobinado; solo después de eso debería inferir algo sobre el comportamiento del espesor a partir de la misma corrida de producción.""",
    # -- sustainability-officer ---------------------------------------------
    "persona-sustainability-officer-q1": """**En su mayor parte sí, pero el trimestre ya no va sobrado.** El uso de derechos de emisión ya es del **71%**, y el margen ha bajado al **6.2%**.

- El precio actual del derecho de emisión es **€86/t**
- La previsión de exposición es de aproximadamente **€248,000** en el punto operativo actual
- La intensidad actual del escenario operativo es **1.42 tCO₂e/t** frente a un objetivo de **1.35**
- La alerta activa del libro de registros para esto es **ALERT-ETS-ALLOWANCE-Q3**
- El julio de 2026 ya cerrado sigue viéndose sólido en **1.019 tCO₂e/t** frente a un objetivo de **1.638** y una línea base de **2.10**

Así que el programa va según lo previsto en el cuadro histórico de indicadores, pero el colchón del trimestre actual es fino. La consecuencia operativa es seguir usando ahora el desplazamiento de carga y otras palancas de corto plazo, porque unos pocos días operativos débiles consumirían rápidamente el 6.2% de margen restante.""",
    "persona-sustainability-officer-q2": """**La plataforma no incluye una columna de exposición específica de CBAM.** El proxy demostrado más cercano es la exposición ETS más la intensidad actual de Alcance 1.

- La carga de Alcance 1 de hoy es de **1,368 t CO₂e/day** para **960 t** de acero, o aproximadamente **1,425 kg/t**
- Un aumento lineal del **10%** de producción con la intensidad sin cambios añadiría aproximadamente **136.8 t CO₂e/day**
- El uso de derechos de emisión ya es del **71%**, con una previsión de exposición de **€248,000** y un margen del **6.2%**
- La intensidad operativa actual se sitúa en **1.42 tCO₂e/t** frente a un objetivo de **1.35**

Así que no reclamaría una cifra de factura CBAM que el paquete de datos no contiene. Lo que sí dice la evidencia es que un incremento del 10% en el tonelaje aumentaría materialmente la exposición con precio al carbono salvo que la intensidad mejore al mismo tiempo. La consecuencia operativa es acompañar cualquier aumento de producción con una acción de eficiencia o de despacho, no dejar que suban las toneladas con un perfil de emisiones sin cambios.""",
    "persona-sustainability-officer-q3": """**1.42 tCO₂e/t** en el escenario operativo actual.

- Esa es la cifra en vivo del día, no la media mensual ya cerrada
- Está por encima del objetivo de **1.35** para el modo operativo actual
- En el último mes cerrado, julio de 2026, la planta quedó en **1.019 tCO₂e/t**
- Ese resultado de julio superó ampliamente el objetivo de **1.638** y la línea base de **2.10**
- El reparto por alcance de julio es **355,336 t** de Alcance 1 y **147,868 t** de Alcance 2

Así que su intensidad actual es peor que el cierre mensual de referencia, aunque la tendencia del programa siga por delante del objetivo. La consecuencia operativa es leer el valor 1.42 como una señal de corrección en vivo - especialmente en torno a la carga térmica y al momento de la electricidad - no como una razón para dudar del libro de cierre mensual.""",
    "persona-sustainability-officer-q4": """**Frente al benchmark, el programa va por delante en el mes y por detrás en el día en vivo.** Ambas cosas son ciertas a la vez.

- Escenario actual: **1.42 tCO₂e/t** frente a un objetivo de **1.35**, es decir, alrededor de **0.07 tCO₂e/t** por encima
- Julio de 2026 ya cerrado: **1.019 tCO₂e/t** frente a un objetivo de **1.638** y una línea base de **2.10**
- Contexto del trimestre actual: uso de derechos de emisión **71%**, margen **6.2%**, exposición prevista **€248,000** a **€86/t**
- El despacho sigue siendo la palanca más rápida, reduciendo CO₂ en **3.29%** en el programa demostrado

Así que, comparado con el benchmark, el sistema gana en el libro histórico pero está bajo presión en la ventana operativa actual. La consecuencia operativa es seguir presentando juntas ambas cifras: la puntuación mensual demuestra que el programa funciona, mientras que la cifra en vivo le dice que hoy aún necesita intervención activa.""",
    # -- knowledge-engineer --------------------------------------------------
    "persona-knowledge-engineer-q1": """**El paquete de fixtures no almacena la frecuencia de consulta del glosario por término.** La evidencia real más cercana es la demanda y la cobertura por dominio de conocimiento.

- Cobertura del alto horno **82%**
- Laboratorio de calidad **77%**
- Tren de laminación en caliente **71%**
- Horno de recalentamiento **64%**
- Energía y utilities **58%**
- Los estados de los procedimientos se reparten entre **PROC-DEMO-0001 IN_REVIEW v2**, **PROC-DEMO-0002 APPROVED v3** y **PROC-DEMO-0003 DRAFT v1**

Así que no puedo nombrar con veracidad el término de glosario más consultado de este paquete. Lo que sí puedo decir es que los dominios con menor cobertura son los puntos de presión más probables para las consultas, especialmente energía y recalentamiento. La consecuencia operativa es mejorar primero la captura y la aprobación ahí, porque es donde es más probable que se acumulen preguntas sin soporte.""",
    "persona-knowledge-engineer-q2": """**Cita las fuentes que son a la vez relevantes y gobernables, no solo cualquier texto que se haya recuperado.** En esta plataforma la cadena de evidencia es deliberadamente auditable.

- El libro de registros de decisión muestra **AUD-0001** a **AUD-0005**, y los cinco tienen **complete_audit_flag true**
- Los procedimientos no son iguales: **PROC-DEMO-0002** es **APPROVED v3**, mientras que **PROC-DEMO-0001** es **IN_REVIEW v2** y **PROC-DEMO-0003** es **DRAFT v1**
- Para las preguntas predefinidas por persona, el Copilot usa tarjetas fijas de Fabric, por lo que los conjuntos de datos citados son deterministas y no improvisados

Así que el sistema prefiere conocimiento aprobado y cadenas de auditoría completas frente a texto meramente disponible. La consecuencia operativa es que una fuente aparentemente útil pero no aprobada debe seguir quedándose fuera de la respuesta final si no puede cumplir el mismo estándar de gobernanza que la evidencia aprobada o auditada.""",
    "persona-knowledge-engineer-q3": """**La arquitectura de fundamentación está estratificada y es deliberadamente estrecha.** La evidencia real más cercana es la combinación de procedimientos gobernados, hechos de Fabric y la ruta de ontología que enlaza activos a través de la ruta del proceso.

- Capa de texto gobernado: **PROC-DEMO-0002 APPROVED v3**, con **PROC-DEMO-0001 IN_REVIEW v2** y **PROC-DEMO-0003 DRAFT v1** todavía fuera del mismo nivel de confianza
- Capa analítica: hechos gold de Fabric para el histórico de KPI y vistas KQL activas para el estado en vivo
- Capa estructural: la ontología puede trazar rutas como **LUX-BF-01** hacia delante a través de la cadena siderúrgica hasta **LUX-HSM-01**
- Capa de decisión: **AUD-0001..AUD-0005**, todos con **complete_audit_flag true**

Así que la plataforma fundamenta las respuestas en un pequeño número de rutas de recuperación explícitas en lugar de en síntesis libre. La consecuencia operativa es la previsibilidad: puede inspeccionar qué nivel de datos, estado de procedimiento o ruta de grafo respaldó la respuesta, en lugar de confiar en un resumen de caja negra.""",
    "persona-knowledge-engineer-q4": """**La plataforma no expone en Fabric una tabla dedicada de 'prompt-injection score'.** La evidencia operativa más cercana es que ya aplica fundamentación basada exclusivamente en procedimientos aprobados, registros completos de auditoría y revisión humana antes de actuar.

- Las cinco filas de auditoría **AUD-0001** a **AUD-0005** están completas
- Solo **PROC-DEMO-0002** está aprobado para uso operativo directo; **PROC-DEMO-0001** y **PROC-DEMO-0003** quedan por debajo de ese listón
- Recomendaciones como **REC-DEMO-LUX-240725** permanecen pendientes de aprobación humana en lugar de comprometerse automáticamente

Así que las salvaguardas reales que puede demostrar a partir de los datos son límites de gobernanza, trazabilidad y control humano en el bucle. La consecuencia operativa es importante: aunque se recuperara texto no confiable, seguiría sin tener una vía directa para aprobar un programa, alterar una acción de control o borrar el rastro de auditoría.""",
    # -- ot-systems-engineer -------------------------------------------------
    "persona-ot-systems-engineer-q1": """**Ninguno está materialmente retrasado o ausente en este momento.** El parque en vivo está sano según las medidas que la plataforma realmente incorpora.

- **17 dispositivos** y **91 señales** están en línea
- La frescura de las señales está por debajo de **5 s** para los feeds rápidos en vivo
- La frescura de extremo a extremo es de aproximadamente **12 s**
- Los incidentes activos son **0**
- El umbral de alerta de cuarentena es del **2% por 15 minutes**, y aquí no hay evidencia de que se haya superado ese umbral

Lo único que hay que recordar es que no se espera que todas las señales se actualicen con la misma cadencia: **hearth_refractory_estimate** es una señal de **900,000 ms** por diseño, no un feed retrasado de 5 segundos. La consecuencia operativa es que ahora no necesita triaje de feeds; necesita preservar la ruta sana mientras trabaja por separado las alertas de proceso.""",
    "persona-ot-systems-engineer-q2": """**5,000 ms** para las señales rápidas del crisol, con una frescura global de la plataforma de aproximadamente **12 s** de extremo a extremo.

- **hearth_shell_temperature** publica cada **5,000 ms**
- **local_heat_flux** publica cada **5,000 ms**
- **hearth_refractory_estimate** es deliberadamente más lenta a **900,000 ms**
- El parque sigue sano en conjunto: **17 dispositivos**, **91 señales**, **0 incidentes**
- La deriva de **TC-114** a **1.8 °C/h** es un problema de señal térmica, no una prueba de latencia de red

Así que la red de sensores del horno no es el cuello de botella. La consecuencia operativa es separar la latencia de la ruta de datos del comportamiento del proceso: los feeds de 5 segundos llegan a tiempo, así que la tendencia anómala del crisol debe tratarse como una condición de planta y no como un artefacto de transporte.""",
    "persona-ot-systems-engineer-q3": """**La plataforma no proporciona un asistente dentro del producto para aprovisionar tags PLC.** El objeto con mayor autoridad más cercano es el contrato del evento de telemetría que la pasarela debe publicar.

- El sobre incluye **source_id**, **asset_id**, **plant_id**, **sequence**, **schema_name** y **schema_version**
- El nombre del esquema de telemetría es **novasteel.telemetry.v1**
- Un buen source id tiene este aspecto: **LUX-BF-01-TC-H07-03**, para que la identidad del activo y de la señal siga siendo explícita a través de la pasarela
- Los tags rápidos deben alinearse con la cadencia correcta, como **5,000 ms** para la temperatura de carcasa del crisol, mientras que las estimaciones más lentas pueden ir a **900,000 ms**
- Las cargas mal formadas están pensadas para caer en cuarentena en lugar de deslizarse sin ser vistas hacia silver

Así que configurar aquí una nueva etiqueta PLC significa mapearla limpiamente al sobre publicado y al registro de señales, no editar una tabla de analítica oculta. La consecuencia operativa es que la conformidad con el contrato importa tanto como la propia etiqueta, porque una forma incorrecta será rechazada a propósito.""",
    "persona-ot-systems-engineer-q4": """**El protocolo de cable no se almacena en Fabric.** Lo que la plataforma demuestra es el patrón mediado por pasarela que hay por encima.

- El parque en vivo muestra **17 dispositivos** y **91 señales** con **0 incidentes**
- Los eventos llegan como sobres versionados con source ids como **LUX-BF-01-TC-H07-03**
- La salud se mide a través del estado de conexión de la pasarela, la frescura y el comportamiento de la cola, no mediante una columna de protocolo
- La frescura de extremo a extremo es de aproximadamente **12 s**, y las señales térmicas rápidas siguen publicando cada **5,000 ms**

Así que no fingiría que la capa analítica puede decirle si la matriz térmica es Modbus, Profinet o cualquier otra cosa. La respuesta veraz más cercana es que el protocolo está abstraído detrás del patrón de pasarela de planta, y la evidencia que tiene aquí es que el puente está lo bastante sano como para entregar la telemetría del horno a tiempo. La consecuencia operativa es buscar los detalles del protocolo en el registro OT, no en los hechos de Fabric.""",
}
