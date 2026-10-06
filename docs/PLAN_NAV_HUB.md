# Plan de ejecución: Hub "[ I | b ]", navbar contextual y tema Marea

Archivo: `docs/PLAN_NAV_HUB.md`
Estado: propuesto, pendiente de aprobación por fases.
Alcance: `src/frontend/` (`views/hub/`, `views/geometry/`, `components/navbar.py`, `components/app_shell.py`, `components/icons.py`, `components/theme_switcher.py` nuevo, `navigation.py`, `assets/css/theme.css`, `assets/js/hub.js`) y tests nuevos en `tests/`. No toca `src/backend/`, no toca `src/ai/`, no añade dependencias.
Relación con otros documentos: sustituye el diseño visual del Hub de `docs/PLAN_HUB.md` (secciones 3 y 4, la escalera) y conserva de ese plan `pick_featured`, la lectura de `localStorage` y el estado "Empieza aquí" / "Sigue aquí" (E15). Requiere las enmiendas E16 y E17 de la sección 9.

Leyenda de verificación (como en las REGLAS): VERIFICADO (se ejecutó o se vio en el navegador), INFERIDO (se deduce del código) y NO PROBADO. A la fecha todo es INFERIDO: sale de leer el código, sin navegador (E9).

---

## 1. Resumen

Tres cambios que se apoyan entre sí:

1. **Hub nuevo con un solo concepto memorable.** La portada pasa a ser una matriz aumentada `[ I | b ]`: a la izquierda la identidad 3×3, donde cada pivote es un pilar (Álgebra lineal, Visualizador, Utilidades); a la derecha la columna `b`, que lista las herramientas del pilar elegido. Es la meta de Gauss-Jordan convertida en puerta de entrada.
2. **Navbar contextual.** Desaparece del Hub. En cada pilar muestra, en línea y sin menús desplegables, las herramientas de ese pilar. Con esto la navbar y el Hub dejan de repetir el mismo contenido.
3. **Marea más celeste.** Se cambia la familia de grises azulados por una familia cian. Recomendación: `#def7ff` como fondo de página y `#bceeff` como tono hundido (inputs).

### Decisiones tomadas

| # | Decisión | Elegido | Por qué |
|---|---|---|---|
| D1 | Concepto del Hub | Matriz aumentada `[ I \| b ]` con pilares como pivotes | Una sola imagen que se recuerda, usa el idioma del producto (pivote, identidad, aumentada) y deja un único punto focal. |
| D2 | Cómo se llega a una herramienta desde el Hub | Elegir pilar (1 toque) y luego herramienta (1 toque); el pilar del último uso viene preseleccionado | Quita la repetición con la navbar. Costo asumido en R3. |
| D3 | Navbar en el Hub | No se muestra. El Hub trae su propio selector de tema | Es lo que pediste, y evita el choque visual. |
| D4 | Navbar en un pilar | Inicio + nombre del pilar + sub-pestañas en línea + tema | Sustituye al combo desplegable. |
| D5 | Breadcrumb | Se elimina | Con el nombre del pilar y la pestaña activa en la navbar, la miga repite lo mismo. |
| D6 | Pilar Visualizador | Sus 3 escenas (Rectas y planos, Vectores, Combinación lineal) pasan a ser sus sub-pestañas en la navbar | Hoy el pilar tiene 1 herramienta y 3 pestañas internas; con 1 solo ítem la navbar quedaría vacía. Las escenas ya pierden sus datos al cambiar, así que un enlace real no empeora nada. |
| D7 | Cambio de pilar | Vía Inicio (la navbar de un pilar no enlaza a otros pilares) | Es la consecuencia directa de lo que pediste. Costo asumido en R2. |
| D8 | Color de Marea | `#def7ff` página, `#bceeff` zona hundida | Ver sección 6. |

### Alternativas de Hub que se descartaron

| Opción | Qué es | Por qué no |
|---|---|---|
| A (elegida) | `[ I \| b ]` | Ver D1. |
| B | Pizarra con una reducción de Gauss que se reproduce sola en la portada | Es una animación perpetua sin propósito funcional (REGLAS 5) y compite con la herramienta de pasos que ya existe en Matriz inversa. |
| C | Tipografía gigante con los nombres como único elemento | Se recuerda, pero no dice nada de álgebra lineal y en 320 px pierde fuerza. |

---

## 2. Diagnóstico

Las medidas de color se calcularon con los hex del CSS. El resto sale de leer el código.

