# Plan de Ejecución: Cumplimiento Completo de Reglas SCALARIS

## Objetivo
Llevar la totalidad del repositorio al cumplimiento estricto y verificable de las reglas SCALARIS (secciones 0 a 14), preservando exactamente el comportamiento matemático y observable bajo las excepciones explícitas autorizadas E1 a E7.

---

## Excepciones Explícitas del Usuario (Sección 0, Punto 2)

- **E1 Backend editable**: `src/backend` es editable para esta tarea. Prohibido cambiar el comportamiento matemático: aritmética exacta con `Fraction`, mismos resultados numéricos y mismos textos de pasos que ya cumplen. No se redacta MANUAL DE REQUERIMIENTOS PARA BACKEND.
- **E2 Pruebas**: Edición de pruebas existentes permitida solo para: (a) seguir renombrados, (b) renombrar archivos y funciones a español descriptivo sin referencias a fases (`f4`, `f8c`, `f9`, `p5`, `h7`...), (c) extraer helpers duplicados a módulo común `tests/comun.py`, (d) actualizar aserciones cuyo valor cambia por E5 o E6. Prohibido borrar pruebas, debilitar aserciones o cambiar su intención. Registro obligatorio de tabla "aserción antes / después". Código nuevo con lógica lleva pruebas en archivos nuevos.
- **E3 Cero alias**: Ningún nombre en inglés se conserva como alias. Renombrado y propagación en el mismo paso a todo el repositorio (`src`, `tests`, JS, CSS, cadenas con selectores, atributos `data-*`), limitándose al renombrado fuera del alcance de la fase.
- **E4 Contratos internos**: Pasan a español ASCII: claves y valores de retorno y JSON entre capas (ej. `SOLUCION_UNICA`), nombres de módulos, archivos, carpetas, globales JS (`window.scalaris`), atributos `data-*`, ids y clases CSS con prefijo por módulo. Se conservan en su idioma original únicamente: APIs de NiceGUI, Quasar, Tailwind, Plotly, MathJax, FastAPI y stdlib; propiedades CSS y eventos del navegador; dunders; tokens de diseño (`--bg-page`, `--text-main`...); variables de entorno (`OPENROUTER_*`, `SCALARIS_ENV`, `STORAGE_SECRET`, `SCALARIS_NAV`, `SCALARIS_DOCK`, `SCALARIS_PROACTIVE`); claves del payload de OpenRouter; carpetas `src/frontend`, `src/backend`, `src/ai` y `main.py`; y tecnicismos autorizados de la sección 5.1.
- **E5 Movimiento**: Duraciones $\le 250\text{ ms}$, entradas desde `scale(0.95)` y opacidad 0; splash y cambio de tema con fundido $\le 250\text{ ms}$; `:active` con `scale(0.97)` o `scale(0.98)`; eliminación de `ease-elastic`, `ease-in`, `ease-in-out`, `filter` y animaciones de `width` o `clip-path`.
- **E6 CSS**: División modular de `theme.css` en hojas semánticas $\le 300$ líneas. Reemplazo de banners de bloque por localización por archivo y selector en las pruebas.
- **E7 Dominio**: Lógica matemática y reglas de dominio migradas al backend. Controladores y vistas solo delegan y serializan. Eliminación de validaciones duplicadas en la interfaz.

---

## Glosario de Renombrado Ampliado (Única Fuente de Verdad)

