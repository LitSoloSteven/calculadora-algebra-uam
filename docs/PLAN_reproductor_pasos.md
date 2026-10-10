# Plan: reproductor de pasos

## 1. OBJETIVO

### a) Reproductor compartido
Todos los módulos que muestran pasos (Sistemas de ecuaciones Gauss y Gauss-Jordan, Matrices, Vectores, Conversor de bases y Números romanos) usarán el mismo reproductor interactivo que hoy tiene Matriz inversa. Incluirá navegación al primero, anterior, siguiente y último; reproducción automática con selección de velocidad; slider; barra de progreso; chip del tipo de paso; explicación; índice por fases; y botón de Glosa para el paso actual. La migración de Matriz inversa conservará su presentación y comportamiento actuales.

### b) Sistemas de ecuaciones
Quitar el desplegable «Visualización Gráfica» de Sistemas de ecuaciones, porque ya existe el botón «Ver en el Visualizador».

### c) Vista previa
Corregir la vista previa del modo Ecuaciones de Sistemas, que actualmente no muestra contenido.

## 2. ALCANCE

- **Editable:** `src/frontend/` (vistas, componentes, controladores y assets) y `src/ai/`.
- **Protegido:** `src/backend/`; solo lectura e importación.
- No se prevé un **MANUAL DE REQUERIMIENTOS PARA BACKEND**. Si alguna fase requiere soporte que no existe en el backend, detener esa fase y redactar el manual requerido por las reglas del agente antes de continuar.

## 3. FASES

### F1. Vista previa del modo Ecuaciones
- **Archivos:** `src/frontend/views/linear_systems/_vista_previa.py`, `src/frontend/views/linear_systems/preview_mixin.py`, `src/frontend/views/linear_systems/results_mixin.py`, `src/frontend/views/linear_systems/sync_mixin.py`, `src/frontend/views/linear_systems/view_linear_systems.py`, `src/frontend/assets/js/app.js` y `tests/test_vista_previa_ecuaciones.py`.
- **Criterio de aceptación:** al activar Vista previa en modo Ecuaciones se renderizan las ecuaciones ingresadas, se actualiza al editar, añadir, quitar o cambiar de modo, y los estados vacío e inválido presentan una orientación clara. La vista previa del modo Matriz conserva matriz aumentada, fracciones y el marcador gris para celdas inválidas. El análisis limita el volumen de entrada y los IDs de MathJax se reintentan si todavía no están montados.
- **Estado:** implementada; suite global y comprobación visual manual pendientes.

### F2. Quitar visualización gráfica de Sistemas
- **Archivos:** `src/frontend/views/linear_systems/graphics_mixin.py`, `src/frontend/views/linear_systems/results_mixin.py` y `src/frontend/views/linear_systems/view_linear_systems.py`.
- **Criterio de aceptación:** desaparece el desplegable «Visualización Gráfica» y se conserva el botón «Ver en el Visualizador» con el traspaso de datos operativo; no se eliminan otros resultados de Sistemas.
- **Estado:** pendiente.

### F3. Componente compartido y migración de Matriz inversa
- **Archivos:** nuevo `src/frontend/components/reproductor_pasos/` (API pública, renderizado y adaptación de datos en módulos separados según responsabilidades); `src/frontend/views/inverse_ops/steps_mixin.py`, `src/frontend/views/inverse_ops/_render.py`, `src/frontend/views/inverse_ops/_config.py`, `src/frontend/views/inverse_ops/view_inverse_ops.py`; nuevo `src/frontend/assets/css/reproductor_pasos.css`; `src/frontend/theme.py` para enlazar el CSS y cualquier script nuevo desde `_HEAD_HTML`; pruebas nuevas en archivos separados dentro de `tests/` si se incorpora lógica.
- **Criterio de aceptación:** Matriz inversa usa el componente compartido con controles, explicación, índice y Glosa funcionales; su salida visual y sus interacciones existentes se conservan. Se respetan las salidas de `InverseOpsController.process_inverse` y `InverseOpsController.build_focus_for_step`. Los assets se enlazan desde `_HEAD_HTML`, sin modificar `theme.css`.
- **Estado:** implementación y pruebas focalizadas completadas (29 pasaron); suite global detenida durante `tests/test_conversor_ui_logic.py::test_cambiar_base_destino_permite_decimal[asyncio]`; verificación visual manual pendiente.

