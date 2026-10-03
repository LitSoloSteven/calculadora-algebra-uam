from src.frontend.navigation import tool_by_id, Tool

RECENT_MAX = 4

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
