"""Fase 3 — recall@1 e recall@3 da busca e escolha do limiar de similaridade.

    python scripts/04_avaliar_busca.py

1. recall@k nas perguntas respondíveis: o trecho do gabarito está entre os k primeiros?
   Se recall@3 < 0,8, revise o tamanho dos trechos (base/fontes.yaml, base.py) antes de seguir.
2. Varredura do limiar: para cada valor, mede
     - acerto nas respondíveis: melhor score >= limiar E o trecho certo no top-3;
     - recusa correta nas "não consta": melhor score < limiar.
   O limiar escolhido maximiza a média das duas taxas (acurácia balanceada) no split DEV
   (as 45 de teste não são usadas para escolher nada). A curva das 60 também vai para o
   gráfico, só para o relatório.
Saídas: avaliacao/busca.json, avaliacao/limiar.json, avaliacao/curva_limiar.png
"""

import json
import sys

import numpy as np

import _comum  # noqa: F401
from _comum import titulo
from passo_genai.avaliacao import carregar_teste
from passo_genai.busca import Buscador, acertou
from passo_genai.config import ARQ_LIMIAR, AVALIACAO


def curva(itens, resultados, limiares):
    pontos = []
    for lim in limiares:
        resp = [(i, r) for i, r in zip(itens, resultados) if i.tipo == "respondivel"]
        nc = [(i, r) for i, r in zip(itens, resultados) if i.tipo == "nao_consta"]
        acerto = np.mean([r[0].score >= lim and acertou([x.trecho.trecho_id for x in r], i.trecho_id) for i, r in resp]) if resp else 0
        recusa = np.mean([r[0].score < lim for i, r in nc]) if nc else 0
        pontos.append({"limiar": round(float(lim), 3), "acerto_respondiveis": round(float(acerto), 3),
                       "recusa_correta_nao_consta": round(float(recusa), 3),
                       "equilibrio": round(float((acerto + recusa) / 2), 3)})
    return pontos


def main() -> int:
    itens = carregar_teste()
    b = Buscador.carregar()
    resultados = b.buscar_lote([i.pergunta for i in itens], k=3)

    titulo("Recall da busca (respondíveis)")
    rel = {}
    for nome, filtro in (("dev", "dev"), ("todas", None)):
        sel = [(i, r) for i, r in zip(itens, resultados) if i.tipo == "respondivel" and (filtro is None or i.split == filtro)]
        r1 = np.mean([acertou([r[0].trecho.trecho_id], i.trecho_id) for i, r in sel])
        r3 = np.mean([acertou([x.trecho.trecho_id for x in r], i.trecho_id) for i, r in sel])
        rel[nome] = {"n": len(sel), "recall@1": round(float(r1), 3), "recall@3": round(float(r3), 3)}
        print(f"{nome:6s} n={len(sel):2d}  recall@1={r1:.3f}  recall@3={r3:.3f}")
    if rel["todas"]["recall@3"] < 0.8:
        print("ATENÇÃO: recall@3 < 0,8. Revise o fatiamento antes de seguir (ver PASSO_A_PASSO.md, passo 4).")
    falhas = [(i.id, i.pergunta, i.trecho_id, [x.trecho.trecho_id for x in r])
              for i, r in zip(itens, resultados)
              if i.tipo == "respondivel" and not acertou([x.trecho.trecho_id for x in r], i.trecho_id)]
    for f in falhas:
        print(f"  errou {f[0]}: esperado {f[2]}, veio {f[3]}  — {f[1]}")

    scores = [r[0].score for r in resultados]
    lo, hi = max(0.0, min(scores) - 0.02), min(1.0, max(scores) + 0.02)
    # o guia pede 0,3 a 0,8; com e5 as similaridades se concentram mais alto, então a varredura
    # cobre 0,3 até o maior score observado
    limiares = np.round(np.arange(min(0.30, round(lo, 2)), max(0.80, hi) + 1e-9, 0.005), 3)
    dev = [(i, r) for i, r in zip(itens, resultados) if i.split == "dev"]
    pontos_dev = curva([i for i, _ in dev], [r for _, r in dev], limiares)
    pontos_todas = curva(itens, resultados, limiares)
    melhor = max(pontos_dev, key=lambda p: (p["equilibrio"], -p["limiar"]))
    titulo("Limiar escolhido (split dev)")
    print(melhor)
    print(f"faixa de scores observada: {lo:.3f} a {hi:.3f}")

    AVALIACAO.mkdir(exist_ok=True)
    ARQ_LIMIAR.write_text(json.dumps({"limiar": melhor["limiar"], "escolhido_em": "dev", **melhor}, indent=2), encoding="utf-8")
    (AVALIACAO / "busca.json").write_text(json.dumps({"recall": rel, "falhas": falhas, "curva_dev": pontos_dev,
                                                      "curva_todas": pontos_todas}, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 4.5))
        for pts, estilo, rotulo in ((pontos_dev, "-", "dev"), (pontos_todas, ":", "todas as 60")):
            x = [p["limiar"] for p in pts]
            ax.plot(x, [p["acerto_respondiveis"] for p in pts], estilo, color="#1f6feb", label=f"acerto nas respondíveis ({rotulo})")
            ax.plot(x, [p["recusa_correta_nao_consta"] for p in pts], estilo, color="#d1242f", label=f"recusa correta nas não consta ({rotulo})")
        ax.axvline(melhor["limiar"], color="gray", ls="--")
        ax.annotate(f"limiar = {melhor['limiar']}", (melhor["limiar"], 0.05), xytext=(5, 0), textcoords="offset points")
        ax.set_xlim(min(0.3, lo), max(0.8, hi))
        ax.set_xlabel("limiar de similaridade (cosseno do melhor trecho)")
        ax.set_ylabel("taxa")
        ax.set_title("Acerto × recusa conforme o limiar")
        ax.legend(fontsize=8, loc="lower left")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(AVALIACAO / "curva_limiar.png", dpi=150)
        print(f"gráfico: {AVALIACAO / 'curva_limiar.png'}")
    except ImportError:
        print("(matplotlib não instalado: sem gráfico)")
    print(f"\nlimiar salvo em {ARQ_LIMIAR}. Próximo: python scripts/05_testar_geracao.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