### F4. Sistemas de ecuaciones (Gauss y Gauss-Jordan)
- **Archivos:** `src/frontend/views/linear_systems/results_mixin.py`, `src/frontend/controllers/linear_systems/controller_gauss.py`, `src/frontend/controllers/linear_systems/controller_gauss_jordan.py`, `src/frontend/controllers/linear_systems/_shared.py`, y `src/frontend/components/reproductor_pasos/`.
- **Criterio de aceptación:** ambas variantes muestran los pasos en el reproductor compartido con todas sus funciones y Glosa; se mantienen disponibles y compatibles `intermediate_steps_latex`, `steps_meta`, `back_substitution_steps` y `verification_steps_latex`, además de las claves existentes. Sistemas de 10x10 con fracciones de denominador de cuatro dígitos se pueden consultar sin desbordar el diseño.
- **Estado:** implementada; suite global completada (1002 pasaron); verificación visual manual pendiente.

### F5. Matrices
- **Archivos:** `src/frontend/views/matrix_ops/view_matrix_ops.py`, `src/frontend/controllers/matrix_ops/controller_matrix_ops.py` y `src/frontend/components/reproductor_pasos/`.
- **Criterio de aceptación:** todos los pasos y segmentos de operaciones matriciales se presentan mediante el reproductor compartido, con navegación, explicación, índice y Glosa. Se conserva `segment_steps` y el resto del contrato actual; las operaciones de celdas siguen vinculadas al paso correspondiente.
- **Estado:** pendiente.

### F6. Vectores
- **Archivos:** `src/frontend/views/vector_ops/results_mixin.py`, `src/frontend/controllers/vector_ops/controller_vector_ops.py`, `src/frontend/controllers/vector_ops/_shared.py` y `src/frontend/components/reproductor_pasos/`.
- **Criterio de aceptación:** pasos de preparación, Gauss, sustitución y verificación que actualmente se muestran se integran en el reproductor con controles, índice y Glosa; se mantienen `setup_steps`, `gauss_steps`, `steps`, `steps_meta` y `back_substitution_steps`. Vectores de dimensión 10 con 9 vectores conservan desplazamiento y legibilidad.
- **Estado:** pendiente.

### F7. Conversor de bases
- **Archivos:** `src/frontend/views/numeric_systems/rendering_mixin.py`, `src/frontend/views/numeric_systems/interaction_mixin.py`, `src/frontend/views/numeric_systems/view_numeric_systems.py` y `src/frontend/components/reproductor_pasos/`.
- **Criterio de aceptación:** expansiones posicionales y divisiones sucesivas se recorren desde el reproductor compartido, con navegación, velocidad, slider, progreso, tipo, explicación, fases y Glosa. Se preservan los métodos `_agrupar`, `_limpiar_resultados`, `_marcar_resultado_desincronizado` y `_cambiar_base_destino` compatibles con los dobles de `tests/test_conversor_ui_logic.py`. Se contemplan números de 200 bits.
- **Estado:** pendiente.

### F8. Números romanos, verificación global y cierre
- **Archivos:** `src/frontend/views/numeric_systems/view_roman_calculator.py`, `src/frontend/components/reproductor_pasos/` y, si se necesitan estilos o scripts adicionales, `src/frontend/assets/css/reproductor_pasos.css`, `src/frontend/theme.py` y assets dedicados enlazados desde `_HEAD_HTML`; al cierre, eliminar `docs/PLAN_reproductor_pasos.md`.
- **Criterio de aceptación:** procedimiento de operaciones romanas y construcción canónica se presenta en el reproductor compartido con Glosa y navegación; conversión y reglas actuales siguen operativas. Se completa verificación global contra las restricciones heredadas, los contratos y los datos desfavorables, se ejecutan las verificaciones y revisiones exigidas y se informa su estado honestamente. Al entregar F8 se elimina este plan temporal.
- **Estado:** pendiente.