| Before | After | Why |
|---|---|---|
| Hub: 3 peldaños con 7 tiles del mismo peso, escalera y corchetes. | Un bloque `[ I \| b ]` con un pivote elegido y 2 a 4 opciones a la derecha. | La escalera ordena pero no deja una imagen que se recuerde; todos los tiles pesan igual. |
| La navbar muestra 3 pilares con menú desplegable, y el Hub muestra los mismos 3 pilares con sus herramientas. | Hub sin navbar; navbar solo dentro de un pilar. | Es el mismo mapa dibujado dos veces. |
| Llegar a una herramienta desde un pilar exige abrir el combo (2 clics) y el pilar activo solo aparece como una etiqueta. | Las herramientas del pilar quedan visibles, la activa va en estado hundido. | Un clic, y siempre sabes dónde estás. |
| Miga `Álgebra lineal / Matriz inversa` bajo la navbar. | Se elimina. | La navbar ya dice pilar y herramienta activa. |
| Visualizador: 1 ítem en el registro y 3 escenas en pestañas dentro de la página. | 3 ítems en la navbar y sin pestañas internas. | Un pilar con un solo ítem no justifica una navbar contextual; así se unifica la forma de navegar. |
| Marea: `#EDF2F8` tiene saturación HSL de 44 %. | `#DEF7FF` y `#BCEEFF` tienen ≈ 100 %. | Marea se lee como Papel con un matiz azul; hace falta que se distinga. |
| `navbar.py` pinta el punto del selector de tema con el literal `#EDF2F8`. | Los puntos leen tokens `--swatch-*` y un test los compara con cada `--bg-page`. | Un literal duplicado se desfasa en cuanto cambia el tema. |

---

## 3. Concepto del Hub: `[ I | b ]`

```
 [logo] Scalaris                                                    (tema)
 Álgebra lineal y utilidades numéricas, con cada paso a la vista.

 ⎡ 1  0  0 ⎤  Álgebra lineal    ¦  Sistemas de ecuaciones   Empieza aquí
 ⎢ 0  1  0 ⎥  Visualizador      ¦  Vectores
 ⎣ 0  0  1 ⎦  Utilidades        ¦  Matrices
                                ¦  Matriz inversa
```

- La fila elegida va en estado hundido (`--elev-inset`) y su `1` en `--accent`. Las otras filas van elevadas y su `1` en `--text-sec`.
- Los `0` son decorativos (`aria-hidden`), en `--text-sec` con opacidad reducida. Los `1` son números grandes con `font-variant-numeric: tabular-nums`.
- La barra de aumentación `¦` y los corchetes se dibujan con bordes CSS (sin SVG) y tokens de color.
- La columna `b` lista las herramientas del pilar elegido. Todos los paneles ocupan la misma celda de la grilla, así que la altura es la del más alto y nada se mueve al cambiar de pilar.
- Punto focal: el tile de `pick_featured` lleva el borde de pivote (`.is-featured`) y la marca "Sigue aquí" o "Empieza aquí". El pilar inicial es el de ese tile.
- No hay fórmulas ni MathJax en el Hub (se mantiene la decisión H1 de `PLAN_HUB.md`).
- No hay animación de entrada. La pantalla se usa a diario.

---

## 4. Especificación del Hub

### 4.1 Estructura semántica

```
main.hub-root.view-root
  header.hub-head
    div.hub-brand            logo (claro/oscuro por tema, alt vacío) + h1.hub-title "Scalaris"
    p.hub-lead
    div.hub-theme            botón de tema compartido (theme_switcher)
  div.hub-stage
    div.hub-matrix           role="tablist" aria-orientation="vertical" aria-label="Áreas de Scalaris"
      button.hub-row x3      role="tab" id="hub-tab-<pillar>" aria-selected aria-controls="hub-panel-<pillar>"
        span.hub-cells       aria-hidden
          span.hub-cell x3   "1" en la diagonal (.is-pivot), "0" fuera
        span.hub-row-name    pillar.short_name
    div.hub-bar              aria-hidden (barra de aumentación)
    div.hub-aug
      section.hub-panel x3   role="tabpanel" aria-labelledby="hub-tab-<pillar>"  (.is-active; inert si no)
        ul.hub-tool-list > li > a.hub-tile
          span.hub-tile-icon (aria-hidden) | span.hub-tile-name | span.hub-tile-desc | span.hub-tile-mark
```

