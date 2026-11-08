"""Fase 2 — baixa as fontes oficiais de base/fontes.yaml para base/brutos/, com URL e data de acesso.

    python scripts/01_baixar_base.py            # baixa só o que falta
    python scripts/01_baixar_base.py --forcar   # baixa tudo de novo (nova data de acesso)

Se uma fonte for bloqueada (o Planalto bloqueia robôs), abra a URL no navegador e salve como
"Página da Web, somente HTML" em base/brutos/<id>.html (PDF: base/brutos/<id>.pdf). Rode de
novo: o script registra o arquivo local com a data de hoje.
"""

import argparse
import sys

import yaml

import _comum  # noqa: F401
from _comum import titulo
from passo_genai.base import baixar, caminho_bruto
from passo_genai.config import BASE


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forcar", action="store_true")
    args = ap.parse_args()
    fontes = yaml.safe_load((BASE / "fontes.yaml").read_text(encoding="utf-8"))["fontes"]
    falhas = []
    for f in fontes:
        if not f.get("ativo"):
            print(f"pulando  {f['id']} (ativo: false)")
            continue
        try:
            m = baixar(f, forcar=args.forcar)
            print(f"ok       {f['id']}: {m['bytes'] / 1024:.0f} KB ({m['origem']}, acesso {m['data_acesso']})")
        except Exception as e:
            falhas.append(f)
            print(f"FALHOU   {f['id']}: {type(e).__name__}: {str(e)[:120]}")
    if falhas:
        titulo("Salve estas pelo navegador e rode de novo")
        for f in falhas:
            print(f"{f['url']}\n   -> {caminho_bruto(f)}")
        return 1
    print("\nPróximo: python scripts/02_fatiar.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
