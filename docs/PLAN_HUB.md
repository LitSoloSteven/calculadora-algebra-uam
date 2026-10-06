# Plan de ejecución: página de inicio (Hub) de Scalaris

Archivo: `docs/PLAN_HUB.md`
Estado: propuesto, pendiente de aprobación por fases.
Alcance: `src/frontend/` (`views/hub/`, `assets/css/theme.css`, `assets/js/hub.js`, `components/navbar.py` y, solo si H0 lo confirma, el FAB de Glosa) y tests nuevos en `tests/`. No toca `src/backend/`, no añade dependencias y no cambia el registro de `navigation.py`.
Relación con otros documentos: sustituye la sección 2.3 de `docs/PLAN_SCALARIS.md` (Hub) y la enmienda E6 en lo que respecta al Hub. Ver la sección 9 para la enmienda E14 que hay que añadir a las REGLAS DEL AGENTE.

Leyenda de verificación (como en las REGLAS): VERIFICADO (se ejecutó o se vio en el navegador), INFERIDO (se deduce del código o de la captura) y NO PROBADO. A la fecha, todo el diagnóstico es INFERIDO: se hizo con una captura a 1440 px de ancho aproximado y con la lectura del código, sin navegador.

---

## 1. Resumen

El Hub actual se siente cargado y sin foco por tres causas de fondo, no por tener 7 herramientas:

1. El layout es accidental: las columnas toman el ancho de su contenido y los bloques quedan descentrados.
2. Todo tiene el mismo rango: título, pilares, nombres y fórmulas pesan casi igual y el espaciado es uniforme.
3. La información se repite: "Continuar" duplica herramientas que ya están abajo, y el pilar Visualizador repite su único hijo.

La propuesta convierte la página en una matriz en forma escalonada: tres peldaños (los tres pilares de la barra de navegación), cada uno desplazado una columna a la derecha sobre una grilla de 4 columnas, con tiles de tamaño idéntico y un único punto focal marcado como el pivote de la matriz.

---

## 2. Diagnóstico

Las medidas en píxeles se tomaron sobre la captura, no en el navegador.

| Before | After | Why |
|---|---|---|
| Tarjetas de 496, 435 y 492 px según su contenido y unos 550 px vacíos entre columnas. El bloque queda descentrado respecto de la barra. | Grilla de 4 columnas con tiles del mismo ancho en todos los peldaños. | Causa inferida: `ui.column` alinea los hijos al inicio y `.hub-col` no los estira (falta `w-full` o `align-items: stretch`). |
| Cada pilar es una tarjeta con filas dentro. Visualizador repite "Rectas, planos y vectores" como título y como fila. | Sin tarjeta de pilar: un encabezado por peldaño y los tiles debajo. | Caja dentro de caja y dos niveles de elevación compitiendo. |
| Cada herramienta muestra icono, nombre, descriptor y fórmula (28 elementos), y "Continuar" repite 4 de ellas. | Tile con icono, nombre y descriptor. Sin fórmula y sin lista de recientes. | Menos datos por celda y cada dato dice algo distinto. |
| Una barra de scroll vertical aparece junto a cada fórmula. | Sin fórmulas ni MathJax en el Hub. | Causa probable: `.math-scroll-container` define `overflow-x: auto`, lo que vuelve `overflow-y` automático, y el margen de las fórmulas display de MathJax lo desborda. |
| Scalaris (2rem), pilares (1.125rem) y nombres de herramienta se distinguen poco. Todo son `div`, sin `h1`, `h2`, `ul` ni `main`. | Cuatro niveles tipográficos con semántica real. | La jerarquía hoy la dan solo la posición y el tamaño. |
| El mismo `gap-8` en todo. Título y subtítulo se separan como dos secciones y hay mucho aire entre la barra y el título. | Ritmo: 8 px entre título y subtítulo, 40 px entre cabecera y tablero, 24 px entre peldaños. | El espaciado uniforme no agrupa nada. El desglose real del aire superior lo mide H0. |
| "Continuar" son 4 pastillas elevadas, lo más parecido a un botón de la página. Promete reanudar pero solo reabre la herramienta. Su estado vacío es mucho más alto que el skeleton y desplaza el catálogo. | Un solo tile marcado: "Sigue aquí" o "Empieza aquí". | Un único punto focal y ningún desplazamiento de layout. |
| Barra de navegación: dos separadores seguidos tras "Utilidades" con un hueco vacío. | Un separador solo entre grupos. | `navbar.py` emite `nav-sep` después de cada pilar y otra vez antes del tema. Se corrige en H3. |
| El icono del FAB se ve magenta. | El icono usa `--accent` del tema. | Hipótesis: `.text-accent` de Quasar (por defecto `#9C27B0` en NiceGUI) gana a la regla de `theme.css`. La confirma H0 y la corrige H3. |

