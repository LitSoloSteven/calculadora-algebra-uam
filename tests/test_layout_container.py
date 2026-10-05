import os
from pathlib import Path

def test_theme_css_container_queries():
    css_path = Path("src/frontend/assets/css/theme.css")
    assert css_path.exists()
    content = css_path.read_text(encoding="utf-8")
    
    # .view-root tiene container-type: inline-size
    assert ".view-root { container-type: inline-size; }" in content or ".view-root { container-type: inline-size" in content
    assert ".hub-root { container-type: inline-size; }" in content or ".hub-root { container-type: inline-size" in content
    
    # Ningún otro selector lo tiene
    # Contamos cuántas veces aparece "container-type: inline-size"
    count = content.count("container-type: inline-size")
    assert count == 3, f"Expected 3 container-type declarations, found {count}"
    
    # Existen reglas @container para .layout-split y .layout-grid-2
    assert "@container" in content
    assert ".layout-split" in content
    assert ".layout-grid-2" in content
    
    # --fab-reserve aparece en :root y en los tres bloques de tema
    count_fab = content.count("--fab-reserve:")
    assert count_fab >= 4, f"Expected at least 4 --fab-reserve declarations, found {count_fab}"
    
    # No aparece 100vh en el css (al menos en los cambios nuevos)
    assert "100vh" not in content, "Found 100vh in theme.css"

def test_views_migrated_to_container_layout():
    views = [
        "src/frontend/views/linear_systems/view_linear_systems.py",
        "src/frontend/views/vector_ops/view_vector_ops.py",
        "src/frontend/views/matrix_ops/view_matrix_ops.py",
        "src/frontend/views/inverse_ops/view_inverse_ops.py",
        "src/frontend/views/numeric_systems/view_numeric_systems.py",
        "src/frontend/views/numeric_systems/view_roman_calculator.py"
    ]
    
    for view in views:
        view_path = Path(view)
        assert view_path.exists()
        content = view_path.read_text(encoding="utf-8")
        
        # Ninguno contiene los breakpoints viejos
        assert "lg:flex-row" not in content
        assert "lg:w-1/2" not in content
        assert "lg:flex-1" not in content
        assert "md:grid-cols-2" not in content
        
        # Contienen view-root
        assert "view-root" in content, f"view-root missing in {view}"
        
def test_hub_contains_view_root():
    hub_path = Path("src/frontend/views/hub/view_hub.py")
    assert hub_path.exists()
    content = hub_path.read_text(encoding="utf-8")
    assert "view-root" in content
