# Plan de Ejecución: Cumplimiento Completo de Reglas SCALARIS

## Objetivo
Llevar la totalidad del repositorio al cumplimiento estricto de las reglas SCALARIS (secciones 0 a 14) preservando exactamente el comportamiento matemático y observable, bajo las excepciones autorizadas E1 a E7.

---

## Glosario de Renombrado Ampliado (Única Fuente de Verdad)

| Concepto en Inglés | Concepto en Español ASCII | Notas / Atributos / Claves |
|---|---|---|
| Matrix | Matriz | rows=filas, cols=columnas, data=datos, get=obtener, set=establecer, clone=clonar |
| solve / solver / solvers | resolver / resolutor / resolutores | solve_system -> resolver_sistema |
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
| controller / controllers | controlador / controladores | Capa de frontend |
| view / views | vista / vistas | Capa de frontend |
| components | componentes | Capa de frontend |
| models | modelos | Capa de backend |
| utils | utilidades | Módulos auxiliares |
| build | construir | Funciones de ensamblado |
| UNIQUE_SOLUTION | SOLUCION_UNICA | Constante y estado de retorno |
| INFINITE_SOLUTIONS | SOLUCIONES_INFINITAS | Constante y estado de retorno |
| NO_SOLUTION | SIN_SOLUCION | Constante y estado de retorno |
| SUCCESS | EXITO | Estado de respuesta |
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

### Fase 1: Higiene inicial, resolución de conflictos de fusión e infraestructura de prueba de cumplimiento
- **Estado**: Completada
- **Archivos de la fase**:
  - Eliminación: `check_dry_refactor.py`, `replace_ls.py`, `replace_romanos.py`, `replace_script.py`, `replace_vo.py`, directorio `regression_output/`.
  - Corrección: `src/frontend/controllers/linear_systems/_shared.py` (eliminar marcadores de conflicto de fusión).
  - Corrección: `src/frontend/views/vector_ops/results_mixin.py` (eliminar marcadores de conflicto de fusión y código residual de HEAD).
  - Creación: `tests/test_cumplimiento_reglas.py` (auditoría programática de límites duros de líneas/funciones, comentarios prohibidos y glosario para archivos bajo alcance).
- **Criterios de aceptación**:
  - Cero scripts sueltos de parcheo en la raíz del repositorio.
  - Cero marcadores de conflicto de fusión en el árbol de trabajo.
  - Ejecución completa y exitosa de `pytest` en el entorno virtual (`venv`).
  - `tests/test_cumplimiento_reglas.py` operativo y validando los archivos de la Fase 1.

### Fase 2: Núcleo del Backend, Modelos y Utilidades (E1, E3, E4, E7)
- **Estado**: Pendiente
- **Archivos de la fase**:
  - `src/backend/models/matrix.py` -> `matriz.py`
  - `src/backend/constants.py` -> `constantes.py`
  - `src/backend/exceptions.py` -> `excepciones.py`
  - `src/backend/utils/` -> `utilidades/` (`formatters.py`, `parsers.py`, `math_utils.py`, división de `validators.py` <= 300 líneas)
  - Migración de lógica de dominio desde controladores frontend (E7).
  - Reubicación de `src/backend/test_backend.py` a `tests/test_backend_dominio.py`.
  - Propagación de renombrados nucleares sin alias en todo el repositorio (E3).
- **Criterios de aceptación**:
  - Todos los identificadores y contratos en español ASCII.
  - Módulos con menos de 300 líneas y funciones con menos de 40 líneas.
  - Toda la suite de pruebas del backend pasa.

### Fase 3: Resolutores del Backend (E1, E3, E4)
- **Estado**: Pendiente
- **Archivos de la fase**:
  - `src/backend/solvers/` -> `resolutores/`
  - `sistemas_lineales/` (gauss, gauss_jordan, etc.)
  - `operaciones_matrices/` (evaluador de expresiones, determinantes, etc.)
  - `operaciones_vectores/`
  - `sistemas_numericos/`
  - `_rastreo.py`