- Un único `h1`. Los paneles se nombran con `aria-labelledby`, sin `h2` extra.
- Cada tile es un `<a>` real. En el pilar Visualizador los tiles son las 3 escenas (salen de `nav_items`, sección 5.1), con `href="/visualizador?escena=..."`.
- La firma `HubUI(glosa_open: bool = False)` y `async def build(self, client)` no cambian. `routes.py` no se toca.
- `AIPanel(self)`, `ai_panel.build()` y `ai_panel.open()` si `glosa_open` se conservan. El Hub sigue sin definir `get_ai_context` ni `get_ai_signals`.
- Modelo puro en `views/hub/_model.py` (sin NiceGUI): `hub_pillars()`, `matrix_cells(n)`, `initial_selection(raw)`. Es lo que se prueba con pytest.

### 4.2 Geometría y modos responsive (por contenedor `.hub-root`, que ya es `container-type: inline-size`)

| Contenedor | Modo | Detalle |
|---|---|---|
| >= 720 px | Dos columnas | Matriz a la izquierda (ancho `clamp(300px, 42%, 440px)`), barra vertical y panel `b` a la derecha. Paneles apilados en una misma celda. |
| < 720 px | Apilado | Matriz arriba, barra horizontal, panel debajo. Solo se renderiza el panel activo (`display: none` en los demás). |
| < 480 px | Compacto | Celdas más pequeñas (`--hub-cell: 40px`), corchetes ocultos. |

Tamaño de celda: `--hub-cell: clamp(40px, 9cqi, 72px)`. Los umbrales son INFERIDOS; se calibran en la fase P6.

### 4.3 Tipografía y espaciado (tokens existentes, sin colores literales)

| Elemento | Tamaño | Peso | Color |
|---|---|---|---|
| `h1.hub-title` | `--fs-display`, `--ls-display`, `text-wrap: balance` | 700 | `--text-main` |
| `p.hub-lead` | `--fs-body`, ancho máximo 65ch | 400 | `--text-sec` |
| `.hub-cell` (1 y 0) | `calc(var(--hub-cell) * 0.62)` | 700 | `--text-sec` (pivote elegido: `--accent`) |
| `.hub-row-name` | 1.125rem | 600 | `--text-main` |
| `.hub-tile-name` | 1rem | 700 | `--text-main` |
| `.hub-tile-desc` | `--fs-small` | 500 | `--text-sec` |
| `.hub-tile-mark` | 0.75rem | 700 | `--accent` |

Ritmo: título a subtítulo `--space-2`, cabecera a escenario `--space-10`, entre filas `--space-3`, entre tiles `--space-3`. El `.view-root::after` que reserva espacio para el FAB se conserva.

### 4.4 Estados

| Estado | Comportamiento |
|---|---|
| Vacío (sin historial) | Pilar Álgebra lineal elegido; tile "Sistemas de ecuaciones" con "Empieza aquí". |
| Con historial | Pilar del último uso elegido; tile de esa herramienta con "Sigue aquí". Para Visualizador, el tile marcado es la primera escena. |
| Cargando | Se pinta primero Álgebra lineal y sin marca. Al leer `localStorage` se cambia el pilar y se pone la marca en un solo paso, sin transición y sin mover el layout (los paneles ocupan la misma celda). |
| Error (storage bloqueado, valor corrupto, ids desconocidos, timeout de JS) | Se degrada en silencio al estado vacío. No se muestra aviso. |

### 4.5 Movimiento

| Evento | Propiedad | Duración y curva |
|---|---|---|
| Elegir pilar con puntero | Opacidad del panel entrante | 120 ms, `--ease-std`. Solo si `scalarisMotionOK()` es verdadero. |
| Elegir pilar con teclado | Ninguna | Instantáneo (acción de teclado). |
| Hover de fila o tile | Opacidad de un `::after` que lleva `--elev-3` | 120 ms, `--ease-std`, solo bajo `@media (hover: hover) and (pointer: fine)`. |
| `:active` de fila o tile | `scale(0.98)` | 120 ms, `--ease-std`. |
| Aparición de la marca | Ninguna | Instantánea. |

Con `prefers-reduced-motion: reduce`: sin transform; la opacidad no pasa de 120 ms. Los selectores retirados (`.hub-step*`, `.hub-board*`) salen del bloque de reduced-motion y entran los nuevos.

### 4.6 Teclado

Patrón WAI-ARIA de pestañas verticales con activación automática:

- Flecha abajo y arriba: mueven el foco y la selección entre pilares, con vuelta al extremo. Inicio y Fin saltan al primero y al último.
- Flecha derecha en una pestaña: foco en el primer tile del panel activo.
- Flecha izquierda en un tile: foco en la pestaña activa.
- Flecha abajo y arriba dentro del panel: recorren los tiles del panel activo.
- Tab entra al panel activo y Enter abre la herramienta (son enlaces reales).
- Se ignoran las teclas con Alt, Ctrl, Meta o Shift y los eventos con `defaultPrevented`. Solo se hace `preventDefault()` si existe destino.
- Los paneles inactivos llevan `inert` además de `visibility: hidden`. El listener de tiles solo mira `.hub-panel.is-active .hub-tile`.

