import os
import requests
from dotenv import load_dotenv

load_dotenv()

class OpenRouterIA:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def analizar_sistema(self, prompt_text: str):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "nex-agi/nex-n2.5-pro:free", 
            "messages": [
                {
                    "role": "system", 
                    "content": "Eres un tutor experto en álgebra lineal ayudando a estudiantes de ingeniería en la UAM. Cuando escribas matrices, sistemas de ecuaciones o pasos matemáticos, NO uses códigos LaTeX ni símbolos de dólar ($$). Escríbelos siempre en formato de texto plano ordenado, usando corchetes limpios y espacios para que se entiendan perfectamente a simple vista en el chat."
                },
                {"role": "user", "content": prompt_text}
            ]
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error en la IA: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error de conexión: {str(e)}"