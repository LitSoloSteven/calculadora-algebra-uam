"""Entry point ejecutable principal de Scalaris."""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Garantizar resolución de imports raíz (src.backend, src.frontend, src.ai)
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Cargar variables de entorno (raíz y módulo AI)
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "src" / "ai" / ".env")

from src.frontend.app import run

if __name__ in {"__main__", "__mp_main__"}:
    run()
