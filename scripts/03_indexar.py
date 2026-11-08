"""Fase 3 — gera os embeddings dos trechos e salva o índice em base/indice/.

    python scripts/03_indexar.py      (na 1ª vez baixa o modelo de embeddings, ~1 GB)
"""

import sys
import time

import _comum  # noqa: F401
from passo_genai.busca import Buscador
from passo_genai.config import INDICE, Config


def main() -> int:
    cfg = Config()
    t0 = time.time()
    b = Buscador.construir(cfg)
    b.salvar()
    print(f"{len(b.trechos)} trechos indexados com {cfg.modelo_embeddings} em {time.time() - t0:.0f}s -> {INDICE}")
    print("Próximo: python scripts/04_avaliar_busca.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