### 4.7 Accesibilidad

- Contraste AA en Papel, Marea y Medianoche, en especial `--text-sec` sobre `--bg-panel` y `--accent` sobre `--bg-panel`.
- El nombre accesible de cada pestaña es el nombre del pilar; los `1` y `0` van con `aria-hidden`.
- El anillo de foco global (`:focus-visible`) se conserva.

---

## 5. Especificación de la navbar

### 5.1 Registro (`navigation.py`, solo stdlib)

Se añade sin tocar `Tool`, `Pillar` ni `legacy_redirects`:

```
NavItem(key, label, short_label, descriptor, icon, route, query, tool_id)
VISUALIZER_SCENES = (("rectas-planos", ...), ("vectores", ...), ("combinacion", ...))
nav_items(pillar_id) -> tuple[NavItem, ...]
nav_item_href(item) -> str
default_item_key(route) -> str | None
```

| Pilar | Ítems (label / short_label) |
|---|---|
| Álgebra lineal | Sistemas de ecuaciones / Sistemas; Vectores / Vectores; Matrices / Matrices; Matriz inversa / Inversa |
| Visualizador | Rectas y planos / Rectas; Vectores / Vectores; Combinación lineal / Combinación |
| Utilidades | Conversor de bases / Bases; Números romanos / Romanos |

- Las claves son estables: `sistemas`, `vectores`, `matrices`, `inversa`, `vis:rectas-planos`, `vis:vectores`, `vis:combinacion`, `bases`, `romanos`.
- Los descriptores nuevos de las escenas: "Sistemas de 2 y 3 variables", "Suma y escalamiento de u y v", "Cómo se forma b con tus vectores".
- Un test fija que `VISUALIZER_SCENES` coincide con `VALID_SCENES` de `view_geometry.py`, para que no se desfasen.

### 5.2 Estructura

```
header.nav-header (container-type: inline-size; container-name: navbar)
  a.brand-corner-link                 logo a "/" (sin cambios)
  div.panel-card.nav-pill
    a.nav-trigger.nav-home            icono inicio, aria-label="Inicio", href="/"
    div.nav-sep
    span.nav-pillar                   icono del pilar + nombre (no interactivo)
    nav.nav-items                     aria-label="Herramientas de <pilar>"
      a.nav-trigger.nav-item x N      icono + span.nav-label-full + span.nav-label-short; aria-label = label completo; aria-current="page" si es el activo
    div.nav-sep
    botón de tema (theme_switcher)
```

- La firma `create_navbar(active_ui=None, active_route='/')` gana un parámetro opcional `active_key=None`. Si es `None`, se deduce con `default_item_key(route)`. Es compatible hacia atrás.
- `create_app_shell(active_ui, active_route, active_key=None)`: si `active_route == HUB_ROUTE`, no crea navbar. Se retira el bloque del breadcrumb.
- Con `SCALARIS_NAV=0` se conserva el camino plano actual (rollback). El Hub no muestra navbar en ningún modo.
- Con `SCALARIS_DOCK=0` el Hub queda sin botón de Glosa (aceptado, R12). En los pilares el botón sigue donde está hoy.
- El activo usa `.nav-active` (inset + `--accent`), sin pills ni puntos. Hover por pseudo-elemento con `@media (hover: hover) and (pointer: fine)`; `:active` con `scale(0.97)`.
- Al cargar, el ítem activo se centra con `scrollIntoView({ inline: 'center', block: 'nearest' })` por si la lista hace scroll.

### 5.3 Modos responsive (por el ancho del header, que se estrecha solo cuando el dock de Glosa está abierto)

| Ancho del header | Modo |
|---|---|
| >= 960 px | Etiqueta completa + nombre del pilar |
| 700 a 959 px | Etiqueta corta; el nombre del pilar se oculta |
| < 700 px | Solo icono, con `title` y tooltip; `.nav-items` con `overflow-x: auto` y `min-width: 0` |

Estimación (INFERIDA): 4 etiquetas completas, inicio y tema ocupan unos 900 px. Los umbrales se calibran en P6. Los vecinos críticos (`.nav-home`, selector de tema) llevan `flex-shrink: 0`.

### 5.4 Visualizador: escenas en la navbar

