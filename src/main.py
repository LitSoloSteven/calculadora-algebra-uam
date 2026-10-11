"""Punto de entrada ejecutable principal de Scalaris."""
from pathlib import Path
import sys
from dotenv import load_dotenv

DIRECTORIO_RAIZ = Path(__file__).resolve().parent.parent
if str(DIRECTORIO_RAIZ) not in sys.path:
    sys.path.insert(0, str(DIRECTORIO_RAIZ))

load_dotenv(DIRECTORIO_RAIZ / ".env")
load_dotenv(DIRECTORIO_RAIZ / "src" / "ai" / ".env")

from src.frontend.app import ejecutar

if __name__ in {"__main__", "__mp_main__"}:
    ejecutar()
