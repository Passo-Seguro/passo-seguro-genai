"""Fase 7 — separa candidatos a "cinco erros reais" a partir das saídas do placar.

    python scripts/10_erros.py [--config C]

Classifica cada erro pela causa provável (o diagnóstico final é seu, lendo o caso):
    busca_nao_achou    respondível, e o trecho do gabarito não veio no top-k
    recusa_por_limiar  respondível, trecho certo recuperado, mas o score ficou abaixo do limiar
    trecho_mal_cortado trecho certo recuperado, mas a resposta saiu incompleta/errada
                       (confira se a informação estava em outra parte -pN do artigo)
    modelo_inventou    citou fonte fora dos recuperados, ou respondeu uma "não consta"
    json_quebrou       saída inválida duas vezes
Gera avaliacao/resultados/erros_candidatos.md (todos) e avaliacao/resultados/cinco_erros.md (modelo para preencher).
"""

import argparse
import json
import sys
from collections import Counter

import _comum  # noqa: F401
from passo_genai.busca import acertou
from passo_genai.config import RESULTADOS, Config


def causa(l: dict, limiar: float) -> str | None:
    ids = [r[0] for r in l["recuperados"]]
    if not l["json_valido"]:
        return "json_quebrou"
    if l["tipo"] == "nao_consta":
        return "modelo_inventou" if not l["recusou"] else None
    if l.get("correta") and not l["citacao_invalida"]:
        return None
    if l["citacao_invalida"]:
        return "modelo_inventou"
    if l["config"] != "A" and not acertou(ids, l["trecho_esperado"]):
        return "busca_nao_achou"
    if l["nivel_recusa"] == "busca":
        return "recusa_por_limiar"
    if l["recusou"]:
        return "modelo_recusou_com_base"
    return "trecho_mal_cortado" if l["config"] != "A" else "modelo_inventou"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="C")
    args = ap.parse_args()
    arq = RESULTADOS / "saidas" / f"{args.config}.jsonl"
    if not arq.exists():
        print(f"{arq} não existe. Rode avaliacao/avaliar.py.")
        return 1
    linhas = [json.loads(l) for l in open(arq, encoding="utf-8")]
    lim = Config().limiar
    erros = [(causa(l, lim), l) for l in linhas]
    erros = [(c, l) for c, l in erros if c]
    cont = Counter(c for c, _ in erros)
    md = [f"# Erros candidatos — configuração {args.config}", "", f"{len(erros)} erros em {len(linhas)} perguntas: {dict(cont)}", ""]
    for c, l in sorted(erros, key=lambda x: x[0]):
        md += [f"## {l['id']} — {c}", f"- **Pergunta:** {l['pergunta']}", f"- **Esperado:** {l['esperado']} (`{l['trecho_esperado']}`)",
               f"- **Saída:** {l['resposta']}", f"- **Fontes citadas:** {l['fontes']} · recusou={l['recusou']} · nível={l['nivel_recusa']}",
               f"- **Recuperados:** {l['recuperados']}", ""]
    (RESULTADOS / "erros_candidatos.md").write_text("\n".join(md), encoding="utf-8")
    modelo = ["# Cinco erros reais (Fase 7)", "",
              "Escolha 5 erros DIFERENTES em `erros_candidatos.md`, de preferência com causas variadas.", ""]
    escolhidos, vistos = [], set()
    for c, l in erros:  # sugestão: um de cada causa primeiro
        if c not in vistos:
            escolhidos.append((c, l))
            vistos.add(c)
    escolhidos += [e for e in erros if e not in escolhidos]
    for n, (c, l) in enumerate(escolhidos[:5], 1):
        modelo += [f"## Erro {n} ({l['id']})", "", f"- **Pergunta:** {l['pergunta']}", f"- **Saída:** {l['resposta']}",
                   f"- **Causa:** {c.replace('_', ' ')} — [explique olhando os trechos recuperados]",
                   "- **Correção proposta:** [ex.: trecho menor/maior, sobreposição, mais exemplos de recusa no LoRA, "
                   "ajuste do limiar, sinônimo informal na base]", ""]
    if not (RESULTADOS / "cinco_erros.md").exists():
        (RESULTADOS / "cinco_erros.md").write_text("\n".join(modelo), encoding="utf-8")
        print("avaliacao/resultados/cinco_erros.md criado (preencha causa e correção).")
    print(f"{len(erros)} erros: {dict(cont)} -> avaliacao/resultados/erros_candidatos.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