- Se retiran las pestañas internas (`scene_tabs`) y `_on_scene_change`. La escena sale del parámetro `escena` de la URL (ya validado contra `VALID_SCENES`).
- `GeometryUI.build` pasa `active_key=f"vis:{escena}"` al shell.
- Handoff: el payload de vectores trae su escena. Si no coincide con `escena` de la URL, se trata como inválido con el aviso estándar. Los enlaces actuales ya generan `&escena=<scene>` coherente, así que el flujo normal no cambia. El handoff de sistemas a Visualizador sigue entrando por `rectas-planos`.

---

## 6. Especificación de Marea

Se parte de que las dos candidatas son cian saturado y se diferencian por luminosidad: `#def7ff` ≈ 93 % y `#bceeff` ≈ 87 %.

**Recomendación: `#def7ff` como fondo de página y `#bceeff` como tono hundido.** Un cian tan saturado como fondo de toda la página tiñe el área donde se leen tablas y fórmulas durante mucho tiempo; `#def7ff` se ve claramente celeste y deja margen de contraste. `#bceeff` entra donde ya se oscurece el color: el interior de los inputs. La sombra clara del neumorfismo sigue visible porque la página sigue por encima del 90 % de luminosidad.

### Tokens del bloque `:root[data-theme="marea"]` (valores propuestos)

| Token | Hoy | Propuesto | Nota |
|---|---|---|---|
| `--bg-page` | `#EDF2F8` | `#DEF7FF` | |
| `--bg-panel` | `#E1E9F1` | `#CDF2FF` | Punto medio entre los dos hex candidatos. |
| `--bg-elevated` | `#F2F5FA` | `#EEFBFF` | |
| `--bg-calc-btn` | `#EAF0F7` | `#E6F9FF` | |
| `--input-bg` | `#D4DCE8` | `#BCEEFF` | |
| `--accent-soft` | `#D0E4E1` | `#B9E5E5` | El teal de antes se vería gris sobre cian. |
| `--btn-primary-text` | `#F2F5FA` | `#EEFBFF` | |
| `--shadow-dark` | `rgba(11,31,51,0.10)` | `rgba(10,70,100,0.16)` | Sombra tintada al tono del fondo. |
| `--shadow-light` | `rgba(255,255,255,0.75)` | `rgba(255,255,255,0.85)` | |
| `--text-main`, `--text-sec`, `--accent`, `--focus-ring`, `--error`, `--success`, `--warning` y badges | sin cambio | sin cambio | Solo se verifica contraste. |

Contrastes calculados a mano (INFERIDOS; el test de P1 los fija): `--text-main` sobre página ≈ 13 a 1; `--text-sec` sobre página ≥ 7 a 1, sobre panel ≈ 7 a 1, sobre input ≈ 6,7 a 1; `--accent` sobre página ≈ 6,6 a 1 y sobre input ≈ 5,9 a 1; `--btn-primary-text` sobre `--accent` ≈ 7 a 1. Todos sobre 4,5.

### Preset alternativo B (si al verlo quieres más cian)

Página `#BCEEFF`, panel `#A9E6F8`, elevated `#D2F4FF`, input `#96DAF0`. Con `--text-sec` y `--accent` actuales los contrastes dan ≈ 6,1 y ≈ 4,8 a 1 (sobre input: margen justo). Cambiar de preset es editar esa tabla; el mismo test lo revalida.

### Otros puntos del tema

- Tokens nuevos `--swatch-papel`, `--swatch-marea`, `--swatch-medianoche` en `:root` y repetidos en los tres temas (mismo patrón que `--z-*`). `theme_switcher.py` los usa; un test los compara con cada `--bg-page`.
- Sin colores literales en CSS nuevo. Los literales de gráficos en `theme.py` no se tocan.
- Aviso heredado: la serie azul `#4B9FE8` de `CHART_PALETTE` ya rondaba 2,5 a 1 contra el fondo de Marea y queda en ≈ 2,4 a 1 sobre `--bg-panel`. No se cambia en este plan; queda anotada para pulido (R7).

---

## 7. Cambios por archivo

### Crear

| Archivo | Rol | Fase |
|---|---|---|
| `tests/test_theme_marea.py` | Parsea `theme.css`: tokens de Marea y contrastes AA de la sección 6. | P1 |
| `src/frontend/components/theme_switcher.py` | `render_theme_button()`: botón y menú de tema reutilizables, con los `--swatch-*`. | P2 |
| `src/frontend/views/hub/_model.py` | Modelo puro del Hub. | P2 |
| `tests/test_hub_model.py` | `hub_pillars`, `matrix_cells`, `initial_selection` (historial válido, vacío, corrupto, duplicado, ids desconocidos, no lista). | P2 y P3 |
| `tests/test_theme_swatches.py` | Cada `--swatch-*` coincide con el `--bg-page` de su tema. | P2 |
| `tests/test_nav_items.py` | Ítems por pilar, claves únicas, hrefs, short_label no vacío, `default_item_key`, escenas iguales a `VALID_SCENES`. | P4 y P5 |