| Concepto en Inglés | Concepto en Español ASCII | Contexto / Claves / Atributos |
|---|---|---|
| Matrix | Matriz | filas, columnas, datos, obtener, establecer, clonar, intercambiar_filas, sumar_fila_escalada |
| solve / solver / solvers | resolver / resolutor / resolutores | resolver_sistema, resolutor_inversa, etc. |
| status / state | estado | Clave de respuesta |
| message | mensaje | Clave de respuesta |
| steps / step | pasos / paso | Clave de respuesta |
| solution | solucion | Clave de respuesta |
| add / addition | sumar / suma | Operaciones algebraicas |
| subtract / subtraction | restar / resta | Operaciones algebraicas |
| multiply / multiplication | multiplicar / multiplicacion | Operaciones algebraicas |
| transpose | transponer / transpuesta | Operaciones algebraicas |
| determinant | determinante | Operaciones algebraicas |
| inverse | inversa | Operaciones algebraicas |
| controller / controllers | controlador / controladores | Capa de mediación |
| view / views | vista / vistas | Capa de presentación |
| components | componentes | Elementos reutilizables UI |
| models | modelos | Modelos de dominio backend |
| utils | utilidades | Módulos auxiliares backend |
| build | construir | Ensamblado de componentes y vistas |
| UNIQUE_SOLUTION | SOLUCION_UNICA | Constante y estado de retorno |
| INFINITE_SOLUTIONS | SOLUCIONES_INFINITAS | Constante y estado de retorno |
| NO_SOLUTION | SIN_SOLUCION | Constante y estado de retorno |
| SUCCESS | EXITO | Estado de retorno |
| UNIQUE | UNICA | Tipo de solución |
| INFINITE | INFINITA | Tipo de solución |
| ERROR | ERROR | Se conserva idéntico |
| SINGULAR | SINGULAR | Se conserva idéntico |
| linear_systems | sistemas_lineales | Paquetes y rutas |
| matrix_ops | operaciones_matrices | Paquetes y rutas |
| vector_ops | operaciones_vectores | Paquetes y rutas |
| numeric_systems | sistemas_numericos | Paquetes y rutas |
| inverse_ops | operaciones_inversas | Paquetes y rutas |
| geometry | geometria | Paquetes y rutas |
| validators | validadores | Módulo de utilidades |
| parsers | analizadores | Módulo de utilidades |
| formatters | formateadores | Módulo de utilidades |
| constants | constantes | Módulo de backend |
| exceptions | excepciones | Módulo de backend |

---

## Fases de Ejecución

### Fase 0: Línea Base, Limpieza de Conflictos e Infraestructura de Verificación
- **Estado**: Completada
- **Archivos**: `controllers/linear_systems/_shared.py`, `views/vector_ops/results_mixin.py`, `docs/PLAN_cumplimiento_reglas.md`, `tests/test_cumplimiento_reglas.py`.
- **Criterios de aceptación**:
  - Cero marcadores de conflicto de merge en todo el repositorio.
  - Verificación exitosa con `python -m compileall src`.
  - Línea base de `pytest` registrada (1099 pruebas pasando, 0 fallos).
  - Plan de ejecución temporal creado en `docs/PLAN_cumplimiento_reglas.md`.
  - Arnés `tests/test_cumplimiento_reglas.py` creado con `RUTAS_AUDITADAS` inicializado.
  - Inventario inicial medido entregado.

### Fase 1: Capa de Dominio y Backend (`src/backend`) (E1, E3, E4, E7)
- **Estado**: En progreso (Sub-entrega 1.1 completada; Sub-entregas 1.2 y 1.3 pendientes)
- **Sub-entregas**:
  - **Sub-entrega 1.1: Modelos y Utilidades** [COMPLETADA]
    - Modelos: `src/backend/modelos/matriz.py`, `src/backend/modelos/__init__.py`.
    - Utilidades: `src/backend/utilidades/utilidades_matematicas.py`, `formateadores.py`, `validadores.py`, `verificacion.py`, `reglas_dominio.py`, `__init__.py`.
    - Constantes y Excepciones: `src/backend/constantes.py`, `src/backend/excepciones.py`.
    - Eliminado `src/backend/test_backend.py` (movido a `tests/`).
    - Auditado con `tests/test_cumplimiento_reglas.py` y `tests/test_backend_modelos_utilidades.py`.
  - **Sub-entrega 1.2: Sistemas Lineales y Operaciones Matriciales** [PENDIENTE]
    - Resolutores: `gauss.py`, `gauss_jordan.py`, `operations.py`, `inverse.py`, `evaluator.py`, `determinant.py`, `transformations.py`, `leontief.py`.
    - Modularización de `solve`, `_back_substitute`, `_eliminate` ($\le 40$ líneas).
    - Eliminación de código muerto en transformaciones y deduplicación de determinante.
  - **Sub-entrega 1.3: Vectores y Sistemas Numéricos** [PENDIENTE]
    - `linear_combination.py`, `operations.py`, `_base.py`, `conversor_bases.py`, `roman_calculator.py`.
    - Deduplicación de transpuesta entre solvers, eliminación de paquetes antiguos y cierre de backend completo.
