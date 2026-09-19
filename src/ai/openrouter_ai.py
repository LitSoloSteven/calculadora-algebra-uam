import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv("src/ai/.env")

class OpenRouterIA:
    PRIMARY_MODEL = "nex-agi/nex-n2.5-pro:free"
    # TODO: verificar en https://openrouter.ai/models modelos free vigentes y agregar 1-2 aquí como respaldo
    FALLBACK_MODELS: list[str] = ["google/gemini-2.0-pro-exp-02-05:free"]
    TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526}

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def _call_model(self, model: str, prompt_text: str, timeout: int = 30):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://calculadora-algebra-uam.local",
            "X-Title": "Calculadora Algebra Lineal UAM",
        }
        data = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un tutor experto en álgebra lineal ayudando a estudiantes de ingeniería en la UAM. Cuando escribas matrices, sistemas de ecuaciones o pasos matemáticos, NO uses códigos LaTeX ni símbolos de dólar ($$). Escríbelos siempre en formato de texto plano ordenado, usando corchetes limpios y espacios para que se entiendan perfectamente a simple vista en el chat."
                },
                {"role": "user", "content": prompt_text},
            ],
        }
        return requests.post(self.url, headers=headers, json=data, timeout=timeout)

    def analizar_sistema(self, prompt_text: str):
        if not self.api_key:
            return "❌ Error: Python sigue sin encontrar la llave. Revisa que el archivo se llame exactamente '.env' y no '.env.txt'"

        modelos_a_intentar = [self.PRIMARY_MODEL] + self.FALLBACK_MODELS
        ultimo_error = None

        for modelo in modelos_a_intentar:
            for intento in range(2):  # 1 intento + 1 reintento por modelo
                try:
                    response = self._call_model(modelo, prompt_text)
                    if response.status_code == 200:
                        return response.json()['choices'][0]['message']['content']
                    if response.status_code in self.TRANSIENT_STATUS_CODES:
                        ultimo_error = f"{response.status_code} - {response.text[:200]}"
                        time.sleep(1.5 * (intento + 1))
                        continue
                    return f"Error en la IA ({modelo}): {response.status_code} - {response.text}"
                except requests.exceptions.Timeout:
                    ultimo_error = "Tiempo de espera agotado"
                    continue
                except requests.exceptions.RequestException as e:
                    ultimo_error = str(e)
                    continue

        return (
            "⚠️ El servicio de IA no está disponible en este momento "
            f"(proveedor devolvió: {ultimo_error}). Intenta de nuevo en unos minutos."
        )