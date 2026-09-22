import json

def parse_payload(json_payload: str) -> tuple[dict | None, str | None]:
    try:
        data = json.loads(json_payload)
    except json.JSONDecodeError as e:
        return None, json.dumps({
            "status": "ERROR",
            "message": f"Payload JSON malformado: {e.msg} (línea {e.lineno}, columna {e.colno})."
        })
    if not isinstance(data, dict):
        return None, json.dumps({
            "status": "ERROR",
            "message": "El payload debe ser un objeto JSON."
        })
    return data, None
