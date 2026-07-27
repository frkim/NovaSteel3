import type { HelpCatalog } from '../components/help/helpTypes'

export const HELP_ES: HelpCatalog = {
  // ---------------------------------------------------------------- generic
  'generic.kpi': {
    title: 'Número principal',
    what: 'Una tarjeta muestra una medición, su flecha de tendencia y cómo se compara con el objetivo.',
    steel:
      'Una planta siderúrgica se gestiona con unos pocos números. Verlos juntos permite al jefe de turno entender el estado de la planta en segundos, sin leer informes.',
    useIt: 'Una tarjeta con cursor de flecha se puede pulsar para abrir el detalle detrás del número.',
  },
  'generic.chart': {
    title: 'Gráfico',
    what: 'Una imagen de cómo cambió una medición con el tiempo o de cómo se reparte entre partes de la planta.',
    steel:
      'Los números aislados ocultan la historia. Un horno con una temperatura media segura puede tener picos peligrosos, y solo un gráfico los muestra.',
    useIt: 'Pase el puntero por un punto para ver su valor exacto. Los gráficos en un panel se pueden ampliar con el botón maximizar de la barra de pestañas.',
  },
  'generic.table': {
    title: 'Tabla de datos',
    what: 'Los registros individuales detrás de los números resumidos, uno por fila.',
    steel: 'Cuando un número parece incorrecto, la tabla muestra el lote, sensor u orden de trabajo concretos que lo causaron.',
    useIt: 'Pulse un encabezado de columna para ordenar, use los controles del encabezado para filtrar y el cuadro de búsqueda para encontrar texto en toda la tabla.',
  },
  'generic.tableRow': {
    title: 'Un registro',
    what: 'Un elemento único: un lote, una lectura de sensor, una orden de trabajo o una alerta.',
    steel: 'Todo lo que ocurre en la planta acaba escrito como un registro de este tipo. Eso hace posible una auditoría.',
    useIt: 'Cuando una fila es clicable, abre el detalle completo de ese elemento.',
  },
  'generic.tableHeader': {
    title: 'Encabezado de columna',
    what: 'El nombre de una columna y el control que ordena y filtra la tabla por ella.',
    steel: 'Ordenar por riesgo o por fecha es la forma en que un ingeniero convierte una lista larga en una lista corta de acciones para hoy.',
    useIt: 'Pulse una vez para ordenar de forma ascendente y otra vez para descendente. Los filtros reducen la tabla solo a las filas coincidentes.',
  },
  'generic.panel': {
    title: 'Panel de trabajo',
    what: 'Una sección movible de la pantalla. Los paneles se pueden arrastrar por su pestaña a cualquier borde, cambiar de tamaño o apilar.',
    steel: 'Los operadores de sala de control no vigilan todos lo mismo. Por eso el diseño se adapta a la persona, no al revés.',
    useIt: 'Arrastre la pestaña para reorganizar. Restablecer diseño en el encabezado vuelve a colocar todo.',
  },
  'generic.dockTab': {
    title: 'Pestaña de panel',
    what: 'El asa de un panel. Nombra el panel y permite moverlo.',
    steel: 'Los paneles que deben permanecer siempre visibles no tienen botón de cierre. Así una vista crítica no se pierde por accidente.',
    useIt: 'Arrástrela para mover el panel, o pulse el botón maximizar para que llene el área de trabajo.',
  },
  'generic.button': {
    title: 'Acción',
    what: 'Un control que cambia lo mostrado o pide a la plataforma que haga algo.',
    steel:
      'Todo lo que podría cambiar el comportamiento de la planta aquí es solo una propuesta. Un humano aún lo aprueba antes de que llegue al equipo.',
    useIt: 'Pase el puntero por encima para ver una ayuda que describe qué hace la acción.',
  },

  // ------------------------------------------------------------ chart types
  'chart.line': {
    title: 'Gráfico de líneas',
    what: 'El tiempo va de izquierda a derecha, y la medición de abajo arriba. La línea une lecturas consecutivas.',
    steel: 'Los procesos siderúrgicos derivan lentamente, por lo que la pendiente importa más que una lectura aislada. Una línea ascendente es una alerta temprana.',
    useIt: 'Busque saltos bruscos y una pendiente que siga en la misma dirección.',
  },
  'chart.area': {
    title: 'Gráfico de áreas',
    what: 'Un gráfico de líneas con el espacio bajo la línea relleno, lo que facilita comparar totales.',
    steel: 'Útil para cantidades que se acumulan, como energía consumida o emisiones liberadas durante un turno.',
    useIt: 'Compare el tamaño de las áreas rellenas, no la altura de la línea.',
  },
  'chart.bar': {
    title: 'Gráfico de barras',
    what: 'Una barra por categoría. Más alta significa más.',
    steel: 'Sirve para comparar hornos, calidades de acero o turnos entre sí de un vistazo.',
    useIt: 'Busque la barra atípica. Ahí suele estar el problema o la oportunidad.',
  },
  'chart.heatmap': {
    title: 'Mapa de calor',
    what: 'Una cuadrícula donde el color representa un valor. Los colores más oscuros o más calientes significan lecturas más altas.',
    steel:
      'Un alto horno está equipado con cientos de sensores. Un mapa de calor los muestra todos a la vez, para que un punto caliente en la carcasa destaque de inmediato.',
    useIt: 'Busque celdas brillantes aisladas. Una celda caliente rodeada de celdas frías suele significar un problema local de desgaste.',
  },
  'chart.gauge': {
    title: 'Indicador',
    what: 'Un dial que muestra un valor frente a su rango seguro.',
    steel: 'Refleja los instrumentos analógicos que los operadores han usado durante décadas en la planta. Por eso necesita poca explicación en una pantalla de control.',
    useIt: 'La banda de color indica si el valor actual es cómodo, marginal o está fuera de límites.',
  },
  'chart.control': {
    title: 'Gráfico de control',
    what: 'Un gráfico temporal con una línea central para el objetivo y dos líneas exteriores para el rango aceptable.',
    steel:
      'Es la herramienta clásica de calidad. Un proceso dentro de las líneas exteriores es predecible; un punto fuera significa que algo cambió y debe investigarse.',
    useIt: 'Vigile los puntos fuera de los límites y las rachas largas de puntos a un lado de la línea central.',
  },
  'chart.pareto': {
    title: 'Gráfico de Pareto',
    what: 'Barras ordenadas de mayor a menor, con una línea ascendente que muestra el total acumulado.',
    steel:
      'La mayoría de la chatarra y el retrabajo proceden de pocas causas. Corregir las dos o tres primeras barras suele eliminar la mayor parte de la pérdida.',
    useIt: 'Encuentre dónde la línea cruza el 80 por ciento. Las barras a la izquierda son su lista de prioridades.',
  },
  'chart.donut': {
    title: 'Gráfico de anillo',
    what: 'Un anillo dividido en segmentos, cada segmento como parte del total.',
    steel: 'Se usa para desgloses como el origen de las emisiones, cuando un segmento es más fácil de juzgar que un porcentaje en una tabla.',
    useIt: 'Compare los tamaños de los segmentos; pase el puntero para ver la proporción exacta.',
  },
  'chart.gantt': {
    title: 'Gráfico de barras de planificación',
    what: 'Cada barra es una actividad, situada y dimensionada según cuándo empieza y cuánto dura.',
    steel:
      'Los revestimientos nuevos de hornos y las paradas de mantenimiento deben encajar entre campañas de producción. Verlos en una sola línea temporal ayuda a los planificadores a evitar choques.',
    useIt: 'Busque solapes y huecos que puedan absorber una ventana de mantenimiento.',
  },
  'chart.priceLoad': {
    title: 'Gráfico de precio y carga',
    what: 'Dos cosas en una misma línea temporal: el precio de la electricidad y cuánta potencia planea tomar la planta.',
    steel:
      'La electricidad es uno de los mayores costes en la fabricación de acero y su precio cambia cada hora. Hacer trabajo intensivo en energía cuando el precio es bajo ahorra dinero real.',
    useIt: 'Compruebe que las barras altas de carga caen bajo los puntos bajos de la línea de precio.',
  },
  'chart.bullet': {
    title: 'Barra de progreso',
    what: 'Una barra que muestra dónde está el valor actual entre cero y su objetivo.',
    steel: 'Da una idea rápida de cuánto se ha usado ya de un compromiso, como un presupuesto anual de emisiones.',
    useIt: 'El marcador en la barra es el objetivo; la parte rellena muestra dónde está realmente.',
  },
  'chart.sparkline': {
    title: 'Minitendencia',
    what: 'Un gráfico de líneas muy pequeño sin ejes, que solo muestra la forma reciente de la medición.',
    steel: 'Cabe dentro de una tarjeta principal, de modo que obtiene la dirección del movimiento sin salir de la pantalla resumen.',
    useIt: 'Lea la forma, no los valores. Pulse la tarjeta para ver el gráfico completo.',
  },

  // ------------------------------------------------------- executive layer
  'kpi:energy': {
    title: 'Intensidad energética',
    what: 'Electricidad y combustible usados para fabricar una tonelada de acero, en kilovatios hora por tonelada.',
    steel:
      'Fabricar acero significa calentar mineral de hierro o chatarra hasta unos 1.600 grados Celsius. Por eso la energía es a la vez el mayor coste y la mayor fuente de emisiones.',
    useIt: 'Compare con la línea objetivo. Una bajada aquí pasa directamente al coste y al carbono.',
  },
  'kpi:co2': {
    title: 'Emisiones de dióxido de carbono',
    what: 'Toneladas de CO2 liberadas, o la reducción lograda frente al periodo de referencia.',
    steel:
      'El acero representa aproximadamente el siete por ciento del CO2 mundial. En Europa una planta debe entregar un derecho de emisión por cada tonelada liberada, así que este número tiene un precio asociado.',
    useIt: 'Léalo junto con la intensidad energética. La mayoría de las reducciones vienen de usar menos electricidad o electricidad más limpia.',
  },
  'kpi:yield': {
    title: 'Rendimiento de alta calidad',
    what: 'La parte de la producción que cumple la especificación premium a la primera.',
    steel:
      'El acero fuera de especificación no es residuo: se vuelve a fundir. Pero refundir gasta la energía dos veces, así que el rendimiento es también una medida oculta de energía y coste.',
    useIt: 'Una caída aquí suele aparecer poco después en las pantallas de calidad.',
  },
  'kpi:warning': {
    title: 'Antelación de aviso',
    what: 'Cuántos días de aviso dan los modelos antes de que ocurra un problema previsto.',
    steel:
      'Pedir ladrillo refractario y reservar un equipo de reparación lleva semanas. Un aviso que llega demasiado tarde no vale nada, así que la antelación importa tanto como la precisión.',
    useIt: 'El objetivo piloto es al menos 21 días. Menos que eso no deja tiempo para planificar una parada.',
  },
  'kpi:failures': {
    title: 'Paradas no planificadas',
    what: 'Número de veces que la producción se detuvo sin estar programada.',
    steel:
      'Una parada no planificada de un alto horno es extremadamente cara: hay que mantener caliente el recipiente, los trenes posteriores se quedan sin material y el reinicio consume energía.',
    useIt: 'El objetivo de toda la plataforma es convertirlas en paradas planificadas.',
  },

  // ---------------------------------------------------------- furnace health
  'kpi:risk': {
    title: 'Riesgo del revestimiento',
    what: 'Una puntuación de 0 a 1 que estima la probabilidad de que el revestimiento del horno alcance pronto su límite de desgaste.',
    steel:
      'Un alto horno es una carcasa de acero revestida con ladrillo resistente al calor, llamado refractario. El ladrillo se erosiona lentamente; si se perfora, el metal fundido llega a la carcasa. Esta puntuación es la alerta temprana de la planta.',
    useIt: 'Por encima de 0,8, el planificador de mantenimiento debería reservar una ventana de reparación.',
  },
  'kpi:days': {
    title: 'Vida útil restante',
    what: 'Días estimados de operación antes de que el revestimiento alcance su límite de desgaste al ritmo actual.',
    steel:
      'En la industria se conoce como RUL. Sustituir un revestimiento es una campaña de varias semanas, por lo que conocer la fecha con meses de antelación convierte una crisis en un proyecto.',
    useIt: 'Use la cifra de confianza junto a ella. Una vida corta con baja confianza necesita más medición, no una acción inmediata.',
  },
  'kpi:confidence': {
    title: 'Confianza del modelo',
    what: 'Qué seguridad tiene el modelo sobre su propia predicción, dados los datos que tenía.',
    steel: 'Los sensores fallan y las lecturas derivan. Publicar la confianza junto a la respuesta evita que un ingeniero confíe en un número basado en pocos datos.',
    useIt: 'Una confianza baja indica que debe revisar la salud de los sensores antes de actuar sobre la predicción.',
  },
  'kpi:failDate': {
    title: 'Fecha proyectada de desgaste',
    what: 'La fecha de calendario a la que apunta la estimación de vida restante.',
    steel: 'Convertir "tantos días" en una fecha permite a los planificadores alinearla con festivos, disponibilidad de contratistas y libros de pedidos.',
    useIt: 'Compárela con la ventana de mantenimiento prevista en la pantalla del planificador.',
  },
  'kpi:anomalies': {
    title: 'Anomalías térmicas',
    what: 'Número de lecturas que se apartaron del patrón esperado en la ventana seleccionada.',
    steel:
      'Un punto caliente local en la carcasa del horno suele ser la primera señal física de que el ladrillo detrás de él se ha adelgazado.',
    useIt: 'Abra el mapa de calor para ver dónde se agrupan las anomalías en la carcasa.',
  },
  'kpi:cooling': {
    title: 'Rendimiento del agua de refrigeración',
    what: 'Con qué eficacia el sistema de refrigeración retira calor de la carcasa del horno.',
    steel:
      'Las placas refrigeradas por agua están entre el ladrillo y la carcasa de acero. Si la refrigeración se debilita, la carcasa se calienta, así que esta es una medición de seguridad, no solo de eficiencia.',
    useIt: 'La combinación importante es un valor que cae con una temperatura de carcasa que sube.',
  },
  'kpi:slope': {
    title: 'Tendencia de temperatura',
    what: 'Con qué rapidez sube o baja la temperatura, en grados por día.',
    steel: 'El desgaste refractario es lento, por lo que una pendiente ascendente persistente de incluso una fracción de grado al día es significativa.',
    useIt: 'El signo importa más que el tamaño. Una pendiente positiva sostenida en un sector merece revisión.',
  },
  'kpi:sensor': {
    title: 'Cobertura de sensores',
    what: 'Cuántos sensores térmicos están enviando datos sanos ahora mismo.',
    steel: 'Las predicciones solo son tan buenas como sus entradas. Un sector con sensores muertos está, en la práctica, sin vigilancia.',
    useIt: 'Contrástelo con la pantalla del parque de dispositivos cuando el recuento baje.',
  },
  'furnace-health/thermal-explorer:kpi:peak': {
    title: 'Temperatura máxima de carcasa',
    what: 'La temperatura más alta medida en la carcasa del horno durante el periodo seleccionado.',
    steel:
      'La carcasa debe mantenerse mucho más fría que el interior fundido. Un pico que sube significa que el calor encuentra un camino a través del revestimiento refractario.',
    useIt: 'Use el mapa de calor para encontrar qué sector produjo el pico.',
  },
  'kpi:open': {
    title: 'Órdenes de trabajo abiertas',
    what: 'Trabajos de mantenimiento creados pero aún no completados.',
    steel: 'Las plantas siderúrgicas funcionan de forma continua, por lo que el mantenimiento compite con la producción por el tiempo. El atraso es el coste visible de aplazarlo.',
    useIt: 'Ordene la tabla de órdenes de trabajo por prioridad para ver qué debe entrar en la próxima ventana.',
  },
  'kpi:urgent': {
    title: 'Órdenes de trabajo urgentes',
    what: 'Trabajos marcados como necesarios antes de la próxima parada planificada.',
    steel: 'Estas son las que deciden si la próxima parada será planificada o forzada.',
    useIt: 'Todo lo que esté aquí debe compararse con la duración de la ventana de mantenimiento.',
  },
  'kpi:completed': {
    title: 'Órdenes de trabajo completadas',
    what: 'Trabajos cerrados en el periodo actual.',
    steel: 'La tasa de finalización frente al atraso indica si la capacidad de mantenimiento encaja con las necesidades de la planta.',
    useIt: 'Léala junto con el recuento abierto. Que ambos bajen es bueno; que solo baje completadas, no.',
  },
  'kpi:window': {
    title: 'Ventana de mantenimiento',
    what: 'La duración de la próxima parada de producción programada disponible para reparaciones.',
    steel:
      'Revestir de nuevo parte de un horno puede llevar días y el recipiente debe enfriarse primero. Encajar el trabajo en la ventana es el problema central del planificador.',
    useIt: 'Compárela con la duración total de las órdenes de trabajo urgentes.',
  },

  // ------------------------------------------------------------------ energy
  'kpi:price': {
    title: 'Precio spot de electricidad',
    what: 'Lo que cuesta ahora un megavatio hora de electricidad en el mercado mayorista.',
    steel:
      'Los precios europeos de la electricidad cambian cada hora y pueden variar varias veces dentro de un día. Una planta que puede mover carga flexible a horas baratas reduce su factura sin producir menos.',
    useIt: 'Alinéelo con la carga prevista en el gráfico de precio y carga.',
  },
  'kpi:savings': {
    title: 'Ahorros proyectados',
    what: 'Dinero que el calendario propuesto ahorraría frente a ejecutar el mismo trabajo a una tarifa plana.',
    steel: 'El ahorro procede solo del momento elegido. Se producen las mismas toneladas, pero en horas más baratas.',
    useIt: 'Esto es una propuesta. Solo se vuelve real cuando un operador aprueba el calendario.',
  },
  'kpi:shiftable': {
    title: 'Carga desplazable',
    what: 'Cuánta demanda eléctrica de la planta puede moverse a otra hora.',
    steel:
      'Un alto horno no puede pausarse, pero los hornos de recalentamiento, trenes de laminación y plantas de oxígeno tienen cierta flexibilidad. Solo esa parte flexible puede perseguir electricidad barata.',
    useIt: 'Marca el techo de lo que cualquier optimización puede lograr.',
  },
  'kpi:baseline': {
    title: 'Escenario de referencia',
    what: 'Cuáles serían el coste y las emisiones sin ningún desplazamiento de carga.',
    steel: 'Toda mejora afirmada necesita algo contra lo que medirse. Esta es esa referencia.',
    useIt: 'Compárelo con el escenario optimizado para leer el beneficio.',
  },
  'kpi:optimized': {
    title: 'Escenario optimizado',
    what: 'Coste y emisiones con el calendario que propone el optimizador.',
    steel: 'El optimizador respeta restricciones reales de planta, como tiempos mínimos de marcha, rampas y límites de conexión a la red, no solo el precio.',
    useIt: 'Revise la tarjeta de violaciones de restricciones antes de confiar en el número.',
  },
  'kpi:estimate': {
    title: 'Estimación de escenario',
    what: 'El resultado de los ajustes de simulación seleccionados ahora mismo en esta pantalla.',
    steel: 'Permite a un planificador probar una idea antes de comprometer la planta.',
    useIt: 'Cambie los deslizadores y observe cómo reacciona este número.',
  },
  'kpi:violations': {
    title: 'Violaciones de restricciones',
    what: 'Cuántas reglas de planta rompería el escenario actual.',
    steel:
      'Las restricciones codifican la realidad física: un horno que debe mantenerse por encima de una temperatura, o un tren que no puede arrancar y parar repetidamente. Un calendario barato que las rompe no es un calendario.',
    useIt: 'Debe ser cero antes de que un escenario pueda proponerse para aprobación.',
  },
  'energy-optimization/load-shift-simulator:kpi:peak': {
    title: 'Demanda máxima',
    what: 'La mayor demanda eléctrica que alcanzaría el escenario.',
    steel:
      'Las conexiones a la red se facturan en parte por el mayor pico alcanzado, por lo que recortar el pico ahorra dinero aunque el consumo total no cambie.',
    useIt: 'Vigílela al desplazar carga. Mover trabajo puede crear por accidente un pico nuevo y más alto.',
  },
  'kpi:server': {
    title: 'Estado del solucionador',
    what: 'Si el motor de optimización encontró una respuesta válida, y qué tan buena es.',
    steel: 'Ser claro sobre si las matemáticas convergieron separa una herramienta de apoyo a la decisión de una caja negra.',
    useIt: 'Un resultado inviable significa que no todas las restricciones pueden cumplirse. Relaje una y vuelva a ejecutar.',
  },

  // ----------------------------------------------------------------- quality
  'kpi:firstpass': {
    title: 'Tasa a la primera',
    what: 'Proporción de lotes que cumplieron la especificación sin retrabajo.',
    steel: 'El retrabajo significa refundir, lo que gasta energía dos veces y retrasa el pedido. La tasa a la primera es donde se juntan calidad y coste.',
    useIt: 'Una caída aquí debería poder rastrearse a una causa en el gráfico de Pareto.',
  },
  'kpi:defect': {
    title: 'Tasa de defectos',
    what: 'Proporción de producción con un defecto registrado.',
    steel: 'Los defectos típicos son grietas superficiales, inclusiones de escoria o una química que se salió del rango del cliente.',
    useIt: 'Use el gráfico de Pareto para encontrar los pocos tipos de defecto que dominan.',
  },
  'kpi:ncr': {
    title: 'Informes de no conformidad',
    what: 'Registros formales creados cuando un lote no cumplió su especificación.',
    steel: 'Los clientes de automoción y construcción auditan estos registros, así que son una obligación de cumplimiento y también una señal de calidad.',
    useIt: 'Abra la tabla para ver qué calidades de producto están afectadas.',
  },
  'kpi:cpk': {
    title: 'Capacidad del proceso (Cpk)',
    what: 'Un solo número que indica con qué holgura el proceso cabe dentro de la tolerancia del cliente.',
    steel:
      'Por encima de 1,33 se considera generalmente capaz; por debajo de 1,0 se esperan defectos por sistema más que por accidente.',
    useIt: 'Léalo con el gráfico de control. Cpk resume lo que el gráfico muestra en detalle.',
  },
  'kpi:ooc': {
    title: 'Puntos fuera de control',
    what: 'Lecturas que cayeron fuera de los límites estadísticos del gráfico de control.',
    steel:
      'Fuera de control no significa fuera de especificación. Significa que el proceso cambió, lo que es una razón para investigar antes de que el cliente lo note.',
    useIt: 'Cada punto debería tener una causa asignada registrada junto a él.',
  },
  'kpi:total': {
    title: 'Mediciones totales',
    what: 'Cuántas lecturas sostienen las estadísticas de esta pantalla.',
    steel: 'Las reglas estadísticas necesitan suficientes datos para tener sentido. Una cifra de capacidad basada en unas pocas muestras no es fiable.',
    useIt: 'Amplíe el rango de tiempo si este recuento es bajo.',
  },
  'kpi:top': {
    title: 'Mayor contribuyente',
    what: 'La categoría única responsable de la mayor parte del problema.',
    steel: 'Los programas de mejora funcionan corrigiendo una causa dominante cada vez, no todo a la vez.',
    useIt: 'Es la primera barra del gráfico de Pareto.',
  },

  // -------------------------------------------------------- sustainability
  'kpi:allowance': {
    title: 'Derechos de emisión',
    what: 'Permisos mantenidos, cada uno de los cuales cubre una tonelada de CO2.',
    steel:
      'Según el Régimen de Comercio de Derechos de Emisión de la Unión Europea (RCDE UE), una planta debe entregar un derecho por cada tonelada emitida. Algunos se conceden gratis, el resto debe comprarse.',
    useIt: 'Compare con el límite y con las emisiones reales para ver la brecha.',
  },
  'kpi:cap': {
    title: 'Límite de derechos',
    what: 'La asignación gratuita que recibe la planta para el año de cumplimiento.',
    steel: 'El límite se reduce cada año por diseño, y ese es el mecanismo que obliga al sector a descarbonizarse.',
    useIt: 'Las emisiones por encima del límite deben cubrirse con derechos comprados.',
  },
  'kpi:used': {
    title: 'Derechos usados',
    what: 'Cuánta asignación se ha consumido en lo que va de año.',
    steel: 'El consumo no es uniforme durante el año. Un invierno frío o una campaña larga lo desplazan.',
    useIt: 'Compare el porcentaje usado con el porcentaje del año transcurrido.',
  },
  'kpi:overage': {
    title: 'Déficit proyectado',
    what: 'Derechos que se prevé que falten a la planta al cierre del año.',
    steel: 'Un déficit debe comprarse en el mercado al precio del carbono que exista entonces, así que es una exposición financiera directa.',
    useIt: 'Multiplique por el precio del carbono para ver el coste, mostrado en la tarjeta de exposición.',
  },
  'kpi:exposure': {
    title: 'Exposición al coste del carbono',
    what: 'El valor monetario del déficit proyectado de derechos.',
    steel: 'Esto convierte un número ambiental en una línea que entiende la dirección financiera, y eso es lo que consigue financiación para la descarbonización.',
    useIt: 'Se mueve tanto con las emisiones de la planta como con el precio de mercado del carbono.',
  },
  'kpi:intensity': {
    title: 'Intensidad de emisiones',
    what: 'CO2 liberado por tonelada de acero producida.',
    steel:
      'La intensidad es la forma justa de comparar plantas y años, porque las emisiones totales bajan simplemente produciendo menos. La intensidad solo baja si el proceso mejora.',
    useIt: 'Use esto en lugar de toneladas totales al juzgar el progreso.',
  },
  'kpi:target': {
    title: 'Objetivo',
    what: 'El valor que la planta se ha comprometido a alcanzar, mostrado junto a donde está realmente.',
    steel: 'Los objetivos de esta demo son compromisos piloto, no resultados medidos. El valor medido siempre se muestra al lado.',
    useIt: 'La brecha entre ambos es lo que el programa de mejora debe cerrar.',
  },
  'kpi:records': {
    title: 'Registros de auditoría',
    what: 'Cuántos eventos se han escrito en el registro de auditoría resistente a manipulaciones.',
    steel: 'Reguladores y clientes preguntan cómo se produjo un número declarado. Cada cálculo aquí deja un registro que responde a eso.',
    useIt: 'Abra la tabla para inspeccionar entradas individuales.',
  },
  'kpi:immutable': {
    title: 'Integridad de cadena',
    what: 'Si el registro de auditoría verifica de extremo a extremo.',
    steel:
      'Cada entrada lleva una huella criptográfica de la anterior. Alterar un registro antiguo rompe todas las huellas posteriores y se ve de inmediato.',
    useIt: 'Cualquier estado distinto de verificado significa que no se debe confiar en el registro.',
  },
  'kpi:models': {
    title: 'Modelos registrados',
    what: 'Cuántos modelos de predicción están registrados con una versión anotada.',
    steel: 'Si una predicción influyó en una decisión, necesita saber exactamente qué versión de qué modelo la produjo.',
    useIt: 'La versión del modelo aparece junto a cada predicción en la tabla de auditoría.',
  },
  'kpi:domains': {
    title: 'Dominios cubiertos',
    what: 'Cuántas áreas de la planta están representadas en la pista de auditoría.',
    steel: 'La cobertura parcial es una brecha de cumplimiento. El objetivo es que toda área relevante para decisiones escriba en el mismo registro.',
    useIt: 'Filtre la tabla de auditoría por dominio para inspeccionar un área.',
  },

  // --------------------------------------------------------------- knowledge
  'kpi:sessions': {
    title: 'Sesiones de captura',
    what: 'Entrevistas grabadas con operadores experimentados y convertidas en borradores de procedimientos.',
    steel:
      'Mucho del saber hacer de una planta siderúrgica vive en la cabeza de personas que han llevado el horno durante treinta años. Capturarlo antes de que se jubilen es un problema industrial real.',
    useIt: 'Abra una sesión para ver la transcripción junto al borrador que produjo.',
  },
  'kpi:coverage': {
    title: 'Cobertura de procedimientos',
    what: 'Proporción de tareas críticas que ya tienen un procedimiento escrito y aprobado.',
    steel: 'Las brechas de cobertura son donde la planta depende de que una sola persona esté disponible.',
    useIt: 'Úsela para priorizar qué entrevistas realizar después.',
  },
  'kpi:approved': {
    title: 'Procedimientos aprobados',
    what: 'Borradores que un humano cualificado ha revisado y firmado.',
    steel: 'Un procedimiento escrito por una máquina y nunca comprobado es una responsabilidad. La aprobación es el control que hace utilizable la salida.',
    useIt: 'Solo los procedimientos aprobados son devueltos como respuestas por el asistente.',
  },
  'kpi:review': {
    title: 'Pendiente de revisión',
    what: 'Borradores que esperan que un humano los acepte, corrija o rechace.',
    steel: 'Esta cola es la puerta de humano en el circuito. Nada la evita.',
    useIt: 'Una cola creciente significa que la capacidad de revisión, no la de captura, es el cuello de botella.',
  },

  // -------------------------------------------------------------- operations
  'kpi:oee': {
    title: 'Eficiencia global de los equipos (OEE)',
    what: 'Un número que combina cuánto tiempo funcionó el equipo, a qué velocidad funcionó y cuánto de la salida fue bueno.',
    steel: 'Es el cuadro de mando estándar de fabricación. Evita que una planta presuma de disponibilidad mientras desecha producto en silencio.',
    useIt: 'Cuando baja, compruebe cuál de las tres partes lo causó.',
  },
  'kpi:throughput': {
    title: 'Producción',
    what: 'Toneladas de acero producidas en el periodo.',
    steel: 'Es la salida de la planta y el denominador de casi cualquier otra medida en este portal.',
    useIt: 'Lea siempre las medidas de intensidad frente a ella. Una producción baja embellece las emisiones totales.',
  },
  'kpi:ontime': {
    title: 'Entrega a tiempo',
    what: 'Proporción de pedidos de clientes enviados antes de la fecha prometida.',
    steel: 'El acero entra en líneas de producción posteriores ya programadas, por lo que una entrega tarde detiene la fábrica de otra persona.',
    useIt: 'Las entregas tardías suelen remontarse a paradas no planificadas o retrabajo.',
  },
  'kpi:alerts': {
    title: 'Alertas activas',
    what: 'Condiciones marcadas actualmente como necesitadas de atención.',
    steel: 'La fatiga de alertas es un riesgo de seguridad real, así que esta plataforma busca pocas alertas con sentido en lugar de muchas.',
    useIt: 'Pulse para ver la señal subyacente de cada alerta.',
  },

  // ---------------------------------------------------------- platform ops
  'kpi:util': {
    title: 'Utilización de capacidad',
    what: 'Cuánta capacidad de cálculo analítico reservada está en uso.',
    steel: 'La plataforma funciona con una capacidad deliberadamente pequeña y pagada por hora, para que un entorno de demostración no cueste como uno de producción.',
    useIt: 'Una utilización alta sostenida es la señal para escalar antes de que los trabajos empiecen a hacer cola.',
  },
  'kpi:utilization': {
    title: 'Utilización de capacidad',
    what: 'Cuánta capacidad de cálculo analítico reservada está en uso.',
    steel: 'La capacidad analítica se factura por hora esté ocupada o no, así que la capacidad ociosa es desperdicio puro.',
    useIt: 'Úsela con la tarjeta de coste para juzgar si el tamaño actual es correcto.',
  },
  'kpi:spend': {
    title: 'Gasto de plataforma',
    what: 'Lo que ha costado la plataforma analítica durante el periodo mostrado.',
    steel: 'Un sistema de apoyo a decisiones debe costar menos que las pérdidas que evita. Mostrar el coste abiertamente forma parte de ese argumento.',
    useIt: 'Compare con los ahorros indicados en las pantallas de energía.',
  },
  'kpi:cost': {
    title: 'Coste',
    what: 'La cifra de dinero para el elemento mostrado en esta tarjeta.',
    steel: 'Cada elección técnica en esta plataforma tiene un precio, y se muestra deliberadamente en lugar de ocultarse.',
    useIt: 'Abra la tabla de costes para ver el desglose por servicio.',
  },
  'kpi:rate': {
    title: 'Tasa de procesamiento',
    what: 'Cuántos registros procesa la canalización por unidad de tiempo.',
    steel: 'Los datos de sensores llegan continuamente. Si la canalización procesa más despacio de lo que llegan los datos, los cuadros de mando se retrasan en silencio.',
    useIt: 'Léala con la frescura de datos. Una tasa sana con datos antiguos significa que algo aguas arriba se detuvo.',
  },
  'kpi:fresh': {
    title: 'Frescura de datos',
    what: 'Cuánto tiempo ha pasado desde que llegó el dato más reciente.',
    steel: 'Una pantalla de sala de control que muestra temperaturas de ayer es peor que no tener pantalla, porque parece actual.',
    useIt: 'Si esto crece, trate cualquier otro número del portal como sospechoso hasta que se recupere.',
  },
}
