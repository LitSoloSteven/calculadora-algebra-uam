"""Tests F8c — Verificación de tokens de movimiento, estilos break-UI, chips y accesibilidad."""
from pathlib import Path
import re
import pytest


def test_theme_css_motion_and_break_ui_tokens():
    css_path = Path("src/frontend/assets/css/theme.css")
    assert css_path.exists()
    content = css_path.read_text(encoding="utf-8")

    # Layout container constraints
    assert content.count("container-type: inline-size") == 2
    assert "100vh" not in content
    assert content.count("--fab-reserve:") >= 4

    # C4: --cell-w en :root y en los tres temas
    assert content.count("--cell-w:") >= 4
    assert ".grid-cell {" in content
    assert ".grid-cell-compact {" in content

    # C2: No keyPulse ni .key-pulse en theme.css
    assert "@keyframes keyPulse" not in content
    assert ".key-pulse" not in content
    assert ".cross-hl {" in content

    # C3: Transición de neo-tabs indicador
    assert "transition: transform var(--dur-med) var(--ease-std), opacity var(--dur-med) var(--ease-std) !important;" in content
    assert "var(--ease-elastic)" not in content.split(".neo-tabs .q-tab__indicator")[1].split("}")[0]

    # C3: Sin ease-elastic en botones de iconos, calc y logo
    icon_btn_css = content.split(".btn-neo-icon {")[1].split("}")[0]
    assert "var(--ease-elastic)" not in icon_btn_css
    assert "var(--ease-std)" in icon_btn_css

    calc_btn_css = content.split(".btn-neo-calc {")[1].split("}")[0]
    assert "var(--ease-elastic)" not in calc_btn_css
    assert "var(--ease-std)" in calc_btn_css

    logo_css = content.split(".brand-logo-link {")[1].split("}")[0]
    assert "var(--ease-elastic)" not in logo_css
    assert "var(--ease-std)" in logo_css

    # C3: slide-up y slide-bounce reducidos a dur-med y ease-std
    slide_up_css = content.split(".animate-slide-up {")[1].split("}")[0]
    assert "var(--dur-med)" in slide_up_css
    assert "var(--ease-std)" in slide_up_css

    slide_bounce_css = content.split(".animate-slide-bounce {")[1].split("}")[0]
    assert "var(--dur-med)" in slide_bounce_css
    assert "var(--ease-std)" in slide_bounce_css

    squash_css = content.split(".squash-bounce {")[1].split("}")[0]
    assert "var(--dur-med)" in squash_css
    assert "var(--ease-std)" in squash_css

    # C4: inv-table celdas sin truncado estricto de 16ch
    inv_cell_css = content.split(".inv-table th,")[1].split(".inv-table thead th {")[0]
    assert "max-width: 16ch" not in inv_cell_css
    assert "text-overflow: ellipsis" not in inv_cell_css

    # C1: prefers-reduced-motion block
    reduced_part = content.split("/* === ACCESIBILIDAD: Reduced motion === */")[1].split("/* === MATRIZ INVERSA === */")[0]
    assert "@media (prefers-reduced-motion: reduce)" in reduced_part
    assert ".tw-cursor" in reduced_part
    assert ".glosa-typing-indicator span" in reduced_part
    assert ".animate-shake" in reduced_part
    assert ".squash-bounce" in reduced_part
    assert ".animate-slide-up" in reduced_part
    assert "animation: none !important;" in reduced_part
    assert "transition-duration: 120ms !important;" in reduced_part

    # C5: Glosa Chips
    assert ".glosa-chips {" in content
    assert ".glosa-chips-inline {" in content
    assert ".glosa-chip {" in content
    assert ".glosa-chip-inline {" in content
    assert ".glosa-followups {" in content
    assert ".glosa-followup {" in content


def test_js_app_delegated_tooltip_and_no_key_pulse():
    app_js = Path("src/frontend/assets/js/app.js").read_text(encoding="utf-8")
    assert "key-pulse" not in app_js
    assert "scrollWidth > target.clientWidth" in app_js
    assert "target.title = target.value" in app_js
    assert "transform 240ms cubic-bezier(0.32, 0.72, 0, 1), opacity 240ms cubic-bezier(0.32, 0.72, 0, 1)" in app_js


def test_js_cross_highlighting_and_no_blur():
    eq_grid = Path("src/frontend/assets/js/equation_grid.js").read_text(encoding="utf-8")
    assert "cross-hl" in eq_grid
    assert "filter: blur" not in eq_grid
    assert "style.background =" not in eq_grid

    mat_cap = Path("src/frontend/assets/js/matrix_capture.js").read_text(encoding="utf-8")
    assert "cross-hl" in mat_cap
    assert "style.background =" not in mat_cap

    vec_cap = Path("src/frontend/assets/js/vector_capture.js").read_text(encoding="utf-8")
    assert "cross-hl" in vec_cap
    assert "filter: blur" not in vec_cap
    assert "style.background =" not in vec_cap

    sq_mat = Path("src/frontend/assets/js/square_matrix.js").read_text(encoding="utf-8")
    assert "filter: blur" not in sq_mat


def test_python_components_break_ui_and_animations():
    # Matrix capture py
    mat_py = Path("src/frontend/components/matrix_capture.py").read_text(encoding="utf-8")
    assert "filter: 'blur" not in mat_py
    assert "grid-cell" in mat_py
    assert "w-20" not in mat_py

    # Equation grid py
    eq_py = Path("src/frontend/components/equation_grid.py").read_text(encoding="utf-8")
    assert "grid-cell" in eq_py
    assert "w-20" not in eq_py

    # Vector capture py
    vec_py = Path("src/frontend/components/vector_capture.py").read_text(encoding="utf-8")
    assert "grid-cell" in vec_py
    assert "w-20" not in vec_py

    # Square matrix panel py
    sq_py = Path("src/frontend/components/square_matrix_panel.py").read_text(encoding="utf-8")
    assert "CELL_PX" not in sq_py
    assert "grid-cell" in sq_py
    assert "grid-cell-compact" in sq_py


def test_views_sanitization_and_break_ui():
    # Numeric systems interaction mixin: no animate-shake
    num_mixin = Path("src/frontend/views/numeric_systems/interaction_mixin.py").read_text(encoding="utf-8")
    assert "animate-shake" not in num_mixin

    # Linear systems results mixin: solution chips styling
    lin_res = Path("src/frontend/views/linear_systems/results_mixin.py").read_text(encoding="utf-8")
    assert "overflow-wrap: anywhere;" in lin_res
    assert "min-w-0 max-w-full" in lin_res

    # Vector ops results mixin: ui.html in math-scroll-container instead of ui.markdown
    vec_res = Path("src/frontend/views/vector_ops/results_mixin.py").read_text(encoding="utf-8")
    assert "math-scroll-container" in vec_res
    assert "html.escape(coef_str)" in vec_res
    assert "html.escape(sol_str)" in vec_res
