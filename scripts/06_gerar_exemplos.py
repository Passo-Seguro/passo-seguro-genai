"""Fase 5 — gera os ~300 exemplos de treino do LoRA a partir da base, com um modelo professor maior.

    python scripts/06_gerar_exemplos.py [--alvo 300] [--recusas 0.25]

Cada exemplo é: pergunta + os 3 trechos que a BUSCA recuperaria -> JSON correto.
- respostas: o professor lê UM trecho e escreve 1–2 perguntas que ele responde, como pedestre
  fala (metade informal), e a resposta curta. O trecho de origem é garantido no contexto.
- recusas (~25%), de dois tipos:
    fora_escopo: perguntas que a base não cobre (custo de obra, indenização, IPTU...) -> recusa;
    sem_base: pergunta respondível, mas com 3 trechos que NÃO a respondem -> recusa.
  Isso ensina o modelo a recusar quando o contexto não sustenta a resposta.

Contra vazamento: descarta todo exemplo com similaridade >= 0,90 com QUALQUER pergunta de
avaliacao/teste.jsonl (dev e teste). Vazamento invalida o placar.

Saída: treino/treino_bruto.jsonl (revisado=false). Depois: scripts/07_revisar_exemplos.py
Configure o professor no .env (ver .env.exemplo).
"""

import argparse
import json
import random
import sys

import numpy as np

import _comum  # noqa: F401
from _comum import titulo
from passo_genai.avaliacao import carregar_teste, normalizar
from passo_genai.busca import Buscador
from passo_genai.config import MENSAGEM_RECUSA, TREINO
from passo_genai.professor import Professor

SISTEMA_PROF = """Você cria dados de treino para um assistente de pedestres de São Paulo. Responda só em JSON."""

PEDIDO_PERGUNTAS = """Leia o TRECHO oficial abaixo e escreva {n} perguntas DIFERENTES que um pedestre de São Paulo \
faria e que este trecho responde sozinho. {estilo}
Para cada pergunta, escreva a resposta correta em até 3 frases, usando SÓ o que o trecho diz \
(sem inventar valores, prazos ou nomes).
Formato: {{"itens": [{{"pergunta": "...", "resposta": "..."}}]}}

TRECHO ({trecho_id}):
{texto}"""

ESTILOS = [
    "Escreva como as pessoas falam no dia a dia, informal, com 'tá', 'pra', 'a gente', sem pontuação perfeita.",
    "Escreva de forma clara e formal.",
]