---

## 3. Decisión de diseño: la página es una matriz escalonada

El nombre viene de *scala*, el reproductor de la inversa ya marca el pivote con un borde y el temario es la forma escalonada. La página usa ese idioma como estructura, no como adorno.

```
Scalaris
Álgebra lineal y utilidades numéricas, con cada paso a la vista.

┌                                                       ┐
   Álgebra lineal
   [Sistemas] [Vectores] [Matrices] [Inversa]

            Visualizador
            [Rectas, planos y vectores]

                         Utilidades
                         [Conversor] [Romanos]
└                                                       ┘
```

- Tres peldaños, uno por pilar, en el mismo orden que la barra. Cada peldaño arranca una columna más a la derecha. Con el catálogo actual (4, 1 y 2 herramientas) la escalera cierra exacta: el peldaño 1 ocupa las columnas 1 a 4, el 2 la columna 2 y el 3 las columnas 3 y 4. Los vacíos son los ceros de la matriz.
- Dos corchetes de matriz laterales hechos con bordes CSS, sin SVG y con tokens de color.
- Un único foco: un tile lleva el borde de pivote (mismo lenguaje que `cell-pivot` en la inversa) y una etiqueta corta.
- Tiles con poco texto y de un solo tamaño. Las tres secciones sirven de estructura y no de contenedor, así que no duplican la barra ni añaden un clic.

### Decisiones tomadas

| # | Decisión | Elegido | Por qué |
|---|---|---|---|
| H1 | Fórmulas en el Hub | Se quitan. `example_latex` queda en el registro sin tocar. | La estructura aporta la personalidad y desaparecen los scrolls y la dependencia de MathJax. |
| H2 | "Continuar" | Un tile marcado. Sustituye a E6. | El estado vacío orientativo pasa a ser "Empieza aquí" sobre Sistemas de ecuaciones. |
| H3 | Tile de Glosa | No | Los vacíos del peldaño son intencionales y el FAB ya existe en todas las páginas. |
| H4 | Fallo de `localStorage` | Degradar en silencio a "Empieza aquí" | El estudiante no puede resolver ese error. |

---

## 4. Especificación

### 4.1 Estructura semántica

```
main.hub-root.view-root           (clases utilitarias actuales: w-full max-w-7xl mx-auto p-6 mt-4)
  header.hub-head
    h1.hub-title                  "Scalaris"
    p.hub-lead                    "Álgebra lineal y utilidades numéricas, con cada paso a la vista."
  nav.hub-board                   aria-label="Herramientas de Scalaris"
    section.hub-step.hub-step-0   (uno por pilar, en el orden de nav_groups())
      h2.hub-step-title           short_name del pilar
      ul.hub-step-list
        li
          a.hub-tile              href = tool.route, data-tool = tool.id
            span.hub-tile-icon    aria-hidden, icon_svg(tool.icon)
            span.hub-tile-name    tool.name
            span.hub-tile-desc    tool.descriptor
```

- Se verifica en H1 que NiceGUI no genere ya un landmark `main` y que `ui.element` permita fijar texto. Si no, se usa `ui.html` con `html.escape`.
- Cada tile guarda su referencia en `self.tiles[tool.id]`.
- La firma `HubUI(glosa_open: bool = False)` y `async def build(self, client)` no cambian. `routes.py` no se toca.
- `AIPanel(self)`, `ai_panel.build()` y `ai_panel.open()` si `glosa_open` se conservan igual. El Hub no define `get_ai_context` ni `get_ai_signals`, y eso sigue siendo válido.

### 4.2 Geometría de la grilla