- **Criterios de aceptación**:
  - Modelos y utilidades en español ASCII sin alias.
  - Módulos $\le 300$ líneas, funciones $\le 40$ líneas.
  - Pruebas matemáticas exactas pasando con resultados numéricos idénticos.

### Fase 2: Módulo de IA y Contratos de Contexto (`src/ai`) (E3, E4)
- **Estado**: Completada
- **Archivos**: `src/ai/constantes.py`, `src/ai/clasificador_respuestas.py`, `src/ai/estrategias_recorte.py`, `src/ai/openrouter_ai.py`, `src/ai/context.py`, `src/ai/prompts.py`.
- **Criterios de aceptación cumplidos**:
  - Módulos $\le 300$ líneas, funciones $\le 40$ líneas, clases $\le 200$ líneas, anidamiento $\le 3$, complejidad ciclomática $\le 10$.
  - Desacoplamiento de `_serialize_context_core` en 6 estrategias atómicas de recorte y `OpenRouterIA.ask` en pasos nombrados.
  - Eliminación de código muerto (`analizar_sistema`, variable `nonzero` en `describir_matriz`, imports a mitad de archivo, Protocol huérfano).
  - Unificación de constantes (TTL 3600 s, caché 128, deadline 40 s, timeouts, códigos transitorios y límites de contexto) en `src/ai/constantes.py`.
  - Inyectables de pruebas renombrados a español ASCII (`_bloqueo_cache`, `_cache_respuestas`, `_peticiones_post`, `_tiempo_monotonico`, `_tiempo_dormir`, `MODELO_PRIMARIO`, `MODELOS_RESERVA`) y propagados con cero alias (E3, E4).
  - Prompts y mensajes en español con tuteo, sin raya larga (`—`) y sin filtración de detalles internos.
  - Ampliación de `RUTAS_AUDITADAS` en `tests/test_cumplimiento_reglas.py` con todos los módulos de `src/ai`.
  - Suite de 1112 pruebas pasando al 100%.

### Fase 3: Núcleo de Aplicación y Navegación Frontend (E3, E4)
- **Estado**: Completada
- **Archivos**: `src/main.py`, `src/frontend/app.py`, `routes.py`, `flags.py`, `helpers.py`, `suggestions.py`, `catalogo_sugerencias.py`, `theme.py`, `constantes.py`, `textos.py`, y paquete `src/frontend/navigation/` (`modelo.py`, `catalogo.py`, `consultas.py`, `redirecciones.py`, `__init__.py`).
- **Criterios de aceptación cumplidos**:
  - `navigation.py` modularizado en paquete de 4 submódulos (`modelo`, `catalogo`, `consultas`, `redirecciones`), todos $\le 165$ líneas y funciones $\le 40$ líneas.
  - Resolución dinámica de `HUB_ENABLED` en tiempo de llamada conservada en `legacy_redirects`.
  - Catálogo de sugerencias desacoplado como datos puros a `catalogo_sugerencias.py` y lógica de selección optimizada ($\le 40$ líneas, complejidad ciclomática $\le 10$).
  - Creación de `src/frontend/constantes.py` (límites de dimensión 10 y 50, debounces 0.25, 0.3, 0.35 s, `MAX_HISTORIAL`, TTL y tamaño de handoff, anti-rebote de envío a Glosa) y migración de todos sus consumidores en el frontend.
  - Creación de `src/frontend/textos.py` centralizando copy repetido (mensajes de handoff, avisos de secretos y anti-rebote).
  - Paleta de gráficos en `theme.py` con contraste no textual $\ge 3.0:1$ verificado en los tres temas (`papel`, `marea`, `medianoche`) y consumida como fuente única por JS en `app.js` (`window.scalaris.graficos`).
  - Identificadores en español ASCII sin alias (`resolver_secreto_almacenamiento`, `inicializar_aplicacion`, `ejecutar`, `registrar_rutas`, `a_flotante`, `formatear_paso_mathjax`).
  - Ampliación de `RUTAS_AUDITADAS` en `tests/test_cumplimiento_reglas.py` a 30 archivos, pasando al 100%.
  - Suite de 1112 pruebas pasando (`0 failed, 1112 passed`).

