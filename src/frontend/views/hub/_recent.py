from src.frontend.navigation import Tool, tool_by_id, visible_tools

RECENT_MAX = 4
FEATURED_DEFAULT_ID = "sistemas"


def normalize_recent(raw) -> tuple[Tool, ...]:
    if not isinstance(raw, list):
        return ()

    tools = []
    seen = set()
    for item in raw:
        if not isinstance(item, str):
            continue
        try:
            tool = tool_by_id(item)
            if tool.enabled and item not in seen:
                tools.append(tool)
                seen.add(item)
                if len(tools) >= RECENT_MAX:
                    break
        except KeyError:
            continue

    return tuple(tools)


def pick_featured(raw) -> tuple[Tool, bool]:
    """Elige el tile con la marca.

    Devuelve (herramienta, hay_historial). Si raw no es una lista, esta corrupto,
    viene vacio o solo tiene ids invalidos, devuelve Sistemas de ecuaciones con
    hay_historial=False. Nunca lanza.
    """
    tools = normalize_recent(raw)
    if tools:
        return tools[0], True
    try:
        default = tool_by_id(FEATURED_DEFAULT_ID)
        if default.enabled:
            return default, False
    except KeyError:
        pass
    return visible_tools()[0], False