- `BOARD_COLUMNS = 4`. Cada peldaño es una grilla de 4 columnas con gap `--space-4`.
- El peldaño de índice `i` tiene `offset = min(i, 3)`. Su encabezado y su lista empiezan en la columna `offset + 1` y llegan al final. La lista es una grilla de `4 - offset` columnas iguales con el mismo gap, de modo que el ancho del tile coincide exactamente con el de los demás peldaños.
- Si un pilar tuviera más herramientas que columnas disponibles, las sobrantes pasan a una nueva fila dentro del mismo peldaño. Un test fija hoy el invariante `offset + cantidad <= 4` para el catálogo real, para que un cambio de registro avise de que la escalera ya no cierra.
- Clases: `.hub-step-0` a `.hub-step-3` definen `--hub-col` (columna de inicio) y `--hub-span` (columnas disponibles). Los tiles de una misma fila tienen la misma altura.
- Modificadores del tablero: `.hub-board-flat` pone `--hub-col: 1` y `--hub-span: 4` en todos los peldaños (bandas limpias, sin escalera). `.hub-board-bare` oculta los corchetes. Se controlan con dos constantes en `views/hub/_layout.py`: `HUB_STAIRCASE` y `HUB_BRACKETS`.

### 4.3 Modos responsive (por contenedor, no por viewport)

El contenedor es `.hub-root` (ya tiene `container-type: inline-size`). El umbral se calcula sobre su content box.

| Contenedor | Modo | Detalle |
|---|---|---|
| >= 860 px | Escalera | Grilla de 4 columnas, tiles verticales (icono arriba, nombre, descriptor). |
| < 860 px | Lista | Una columna. Tile horizontal (icono a la izquierda, nombre y descriptor a la derecha). Sangría de `--space-5` por peldaño para que la escalera siga leyéndose. |
| < 480 px | Lista compacta | Sangría de `--space-3` por peldaño y corchetes ocultos. |

Derivación del umbral: con corchetes de `--space-6` por lado y gap de `--space-4`, a 860 px el tile mide (860 - 48 - 48) / 4 = 191 px, suficiente para "Sistemas de ecuaciones" en dos líneas.

Referencia de calibración (INFERIDO, a validar en H3; parte de `max-w-7xl` = 1280, `p-6` y `.nicegui-content` con 16 px de padding):

| Viewport | Dock | Contenedor aprox. | Modo |
|---|---|---|---|
| 1920 | cerrado o abierto | 1232 | Escalera |
| 1440 | cerrado | 1232 | Escalera |
| 1440 | abierto (472 px reservados) | 888 | Escalera, con margen estrecho por el scrollbar |
| 1280 | abierto (442 px reservados) | 758 | Lista |
| 1024 | cerrado | 944 | Escalera |
| 768 | cerrado | 688 | Lista |

Ambos modos deben verse bien, porque un viewport puede cruzar el umbral por pocos píxeles.

### 4.4 Tile

- Es un `<a>` real. Fondo `--bg-panel`, elevación `--elev-2`, radio `--radius-card`, padding `--space-4`, `min-height` de unos 128 px (no altura fija).
- Nombre: 1rem, 700, `--text-main`, `overflow-wrap: anywhere`. Descriptor: `--fs-small`, `--text-sec`. Icono: `--accent`, con 1 o 2 px de ajuste óptico respecto de la primera línea del nombre en modo lista.
- Todos los hijos de grilla o flex llevan `min-width: 0` y el icono lleva `flex-shrink: 0`.
- Sin fórmulas. Sin pills ni puntos decorativos.
- Texto no numérico largo: se parte con `overflow-wrap: anywhere` (no se recorta con elipsis, porque el nombre es lo que el estudiante necesita leer).

### 4.5 Marca de pivote (H2)

- Clase `.is-featured` sobre el tile elegido: un borde de 2 px en `--accent` dibujado con un pseudo-elemento `::before` (no con `outline`, para no pisar el anillo de foco global).
- Etiqueta `.hub-tile-mark`: texto de 0.75rem, 700, `--accent`, sin pill. Texto "Sigue aquí" cuando hay historial y "Empieza aquí" cuando no.
- La marca no cambia la altura ni el ancho de ningún tile: en modo escalera ocupa la fila del icono (que ya mide más que la etiqueta) y en modo lista una columna propia a la derecha.
- Elección (función pura `pick_featured`): primer id válido del historial, ignorando ids desconocidos, duplicados, no strings y herramientas deshabilitadas. Si no queda ninguno, o si la lectura falla, Sistemas de ecuaciones con "Empieza aquí".
- Se aplica tras `await client.connected()` leyendo `window.scalarisReadRecent` (ya existe, con timeout de 3 s). Hasta entonces no hay marca; al llegar aparece al instante y sin transición.