### Modificar

| Archivo | Cambio | Fase |
|---|---|---|
| `assets/css/theme.css` | Marea (P1); swatches y bloque del Hub (P2 y P3); bloque `.nav-*` nuevo y retiro de `.crumbs*` (P4). | P1 a P4 |
| `components/navbar.py` | Usa `theme_switcher` (P2). Estructura contextual y parámetro `active_key` (P4). | P2, P4 |
| `views/hub/view_hub.py` | `build()` reescrito con la estructura 4.1 y `_apply_featured` adaptado a pilar + tile. | P2, P3 |
| `views/hub/_recent.py` | Sin cambios de comportamiento. Se reutiliza `pick_featured`. | P3 |
| `assets/js/hub.js` | Selección de pilar, teclado y restricción al panel activo. Se conservan `scalarisReadRecent` y `scalarisRecordVisit`. | P2, P3 |
| `components/app_shell.py` | Sin navbar en el Hub (P2). Sin breadcrumb y con `active_key` (P4). | P2, P4 |
| `components/icons.py` | Dos iconos nuevos: `escena_rectas_planos` y `escena_combinacion` (la escena Vectores reutiliza `vectores`). | P5 |
| `navigation.py` | `NavItem`, `VISUALIZER_SCENES`, `nav_items`, `nav_item_href`, `default_item_key`. | P4 |
| `views/geometry/view_geometry.py` | Quita `scene_tabs` y `_on_scene_change`; pasa `active_key`; ajusta el handoff de vectores. | P5 |

### Eliminar

- `views/hub/_layout.py` y `tests/test_hub_layout.py`: solo si se aprueba la enmienda E16. Si no, se dejan sin uso.
- Selectores CSS sin uso: `.hub-step*`, `.hub-board*`, `.hub-tile` de modo vertical y `.crumbs`, `.crumb`, `.crumb-sep`. Antes de borrarlos, P0 verifica con `grep` que nada más los usa. En `glosa_dock.js` el selector `.crumbs` en la lista de FLIP es inofensivo y no se toca (E5).

---

## 8. Fases

Cada fase es un PR independiente. Al cerrar cada una: `pytest -q` verde (línea base de 379 tests más los nuevos) e INFORME DE FASE con estados VERIFICADO, INFERIDO o NO PROBADO. Todo lo visual se entrega NO PROBADO con pasos manuales exactos (E9). Orden pensado para que ninguna fase deje la app sin una forma de navegar o de cambiar de tema.

### P0. Confirmar supuestos (S, sin editar archivos)

Inspección estática del código y de NiceGUI 3.16.0 instalado:

1. `grep` en `tests/` y `src/` de `create_navbar`, `create_app_shell`, `crumbs`, `nav_groups`, `hub-`, `_layout`, `EDF2F8`, `marea` y `scene_tabs`. Lista de tests que dependen de lo que se va a cambiar.
2. Que una página sin `ui.header()` no deja padding superior ni rompe `q-page-container`.
3. Que `container-type: inline-size` sobre `.q-header` no descoloca `q-menu` (el menú del tema se teletransporta al body) y que `reveal` sigue funcionando.
4. Que `ui.element(...).props('inert')` y `.props('role=tab ...')` se renderizan como atributos y que `ui.button(...).props('href=...')` genera un `<a>` con `aria-current`.
5. Que `ui.html(..., tag='h1', sanitize=False)` sigue disponible (se usa hoy en el Hub).

Salida: INFORME P0 con cada supuesto marcado y los ajustes que haya que hacer al plan.

### P1. Marea (S)

Archivos: `theme.css` (solo el bloque de Marea), `navbar.py` (solo el literal del punto de tema, temporal hasta P2), `tests/test_theme_marea.py`.

Aceptación:
- Los tokens de la sección 6 están en el bloque de Marea y los contrastes de texto sobre página, panel e input son >= 4,5 (VERIFICADO por pytest).
- Papel y Medianoche no cambian (el test compara sus tokens con los actuales).
- Pasos manuales: alternar los tres temas en `/algebra-lineal/matrices` y `/algebra-lineal/inversa` y revisar tablas `inv-table`, badges, tabs y la calculadora (NO PROBADO).

