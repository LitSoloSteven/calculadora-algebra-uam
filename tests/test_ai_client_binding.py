import inspect
from src.ai.openrouter_ai import OpenRouterIA

def test_peticiones_post_vinculacion():
    # El primer parámetro de _peticiones_post debe ser 'url', no 'self'
    sig = inspect.signature(OpenRouterIA()._peticiones_post)
    primer_parametro = list(sig.parameters.keys())[0]
    assert primer_parametro == "url"