### 4.6 Corchetes

Dos pseudo-elementos de `.hub-board` (`::before` y `::after`) con borde de 2 px en `--text-sec`, opacidad reducida, sin borde interior, altura completa y ancho de `--space-4`. El tablero lleva `padding-inline` de `--space-6` (escalera) o `--space-4` (lista). Son decorativos y no interceptan eventos.

### 4.7 Tipografía y espaciado (tokens existentes, sin colores literales)

| Elemento | Tamaño | Peso | Color |
|---|---|---|---|
| `h1.hub-title` | `--fs-display`, `--ls-display`, `text-wrap: balance` | 700 | `--text-main` |
| `p.hub-lead` | `--fs-body`, ancho máximo 65ch | 400 | `--text-sec` |
| `h2.hub-step-title` | `--fs-h2` | 600 | `--text-sec` |
| `.hub-tile-name` | 1rem | 700 | `--text-main` |
| `.hub-tile-desc` | `--fs-small` | 500 | `--text-sec` |

Todo en minúsculas con la capitalización normal, sin versales ni tracking ancho. Ritmo: título a subtítulo `--space-2`, cabecera a tablero `--space-10`, entre peldaños `--space-6`, encabezado a lista `--space-3`, entre tiles `--space-4`. El `.view-root::after` que reserva espacio para el FAB se conserva.

### 4.8 Movimiento

La pantalla se usa a diario, así que no tiene animación de entrada.

| Evento | Propiedad | Duración y curva |
|---|---|---|
| Hover del tile | Opacidad de un `::after` que lleva `--elev-3` | 120 ms, `--ease-std`, solo bajo `@media (hover: hover) and (pointer: fine)` |
| `:active` del tile | `scale(0.98)` | 120 ms, `--ease-std` |
| Aparición de la marca | Ninguna | Instantánea |
| Foco con flechas | Ninguna | Instantáneo (acción de teclado) |

Con `prefers-reduced-motion: reduce` no hay transform y la opacidad del hover no pasa de 120 ms. Se retiran de ese bloque los selectores `.hub-row` y `.hub-recent-item`.

### 4.9 Teclado (H2)

Tab y Enter siguen funcionando porque los tiles son enlaces reales. Se añaden las flechas, como en la matriz del producto, con un listener delegado en `hub.js` que solo actúa sobre `.hub-tile`:

- Se ignoran las teclas con Alt, Ctrl, Meta o Shift y los eventos con `defaultPrevented`.
- Derecha e Izquierda: el tile más cercano en la misma fila visual, por geometría (`getBoundingClientRect`).
- Abajo y Arriba: el tile de la fila siguiente o anterior con el centro horizontal más cercano. En modo lista eso equivale a recorrer los tiles uno a uno.
- Solo se hace `preventDefault()` cuando existe un destino. Sin destino la flecha conserva su comportamiento normal (scroll).

### 4.10 Accesibilidad

- `h1` único, un `h2` por peldaño, `ul` por peldaño. No se usa `role="grid"` ni `order` en CSS, así que el orden del DOM coincide con el visual y con el de Tab.
- El nombre accesible de cada enlace es el contenido del tile (nombre, descriptor y, si aplica, la marca). El icono lleva `aria-hidden`.
- Contraste AA en Papel, Marea y Medianoche, en especial `--text-sec` sobre `--bg-panel` y `--accent` sobre `--bg-panel` para la marca.
- El anillo de foco global (`:focus-visible`) se conserva.

### 4.11 Estados

| Estado | Comportamiento |
|---|---|
| Vacío (sin historial) | Tile de Sistemas con "Empieza aquí". |
| Cargando | Sin marca hasta leer `localStorage`, sin skeleton ni desplazamiento. |
| Error (storage bloqueado, valor corrupto, ids desconocidos, timeout de JS) | Se degrada en silencio a "Empieza aquí". No se muestra aviso. |
| Con historial | Tile de la última herramienta con "Sigue aquí". |

---

## 5. Cambios por archivo

### Crear

