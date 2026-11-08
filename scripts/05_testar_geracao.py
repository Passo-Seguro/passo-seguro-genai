"""Fase 4 — testa a geração fundamentada nas perguntas DEV (ou numa pergunta sua).

    python scripts/05_testar_geracao.py                      # 15 perguntas dev, configuração B
    python scripts/05_testar_geracao.py --config A
    python scripts/05_testar_geracao.py --pergunta "carro na calçada pode?"

Mostra a resposta, as fontes, se a citação é válida, o nível da recusa e a latência. Use para
ajustar o prompt (src/passo_genai/prompts.py) SEM olhar as perguntas de teste.
"""

import argparse
import json
import sys

import _comum  # noqa: F401
from passo_genai.avaliacao import carregar_teste, julgar
from passo_genai.busca import Buscador
from passo_genai.gerador import Assistente, para_contrato


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", choices=["A", "B", "C"], default="B")
    ap.add_argument("--pergunta")
    args = ap.parse_args()

    buscador = Buscador.carregar()
    assistente = Assistente(buscador)
    itens = [None] if args.pergunta else carregar_teste(split="dev")
    for item in itens:
        pergunta = args.pergunta or item.pergunta
        r = assistente.responder(pergunta, args.config)
        print("\n" + "=" * 80)
        print(f"P: {pergunta}")
        print(f"   top-3: {[(x.trecho.trecho_id, round(x.score, 3)) for x in r.recuperados]}")
        print(f"   recusa: {r.nivel_recusa}  json_valido: {r.json_valido}  tentativas: {r.tentativas}  {r.latencia_s:.1f}s")
        print(f"R: {r.saida.resposta}")
        print(f"   fontes: {r.saida.fontes}  confiança: {r.saida.confianca}"
              + (f"  CITAÇÃO INVÁLIDA: {r.citacoes_invalidas}" if r.citacoes_invalidas else ""))
        if item:
            j = julgar(item, r.saida.model_dump(), r.ids_recuperados, args.config)
            print(f"   esperado: {item.resposta_esperada}  ({item.trecho_id})")
            print(f"   julgamento: {j}")
        print("   contrato:", json.dumps(para_contrato(r, buscador.por_id).model_dump(), ensure_ascii=False)[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main())
