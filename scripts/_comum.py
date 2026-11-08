"""Ajusta o sys.path para os scripts acharem o pacote src/passo_genai sem instalação."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (RAIZ / "src", RAIZ):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def titulo(texto: str) -> None:
    print(f"\n=== {texto} ===", flush=True)
