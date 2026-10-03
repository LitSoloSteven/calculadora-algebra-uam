# PLAN SCALARIS

# FASE 0: LÍNEA BASE Y SPIKES (sin cambios funcionales)

Sigue las REGLAS del workspace y las ENMIENDAS. Esta fase corresponde a "F0" del plan en docs/PLAN_SCALARIS.md.
Meta: medir y decidir ANTES de escribir la feature.
Restricción: NO modifiques código de producción. Únicas excepciones: borrar src/frontend/views/numeric_systems/roman_view.py (T5) y crear docs/F0_registro_decisiones.md.
Trabaja T1 a T7 en orden y escribe una línea de estado al terminar cada tarea.

## T1. Versiones
Registra: Python, nicegui, plotly, pytest (con pip show). Para Quasar, lee el encabezado de los archivos nicegui/static/quasar*.js o evalúa `Quasar.version` en la consola del navegador.

## T2. Línea base de pruebas y rutas
- Ejecuta `pytest -q` completo. Anota cantidad de tests y fallos. NO arregles nada de src/backend/. Si hay fallos preexistentes, solo repórtalos.
- Smoke: `python -c "import src.frontend.app"`.
- Arranca la app y, con curl sin seguir redirecciones, registra el código de estado y el Location de: /, /gauss, /gauss-jordan, /ia, /sistemas-lineales, /operaciones-matrices, /matriz-inversa, /vectores, /conversor, /romanos. Indica cuáles son cadenas de dos saltos.

## T3. Línea base de rendimiento (servidor)
Con un script temporal fuera de src/ (por ejemplo scratch/bench.py) llama a InverseOpsController.process_inverse con matrices densas de fracciones tipo "7/13", n = 3, 10, 25 y 50. Mide `elapsed_s`, número de pasos y pico de memoria (tracemalloc). Si un caso supera 120 s, aborta y anótalo. Mide también GaussJordanController en 10x10.

## T4. Spikes (solo en src/frontend/_spikes/, desechable)
Crea un entry independiente (`python -m src.frontend._spikes.run_spikes`, puerto 8081) que monte los assets y use setup_theme(). NO lo registres en routes.py. Puedes reutilizar SquareMatrixPanel y EquationGrid solo para lectura. Excepción explícita: el CSS y JS de los spikes es desechable y puede ir local en la página del spike.

- S1 (layout de Quasar): con html[data-glosa="open"] aplica `padding-right: calc(var(--glosa-w) + 32px)` a .q-page-container y desplaza `right` de .q-header (que usa `reveal`), con `--glosa-w: clamp(360px, 32vw, 440px)`.
  Criterios: el contenido se comprime, no hay scroll horizontal de página, la píldora se recentra, `reveal` sigue funcionando y los elementos fixed no se desplazan. Viewports: 1024, 1280, 1440, 1920.
- S2 (Plotly): ui.plotly 2D y 3D (surface). Añade un ResizeObserver por .js-plotly-plot que llame a Plotly.Plots.resize con debounce de 120 ms y guarda si el nodo ya no existe.
  Criterios: la gráfica se ajusta al contenedor tras alternar el dock en menos de 150 ms, el 3D no parpadea y no hay errores de consola al destruir el nodo. Prueba también dentro de un ui.expansion.
- S3 (presupuesto de reflow): cuadrícula 50x50 con SquareMatrixPanel y alternancia del estado del dock. Compara (a) snap y (b) FLIP con translateX (viewport >= 1750), y con `contain: content` en el scroller activado y desactivado. Mide con performance.now() desde el cambio de estado hasta el siguiente frame con lectura de layout forzada; 3 corridas por variante, reporta la mediana.
  Criterio: mediana <= 100 ms.
- S5 (storage): con STORAGE_SECRET definido, verifica que (i) la mutación in-place `app.storage.user['h'].append(...)` persiste tras F5 y tras ui.navigate.to; (ii) el mismo patrón que usa AIPanel.chat_history (get que devuelve la lista) persiste; (iii) dos pestañas del mismo navegador comparten historial. Sin STORAGE_SECRET: qué excepción lanza app.storage.user y qué hace el fallback actual de AIPanel._storage.
- S6 (container queries): aplica `container-type: inline-size` a un wrapper .view-root equivalente al de las vistas (w-full, max-w-7xl, mx-auto, p-6).
  Criterios: el ancho no colapsa a 0; el header sticky de EquationGrid sigue pegado; ui.dialog, ui.notify y ui.menu siguen centrados y visibles; un FAB fixed fuera del .view-root no se afecta; una regla @container (min-width: 900px) conmuta una .layout-split de fila a columna.

Si no puedes controlar un navegador, marca el spike NO PROBADO y deja los pasos manuales exactos para que yo los ejecute. No inventes mediciones.

## T5. Código muerto
Antes de borrar roman_view.py, ejecuta `grep -rn "roman_view" src tests` y confirma que nada lo importa. Si algo lo importa, NO lo borres y repórtalo.

## T6. Registro de decisiones
Crea docs/F0_registro_decisiones.md con estas secciones:
1. Versiones.
2. Línea base de pruebas y de redirecciones.
3. Línea base de rendimiento.
4. Spikes: tabla | ID | criterio | resultado (VERIFICADO/INFERIDO/NO PROBADO) | evidencia | ajuste al plan |.
5. Ajustes propuestos al plan (tabla | Sección del plan | Cambio | Motivo |).
6. Preguntas abiertas.

## T7. Limpieza
Copia al registro el código mínimo reproducible de cada spike y luego borra src/frontend/_spikes/ y scratch/. `git status` final: solo debe aparecer el borrado de roman_view.py y el nuevo docs/F0_registro_decisiones.md.

## Cierre
Entrega el INFORME DE FASE y DETENTE. No empieces F1.
