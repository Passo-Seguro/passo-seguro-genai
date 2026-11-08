"""Fase 2 — limpa e fatia as fontes em base/trechos.jsonl e gera a tabela da base para o relatório.

    python scripts/02_fatiar.py

Também confere o gabarito: todo `trecho_id` de avaliacao/teste.jsonl precisa existir na base
(senão a pergunta "respondível" não tem como ser respondida).
"""

import json
import statistics
import sys
from collections import defaultdict

import yaml

import _comum  # noqa: F401
from _comum import titulo
from passo_genai.avaliacao import carregar_teste
from passo_genai.base import caminho_bruto, contar_tokens, fatiar_fonte, salvar_trechos
from passo_genai.busca import acertou
from passo_genai.config import BASE, TRECHOS


def main() -> int:
    fontes = yaml.safe_load((BASE / "fontes.yaml").read_text(encoding="utf-8"))["fontes"]
    trechos, linhas_tabela = [], []
    for f in fontes:
        if not f.get("ativo"):
            continue
        bruto = caminho_bruto(f)
        meta_arq = bruto.with_suffix(".meta.json")
        if not bruto.exists() or not meta_arq.exists():
            print(f"FALTA {f['id']}: rode o 01_baixar_base.py")
            return 1
        meta = json.loads(meta_arq.read_text(encoding="utf-8"))
        ts = fatiar_fonte(f, meta)
        tokens = [contar_tokens(t.texto) for t in ts]
        print(f"{f['id']}: {len(ts)} trechos, tokens mediana {statistics.median(tokens) if ts else 0:.0f}, "
              f"máx {max(tokens) if ts else 0}")
        trechos += ts
        formato = {"lei_html": "HTML (lei/decreto)", "pagina": "HTML (página)", "pdf": "PDF"}[f["tipo"]]
        linhas_tabela.append(f"| {f['titulo']} | {formato} | {f['licenca']} | {len(ts)} | {meta['data_acesso']} | {f['url']} |")
    ids = [t.trecho_id for t in trechos]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        print(f"ERRO: trecho_id repetido: {sorted(dup)[:5]}")
        return 1
    salvar_trechos(trechos)
    tabela = ["| Fonte | Formato | Licença | Trechos | Acesso | URL |", "|---|---|---|---|---|---|", *linhas_tabela,
              f"| **Total** | | | **{len(trechos)}** | | |"]
    (BASE / "tabela_base.md").write_text("\n".join(tabela) + "\n", encoding="utf-8")
    titulo(f"{len(trechos)} trechos em {TRECHOS}")
    print("\n".join(tabela))

    titulo("Conferindo o gabarito contra a base")
    sem_base = defaultdict(list)
    for item in carregar_teste():
        if item.tipo == "respondivel" and not acertou(ids, item.trecho_id):
            sem_base[item.trecho_id].append(item.id)
    if sem_base:
        for ref, qs in sem_base.items():
            print(f"AVISO: {ref} não existe na base (perguntas {qs}). Fonte inativa, artigo fora do filtro ou id diferente.")
        print("Ajuste base/fontes.yaml ou o trecho_id dessas perguntas antes do placar.")
    else:
        print("ok: todo trecho_id do gabarito existe na base.")
    print("\nPróximo: python scripts/03_indexar.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
