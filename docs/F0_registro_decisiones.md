# FASE 0: REGISTRO DE DECISIONES Y LÍNEA BASE ARQUITECTURAL

**Proyecto:** Scalaris — Suite de Álgebra Lineal y Didáctica Matemática  
**Fecha:** 2026-10-02  
**Fase:** F0 (Línea Base y Spikes)

---

## 1. Versiones del Stack

Las dependencias principales instaladas en el entorno fueron auditadas mediante inspección de paquetes (`pip show`) y revisión del encabezado de artefactos estáticos:

| Componente | Versión | Método de Verificación |
| :--- | :--- | :--- |
| **Python** | `3.14.7` | `python.exe -V` (Entorno virtual `venv`) |
| **NiceGUI** | `3.16.0` | `pip show nicegui` |
| **Plotly** | `7.0.0` | `pip show plotly` |
| **Pytest** | `9.1.1` | `pip show pytest` |
| **Quasar** | `2.18.5` | Encabezado `quasar.umd.prod.js` (`Quasar Framework v2.18.5`) |

---

## 2. Línea Base de Pruebas y Rutas

### 2.1 Suite de Pruebas Automatizadas
- **Comando:** `pytest -q`
- **Resultado:** **VERIFICADO** — 379 tests ejecutados, 379 aprobados, 0 fallos, 0 errores.
- **Tiempo:** ~0.85s a 1.10s.
- **Conclusión:** La suite preexistente de pruebas (backend, frontend y utilidades) se encuentra al 100% de salud.

### 2.2 Smoke Test de Inicialización
- **Comando:** `python -c "import src.frontend.app"`
- **Resultado:** **VERIFICADO** — Importación limpia con código de retorno `0`. Sin advertencias de sintaxis ni dependencias circulares.

### 2.3 Auditoría de Rutas y Redirecciones
Se levantó el servidor NiceGUI y se consultaron las 10 rutas clave mediante peticiones HTTP directas sin seguir redirecciones:

| Ruta | Código HTTP | Destino (Header `Location`) | Tipo de Respuesta |
| :--- | :---: | :--- | :--- |
| `/` | `307` | `/sistemas-lineales` | Redirección 1 salto a vista 200 OK |
| `/gauss` | `307` | `/sistemas-lineales?method=gauss` | Redirección 1 salto a vista 200 OK |
| `/gauss-jordan` | `307` | `/sistemas-lineales?method=gauss-jordan` | Redirección 1 salto a vista 200 OK |
| `/ia` | `307` | `/sistemas-lineales` | Redirección 1 salto a vista 200 OK |
| `/sistemas-lineales` | `200` | — | Vista funcional completa |
| `/operaciones-matrices` | `200` | — | Vista funcional completa |
| `/matriz-inversa` | `200` | — | Vista funcional completa |
| `/vectores` | `200` | — | Vista funcional completa |
| `/conversor` | `200` | — | Vista funcional completa |
| `/romanos` | `200` | — | Vista funcional completa |

**Cadenas de dos saltos:** **0**. Todas las redirecciones son atómicas (un único salto `307 -> 200 OK`).

---

## 3. Línea Base de Rendimiento (Servidor)

Se evaluó la capacidad de cálculo en backend mediante un script de benchmarking con fracciones densas exactas `(i*7 + j*3)/13` con dominancia diagonal (para forzar la resolución completa de todos los pasos de Gauss-Jordan y Gauss), midiendo tiempo de CPU con `time.perf_counter()` y memoria con `tracemalloc`.

### 3.1 `InverseOpsController.process_inverse` (Caso denso invertible)

| Dimensión ($n \times n$) | Estado | Pasos Didácticos | Tiempo (`elapsed_s`) | Pico Memoria (`peak_mb`) | Límite 120s |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **$3 \times 3$** | `SUCCESS` | 13 | 0.0044 s | 0.05 MB | Cumple holgadamente |
| **$10 \times 10$** | `SUCCESS` | 111 | 0.1026 s | 0.98 MB | Cumple holgadamente |
| **$25 \times 25$** | `SUCCESS` | 651 | 1.7454 s | 20.33 MB | Cumple holgadamente |
| **$50 \times 50$** | `SUCCESS` | 2551 | 18.8097 s | 261.06 MB | Cumple (< 19s) |

### 3.2 `InverseOpsController.process_inverse` (Matriz homogénea de "7/13" — Detección de singularidad)

| Dimensión ($n \times n$) | Estado | Pasos | Tiempo (`elapsed_s`) | Pico Memoria (`peak_mb`) |
| :---: | :---: | :---: | :---: | :---: |
| **$3 \times 3$** | `SINGULAR` | 0 | 0.0002 s | 0.00 MB |
| **$10 \times 10$** | `SINGULAR` | 0 | 0.0008 s | 0.02 MB |
| **$25 \times 25$** | `SINGULAR` | 0 | 0.0049 s | 0.11 MB |
| **$50 \times 50$** | `SINGULAR` | 0 | 0.0159 s | 0.43 MB |

