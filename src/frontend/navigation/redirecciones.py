"""Reglas de resolución y redirección para rutas heredadas (legacy)."""
import urllib.parse

from src.frontend.navigation.modelo import LegacyRedirect


def _obtener_redirecciones_estaticas() -> list[LegacyRedirect]:
    """Retorna las reglas fijas de redirección legacy hacia las nuevas rutas."""
    return [
        LegacyRedirect(path="/sistemas-lineales", target_route="/algebra-lineal/sistemas"),
        LegacyRedirect(
            path="/gauss",
            target_route="/algebra-lineal/sistemas",
            fixed_query=(("method", "gauss"),),
        ),
        LegacyRedirect(
            path="/gauss-jordan",
            target_route="/algebra-lineal/sistemas",
            fixed_query=(("method", "gauss-jordan"),),
        ),
        LegacyRedirect(path="/operaciones-matrices", target_route="/algebra-lineal/matrices"),
        LegacyRedirect(path="/matriz-inversa", target_route="/algebra-lineal/inversa"),
        LegacyRedirect(path="/vectores", target_route="/algebra-lineal/vectores"),
        LegacyRedirect(path="/conversor", target_route="/utilidades/bases"),
        LegacyRedirect(path="/romanos", target_route="/utilidades/romanos"),
    ]


def legacy_redirects() -> tuple[LegacyRedirect, ...]:
    """Devuelve la tupla de redirecciones legacy activas según el estado dinámico del Hub."""
    import src.frontend.navigation as modulo_nav

    hub_activo = getattr(modulo_nav, "HUB_ENABLED", False)
    redirects: list[LegacyRedirect] = []

    if not hub_activo:
        redirects.append(
            LegacyRedirect(
                path="/",
                target_route="/algebra-lineal/sistemas",
                permanent=False,
            )
        )
        redirects.append(
            LegacyRedirect(
                path="/ia",
                target_route="/algebra-lineal/sistemas",
                permanent=False,
            )
        )
    else:
        redirects.append(
            LegacyRedirect(
                path="/ia",
                target_route="/",
                fixed_query=(("glosa", "1"),),
                permanent=True,
            )
        )

    redirects.extend(_obtener_redirecciones_estaticas())
    return tuple(redirects)


def redirect_location(redirect: LegacyRedirect, incoming_items: list[tuple[str, str]]) -> str:
    """Calcula la URL de destino final preservando parámetros de consulta no colisionantes."""
    fixed_pairs: list[tuple[str, str]] = list(redirect.fixed_query)
    fixed_keys = {k for k, _ in fixed_pairs}

    for k, v in incoming_items:
        if k not in fixed_keys:
            fixed_pairs.append((k, v))

    if fixed_pairs:
        encoded_query = urllib.parse.urlencode(fixed_pairs)
        return f"{redirect.target_route}?{encoded_query}"
    return redirect.target_route
