"""Fase 6 — PLACAR: roda as três configurações nas 45 perguntas de teste.

    python avaliacao/avaliar.py                 # A, B e C no split teste
    python avaliacao/avaliar.py --split dev     # ensaio nas 15 de desenvolvimento
    python avaliacao/avaliar.py --configs B C   # só algumas
    python avaliacao/avaliar.py --split app     # 16 perguntas no estilo do app (perguntas_app.jsonl)

    A = modelo base sem contexto      B = RAG simples (base + busca)      C = RAG + LoRA

Mesma máquina, mesma busca (feita uma vez e reaproveitada em B e C), mesmo limiar, mesma
temperatura. Saídas em avaliacao/:
    resultados/saidas/<config>.jsonl      saída bruta de cada pergunta (para os 5 erros e a revisão)
    resultados/placar.csv                 uma linha por configuração, com as métricas de criterio.md
    resultados/placar_por_registro.csv    as mesmas métricas separadas em formal × informal (viés)
    resultados/revisao_manual.csv         coluna correta_manual (1/0) para corrigir o julgamento automático
    resultados/placar.md                  tabela pronta para o README/relatório
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from passo_genai.avaliacao import carregar_teste, julgar, resumir, salvar_jsonl  # noqa: E402
from passo_genai.busca import Buscador  # noqa: E402
from passo_genai.config import AVALIACAO, RESULTADOS, Config  # noqa: E402
from passo_genai.gerador import Assistente, LLMIndisponivel  # noqa: E402

NOMES = {"A": "A — modelo sem contexto", "B": "B — RAG simples", "C": "C — RAG + LoRA"}
METRICAS = ["exatidao", "citacao_correta", "taxa_alucinacao", "recusa_correta_nao_consta", "recusa_indevida",
            "json_valido", "latencia_media_s"]


def ler_revisao() -> dict:
    arq = RESULTADOS / "revisao_manual.csv"
    if not arq.exists():
        return {}
    with open(arq, encoding="utf-8") as f:
        return {(r["config"], r["id"]): r["correta_manual"] for r in csv.DictReader(f) if r.get("correta_manual") in ("0", "1")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="teste", choices=["teste", "dev", "app"])
    ap.add_argument("--configs", nargs="+", default=["A", "B", "C"])
    args = ap.parse_args()

    cfg = Config()
    if args.split == "app":  # perguntas de "como fazer" que o app recebe; fora do teste oficial de 60
        itens = carregar_teste(AVALIACAO / "perguntas_app.jsonl", split="app")
    else:
        itens = carregar_teste(split=args.split)
    buscador = Buscador.carregar()
    assistente = Assistente(buscador, cfg)
    print(f"{len(itens)} perguntas ({args.split}); limiar={cfg.limiar}; top_k={cfg.top_k}; "
          f"base={cfg.modelo_base}; lora={cfg.modelo_lora}")
    t0 = time.perf_counter()
    busca = dict(zip([i.id for i in itens], buscador.buscar_lote([i.pergunta for i in itens], cfg.top_k)))
    t_busca = (time.perf_counter() - t0) / len(itens)

    revisao = ler_revisao()
    todas, placar = [], []
    for c in args.configs:
        linhas = []
        print(f"\n--- {NOMES[c]} ---")
        try:
            for k, item in enumerate(itens, 1):
                r = assistente.responder(item.pergunta, c, recuperados=None if c == "A" else busca[item.id])
                if c != "A":
                    r.latencia_s += t_busca  # a busca foi feita uma vez só; soma o custo médio dela
                j = julgar(item, r.saida.model_dump(), r.ids_recuperados, c)
                manual = revisao.get((c, item.id))
                if manual is not None and item.tipo == "respondivel":
                    j["correta_automatica"] = j["correta"]
                    j["correta"] = manual == "1"
                    j["alucinacao"] = (not j["recusou"]) and (not j["correta"] or j["citacao_invalida"] or not r.saida.fontes)
                linhas.append({"config": c, "id": item.id, "tipo": item.tipo, "registro": item.registro,
                               "pergunta": item.pergunta, "esperado": item.resposta_esperada, "trecho_esperado": item.trecho_id,
                               "resposta": r.saida.resposta, "fontes": r.saida.fontes, "confianca": r.saida.confianca,
                               "recuperados": [(x.trecho.trecho_id, round(x.score, 4)) for x in r.recuperados],
                               "score_max": r.score_max, "nivel_recusa": r.nivel_recusa, "json_valido": r.json_valido,
                               "tentativas": r.tentativas, "citacoes_invalidas": r.citacoes_invalidas,
                               "latencia_s": round(r.latencia_s, 3), "bruto": r.bruto, **j})
                print(f"  {k:2d}/{len(itens)} {item.id} {'ok ' if j.get('correta') or j.get('recusa_correta') else '-- '}"
                      f"{r.latencia_s:5.1f}s", end="\r")
        except LLMIndisponivel as e:
            print(f"\n{NOMES[c]}: Ollama indisponível ou modelo ausente ({e}). Pulando.")
            continue
        salvar_jsonl(RESULTADOS / "saidas" / f"{c}{'' if args.split == 'teste' else '_' + args.split}.jsonl", linhas)
        res = resumir(linhas)
        placar.append({"config": NOMES[c], **res})
        print(f"\n{json.dumps(res, ensure_ascii=False)}")
        todas += linhas

    if not placar:
        return 1
    sufixo = "" if args.split == "teste" else f"_{args.split}"
    with open(RESULTADOS / f"placar{sufixo}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["config", "n", *METRICAS])
        w.writeheader()
        w.writerows(placar)
    with open(RESULTADOS / f"placar_por_registro{sufixo}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["config", "registro", "n", *METRICAS])
        w.writeheader()
        for c in args.configs:
            for reg in ("formal", "informal"):
                sel = [l for l in todas if l["config"] == c and l["registro"] == reg]
                if sel:
                    w.writerow({"config": NOMES[c], "registro": reg, **resumir(sel)})
    arq_rev = RESULTADOS / f"revisao_manual{sufixo}.csv"
    if not arq_rev.exists():
        with open(arq_rev, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["config", "id", "pergunta", "esperado", "resposta", "correta_automatica", "correta_manual"])
            w.writeheader()
            for l in todas:
                if l["tipo"] == "respondivel":
                    w.writerow({"config": l["config"], "id": l["id"], "pergunta": l["pergunta"], "esperado": l["esperado"],
                                "resposta": l["resposta"], "correta_automatica": int(bool(l["correta"])), "correta_manual": ""})

    def fmt(v):
        return "–" if v is None else (f"{v:.0%}" if isinstance(v, float) and v <= 1 else str(v))

    cab = ["Configuração", "Exatidão", "Citação correta", "Alucinação", "Recusa correta (não consta)",
           "Recusa indevida", "JSON válido", "Latência média (s)"]
    md = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for p in placar:
        md.append("| " + " | ".join([p["config"], *(fmt(p[m]) if m != "latencia_media_s" else str(p[m]) for m in METRICAS)]) + " |")
    md += ["", f"{len(itens)} perguntas do split `{args.split}`; limiar {cfg.limiar}; top-{cfg.top_k}; "
               f"{len(revisao)} julgamentos corrigidos à mão.", "",
           "Interpretação (2–3 frases por diferença): onde o LoRA ganhou, onde não ganhou e por quê; "
           "o efeito do RAG sobre a alucinação; o custo em recusas indevidas; formal × informal "
           f"(ver placar_por_registro{sufixo}.csv)."]
    (RESULTADOS / f"placar{sufixo}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n" + "\n".join(md))
    print(f"\nSaídas em {RESULTADOS}. Próximo: python scripts/10_erros.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