PEDIDO_FORA = """Escreva {n} perguntas variadas que um pedestre de São Paulo poderia fazer a um assistente sobre \
calçadas, mas que NÃO são respondidas por leis de trânsito, leis de calçada ou serviços do 156. Exemplos de tema: \
custo de obra, empresa para contratar, indenização por queda, IPTU, horários de órgãos, previsão do tempo, \
regras de condomínio, investimentos, dados estatísticos, outras cidades, patinete, recursos de multa. \
Metade informal, metade formal. Formato: {{"perguntas": ["..."]}}"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alvo", type=int, default=300)
    ap.add_argument("--recusas", type=float, default=0.25)
    ap.add_argument("--por-trecho", type=int, default=2)
    ap.add_argument("--semente", type=int, default=42)
    args = ap.parse_args()
    rnd = random.Random(args.semente)

    buscador = Buscador.carregar()
    prof = Professor()
    titulo(f"Professor: {prof.descricao}")
    teste = carregar_teste()
    vetores_teste = buscador.emb.consultas([t.pergunta for t in teste])
    textos_teste = {normalizar(t.pergunta) for t in teste}

    def vaza(pergunta: str) -> bool:
        if normalizar(pergunta) in textos_teste:
            return True
        v = buscador.emb.consultas([pergunta])[0]
        return float((vetores_teste @ v).max()) >= 0.90

    n_recusa = int(args.alvo * args.recusas)
    n_resp = args.alvo - n_recusa
    exemplos, descartes = [], 0
    trechos = buscador.trechos[:]
    rnd.shuffle(trechos)

    titulo(f"Gerando {n_resp} respostas")
    i = 0
    while sum(e["tipo"] == "resposta" for e in exemplos) < n_resp and i < len(trechos) * 2:
        t = trechos[i % len(trechos)]
        i += 1
        try:
            dados = prof.json(SISTEMA_PROF, PEDIDO_PERGUNTAS.format(n=args.por_trecho, estilo=rnd.choice(ESTILOS),
                                                                     trecho_id=t.trecho_id, texto=t.texto[:3500]))
        except Exception as e:
            print(f"  professor falhou em {t.trecho_id}: {type(e).__name__}")
            continue
        for it in dados.get("itens", [])[: args.por_trecho]:
            p, r = (it.get("pergunta") or "").strip(), (it.get("resposta") or "").strip()
            if len(p) < 8 or len(r) < 8:
                continue
            if vaza(p):
                descartes += 1
                continue
            ctx = [x.trecho.trecho_id for x in buscador.buscar(p, 3)]
            if t.trecho_id not in ctx:
                ctx = ctx[:2] + [t.trecho_id]
                rnd.shuffle(ctx)
            exemplos.append({"id": f"t{len(exemplos):04d}", "tipo": "resposta", "pergunta": p, "trecho_origem": t.trecho_id,
                             "contexto_ids": ctx,
                             "saida": {"resposta": r, "fontes": [t.trecho_id], "confianca": round(rnd.uniform(0.8, 0.95), 2),
                                       "recusou": False},
                             "revisado": False, "aprovado": None})
        print(f"  {sum(e['tipo'] == 'resposta' for e in exemplos)}/{n_resp}", end="\r")

    titulo(f"Gerando {n_recusa} recusas")
    fora, tentativas = [], 0
    while len(fora) < n_recusa // 2 + 5 and tentativas < 20:
        tentativas += 1
        try:
            fora += [p for p in prof.json(SISTEMA_PROF, PEDIDO_FORA.format(n=15), 0.9).get("perguntas", []) if isinstance(p, str)]
        except Exception as e:
            print(f"  professor falhou: {type(e).__name__}")
            break
    recusa = {"resposta": MENSAGEM_RECUSA, "fontes": [], "confianca": 0.1, "recusou": True}
    for p in fora[: n_recusa // 2]:
        if vaza(p):
            descartes += 1
            continue
        exemplos.append({"id": f"t{len(exemplos):04d}", "tipo": "recusa_fora_escopo", "pergunta": p.strip(), "trecho_origem": None,
                         "contexto_ids": [x.trecho.trecho_id for x in buscador.buscar(p, 3)], "saida": dict(recusa),
                         "revisado": False, "aprovado": None})
    respostas = [e for e in exemplos if e["tipo"] == "resposta"]
    for base in rnd.sample(respostas, min(len(respostas), n_recusa - (n_recusa // 2))):
        origem = base["trecho_origem"]
        artigo = origem.rsplit("-p", 1)[0]
        v = buscador.emb.consultas([base["pergunta"]])[0]
        sims = buscador.vetores @ v
        # trechos "parecidos mas errados": medianamente similares, de outro artigo
        ordem = [buscador.trechos[j].trecho_id for j in np.argsort(-sims)]
        candidatos = [x for x in ordem[5:40] if not x.startswith(artigo)]
        ctx = rnd.sample(candidatos, 3) if len(candidatos) >= 3 else candidatos
        exemplos.append({"id": f"t{len(exemplos):04d}", "tipo": "recusa_sem_base", "pergunta": base["pergunta"], "trecho_origem": origem,
                         "contexto_ids": ctx, "saida": dict(recusa), "revisado": False, "aprovado": None})

    TREINO.mkdir(exist_ok=True)
    destino = TREINO / "treino_bruto.jsonl"
    with open(destino, "w", encoding="utf-8") as f:
        for e in exemplos:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    tipos = {t: sum(e["tipo"] == t for e in exemplos) for t in ("resposta", "recusa_fora_escopo", "recusa_sem_base")}
    titulo("Pronto")
    print(f"{len(exemplos)} exemplos {tipos}; {descartes} descartados por parecerem perguntas do teste.")
    print(f"{destino}\nPróximo: python scripts/07_revisar_exemplos.py  (revisão à mão é obrigatória)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