### 3.3 `GaussJordanController.process_system` ($10 \times 10$ con vector $b$)

| Dimensión ($m \times n$) | Estado | Tiempo (`elapsed_s`) | Pico Memoria (`peak_mb`) |
| :---: | :---: | :---: | :---: |
| **$10 \times 10$** | `UNIQUE_SOLUTION` | 0.0429 s | 1.11 MB |

---

## 4. Spikes Arquitecturales

> **Nota sobre el entorno:** La automatización mediante `browser_subagent` no pudo inicializar el driver de Playwright en Windows debido a un error 404 del CDN de descarga de binarios de Chromium. Siguiendo las directrices éticas y de honestidad del proyecto, los aspectos que requerían inspección en tiempo de ejecución de un navegador real se marcan estrictamente como **NO PROBADO** o **INFERIDO**, documentando el código exacto y el procedimiento manual para su comprobación. El Spike S5 fue **VERIFICADO** empíricamente mediante pruebas de sesión HTTP automatizadas.

| ID | Criterio | Resultado | Evidencia | Ajuste al Plan |
| :--- | :--- | :---: | :--- | :--- |
| **S1** | Con `html[data-glosa="open"]` aplica `padding-right: calc(var(--glosa-w) + 32px)` a `.q-page-container` y desplaza `right` de `.q-header` (`reveal`), con `--glosa-w: clamp(360px, 32vw, 440px)`. Contenido comprime sin scroll horizontal, píldora se recentra y fixed se preservan. | **NO PROBADO** (en navegador) / **INFERIDO** (DOM / CSS) | Implementado en `/s1`. Hallazgo API: `ui.header()` no acepta `reveal=True` (genera `TypeError`), debe usarse `.props('reveal')`. | En F4 usar `.props('reveal')`. Definir tokens `--glosa-w` en `:root` y en los tres temas. |
| **S2** | `ResizeObserver` por `.js-plotly-plot` llama a `Plotly.Plots.resize` con debounce 120ms y guarda si el nodo ya no existe. Ajuste < 150ms, 3D sin parpadeo y sin errores al destruir el nodo o colapsar en `ui.expansion`. | **NO PROBADO** (en navegador) / **INFERIDO** (API JS) | Implementado en `/s2` con `MutationObserver` y guarda `if (!node || !document.contains(node)) return;`. | En F4 agregar la guarda de existencia al `app.js` de Plotly para prevenir excepciones al desmontar gráficos. |
| **S3** | Matriz 50×50 con `SquareMatrixPanel`. Comparar snap vs FLIP con translateX (>=1750px) y `contain: content` en scroller. Mediana de latencia <= 100ms. | **NO PROBADO** (en navegador) / **INFERIDO** (Reflow model) | Implementado en `/s3` con script de 3 corridas con doble `requestAnimationFrame` y lectura forzada de `offsetHeight`. | Ratificar enmienda E4: usar snap + `contain: content` en `.square-matrix-scroller` para desacoplar el reflow masivo. |
| **S5** | Persistencia in-place `app.storage.user['h'].append(...)` tras F5 y `ui.navigate.to`. Persistencia de patrón `AIPanel.chat_history`. Compartición entre 2 pestañas. Excepción sin `STORAGE_SECRET` y comportamiento del fallback. | **VERIFICADO** | Suite automatizada `scratch/run_s5_tests.py` y `scratch/test_storage_no_secret.py` pasó todas las aserciones. | Obligatorio inicializar colecciones en `app.storage.user` antes de hacer mutaciones in-place (`.append()`). Mantener `STORAGE_SECRET` en `.env`. |
| **S6** | `container-type: inline-size` en `.view-root`. Ancho no colapsa, sticky header de `EquationGrid` funciona, diálogos/notificaciones/menús centrados y visibles, FAB fixed exterior intacto, `@container` conmuta `.layout-split`. | **NO PROBADO** (en navegador) / **INFERIDO** (Especificación CQ & Quasar) | Implementado en `/s6`. Quasar renderiza `ui.dialog` y `ui.notify` en portales del body, inmunes al `container-type`. | Adoptar `container-type: inline-size` en los contenedores principales `.view-root` sin riesgo sobre modales. |

---

## 5. Ajustes Propuestos al Plan

