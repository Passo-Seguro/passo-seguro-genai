"""Fase 5 — revisão À MÃO dos exemplos gerados, e exportação do treino/treino.jsonl.

    python scripts/07_revisar_exemplos.py            # revisa os pendentes (salva a cada item)
    python scripts/07_revisar_exemplos.py --exportar # gera treino/treino.jsonl com os aprovados

Para cada exemplo aparecem a pergunta, o trecho de origem e a resposta. Teclas:
    a = aprovar      e = editar a resposta      r = rejeitar      p = pular      q = sair
Rejeite: pergunta que o trecho não responde, resposta que inventa algo, pergunta repetida.
Edite: resposta longa demais, termo errado, informação faltando. O guia pede revisão de todos.
"""

import argparse
import json
import sys
import textwrap

import _comum  # noqa: F401
from _comum import titulo
from passo_genai.base import carregar_trechos
from passo_genai.config import TREINO
from passo_genai.prompts import mensagens_rag

BRUTO = TREINO / "treino_bruto.jsonl"


def carregar():
    return [json.loads(l) for l in open(BRUTO, encoding="utf-8") if l.strip()]


def salvar(exemplos):
    with open(BRUTO, "w", encoding="utf-8") as f:
        for e in exemplos:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def revisar(exemplos, por_id):
    pendentes = [e for e in exemplos if not e["revisado"]]
    print(f"{len(pendentes)} pendentes de {len(exemplos)}")
    for n, e in enumerate(pendentes, 1):
        print("\n" + "=" * 90)
        print(f"[{n}/{len(pendentes)}] {e['id']}  tipo={e['tipo']}")
        print(f"PERGUNTA: {e['pergunta']}")
        if e["trecho_origem"]:
            t = por_id.get(e["trecho_origem"])
            print(f"TRECHO DE ORIGEM ({e['trecho_origem']}):")
            print(textwrap.indent(textwrap.shorten(t.texto if t else "?", 900), "   "))
        if e["tipo"] == "recusa_sem_base":
            print(f"CONTEXTO DADO (não deve responder): {e['contexto_ids']}")
        print(f"RESPOSTA: {e['saida']['resposta']}")
        print(f"FONTES: {e['saida']['fontes']}  recusou={e['saida']['recusou']}")
        while True:
            op = input("[a]provar [e]ditar [r]ejeitar [p]ular [q]sair > ").strip().lower()
            if op in ("a", "r"):
                e["revisado"], e["aprovado"] = True, op == "a"
                break
            if op == "e":
                nova = input("nova resposta: ").strip()
                if nova:
                    e["saida"]["resposta"] = nova
                    e["editado"] = True
                    e["revisado"], e["aprovado"] = True, True
                break
            if op == "p":
                break
            if op == "q":
                salvar(exemplos)
                return
        salvar(exemplos)


def exportar(exemplos, por_id):
    aprovados = [e for e in exemplos if e.get("aprovado")]
    pendentes = sum(not e["revisado"] for e in exemplos)
    if pendentes:
        print(f"AVISO: {pendentes} exemplos ainda não revisados ficam de fora.")
    with open(TREINO / "treino.jsonl", "w", encoding="utf-8") as f:
        for e in aprovados:
            trechos = [por_id[i] for i in e["contexto_ids"] if i in por_id]
            mensagens = mensagens_rag(e["pergunta"], trechos)
            # formato prompt/completion do TRL: a perda é calculada só na resposta
            f.write(json.dumps({"id": e["id"], "tipo": e["tipo"], "prompt": mensagens,
                                "completion": [{"role": "assistant", "content": json.dumps(e["saida"], ensure_ascii=False)}]},
                               ensure_ascii=False) + "\n")
    tipos = {t: sum(e["tipo"] == t for e in aprovados) for t in ("resposta", "recusa_fora_escopo", "recusa_sem_base")}
    rec = (tipos["recusa_fora_escopo"] + tipos["recusa_sem_base"]) / max(len(aprovados), 1)
    resumo = (f"Exemplos aprovados: {len(aprovados)} de {len(exemplos)} gerados; "
              f"rejeitados: {sum(e['revisado'] and not e['aprovado'] for e in exemplos)}; "
              f"editados: {sum(bool(e.get('editado')) for e in exemplos)}\n"
              f"Por tipo: {tipos}\nRecusas: {rec:.0%} (meta ~25%)\n")
    (TREINO / "estatisticas.md").write_text(resumo, encoding="utf-8")
    titulo("treino/treino.jsonl")
    print(resumo)
    print("Próximo: python scripts/08_treinar_lora.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exportar", action="store_true")
    args = ap.parse_args()
    por_id = {t.trecho_id: t for t in carregar_trechos()}
    exemplos = carregar()
    if args.exportar:
        exportar(exemplos, por_id)
    else:
        revisar(exemplos, por_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