| Archivo | Rol | Fase |
|---|---|---|
| `src/frontend/views/hub/_layout.py` | Constantes `BOARD_COLUMNS`, `HUB_STAIRCASE`, `HUB_BRACKETS` y funciones puras `step_offset`, `step_span` y `board_fits`. Solo importa `navigation` si lo necesita. | H1 |
| `tests/test_hub_layout.py` | Geometría de la escalera y que el catálogo real cierre la grilla. | H1 |
| `tests/test_hub_featured.py` | `pick_featured` con historial válido, vacío, corrupto, duplicado, con ids desconocidos y no-lista. | H2 |

### Modificar

| Archivo | Cambio | Fase |
|---|---|---|
| `src/frontend/views/hub/view_hub.py` | `build()` reescrito con la estructura de 4.1. Sin `typesetMathWhenReady`, sin tira "Continuar" y sin lectura de `localStorage` en H1. En H2 se añade la lectura y la marca. | H1, H2 |
| `src/frontend/views/hub/_recent.py` | Se añade `pick_featured(raw)`. `normalize_recent` y `RECENT_MAX` no se tocan. | H2 |
| `src/frontend/assets/css/theme.css` | Se reemplaza el bloque del Hub por `.hub-head`, `.hub-board`, `.hub-step*`, `.hub-tile*` y los modos por contenedor. Se retiran los selectores del Hub del bloque de reduced-motion. Se conserva `.hub-root` con su `container-type` y `.handoff-note`. | H1, H2 |
| `src/frontend/assets/js/hub.js` | Se conservan `scalarisReadRecent` y `scalarisRecordVisit`. Se añade el listener de flechas. | H2 |
| `src/frontend/components/navbar.py` | Un separador solo entre grupos. La firma `create_navbar(active_ui=None, active_route='/')` no cambia. | H3 |
| FAB de Glosa (`components/glosa_dock.py` y `theme.css`) | Solo si H0 confirma la hipótesis de `.text-accent`. | H3 |

### Eliminar

Los selectores CSS del Hub que ya no se usan: `.hub-section-title`, `.hub-cols`, `.hub-col`, `.hub-pillar`, `.hub-row*`, `.hub-recent-list`, `.hub-recent-item` y `.hub-empty`. Antes de borrarlos, H0 verifica con `grep` que nada fuera de `view_hub.py` los usa.

---

## 6. Fases

Cada fase es un PR independiente. Al cerrar cada una: `pytest -q` verde (línea base de 379 tests, sin editar ni borrar tests existentes) e INFORME DE FASE con estados VERIFICADO, INFERIDO o NO PROBADO. No hay Playwright (E9), así que todo lo visual se entrega NO PROBADO con pasos manuales exactos.

### H0. Confirmar causas (S, sin código y sin editar archivos)

Inspección estática del código y de NiceGUI 3.16.0 instalado, más un checklist manual de DevTools. Ver el prompt de H0.

Salida: INFORME H0 con cada hipótesis marcada y los ajustes que haya que hacer a este plan.

### H1. Estructura, grilla, tipografía y estilo (M)

Archivos: `view_hub.py`, `_layout.py`, `theme.css`, `tests/test_hub_layout.py`.

Aceptación:
- Los tiles tienen el mismo ancho en los tres peldaños y la escalera cierra (INFERIDO por la grilla; la comprobación visual es NO PROBADO).
- Sin barras de scroll junto a las tarjetas (no hay fórmulas).
- El tablero pasa de escalera a lista al cruzar 860 px de contenedor y la sangría sigue leyéndose.
- `h1`, `h2`, `ul` y `a` presentes y en orden de lectura correcto (se puede VERIFICAR leyendo el DOM generado).
- Sin colores literales, sin animación de entrada y con `prefers-reduced-motion` cubierto.
- `pytest -q` verde.

### H2. Punto focal y teclado (S a M)

Archivos: `_recent.py`, `view_hub.py`, `hub.js`, `theme.css`, `tests/test_hub_featured.py`.

Aceptación:
- `pick_featured` cumple los casos del test.
- La marca aparece sin mover ningún tile (NO PROBADO en navegador, INFERIDO por el diseño de la fila del icono).
- Con valores corruptos de `localStorage` aparece "Empieza aquí".
- Las flechas mueven el foco según 4.9 y Tab y Enter siguen funcionando.
- Sin animación para acciones de teclado.

### H3. Verificación y pulido (M)

Archivos: `navbar.py`, FAB si aplica, ajustes de `theme.css`.