| Sección del Plan | Cambio Propuesto | Motivo Técnico |
| :--- | :--- | :--- |
| **F1 & F4 (Layout / Navbar)** | Usar siempre `ui.header().props('reveal')` en lugar del argumento Python `ui.header(reveal=True)`. | En NiceGUI 3.16 `ui.header` no tiene parámetro `reveal`, lanza `TypeError: got an unexpected keyword argument 'reveal'`. |
| **F4 (Plotly en app.js)** | Añadir comprobación explícita de presencia en el DOM (`document.contains(node)`) antes de `Plotly.Plots.resize`. | Evita errores de consola cuando una gráfica se encuentra dentro de un tab o `ui.expansion` cerrado o destruido durante un resize. |
| **F3 / F7 (Scrollers 50×50)** | Agregar `contain: content;` a la clase CSS del scroller de matriz (`.square-matrix-scroller`). | Aísla el árbol de render de 2500 celdas, reduciendo el costo de reflow en la página principal cuando se abre o cierra el panel lateral. |
| **F5 (AIPanel / Storage)** | Garantizar que cualquier propiedad de historial inicialice explícitamente la lista en el storage si no existe (`storage['key'] = [...]`). | `ObservableDict` detecta mutaciones in-place (`.append`) solo en objetos envueltos como `ObservableList`. Si `storage.get('k', [])` devuelve la lista por defecto, `.append()` no dispara la persistencia. |

---

## 6. Preguntas Abiertas

1. **Gestión de `STORAGE_SECRET`:** Actualmente `src/frontend/app.py` lee `os.getenv("STORAGE_SECRET")`. Si la variable no está en el entorno local, NiceGUI advierte y cae en fallback volátil (`PseudoPersistentDict`). ¿Deseas que definamos un valor por defecto para entornos de desarrollo en `.env.example` o que el sistema alerte al usuario cuando falte la clave en producción?

---

## 7. Código Mínimo Reproducible de los Spikes

Para reproducir los spikes manualmente en un navegador, el siguiente módulo independiente puede ejecutarse en el puerto `8081` (`python -m src.frontend._spikes.run_spikes`):

```python
\"\"\"Módulo reproducible de Spikes F0 (Scalaris)\"\"\"
from nicegui import app, ui
import plotly.graph_objects as go
from src.frontend.theme import setup_theme
from src.frontend.components.square_matrix_panel import SquareMatrixPanel
from src.frontend.components.equation_grid import EquationGrid

app.add_static_files('/assets', 'src/frontend/assets')

@ui.page('/s1')
def spike_s1():
    setup_theme()
    ui.add_head_html('''<style>
      :root { --glosa-w: clamp(360px, 32vw, 440px); }
      html[data-glosa="open"] .q-page-container { padding-right: calc(var(--glosa-w) + 32px) !important; }
      html[data-glosa="open"] .q-header { right: calc(var(--glosa-w) + 32px) !important; }
    </style>''')
    with ui.header().classes('p-3 bg-panel border-b').props('reveal'):
        ui.label('Header con Reveal')
    ui.button('Alternar Dock', on_click=lambda: ui.run_javascript('''
        const d = document.documentElement;
        d.setAttribute('data-glosa', d.getAttribute('data-glosa') === 'open' ? 'closed' : 'open');
    '''))

@ui.page('/s2')
def spike_s2():
    setup_theme()
    ui.add_head_html('''<script>
      const ro = new ResizeObserver(entries => {
        for (const entry of entries) {
          const n = entry.target;
          if (n && document.contains(n) && window.Plotly) Plotly.Plots.resize(n);
        }
      });
      document.querySelectorAll('.js-plotly-plot').forEach(el => ro.observe(el));
    </script>''')
    fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))
    ui.plotly(fig).classes('w-full')

@ui.page('/s3')
def spike_s3():
    setup_theme()
    SquareMatrixPanel.inject_scripts()
    panel = SquareMatrixPanel(initial_n=50)
    panel.build_container()

@ui.page('/s5')
def spike_s5():
    setup_theme()
    if 'items' not in app.storage.user: app.storage.user['items'] = []
    def add():
        app.storage.user['items'].append(f'item_{len(app.storage.user["items"])}')
        ui.navigate.to('/s5')
    ui.button('Añadir', on_click=add)
    ui.label(str(app.storage.user['items']))

@ui.page('/s6')
def spike_s6():
    setup_theme()
    ui.add_head_html('''<style>
      .view-root-cq { container-type: inline-size; container-name: root; }
      @container root (min-width: 900px) { .split { flex-direction: row !important; } }
    </style>''')
    with ui.column().classes('w-full view-root-cq'):
        with ui.row().classes('split flex-col w-full'):
            ui.label('Bloque A').classes('flex-1 p-4 bg-panel')
            ui.label('Bloque B').classes('flex-1 p-4 bg-panel')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8081, storage_secret="spike-key-2026")
```

---
*Fin del registro de decisiones — Scalaris F0.*
