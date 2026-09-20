import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv("src/ai/.env")

SYSTEM_PROMPT = "Eres un tutor experto en álgebra lineal ayudando a estudiantes de ingeniería en la UAM. Cuando escribas matrices, sistemas de ecuaciones o pasos matemáticos, NO uses códigos LaTeX ni símbolos de dólar ($$). Escríbelos siempre en formato de texto plano ordenado, usando corchetes limpios y espacios para que se entiendan perfectamente a simple vista en el chat."

class OpenRouterIA:
    PRIMARY_MODEL = os.getenv("OPENROUTER_PRIMARY_MODEL", "nex-agi/nex-n2.5-pro:free")
    FALLBACK_MODELS = [m.strip() for m in os.getenv("OPENROUTER_FALLBACK_MODELS", "").split(",") if m.strip()]
    
    TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526}

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def _call_model(self, model: str, history: list, timeout: int = 30):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://calculadora-algebra-uam.local",
            "X-Title": "Calculadora Algebra Lineal UAM",
        }
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        data = {
            "model": model,
            "messages": messages,
        }
        return requests.post(self.url, headers=headers, json=data, timeout=timeout)

    def analizar_sistema(self, prompt_text: str, history: list = None) -> tuple[bool, str]:
        if not self.api_key:
            return False, "❌ Error: Python sigue sin encontrar la llave. Revisa que el archivo se llame exactamente '.env' y no '.env.txt'"

        if history is None:
            history = []
        messages_history = history + [{"role": "user", "content": prompt_text}]

        modelos_a_intentar = [self.PRIMARY_MODEL] + self.FALLBACK_MODELS
        ultimo_error = None

        for modelo in modelos_a_intentar:
            for intento in range(2):
                try:
                    response = self._call_model(modelo, messages_history)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            choices = data.get("choices") or []
                            content = (choices[0].get("message") or {}).get("content") if choices else None
                            if content:
                                return True, content
                            ultimo_error = str(data.get("error", data))[:200]
                            continue
                        except Exception as e:
                            ultimo_error = f"Error parseando respuesta: {e}"
                            break
                            
                    if response.status_code == 404:
                        ultimo_error = f"Modelo no encontrado (404): {modelo}"
                        break
                        
                    if response.status_code in {401, 403}:
                        return False, "OpenRouter rechazó la clave; revisa OPENROUTER_API_KEY."
                        
                    if response.status_code in self.TRANSIENT_STATUS_CODES:
                        ultimo_error = f"{response.status_code} - {response.text[:200]}"
                        time.sleep(1.5 * (intento + 1))
                        continue
                        
                    return False, f"Error en la IA ({modelo}): {response.status_code} - {response.text[:200]}"
                    
                except requests.exceptions.Timeout:
                    ultimo_error = "Tiempo de espera agotado"
                    continue
                except requests.exceptions.RequestException as e:
                    ultimo_error = str(e)
                    time.sleep(1.5)
                    continue

        return False, f"Error en la IA. Se intentaron {len(modelos_a_intentar)} modelos. Último error: {ultimo_error}"