"""Spanish answers served for the Copilot's predefined questions.

Translated from ``fabric_answers_en``: numbers, identifiers, table names and
model versions are byte-identical to the English pack; only the prose differs.

Formatting note: the Copilot panel renders paragraphs, ``**bold**`` and
``_italic_`` only. Do not use tables, headings or code spans.
"""

from __future__ import annotations

from typing import Final

ANSWERS: Final[dict[str, str]] = {
    # -- command-center ----------------------------------------------------
    "command-center-q1": """**ALERT-HEARTH-SECTOR-07-260725** es la alerta prioritaria: es la única alerta CRITICAL abierta y la única con una reparación del revestimiento asociada.

- Activo **LUX-BF-01**, componente **HEARTH-SECTOR-07**, planta NS-DEMO-LUX-01
- Vida útil restante **P50 19.65 días**, puntuación de riesgo **0.90**, confianza del modelo 0.78
- Emitida a las **17:58**, sigue OPEN

Hay dieciséis alertas abiertas en las cuatro plantas: **1 critical, 8 warning, 7 info, 2 acknowledged**. El resto son avisos o de menor gravedad - el pico de precio vespertino de €280/MWh, la desviación de bobinado DP780 en COIL-LUX-260725-017 y el margen ETS del Q3 al 6.2%.

La orden de trabajo **WO-DEMO-LUX-1042** ya está redactada para el crisol, por lo que la decisión pendiente es la ventana de inspección, no el diagnóstico.""",
    "command-center-q2": """Hay cuatro acciones siguientes en cola, una por dominio.

- **Horno** - programar la inspección del crisol BF-01. Riesgo 0.90, RUL P50 19.65 días, orden de trabajo WO-DEMO-LUX-1042 emitida a las 18:00.
- **Energía** - aprobar el desplazamiento de carga de 17:00 a 20:00. El panel muestra una banda de ahorro modelado de aproximadamente €4.2k; el plan de despacho energético comprometido REC-DEMO-LUX-240725 alcanza **€2,688.70 (7.25%)** con la demanda máxima reduciéndose de 56.0 a 51.58 MW.
- **Calidad** - revisar la desviación NS-AUTO-DP780 en COIL-LUX-260725-017: sesgo de bobinado **+11.4 °C**, riesgo 0.429, estado FAIL.
- **ETS** - el margen de derechos de emisión del Q3 ha bajado al **6.2%**, con el 71% de los derechos utilizados a €86/t.

La acción de mayor impacto que se puede aprobar hoy es el plan de despacho. La mayor pérdida que se puede evitar es el fallo del crisol, valorado en el caso de uso en €8M por evento no planificado.""",
    "command-center-q3": """El Turno A (06:00-14:00, A. Weber) efectúa el relevo al Turno B a las **13:45**. Desde el relevo anterior:

- **Escalado** - la alerta del crisol pasó a CRITICAL a las 17:58, riesgo 0.90, RUL P50 19.65 días
- **Nuevo** - aviso de escasez vespertina a las 15:12 (€280/MWh, 18:30-19:00) y aviso de margen ETS del Q3 a las 08:45
- **Reconocido pero pendiente** - desviación de bobinado DP780 (04:00) y deriva del termopar TC-114 (21:10)
- **Emitido** - orden de trabajo WO-DEMO-LUX-1042 a las 18:00; el plan de despacho REC-DEMO-LUX-240725 sigue en PENDING_APPROVAL
- **Decisiones registradas** - 5 entradas de auditoría, AUD-0001 a AUD-0005, en los dominios de horno, energía, calidad, conocimiento y capacidad

No se cerró ninguna incidencia durante el turno, por lo que el recuento de alertas abiertas sigue en **16 alertas**.""",
    "command-center-q4": """**REC-DEMO-LUX-240725**, el plan de despacho energético, es la recomendación con mayor impacto aprobable.

- Coste de €37,109.10 en la línea base a **€34,420.40** optimizado - un ahorro de **€2,688.70 (7.25%)** en el día
- Demanda máxima de 56.0 MW a **51.58 MW**, reducción del 7.89%
- CO₂ **-3.29%** con la misma tonelada producida (960 t)
- **0 infracciones de restricciones duras**; estado PENDING_APPROVAL, modelo energy-dispatch-deterministic:2.1.0

A modo de referencia, durante julio de 2026 la flota aceptó **100 de 116** recomendaciones - adopción 0.862 frente a un objetivo de 0.70 - con **11,431 t** de CO₂ evitado previsto y cero infracciones de restricciones.

La inspección del horno tiene aún mayor valor, pero no es una recomendación que se apruebe: protege el escenario de fallo no planificado de €8M mediante una ventana de mantenimiento.""",
    # -- operations --------------------------------------------------------
    "operations-q1": """Ligeramente por debajo del objetivo. El rendimiento es **128.4 t/h** frente a un objetivo de **130 t/h** - 1.6 t/h por debajo, aunque **+3.2%** respecto al período anterior.

- OEE **84.1%** frente al 85%
- Entrega a tiempo **96.4%** frente al 97%
- Intensidad energética **€312/t** frente a €300/t, mejorando un 4.1%

El perfil de producción cae aproximadamente **6 t/h entre las 17:00 y las 20:00**. Esa caída es deliberada: es la carga del horno de recalentamiento desplazada fuera de la ventana de escasez vespertina de €280/MWh. Fuera de esas tres horas, la línea opera al objetivo o por encima de él.""",
    "operations-q2": """**LUX-RHF-01**, el horno de recalentamiento, durante la ventana de 17:00 a 20:00.

- El rendimiento cae de aproximadamente 130 t/h a **114-122 t/h** durante esas tres horas
- REHEAT-BATCH-06 (NS-AUTO-HSLA420, 120 t) se trasladó de las 18:45 a las **16:45** para evitar la franja de €280/MWh
- Aguas abajo, LUX-HSM-01 acumula la desviación de bobinado DP780 en COIL-LUX-260725-017

En las otras plantas: el bastidor F4 de BE-HSM-01 opera con **un 5.8% por encima en fuerza de laminación**, y la zona 02 del quemador ES-RHF-01 tiene **un 4% de exceso en la mezcla aire/combustible**, equivalente a unas 180 kWh/h de pérdida evitable.

La genealogía de la línea es LUX-BF-01, LUX-BOF-01, LUX-CC-01, LUX-RHF-01 y LUX-HSM-01, por lo que la retención en el horno de recalentamiento es lo que el laminador percibe como horas perdidas - no un fallo del laminador.""",
    "operations-q3": """**Relevo de turno - Turno A (06:00-14:00, A. Weber) al Turno B (14:00-22:00, M. Dupont). Relevo a las 13:45; el Turno C toma el relevo a las 22:00.**

Producción: rendimiento **128.4 t/h** frente a 130, OEE **84.1%** frente a 85%, entregas a tiempo **96.4%** frente a 97%, intensidad energética **€312/t** frente a 300.

Incidencias abiertas - 16 alertas: 1 critical, 8 warning, 7 info, 2 acknowledged.
- CRITICAL ALERT-HEARTH-SECTOR-07-260725 - LUX-BF-01, RUL P50 19.65 días, riesgo 0.90
- WARNING ALERT-ENERGY-SCARCITY-1830 - €280/MWh entre las 18:30 y las 19:00
- WARNING ALERT-QUALITY-DRIFT-DP780 - COIL-LUX-260725-017, reconocida a las 04:00
- WARNING ALERT-ETS-ALLOWANCE-Q3 - margen de derechos de emisión 6.2%

Elementos abiertos y decisiones:
- WO-DEMO-LUX-1042, inspección planificada en HEARTH-SECTOR-07, emitida a las 18:00
- Plan de despacho REC-DEMO-LUX-240725 sigue en PENDING_APPROVAL - €2,688.70, 7.25%
- 5 registros de decisión AUD-0001 a AUD-0005, todos con trazabilidad completa""",
    "operations-q4": """La predicción del crisol en **LUX-BF-01** debería escalar de prioridad.

- ALERT-HEARTH-SECTOR-07-260725, CRITICAL, abierta desde las 17:58
- RUL **P50 19.65 días** (P10 18.69 / P90 20.61), riesgo **0.90**
- Revestimiento refractario a **363 mm** frente a un mínimo seguro de 300 mm, desgaste de aproximadamente **3.0 mm/día**
- Requiere una ventana de reparación del revestimiento en **18-24 días**, lo que es una decisión del plan de producción y no de mantenimiento

En segundo lugar figura el margen ETS del Q3 al **6.2%** - una exposición comercial a €86/t más que operacional. Todo lo demás en el tablero está dentro del triaje habitual del turno.""",
    # -- furnace-health ----------------------------------------------------
    "furnace-health-q1": """La firma térmica es el patrón que forman los cinco sectores del crisol cuando se observan en conjunto, en lugar de uno por uno.

- Los sectores SECTOR-05, -06, -08 y -09 derivan a **0.4 °C/h** desde los 640-664 °C
- **SECTOR-07 asciende a 3.4 °C/h** desde los 652 °C y cruza el umbral de anomalía de **700 °C** alrededor de la hora 14; las celdas a 720 °C o más se marcan como críticas
- El sistema de refrigeración parece sin anomalías - delta T **9.4 °C** a **198 m³/h** - lo que es precisamente lo que da relevancia a la divergencia del sector, en lugar de apuntar a un fallo del sistema de refrigeración
- Flujo de calor **118 kW/m²**, proxy térmico del agua de refrigeración **214.7 kW**, resistencia térmica aparente **8.73**
- La estimación del refractario del sector cae de **372.0 mm a 363 mm** a lo largo de la ventana de 24 horas

El modelo **lining-rul-piml/1.3.0-demo** transforma esos datos en vida útil restante, ponderando heat_flux_6h_slope al 29%, sector_to_ring_temp_delta al 24% y cooling_efficiency_residual al 18%.""",
    "furnace-health-q2": """**ALTO - puntuación de riesgo 0.8995 (90%)** en el componente HEARTH-SECTOR-07.

- Vida útil restante **P50 19.65 días**, P10 18.69, P90 20.61 - una banda estrecha
- Espesor del revestimiento refractario **363 mm** frente a un mínimo estimado de **300 mm**, degradándose aproximadamente a 3.0 mm/día
- Modelo lining-rul-piml/1.3.0-demo, puntuado a las 18:45 hoy
- La segunda unidad, **LUX-RHF-01**, tiene un riesgo del 34% con unos 120 días restantes - vigilancia, sin acción inmediata

El objetivo del programa (KPI-FUR-01) es al menos **21 días** de antelación. En el histórico de julio de 2026, cada episodio de alerta se activó exactamente a los **21.0 días** - BE-EAF-01 el 2026-06-19 para una fecha de fallo el 2026-07-10, LUX-RHF-01 el 2026-06-09 para el 2026-06-30 - y unplanned_outage_flag era **false en cada fila**.""",
    "furnace-health-q3": """Tres factores concentran el 71% de la puntuación.

- **heat_flux_6h_slope - 29%.** Flujo de calor local a 118 kW/m² con una pendiente ascendente de seis horas: el calor llega a la carcasa más rápido de lo que permitiría un revestimiento refractario intacto.
- **sector_to_ring_temp_delta - 24%.** SECTOR-07 sube a 3.4 °C/h mientras sus sectores vecinos derivan a 0.4 °C/h. La divergencia, no la temperatura absoluta, es la señal.
- **cooling_efficiency_residual - 18%.** Un delta T de refrigeración de 9.4 °C a 198 m³/h extrae menos calor del que implica el caudal, por lo que la resistencia térmica aparente ha caído a 8.73.

El 29% restante se distribuye entre características de evolución más lenta. El espesor ahora indica **363 mm** frente a un mínimo de 300 mm, y a aproximadamente 3.0 mm/día eso es lo que fija el P50 en **19.65 días**.""",
    "furnace-health-q4": """**WO-DEMO-LUX-1042 - inspección planificada, HEARTH-SECTOR-07, LUX-BF-01.**

Justificación: el modelo de revestimiento basado en física (lining-rul-piml/1.3.0-demo) puntúa el sector 07 con **riesgo 0.8995** y **RUL P50 19.65 días** (P10 18.69 / P90 20.61). El espesor estimado es **363 mm** frente a un mínimo seguro de **300 mm** y decrece aproximadamente **3.0 mm/día**. Los factores determinantes son una pendiente ascendente de flujo de calor de seis horas (29%), un delta de temperatura sector-anillo de 3.4 °C/h frente a 0.4 °C/h en los sectores vecinos (24%) y un residual de eficiencia de refrigeración (18%). El caudal de refrigeración es nominal a 198 m³/h con delta T de 9.4 °C, por lo que un fallo del sistema de refrigeración no explica la señal.

Alcance: verificar los termopares de la carcasa frente a los sectores vecinos, registrar el delta T de entrada y salida del sistema de refrigeración con el histórico de caudal reciente, y confirmar la estimación del espesor antes de que se abra la ventana de reparación del revestimiento. **PROC-DEMO-0002** (inspección del circuito de refrigeración y escalada ultrasónica, aprobado v3) es aplicable; **PROC-DEMO-0001** (verificación de sobretemperatura en sector del crisol) sigue en revisión.

Calendario: inspección días 1-4, ultrasonidos días 5-8, ventana de reparación del revestimiento **días 18-24**. Actuar dentro de esa ventana es lo que mantiene el evento como planificado - en el histórico de julio de 2026, cada episodio de alerta concluyó con una reparación del revestimiento planificada con unplanned_outage_flag false.""",
    # -- energy-optimization -----------------------------------------------
    "energy-optimization-q1": """**REC-DEMO-LUX-240725** - desplazar el recalentamiento flexible fuera de la ventana de escasez vespertina.

- Línea base **€37,109.10** a optimizado **€34,420.40**, un ahorro de **€2,688.70 (7.25%)**
- Demanda máxima de **56.0 MW a 51.58 MW**, reducción del 7.89%; carga desplazable 18 MW
- El desplazamiento rentable: REHEAT-BATCH-06 fuera de la franja 75 (18:45, **€280.00/MWh**, €3,920.00) hacia la franja 67 (16:45, €97.24/MWh, **€1,361.36**)
- Tonelaje sin cambios en **960 t** en 8 lotes de 120 t / 14 MWh en LUX-RHF-01
- **0 infracciones de restricciones duras**; estado PENDING_APPROVAL, modelo energy-dispatch-deterministic:2.1.0

REHEAT-BATCH-03 permanece fijo a las 09:45 porque está marcado como urgente. Dos lotes se adelantan entre 15 y 30 minutos, y los lotes 00 y 07 se trasladan a franjas nocturnas más baratas.""",
    "energy-optimization-q2": """Porque una franja cuesta más que la mayor parte del resto del día sumada.

- La curva de precio diario (day-ahead) alcanza el máximo en **€280.00/MWh a las 18:45**, frente a 54.85-€112.64/MWh en el resto del día
- Recalentar un único lote de 120 t / 14 MWh en esa franja cuesta **€3,920.00**; el mismo lote a las 16:45 (€97.24/MWh) cuesta **€1,361.36** - una diferencia de €2,558.64 en un solo lote
- La ventana de escasez corre de **17:00 a 20:00**, que es también donde el perfil de producción muestra su caída de 6 t/h
- Se prevé un excedente de PPA eólico de **12 MWh** entre las 02:00 y las 05:00, lo que explica que el lote 07 se traslade a las 23:30 y el lote 00 a las 02:15

El coste total de los lotes flexibles cae de €12,369.70 a €9,681.00. La carga fija de la planta de €24,739.40 tiene el mismo precio en ambos programas, por lo que el ahorro íntegro de **€2,688.70** procede de los ocho lotes de recalentamiento.""",
    "energy-optimization-q3": """Las cinco restricciones indican SATISFIED, con **0 infracciones duras**.

- **equal_planned_tonnage** - 960.00 t planificadas, 960.00 t programadas. El optimizador puede mover el acero, nunca eliminarlo.
- **urgent_batch_fixed** - REHEAT-BATCH-03 (NS-AUTO-HSLA420, urgente) permanece en la franja 39 a las 09:45, sin desplazar.
- **minimum_soak_time** - 60 minutos de tiempo de igualación preservados en cada lote.
- **maximum_hold_time** - ningún lote retenido más allá del límite de 120 minutos; el mayor desplazamiento es el lote 06 con -120 minutos.
- **equipment_capacity** - como máximo 2 lotes concurrentes en LUX-RHF-01.

Eso es lo que hace aprobable el resultado: el ahorro de **€2,688.70** se produce completamente dentro del conjunto de restricciones, y la recomendación está versionada (v1) y es auditable como **AUD-0002**.""",
    "energy-optimization-q4": """**Reducción del 3.29%** en este plan de despacho - obtenida desplazando la carga a franjas más limpias, no reduciendo la producción.

- La intensidad de carbono de la red promedia aproximadamente **244 gCO₂/kWh** a lo largo de las 96 franjas de cuarto de hora, oscilando entre aproximadamente 140 y 310
- El tonelaje no varía con **960 t**, por lo que la reducción es puro arbitraje de carbono
- La demanda máxima también baja de **56.0 a 51.58 MW**, que es donde habitualmente se concentra el carbono de las horas de escasez
- La reducción modelada del plan de despacho completo en el resumen de sostenibilidad es del **8.7%**

A escala de flota en julio de 2026, las **100 recomendaciones aceptadas** (de 116, adopción 0.862 frente a un objetivo de 0.70) representan **11,431 t** de CO₂ evitado previsto.""",
    # -- quality -----------------------------------------------------------
    "quality-q1": """**COIL-LUX-260725-017**, grado NS-AUTO-DP780 - el único lote actualmente en FAIL.

- Puntuación de riesgo **0.429**, característica YIELD_STRENGTH
- Sesgo de temperatura de bobinado **+11.4 °C**, el mayor del tablero; el siguiente más alto es +3.0 °C
- Límite elástico medido **452.4 MPa** frente a una especificación de 380-520 MPa - dentro de especificación, pero el resultado de laboratorio está en REVIEW
- Colada origen H-LUX-260725-0040, laminador LUX-HSM-01
- ALERT-QUALITY-DRIFT-DP780 fue reconocida a las 04:00 y sigue abierta

De los 20 lotes del tablero, este es el que vería un cliente del sector de automoción. La desviación fue marcada antes del primer resultado de laboratorio fuera de especificación, que es el propósito de la señal.""",
    "quality-q2": """Un punto está fuera de control, y es el más reciente.

- Media **1.9**, sigma **2.2**, por lo que LCS **8.5** y LCI **-4.7**
- El subgrupo 20 indica **11.4** - por encima del límite de control superior, el mismo sesgo de bobinado de **+11.4 °C** que presenta COIL-LUX-260725-017
- Los subgrupos 1-19 permanecen dentro de los límites, con un máximo de 5.8. No hay racha, tendencia ni patrón de aproximación a los límites previo
- Capacidad del proceso **Cpk 1.18** frente a un objetivo de **1.33** - capaz, pero sin holgura

En 30 días hay **86 defectos**, y la deriva de la temperatura de bobinado explica **34 de ellos (39.5%)**, por delante de la grieta en borde (21), la cascarilla superficial (14), la variación de espesor (9), la porosidad del recubrimiento (5) y otros (3). Un único punto de causa especial en la familia de defectos dominante apunta a una causa asignable, no a un recentrado del proceso.""",
    "quality-q3": """La cadena detrás de COIL-LUX-260725-017 está íntegra de extremo a extremo, lo que permite localizar la desviación.

- Lote de materia prima LOT-FE-017 a colada **H-LUX-260725-0040** a tratamiento en cuchara LADLE-017 a desbaste SLAB-017
- Recalentamiento en **LUX-RHF-01** (REHEAT-017) a bobina COIL-LUX-260725-017 a muestra SMP-017 a ensayo YIELD_STRENGTH **452.4 MPa** (REVIEW) a expedición SHIP-DEMO-017
- Equivalente de carbono 0.420 al inicio de la secuencia, aumentando 0.002 por lote

El paso que varió es el recalentamiento: ese horno retenía lotes fuera de la ventana de escasez de 17:00 a 20:00, y el sesgo de bobinado resultó en **+11.4 °C**. La desviación se asocia, por tanto, a los pasos de recalentamiento y bobinado, no a la fusión - ningún paso aguas arriba de la cuchara muestra una señal equivalente.""",
    "quality-q4": """Temperatura de bobinado **-8 °C** con fuerza de laminación **-3%** - el análisis hipotético acotado que ya ejecuta esta pantalla.

- El rendimiento a la primera previsto pasa de aproximadamente **88% a aproximadamente 95%**, frente a los límites del escenario de por debajo de 0.90 antes y al menos 0.93 después
- Modelo **quality-yield-gbm/2.1.0-demo**; la ejecución queda registrada como auditoría **AUD-0003**
- Se mantiene dentro de especificación: el límite elástico de 452.4 MPa se sitúa en la banda central de la ventana de 380-520 MPa, por lo que eliminar el sesgo de +11.4 °C no compromete el límite inferior
- En el tablero actual, el rendimiento de alta gama es del 94.8% frente a un objetivo del 95% y el rendimiento a la primera del 97.1% frente al 97%

Frente al KPI del programa, el rendimiento de alta gama a la primera en julio de 2026 fue de **0.9494** frente al objetivo de **0.972** - el único resultado aún por debajo, aproximadamente 2.3 puntos. Las pérdidas de ese mes fueron 4,498 t degradadas, 8,996 t reprocesadas y 1,499 t desechadas en 464 defectos.""",
    # -- sustainability-compliance -----------------------------------------
    "sustainability-compliance-q1": """**71% de los derechos de emisión utilizados**, con el margen del Q3 reducido al **6.2%**.

- Precio del derecho de emisión **€86.00/t**
- Exposición prevista del período **€248,000** a la intensidad de emisión actual
- El Alcance 1 se sitúa en **1,368 t CO₂e/día** para 960 t de acero; el Alcance 2 sigue la red eléctrica, con una media de aproximadamente 244 gCO₂/kWh a lo largo de los 96 intervalos
- CO₂ por tonelada de acero **1.42 t/t** frente a un objetivo de **1.35**
- ALERT-ETS-ALLOWANCE-Q3 está abierta en el libro de registros

Para el último mes con libros cerrados, julio de 2026: intensidad de CO₂ **1.019 tCO₂e/t** frente a un objetivo de 1.638 y una línea base de 2.10, por lo que KPI-CO₂-01 se cumple - con Alcance 1 **355,336 t**, Alcance 2 **147,868 t** y exposición ETS total de **€3,974,153**.""",
    "sustainability-compliance-q2": """**En el mes 5**, con la trayectoria actual.

- El consumo se sitúa en el **71%** y la proyección añade aproximadamente **3.1 puntos al mes**
- El mes 4 llega al 83.4% - todavía por debajo del umbral de orientación del **85%**
- El mes 5 llega al **86.5%**, que es cuando se produce el cruce
- El límite del 100% no se alcanza hasta aproximadamente el mes 10, por lo que el incumplimiento de la orientación llega primero, con unos cinco meses de antelación
- El margen del Q3 ya se ha reducido al **6.2%**, que es lo que rastrea ALERT-ETS-ALLOWANCE-Q3

Aceptar el plan de despacho actual desplaza la línea: **-3.29%** de CO₂ en ese programa, y una reducción modelada del **8.7%** si la optimización del despacho se aplica al plan completo.""",
    "sustainability-compliance-q3": """Ambos residen en el mismo libro de registros de solo adición, pero responden a preguntas distintas.

- **Alcance 1 - directo.** Emisiones de combustión y de proceso en planta: **1,368 t CO₂e** para 960 t de acero hoy, equivalente a 1,425 kg por tonelada. Varía cuando cambia el proceso, e independientemente de lo que haga la red eléctrica.
- **Alcance 2 - indirecto, electricidad comprada.** Calculado por cuarto de hora: consumo en el intervalo multiplicado por la intensidad de carbono de la red en ese mismo intervalo - aproximadamente **244 gCO₂/kWh** de media, entre aproximadamente 40 y 480 a lo largo del día. Varía cuando se desplaza la carga en el tiempo, incluso con el mismo tonelaje.

Por eso la recomendación del plan de despacho reduce el CO₂ un **3.29%** sin producir menos acero: solo afecta al Alcance 2. El libro contiene **96 filas de intervalo inmutables**, y la exposición ETS se deriva de su suma a €86/t.

En julio de 2026, el desglose fue Alcance 1 **355,336 t** y Alcance 2 **147,868 t**.""",
    "sustainability-compliance-q4": """Aprobar el plan de despacho - es la única palanca de acción disponible hoy.

- **REC-DEMO-LUX-240725** - CO₂ **-3.29%** de inmediato, con el tonelaje sin cambios (960 t), 0 infracciones de restricciones duras, sigue en PENDING_APPROVAL
- Ejecutar la optimización del despacho en el plan completo está modelado en **8.7%**
- La siguiente más rápida: la zona 02 del quemador ES-RHF-01 tiene **un 4% de exceso en la mezcla aire/combustible**, equivalente a unas 180 kWh/h de pérdida evitable
- La más lenta pero de mayor impacto: la ruta del proceso del Alcance 1, a la que ningún cambio de programa llega

A **€86/t** y con el margen al 6.2%, el plan de despacho es lo que mantiene el cruce del umbral de orientación sin adelantarse al mes 5. En julio de 2026, las 100 recomendaciones aceptadas llevaron **11,431 t** de CO₂ evitado previsto.""",
    # -- knowledge-hub -----------------------------------------------------
    "knowledge-hub-q1": """**PROC-DEMO-0002 - inspección del circuito de refrigeración y escalada ultrasónica.** Estado APPROVED, versión 3, capturado en la sesión SESS-DEMO-015 y citado en transcript:SESS-DEMO-015#seg-2. Es el único procedimiento aprobado de la biblioteca y el que se aplica a la alerta abierta del crisol.

El más próximo, aún no utilizable: **PROC-DEMO-0001 - verificación de sobretemperatura en sector del crisol**, versión 2, IN_REVIEW, citado en transcript:SESS-DEMO-014#seg-4 y #seg-7. Indica comparar los termopares de la carcasa de sectores vecinos antes de actuar, leer el delta T de entrada y salida del sistema de refrigeración con el histórico de caudal reciente en lugar de solo el caudal actual, y nunca omitir alarmas ni modificar controles basándose únicamente en las indicaciones de una entrevista.

Las respuestas fundamentadas se extraen únicamente de procedimientos aprobados, por lo que PROC-DEMO-0001 puede consultarse pero no será citado como respuesta hasta que un experto lo apruebe.""",
    "knowledge-hub-q2": """**Energía y servicios es el dominio con mayor brecha - 58% de cobertura**, el más bajo de los cinco dominios.

- Alto horno **82%**
- Laboratorio de calidad **77%**
- Tren de laminación en caliente **71%**
- Horno de recalentamiento **64%**
- Energía y servicios **58%**

Tres procedimientos capturados superan el SLA de revisión de 5 días (ALERT-KNOWLEDGE-REVIEW-QUEUE), y solo uno de los tres procedimientos de la biblioteca está aprobado - por lo que la cobertura utilizable es inferior a la cobertura capturada en todos los dominios.

La brecha es más crítica donde se producen las jubilaciones: la experiencia sobre el crisol que hay detrás de PROC-DEMO-0001 está capturada pero sin aprobar, mientras que el dominio de energía - el que soporta la decisión de plan de despacho de €2,688.70/día - es el que menos conocimiento tiene capturado de partida.""",
    "knowledge-hub-q3": """Dos de los tres procedimientos aún no son utilizables.

- **PROC-DEMO-0001 - verificación de sobretemperatura en sector del crisol.** IN_REVIEW, versión 2, sesión SESS-DEMO-014, dos segmentos de transcripción citados (#seg-4, #seg-7). Directamente relevante para la alerta abierta de LUX-BF-01.
- **PROC-DEMO-0003 - recuperación de tiempo de igualación en zona del horno de recalentamiento.** DRAFT, versión 1, sesión SESS-DEMO-016, un segmento citado (#seg-1).
- Ya aprobado: **PROC-DEMO-0002**, versión 3, inspección del circuito de refrigeración y escalada ultrasónica.

**ALERT-KNOWLEDGE-REVIEW-QUEUE** marca tres procedimientos capturados que superan el SLA de revisión de 5 días. La aprobación es un paso humano por diseño: la aprobación de PROC-DEMO-0002 queda registrada como auditoría **AUD-0004** con el actor ke-demo a las 10:15, de modo que la cadena desde la transcripción del operador hasta el procedimiento publicado permanece auditable.""",
    "knowledge-hub-q4": """Guía de entrevista, fundamentada en PROC-DEMO-0001 y la firma actual de LUX-BF-01. Sujeto **OP-DEMO-014**, operador sénior de alto horno; la captura está sujeta a consentimiento y la transcripción se conserva bajo ese ámbito de consentimiento.

- Cuando un sector del crisol se calienta pero el caudal de refrigeración indica valores normales, ¿qué comprueba primero y en qué orden?
- ¿Con qué termopares de carcasa vecinos compara, y qué magnitud del delta le lleva a actuar? SECTOR-07 está subiendo actualmente a 3.4 °C/h frente a 0.4 °C/h en sus sectores vecinos.
- ¿Cómo distingue la degradación del revestimiento refractario de una deriva de sensor? PROC-DEMO-0001 cita la persistencia entre coladas y el enfriamiento post-colada más lento - ¿qué más utiliza?
- ¿Qué le indica el delta T de entrada y salida del sistema de refrigeración junto con el histórico de caudal reciente que no le dice el caudal actual por sí solo? Hoy indica 9.4 °C a 198 m³/h.
- Con un espesor estimado de 363 mm frente a un mínimo de 300 mm, ¿qué le haría adelantar la ventana de reparación del revestimiento?
- ¿Qué ha fallado antes en este horno que un operador nuevo no esperaría?

Límite de seguridad a reiterar formalmente: nunca omitir alarmas ni modificar los controles del horno o del sistema de refrigeración basándose únicamente en las indicaciones de una entrevista.""",
    # -- executive-overview ------------------------------------------------
    "executive-overview-q1": """Tres de los cuatro resultados objetivo se cumplen, uno no alcanza el objetivo. Las cifras corresponden al cierre de julio de 2026 en las tablas de referencia.

- **Intensidad energética (KPI-ENE-01)** - **10.63 GJ/t** frente a un objetivo de 16.77, desde una línea base de 19.5. **Cumplido**, con un coste energético de aproximadamente €46.5M frente a una línea base de €54.1M.
- **Intensidad de CO₂ (KPI-CO₂-01)** - **1.019 tCO₂e/t** frente a un objetivo de 1.638, desde una línea base de 2.10. **Cumplido**.
- **Antelación de alerta del revestimiento (KPI-FUR-01)** - cada episodio de alerta se activó exactamente a los **21.0 días**, el mínimo declarado, con unplanned_outage_flag false en cada fila. **Cumplido**.
- **Rendimiento de alta gama a la primera (KPI-QUA-01)** - **0.9494** frente a un objetivo de 0.972, desde una línea base de 0.90. **No cumplido**, aproximadamente 2.3 puntos por debajo.
- Como indicador de apoyo: adopción del despacho **0.862** (100 de 116 aceptadas) frente a un mínimo de 0.70. **Cumplido**.

Las barras de progreso de esta pantalla muestran 92, 88, 96 y 100 sobre 100 para energía, CO₂, rendimiento y tiempo de antelación. La calidad es la brecha real, y es hacia donde apunta el trabajo de captura de conocimiento.""",
    "executive-overview-q2": """**Saarbrucken (DE)** en rendimiento, **Moselle (LU)** en riesgo.

- Moselle (LU) - energía -14.2%, CO₂ -22.4%, rendimiento +8.1%, **3 alertas abiertas** incluida la única crítica
- Saarbrucken (DE) - energía **-11.8%**, CO₂ **-18.6%**, rendimiento **+6.4%**, 2 alertas abiertas: última en los tres indicadores
- Liege (BE) - energía -13.1%, CO₂ -20.2%, rendimiento +7.2%, 1 alerta abierta
- Asturias (ES) - energía -12.5%, CO₂ -19.4%, rendimiento +7.9%, 2 alertas abiertas

Saarbrucken es la única planta por debajo del objetivo del programa en los tres ejes, y sus elementos abiertos tienen impacto económico: oscilación del nivel del molde del colador por encima de la banda de 4.5 mm y una mezcla de carga de chatarra un 3.1% por encima de la receta de mínimo coste.

Moselle lidera en todos los ejes pero alberga la predicción del crisol de LUX-BF-01 - riesgo 0.90, 19.65 días - que es la cuestión de €8M de esta semana.""",
    "executive-overview-q3": """Cuatro resultados comprometidos, medidos sobre un conjunto de datos piloto sintético, expresados como objetivos donde lo son.

- **Objetivos** - energía por tonelada -14%, CO₂ por tonelada -22%, rendimiento de alta gama +8%, al menos 21 días de antelación en la alerta del revestimiento.
- **Medido en los datos piloto** - intensidad energética 10.63 GJ/t e intensidad de CO₂ 1.019 tCO₂e/t en julio de 2026; cada alerta del revestimiento emitida exactamente a los 21.0 días sin parada no planificada; rendimiento de alta gama a la primera 0.9494, aún por debajo del objetivo de 0.972.
- **Medido en un único plan de despacho hoy** - €2,688.70 ahorrados (7.25%), demanda máxima -7.89%, CO₂ -3.29%, cero infracciones de restricciones.
- **Modelado, no realizado** - un fallo prevenido, valorado en el caso de uso en €8M por fallo no planificado del crisol.

La gobernanza tiene el mismo peso que los números: cinco registros de decisión en cinco dominios, tres de ellos vinculados a modelos, 100% de inmutabilidad, y cada recomendación requiriendo una decisión humana antes de ejecutarse.""",
    "executive-overview-q4": """La separación es clara, y los paneles lo indican en sus descripciones emergentes.

**Objetivos, no medidas:** energía por tonelada -14%, CO₂ por tonelada -22%, rendimiento de alta gama +8%, al menos 21 días de antelación. Estos son los compromisos del caso de uso a escala de flota.

**Medido en esta demo:**
- Plan de despacho - **€2,688.70 (7.25%)** ahorrados, pico de 56.0 a 51.58 MW, CO₂ **-3.29%**, 0 infracciones duras
- Horno - riesgo 0.8995 con **P50 19.65 días** de antelación en LUX-BF-01, por debajo del objetivo de 21 días en este único episodio en vivo
- Análisis hipotético de calidad - rendimiento a la primera previsto de aproximadamente 88% a aproximadamente 95%, modelo quality-yield-gbm/2.1.0-demo
- Cierre de referencia de julio de 2026 - 10.63 GJ/t, 1.019 tCO₂e/t, antelación de 21.0 días en cada episodio, 0.9494 rendimiento de alta gama a la primera

**Modelado:** el valor de €8M de fallo evitado y el recuento de un único fallo prevenido.

El único número que nunca debe presentarse como logrado es el objetivo de CO₂: el objetivo de la flota es -22%, mientras que esta demo de una sola planta mide -3.29% en un único plan de despacho.""",
    # -- platform-ops ------------------------------------------------------
    "platform-ops-q1": """**Running** - capacidad **cap-novasteel-demo-sc**, SKU **F2**, región Sweden Central, entorno demo.

- Reanudada esta mañana: Paused a Resuming a las 07:27, Resuming a ReadinessCheck a las 07:28, ReadinessCheck a Running a las 07:30 - todo por demo-platform-ops con motivo "rehearsal"
- Política de ciclo de vida: comprobación de pausa nocturna a las **01:00 Europe/Luxembourg**
- El SKU es intercambiable entre F2, F4 y F8; el cambio de estado queda registrado como auditoría **AUD-0005**
- El espacio de trabajo NovaSteelV3-Demo alberga el lakehouse lh_novasteelv3_core, la base de datos KQL kql-ns-operations y la ontología onto_novasteelv3

Esta es una capacidad de no producción, y el ciclo de vida está deliberadamente restringido a inicio, pausa y cambio de SKU - cada uno auditado.""",
    "platform-ops-q2": """**Ninguna ha fallado.** Cuatro de las cinco ejecuciones más recientes han tenido éxito y una sigue en curso.

- RUN-4821 bronze-to-silver - SUCCEEDED, 17:45, **214 s**
- RUN-4820 silver-to-gold - SUCCEEDED, 17:30, **176 s**
- RUN-4819 semantic-refresh - **RUNNING**, iniciada a las 18:40, 62 s hasta ahora
- RUN-4818 contract-assertions - SUCCEEDED, 17:10, 41 s
- RUN-4817 quarantine-negative-tests - SUCCEEDED, 16:55, 33 s

Ambos trabajos de guardia han pasado: las aserciones de contratos sobre los sobres de eventos, y las pruebas negativas que demuestran que las cargas incorrectas van a cuarentena en lugar de a silver. La frescura de extremo a extremo es **12 s**. El único elemento abierto es la actualización semántica.""",
    "platform-ops-q3": """Estable y reducido - es un F2 con una carga de trabajo de demo.

- Coste por hora **€2.80**, oscilando aproximadamente €0.40 en ambos sentidos durante la ventana de 06:00 a 18:00
- La utilización promedia aproximadamente el **38%**, siguiendo un perfil suave entre el 26% y el 50% aproximadamente
- El gasto hasta la fecha es la suma de los 13 puntos horarios de la tendencia
- Frescura de la telemetría **12 s**

La forma importa más que el total: la utilización alcanza su máximo junto con las ejecuciones de silver-to-gold y semantic-refresh, por lo que la comprobación de pausa nocturna a las 01:00 no tiene coste en rendimiento. En un F2 la propia capacidad es el mínimo de la factura, por lo que pausar entre demostraciones es la única palanca real.""",
    "platform-ops-q4": """**Todavía no - RUN-4819 (semantic-refresh) sigue en ejecución**, 62 s en curso, iniciada a las 18:40.

- Las otras cuatro ejecuciones han concluido: bronze-to-silver, silver-to-gold, contract-assertions y quarantine-negative-tests todas en SUCCEEDED entre las 16:55 y las 17:45
- Pausar durante una actualización del modelo semántico deja el modelo sin actualizar, por lo que los paneles servirían el snapshot anterior de gold al reanudarse
- La capacidad **cap-novasteel-demo-sc** es F2, Running desde las 07:30, entorno demo
- La política de ciclo de vida ya ejecuta su comprobación de pausa a las **01:00 Europe/Luxembourg**, momento en que esta ejecución habrá terminado desde hace tiempo

Esperar a que RUN-4819 indique SUCCEEDED y luego pausar. La transición queda registrada como las demás, con actor y motivo.""",
    # -- device-operations -------------------------------------------------
    "device-operations-q1": """**Ninguno.** Los **17 dispositivos** están informando y hay **0 incidentes activos** inyectados.

- Flota: 6 en Luxemburgo (LUX-BF-01, LUX-BOF-01, LUX-CC-01, LUX-RHF-01, LUX-HSM-01, LUX-UTIL-01), 4 en Alemania, 4 en Bélgica, 3 en España
- **91 señales de sensor** en línea en toda la flota
- El tiempo de actividad oscila entre **99.10% y 99.95%** por dispositivo
- Simulador: escenario **demo-full**, semilla 240726, tick 720, aproximadamente 6 horas transcurridas a 5 s por tick

El único dispositivo con una alerta abierta es **LUX-BF-01** - la predicción del crisol - y es una condición de proceso, no un fallo del dispositivo: sus termopares y señales de flujo de calor y refrigeración están publicando con normalidad. La salud en esta pantalla se mide por la frescura de las señales y el recuento de alarmas, por lo que una pasarela sana puede estar detrás de una alerta de proceso crítica.""",
    "device-operations-q2": """Mide la salud de la pasarela, no la salud del proceso. Tres entradas:

- **Tiempo de actividad** - la proporción de la ventana en que el dispositivo publicó datos. La flota se sitúa entre **99.10% y 99.95%**.
- **Obsolescencia de señales** - cada señal tiene un período de emisión esperado y se vuelve obsoleta cuando lo supera. Los períodos van de **1 s** (arc_current en DE-EAF-01) y 5 s (hearth_shell_temperature, local_heat_flux) hasta **900 s** (hearth_refractory_estimate, spot_price, grid_carbon_intensity). Una señal es orientada a eventos sin período alguno: hot_metal_temperature, emitida únicamente en un vaciado.
- **Recuento de alarmas** - alarmas activas del dispositivo en la ventana, ponderadas por gravedad.

Un dispositivo está sano cuando los tres criterios se mantienen, degradado cuando la frescura o las alarmas se deterioran, y en fallo cuando deja de publicar. En el tick 720 sin incidente inyectado, los **17 dispositivos y 91 señales** están sanos - por eso la alerta de proceso de LUX-BF-01 aparece junto a una puntuación de dispositivo limpia.""",
    "device-operations-q3": """**Ninguna está obsoleta ahora mismo** - las **91 señales** están dentro de su período esperado en el tick 720.

La obsolescencia de señales se evalúa por señal, y los períodos difieren notablemente:
- **1-5 s** - arc_current (DE-EAF-01), hearth_shell_temperature y local_heat_flux (LUX-BF-01), zinc_bath_temperature (BE-GAL-01)
- **10 s** - bath_temperature en LUX-BOF-01 y DE-EAF-01
- **60 s** - production_rate
- **900 s** - hearth_refractory_estimate, spot_price, grid_carbon_intensity
- **Orientado a eventos** - hot_metal_temperature, emitida únicamente en un vaciado

Importa porque un modelo solo es tan actual como su entrada más lenta. La puntuación del revestimiento depende de hearth_refractory_estimate y local_heat_flux: si la estimación del refractario de 900 s se vuelve obsoleta, el **RUL P50 de 19.65 días** deja de actualizarse mientras el horno sigue adelgazando a aproximadamente 3.0 mm/día. El plan de despacho tiene la misma exposición a través de spot_price y grid_carbon_intensity, ambas también en 900 s.""",
    "device-operations-q4": """Dos formas, según cuánto tiempo se desee que dure.

**Incidente único - degrading-furnace.** Gravedad alta, duración por defecto **30 minutos**, objetivo **LUX-BF-01**, forzando local_heat_flux, hearth_refractory_estimate y hearth_shell_temperature. Seleccionarlo en el panel de incidentes de esta pantalla, confirmar el dispositivo y la duración, e inyectar.

**Escenario completo - lining-degradation-21d.** Reiniciar el simulador con ese escenario en lugar de demo-full para reproducir el arco completo de degradación en lugar de una excursión de 30 minutos.

- Estado actual: escenario **demo-full**, semilla **240726**, tick 720, aproximadamente 6 horas transcurridas, ticks de 5 s, **0 incidentes activos**
- Otros escenarios disponibles: healthy-baseline, energy-price-spike, quality-drift, edge-outage-recovery
- Otros incidentes: cooling-water-loss (crítico, 15 min), sensor-drift (60 min), sensor-dropout (10 min), energy-price-spike (45 min, LUX-UTIL-01), quality-drift (45 min, LUX-CC-01 y LUX-HSM-01), edge-outage-recovery (20 min)

El efecto en Salud del Horno se espera en pocos ticks: puntuación de riesgo por encima de 0.80 y RUL P50 entre **19 y 23 días**, que es la banda a la que está acotado el escenario.""",
    # -- dashboards --------------------------------------------------------
    "dashboards-q1": """**Relevo del turno de mañana** - Gerente de planta, aproximadamente **6 minutos**, etiquetado como daily y triage.

Recorre el Centro de Mando, luego Operaciones, luego las alertas abiertas - que es el orden que realmente necesita un relevo de turno: qué es crítico, qué ha hecho la línea, qué sigue abierto.

Lo que mostraría ahora mismo: **16 alertas abiertas** (1 critical, 8 warning, 7 info, 2 acknowledged), rendimiento **128.4 t/h** frente a 130, OEE **84.1%**, y una orden de trabajo - WO-DEMO-LUX-1042 - emitida contra la predicción del crisol.

Si el relevo trata específicamente del horno, utilice **Investigación de riesgo del horno** (aproximadamente 8 minutos); es la más detallada de las dos.""",
    "dashboards-q2": """**Paquete de evidencias de cumplimiento** - Responsable de Sostenibilidad y Auditor, aproximadamente **7 minutos**, etiquetado como compliance, audit y eu-ai-act.

Ensambla el rastro de evidencias en lugar de las métricas:
- **5 registros de decisión**, AUD-0001 a AUD-0005, cubriendo los **5 dominios**: horno, energía, calidad, conocimiento y capacidad
- **3 de ellos vinculados a modelos** - lining-rul-piml/1.3.0-demo, energy-dispatch-milp/1.2.0-demo y quality-yield-gbm/2.1.0-demo
- **100% de inmutabilidad**, con el id de correlación run-demo-full-240725 vinculando las decisiones de horno, energía y calidad a una única ejecución
- El libro de emisiones detrás de ellas: 96 filas de intervalo de solo adición, Alcance 1 y Alcance 2 separados, ETS valorado a €86/t
- Puntos de decisión humana: cada recomendación lleva un actor y una marca de tiempo, que es en lo que se apoya el argumento de trazabilidad del Reglamento de IA de la UE

Eso es el paquete: qué se decidió, qué versión del modelo lo respaldó, sobre qué datos, y aprobado por quién.""",
    "dashboards-q3": """Seis colecciones, cada una una ruta fija a través de pantallas ya existentes.

- **Relevo del turno de mañana** - Gerente de planta, aproximadamente 6 min, daily y triage. Qué es crítico, qué ha hecho la línea, qué sigue abierto.
- **Investigación de riesgo del horno** - Ingeniero de Mantenimiento y Fiabilidad, aproximadamente 8 min, reliability y root-cause. Si el riesgo del revestimiento es real, qué lo impulsa, cuándo hay que actuar.
- **Revisión energética y de costes** - Gestor de Energía, aproximadamente 7 min, energy y cost. Qué cuesta el programa, qué ahorra la alternativa, qué lo limita.
- **Revisión de escape de calidad** - Ingeniero de Calidad, aproximadamente 6 min, quality y root-cause. Qué lote, qué paso, qué ajuste.
- **Paquete de evidencias de cumplimiento** - Responsable de Sostenibilidad y Auditor, aproximadamente 7 min, compliance, audit y eu-ai-act. Qué se decidió, qué modelo lo respaldó, aprobado por quién.
- **Salud y coste de la plataforma** - Operaciones de Plataforma, aproximadamente 5 min, platform y cost. Si el pipeline está sano, cuánto está costando.

Cada una contiene tres o cuatro pantallas ordenadas y no añade datos propios - los números siguen siendo propiedad de las pantallas a las que enlaza.""",
    "dashboards-q4": """**Investigación de riesgo del horno** - Ingeniero de Mantenimiento y Fiabilidad, aproximadamente **8 minutos**, etiquetado como reliability y root-cause. Recorre la previsión del revestimiento, luego el explorador térmico, luego el planificador de mantenimiento - el orden en que se construye la evidencia.

Lo que mostraría ahora mismo:
- Previsión del revestimiento - LUX-BF-01 / HEARTH-SECTOR-07 con riesgo **0.8995**, RUL **P50 19.65 días** (P10 18.69 / P90 20.61)
- Explorador térmico - SECTOR-07 ascendiendo a **3.4 °C/h** frente a 0.4 °C/h en sus sectores vecinos, cruzando el umbral de anomalía de 700 °C
- Planificador de mantenimiento - **WO-DEMO-LUX-1042** abierta en el sector, ventana de reparación del revestimiento en los días 18-24

Para el relevo más amplio utilice Relevo del turno de mañana (aproximadamente 6 min); para el enfoque de auditoría en lugar del técnico, el Paquete de evidencias de cumplimiento lleva el rastro de decisiones detrás de la misma llamada.""",
}