Aceptación:
- Contraste AA en los tres temas.
- Viewports 320, 390, 768, 1024, 1280, 1440 y 1920, con el dock abierto y cerrado y con zoom 200 %.
- Reduced-motion y navegación solo con teclado.
- Un único separador entre grupos en la barra.
- FAB con `--accent` si la hipótesis se confirmó.

Pasos manuales exactos (se ejecutan en el navegador):

1. Abre `/` y, en DevTools, usa la barra de dispositivos con los anchos 320, 390, 768, 1024, 1280, 1440 y 1920. En cada uno revisa que no haya scroll horizontal de página y que ningún texto se corte.
2. Repite con el dock abierto (clic en el FAB o `/?glosa=1`) en 1024, 1280 y 1440.
3. Cambia entre Papel, Marea y Medianoche con el selector de tema y repite 1440 y 390.
4. Aplica zoom 200 % del navegador en 1280 y comprueba que pase a modo lista sin recortes.
5. Con la consola abierta, prueba el historial: `localStorage.setItem('scalaris:recent','["inversa","romanos"]')` y recarga (marca en Matriz inversa); luego `localStorage.setItem('scalaris:recent','{"a":1}')`, luego `'["zzz"]'` y por último `localStorage.removeItem('scalaris:recent')`. En los tres últimos casos la marca debe ser "Empieza aquí" en Sistemas.
6. Teclado: recarga, pulsa Tab hasta el primer tile y recorre con las flechas. Comprueba que Enter abre la herramienta y que no hay animación.
7. Activa "Reducir movimiento" en el sistema y comprueba que el hover y el `:active` no usan transform.

---

## 7. Break-UI: riesgos y datos desfavorables

| # | Riesgo | Severidad | Mitigación | Verificación |
|---|---|---|---|---|
| R1 | Nombres largos ("Sistemas de ecuaciones", "Rectas, planos y vectores") en tiles de unos 191 px. | Media | `overflow-wrap: anywhere`, `min-height` y no altura fija. | 320, 390 y zoom 200 %. |
| R2 | Descriptor largo ("Decimal, binario, octal y hexadecimal"). | Baja | Se parte en dos o tres líneas. Los tiles de una fila comparten altura. | 1024 y 1440 con dock. |
| R3 | Los vacíos del peldaño parecen aire muerto si los tiles son altos. | Media | `min-height` bajo, corchetes que enmarcan el bloque y sangría clara. | Revisión visual en 1440 y 1920. |
| R4 | El viewport cruza el umbral por pocos píxeles (scrollbar, dock). | Media | Ambos modos son completos y se prueban. | 1440 con dock abierto y cerrado. |
| R5 | `localStorage` bloqueado, corrupto, vacío, con duplicados o con ids desconocidos. | Media | `pick_featured` puro y probado, con degradación silenciosa. | `tests/test_hub_featured.py` y paso 5 de H3. |
| R6 | Un cambio de registro (5.º pilar o 3 herramientas en Utilidades) rompe la escalera. | Baja | Test que fija el invariante y fallback de nueva fila. | `tests/test_hub_layout.py`. |
| R7 | Contraste de `--text-sec` y `--accent` en Medianoche. | Media | Verificación AA y ajuste de token solo si falla. | H3. |
| R8 | Hover en táctil. | Baja | Hover solo bajo `@media (hover: hover) and (pointer: fine)`. | Dispositivo táctil real. |
| R9 | `container-type: inline-size` convierte a `.hub-root` en bloque contenedor de descendientes fijos. | Baja | FAB y dock se renderizan fuera de `.hub-root`. | Abrir el dock en el Hub. |
| R10 | La escalera no convence a los usuarios. | Media | Dos modificadores (`HUB_STAIRCASE`, `HUB_BRACKETS`) la desactivan sin tocar la estructura. | Probar con 2 o 3 estudiantes de la UAM antes de cerrar la estética. |

Datos para QA: viewports 320, 390, 768, 1024, 1280, 1440 y 1920, los tres temas, dock abierto y cerrado, zoom 200 %, y los cinco valores de `localStorage` del paso 5 de H3.

---

## 8. Fuera de alcance

- Resumen contextual en la marca ("Sistema 3×4, Gauss"). Exige que cada vista registre un resumen al calcular y se trata como una fase aparte (H4, opcional).
- Cambios en `navigation.py`, rutas, títulos de página, redirecciones o `routes.py`.
- Cambios de backend o de IA.

---