## 4. RESTRICCIONES HEREDADAS DE LAS PRUEBAS EXISTENTES

Estas restricciones son contrato y no se editan ni debilitan:

- `src/frontend/assets/css/theme.css` no se modifica. Las pruebas leen su texto: exactamente 3 apariciones de `container-type: inline-size`, sin `100vh`, sin `ease-elastic` en ciertos bloques y con tokens en 4 bloques, entre otros contratos. Los estilos nuevos van en `src/frontend/assets/css/reproductor_pasos.css`; se enlazan desde `src/frontend/theme.py` en `_HEAD_HTML`. Los scripts nuevos también se enlazan desde `_HEAD_HTML`.
- No renombrar ni borrar las clases CSS existentes `.inv-*`, `.chip-*` ni `.chip-kind`; las pruebas las leen y deben reutilizarse. Las clases nuevas llevan el prefijo `repro-`.
- Todo `ui.button(icon=...)` sin texto posicional y todo `ui.switch` sin texto lleva `aria-label` dentro del `.props(...)` encadenado en la misma expresión, conforme a la auditoría AST.
- Todo literal con `$$` en `views/` y `components/` debe tener la cadena `math-scroll-container` a 10 líneas o menos.
- Ninguna constante de cadena en `src/frontend/` ni `src/ai/` contiene `—`, `Oops` ni voseo (por ejemplo: ingresá, añadí, escribí, presioná o pegá).
- Sin `100vh`, `backdrop-filter` ni `blur(`, salvo en `splash.js`; sin `z-index` numérico mayor que 10; ningún nombre sin definir o sin importar.
- `views/linear_systems/results_mixin.py` conserva literalmente `overflow-wrap: anywhere;` y `min-w-0 max-w-full`. `views/vector_ops/results_mixin.py` conserva `math-scroll-container`, `html.escape(coef_str)` y `html.escape(sol_str)`.
- Los contratos de controladores solo se amplían con claves nuevas; no se elimina ninguna. Deben preservarse, entre otras, `intermediate_steps_latex`, `steps_meta`, `back_substitution_steps`, `verification_steps_latex`, `segment_steps`, `setup_steps`, `gauss_steps` y `steps`.
- `InverseOpsController.process_inverse`, `InverseOpsController.build_focus_for_step` y `MatrixOpsController.build_step_focus` conservan sus salidas.
- `NumericSystemsUI` mantiene `_agrupar`, `_limpiar_resultados`, `_marcar_resultado_desincronizado` y `_cambiar_base_destino` compatibles con los dobles de `tests/test_conversor_ui_logic.py`.
- Movimiento: ninguna acción de teclado anima; solo se animan `transform` y `opacity`, durante 250 ms como máximo, con `prefers-reduced-motion` obligatorio en todo CSS nuevo.
- Casos desfavorables: Sistemas 10x10 con fracciones de denominador de 4 dígitos; inversa 50x50; vectores de dimensión 10 con 9 vectores; números de 200 bits en distintas bases; ancho de 320 px.

## 5. ESTADO

| Fase | Estado |
|---|---|
| F1. Vista previa del modo Ecuaciones | implementada; suite global y comprobación visual manual pendientes |
| F2. Quitar visualización gráfica de Sistemas | implementada; suite global y verificación visual manual pendientes |
| F3. Componente compartido y migración de Matriz inversa | implementación y pruebas focalizadas completadas (29 pasaron); suite global detenida en una prueba del conversor; verificación visual manual pendiente |
| F4. Sistemas de ecuaciones Gauss y Gauss-Jordan | implementada; suite global completada (1002 pasaron); verificación visual manual pendiente |
| F5. Matrices | pendiente |
| F6. Vectores | pendiente |
| F7. Conversor de bases | pendiente |
| F8. Números romanos, verificación global y cierre | pendiente |