### Fase 4: Sistema de Estilos CSS, Scripts JS y Movimiento (E4, E5, E6)
- **Estado**: Pendiente
- **Archivos**:
  - `src/frontend/assets/css/theme.css` dividido en módulos semánticos $\le 300$ líneas (`tokens.css`, `base.css`, `layout.css`, `componentes.css`, `vistas.css`).
  - `src/frontend/assets/css/reproductor_pasos.css`.
  - `src/frontend/assets/js/` (espacio de nombres único `window.scalaris`, animaciones $\le 250\text{ ms}$, scale(0.95), sin animaciones prohibidas).
- **Criterios de aceptación**:
  - Todos los archivos CSS $\le 300$ líneas.
  - Animaciones conformes a E5 y sección 8.
  - Cero colores literales fuera de definición de tokens.

### Fase 5: Controladores de Interfaz (`src/frontend/controllers`) (E3, E4, E7)
- **Estado**: Pendiente
- **Archivos**: `src/frontend/controllers/` (`sistemas_lineales`, `operaciones_matrices`, `operaciones_vectores`, `operaciones_inversas`, `geometria`, `_agrupar_pasos.py`, `_step_classifier.py`).
- **Criterios de aceptación**:
  - Los controladores únicamente validan, delegan y serializan hacia el backend.
  - Eliminación de validaciones duplicadas delegando al backend (E7).
  - Cero código duplicado entre controladores.

### Fase 6: Componentes de Interfaz (`src/frontend/components`) (E3, E4)
- **Estado**: Pendiente
- **Archivos**: `src/frontend/components/` (`ai_panel.py`, `glosa_dock.py`, `matrix_capture.py`, `vector_capture.py`, `square_matrix_panel.py`, `handoff.py`, etc.).
- **Criterios de aceptación**:
  - Ningún componente supera 300 líneas ni contiene lógica de dominio.
  - Accesibilidad completa: foco visible, nombres accesibles, roles semánticos y cifras tabulares.

### Fase 7: Vistas de Usuario (`src/frontend/views`) (E3, E4, E5)
- **Estado**: Pendiente
- **Archivos**: `src/frontend/views/` (`hub/`, `linear_systems/`, `matrix_ops/`, `vector_ops/`, `inverse_ops/`, `geometry/`, `numeric_systems/`).
- **Criterios de aceptación**:
  - Vistas orquestan sin lógica de negocio ni parseo.
  - Cadenas HTML/JS/CSS largas extraídas a assets o plantillas.
  - Copy en tuteo, sin raya larga ni exclamaciones en éxito.

### Fase 8: Armonización de la Suite de Pruebas y Cierre (E2)
- **Estado**: Pendiente
- **Archivos**: `tests/` completo, `tests/comun.py`, `tests/test_cumplimiento_reglas.py`.
- **Criterios de aceptación**:
  - Todas las pruebas en `tests/` renombradas a español descriptivo sin prefijos de fase (`f4`, `f8c`, `f9`, etc.).
  - Extracción de helpers duplicados a `tests/comun.py`.
  - Ejecución de `test_cumplimiento_reglas.py` sobre la totalidad del repositorio (`RUTAS_AUDITADAS` cubre todo el proyecto, 100% verificado).
  - Eliminación de este plan temporal al completar satisfactoriamente la auditoría.
