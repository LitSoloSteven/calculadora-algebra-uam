import inspect
from src.ai.openrouter_ai import OpenRouterIA

def test_requests_post_binding():
    # El primer parámetro de _requests_post debe ser 'url', no 'self'
    sig = inspect.signature(OpenRouterIA()._requests_post)
    first_param = list(sig.parameters.keys())[0]
    assert first_param == 'url'