### P2. Hub: estructura, estilo y selección por clic (M)

Archivos: `view_hub.py`, `_model.py`, `theme_switcher.py`, `navbar.py` (usa el componente), `app_shell.py` (sin navbar en `/`), `theme.css`, `hub.js`, tests de modelo y swatches.

Aceptación:
- La portada muestra `[ I | b ]` con la matriz a la izquierda y el panel `b` a la derecha; al hacer clic en un pilar cambia el panel sin mover el layout (NO PROBADO en navegador, INFERIDO por la celda de grilla compartida).
- `/` no muestra navbar y trae su selector de tema (INFERIDO por el código del shell).
- Un `h1`, pestañas con `role="tab"` y paneles con `role="tabpanel"` en el DOM generado (se puede VERIFICAR leyendo el DOM).
- Sin colores literales, sin animación de entrada, reduced-motion cubierto.
- `pytest -q` verde.

### P3. Hub: teclado, punto focal y estados (S)

Archivos: `view_hub.py`, `hub.js`, `theme.css`, `tests/test_hub_model.py`.

Aceptación:
- `initial_selection` cumple los casos del test (VERIFICADO por pytest).
- Con valores corruptos de `localStorage` aparece Álgebra lineal con "Empieza aquí" sobre Sistemas (NO PROBADO en navegador).
- Las flechas y Tab funcionan según 4.6, sin animación para acciones de teclado.
- La marca no cambia la altura de ningún tile.

### P4. Navbar contextual (M)

Archivos: `navigation.py`, `navbar.py`, `app_shell.py`, `theme.css`, `tests/test_nav_items.py`.

Aceptación:
- En cada pilar, la navbar muestra Inicio, nombre del pilar, las sub-pestañas en línea y el tema; no hay menús desplegables (INFERIDO por el código).
- La pestaña activa lleva `aria-current="page"` y el estado hundido.
- Sin breadcrumb. La navbar de un pilar no se ve en `/`.
- Los tres modos responsive de 5.3 están definidos y cubiertos por reduced-motion.
- Con `SCALARIS_NAV=0` sigue saliendo el camino plano actual.
- `pytest -q` verde.

### P5. Visualizador: escenas en la navbar (S a M)

Archivos: `view_geometry.py`, `icons.py`, `navigation.py` (descriptores y escenas), `tests/test_nav_items.py`.

Aceptación:
- La navbar del Visualizador muestra las 3 escenas y la activa sigue a `?escena=`.
- Sin pestañas internas; el vacío, la carga y el error con celda se mantienen.
- Un payload de vectores con escena distinta a la URL muestra el aviso y deja la herramienta limpia.
- `VISUALIZER_SCENES` y `VALID_SCENES` coinciden (VERIFICADO por pytest).

### P6. Verificación y pulido (M)

Archivos: ajustes de `theme.css` y, si el contraste lo exige, de un token.

Pasos manuales exactos (se ejecutan en el navegador):

1. Abre `/` y, en DevTools, usa la barra de dispositivos con 320, 390, 768, 1024, 1280, 1440 y 1920. Revisa que no haya scroll horizontal de página y que nada se corte.
2. Repite con el dock abierto (`/?glosa=1`) en 1024, 1280 y 1440. Comprueba que el Hub pasa a modo apilado cuando el contenedor baja de 720 px y que la navbar de un pilar cambia de modo.
3. Cambia entre Papel, Marea y Medianoche y repite 1440 y 390 en `/`, `/algebra-lineal/sistemas` y `/visualizador`.
4. Zoom 200 % en 1280: el Hub debe pasar a apilado y la navbar a solo iconos, sin recortes.
5. Historial: `localStorage.setItem('scalaris:recent','["romanos","inversa"]')` y recarga (pilar Utilidades con "Sigue aquí" en Números romanos); luego `'{"a":1}'`, luego `'["zzz"]'` y por último `localStorage.removeItem('scalaris:recent')`. En los tres últimos casos debe salir Álgebra lineal con "Empieza aquí".
6. Teclado: Tab hasta el Hub, recorre pilares con flechas, entra al panel, abre una herramienta con Enter. Verifica que no hay animación.
7. Reduce movimiento en el sistema y comprueba que hover y `:active` no usan transform.
8. En una herramienta de cada pilar, comprueba que Inicio vuelve al Hub, que el tema cambia sin romper el menú y que, con la lista de la navbar desbordada, el ítem activo queda visible.
9. Con 2 o 3 estudiantes: mostrarles solo el Hub 10 segundos y pedirles que describan qué vieron. Si no recuerdan la idea de la matriz, valorar el concepto B o C antes de cerrar.