- **Criterios de aceptación**:
  - Métodos `resolver`, `pasos`, etc. en español ASCII.
  - Límites de tamaño y complejidad respetados.
  - Pruebas matemáticas pasando con resultados numéricos idénticos.

### Fase 4: Módulo de IA y Contratos de Contexto (`src/ai`) (E3, E4)
- **Estado**: Pendiente
- **Archivos de la fase**:
  - `src/ai/openrouter_ai.py`
  - `src/ai/context.py`
  - `src/ai/prompts.py`
- **Criterios de aceptación**:
  - Límites de 300 líneas por archivo y 40 líneas por función.
  - Identificadores y comentarios limpios en español.
  - Variables de entorno `OPENROUTER_*` y claves de la API de OpenRouter conservadas (E4).

### Fase 5: Sistema de Estilos CSS, Scripts JS y Movimiento (E4, E5, E6)
- **Estado**: Pendiente
- **Archivos de la fase**:
  - `src/frontend/assets/css/theme.css` dividido en módulos semánticos <= 300 líneas (`tokens.css`, `base.css`, `layout.css`, `componentes.css`, `vistas.css`).
  - `src/frontend/assets/css/reproductor_pasos.css`.
  - `src/frontend/assets/js/` (agrupación bajo `window.scalaris`, tiempos <= 250 ms, scale(0.95), sin animaciones prohibidas).
- **Criterios de aceptación**:
  - Archivos CSS <= 300 líneas.
  - Animaciones conformes a E5 y sección 8.
  - Pruebas de estilos adaptadas a la nueva estructura de archivos.

### Fase 6: Componentes de Interfaz (`src/frontend/components` -> `componentes`) (E3, E4)
- **Estado**: Pendiente
- **Archivos de la fase**:
  - Todos los módulos en `src/frontend/components/` -> división de los que superan 300 líneas (`ai_panel.py`, `glosa_dock.py`, `matrix_capture.py`, `vector_capture.py`, `square_matrix_panel.py`, `handoff.py`).
  - Cumplimiento de accesibilidad, foco visible y cifras tabulares.
- **Criterios de aceptación**:
  - Ningún componente supera 300 líneas ni contiene lógica de dominio.
  - Identificadores en español ASCII.

### Fase 7: Controladores de Interfaz (`src/frontend/controllers` -> `controladores`) (E3, E4, E7)
- **Estado**: Pendiente
- **Archivos de la fase**:
  - Módulos en `src/frontend/controllers/` (`sistemas_lineales`, `operaciones_matrices`, `operaciones_vectores`, `operaciones_inversas`, `geometria`).
  - Eliminación de validaciones duplicadas delegando al backend (E7).
- **Criterios de aceptación**:
  - Controladores únicamente validan, delegan y serializan.
  - Cero código duplicado entre controladores.

### Fase 8: Vistas y Núcleo de Aplicación (`src/frontend/views` -> `vistas`, `app.py`, `navigation.py`) (E3, E4, E5)
- **Estado**: Pendiente
- **Archivos de la fase**:
  - `src/frontend/views/`
  - `src/frontend/app.py`, `navigation.py`, `routes.py`, `suggestions.py`, `flags.py`, `helpers.py`, `theme.py`
  - `src/main.py`
- **Criterios de aceptación**:
  - Vistas orquestan sin lógica de negocio ni parseo.
  - Extracción de cadenas HTML/JS/CSS largas a archivos de assets.
  - Copy en tuteo, sin raya larga ni exclamaciones en éxito.

### Fase 9: Armonización de la Suite de Pruebas y Auditoría Final (E2)
- **Estado**: Pendiente
- **Archivos de la fase**:
  - Pruebas en `tests/` renombradas a español descriptivo sin prefijos de fase (`f4`, `f8c`, `f9`, `p5`, `h7`...).
  - Extracción de helpers repetidos a módulo común `tests/comun.py`.
  - Ejecución de `test_cumplimiento_reglas.py` sobre todo el repositorio (100% verificado).
  - Eliminación de este plan al completar satisfactoriamente la auditoría.
- **Criterios de aceptación**:
  - Suite de pruebas completa pasando limpia.
  - 100% de cumplimiento de las reglas SCALARIS.