---

## 9. Enmiendas a las REGLAS

- **E16.** Se permite eliminar `src/frontend/views/hub/_layout.py` y `tests/test_hub_layout.py`, porque el concepto de escalera que probaban desaparece. Se listan en el INFORME de P2. Si no se aprueba, quedan sin uso y no se tocan.
- **E17.** Si P0 encuentra tests existentes cuya aserción se invalida por un cambio deliberado de estas fases (por ejemplo un literal de Marea o una estructura de navbar), se permite editar únicamente esa aserción, nunca borrar el test ni cambiar su intención. Cada edición se lista en el INFORME con la aserción antes y después. En cualquier otro test rige el §1.
- **Nota sobre `create_navbar`.** El §2 prohíbe cambiar su firma salvo que la fase lo indique; P4 lo indica y la única novedad es `active_key=None`, compatible hacia atrás.

---

## 10. Break-UI: riesgos y datos desfavorables

| # | Riesgo | Severidad | Mitigación | Verificación |
|---|---|---|---|---|
| R1 | 4 etiquetas largas ("Sistemas de ecuaciones") en la navbar con el dock abierto o a 320 px. | Alta | Tres modos (completa, corta, solo icono), `overflow-x: auto`, `min-width: 0` y `flex-shrink: 0` en los vecinos. | P6 pasos 1, 2 y 4. |
| R2 | Cambiar de pilar exige pasar por Inicio (un clic más). | Media | Es consecuencia de D7. El Hub preselecciona el pilar del último uso. | Medir con estudiantes (P6 paso 9). |
| R3 | En el Hub, llegar a una herramienta de otro pilar cuesta 2 toques (antes 1). | Media | Preselección por historial y atajos de teclado. | P6 pasos 5, 6 y 9. |
| R4 | `localStorage` bloqueado, corrupto, vacío, con duplicados o con ids desconocidos. | Media | `initial_selection` es pura y se prueba; degradación silenciosa. | `tests/test_hub_model.py` y P6 paso 5. |
| R5 | Paneles de alturas distintas (4, 3 y 2 tiles) provocan saltos. | Media | En 2 columnas comparten celda y la altura es la del más alto; en apilado solo hay un panel y debajo no hay contenido. | P6 pasos 1 y 4. |
| R6 | Un tile marcado con la etiqueta "Empieza aquí" en 320 px. | Baja | La marca pasa a una línea propia con `overflow-wrap: anywhere` en vez de recortarse. | 320 y zoom 200 %. |
| R7 | Series de gráficos con poco contraste sobre Marea (azul `#4B9FE8`). | Baja | Se anota; no se cambia aquí. | Revisión visual en P6. |
| R8 | Cambiar de escena en el Visualizador pasa a ser un enlace completo (recarga). | Baja | Las escenas ya reconstruían sus controles y perdían los datos al cambiar; se acepta el costo de recarga de Plotly. | P6 paso 3. |
| R9 | Contención de `container-type` en el header altera el menú del tema o el `reveal`. | Media | P0 lo comprueba por código y P6 paso 8 lo mira en navegador. Si falla, se usa `@media` con los mismos umbrales. | P0 punto 3 y P6. |
| R10 | Tests existentes dependen de lo que cambia. | Media | P0 los lista; E17 permite editar solo la aserción afectada. | Informe P0. |
| R11 | El concepto `[ I \| b ]` no convence. | Media | Se valida con 2 o 3 estudiantes antes de cerrar P2 y P3; el modelo y la navbar no dependen de él. | P6 paso 9. |
| R12 | Con `SCALARIS_DOCK=0` el Hub no tiene botón de Glosa (no hay navbar). | Baja | Solo afecta al modo de rollback; se documenta. | Revisión por código. |

Datos de QA: viewports 320, 390, 768, 1024, 1280, 1440 y 1920; los tres temas; dock abierto y cerrado; zoom 200 %; historial en `localStorage` con los cinco valores del paso 5 de P6; `?escena=` con valores válidos e inválidos.

---

## 11. Fuera de alcance

- Cambios en `src/backend/` y `src/ai/`.
- Un selector de pilares dentro de la navbar de un pilar (decisión D7).
- Animaciones nuevas del Hub, resúmenes contextuales en la marca ("Sistema 3×4, Gauss") y fórmulas MathJax en la portada.
- Cambios en `routes.py`, redirecciones o títulos de página.
- Nueva paleta de gráficos para Marea.
