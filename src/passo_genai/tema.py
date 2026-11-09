"""Checagem de tema: a pergunta é sobre calçada, pedestre, travessia ou como reclamar em SP?

O limiar do reranker sozinho recusava perguntas do próprio tema escritas de forma informal
("tem um vaso enorme bloqueando a calçada, quem eu chamo?" teve score 0,03 com o trecho certo
em 1º). Agora a recusa pela busca vale só para pergunta FORA do tema; pergunta do tema sempre vai
ao modelo com os trechos mais próximos, e ele recusa se os trechos não responderem.
"""

from __future__ import annotations

import re

from passo_genai.avaliacao import normalizar

# radicais sem acento (a pergunta é normalizada antes): "calcad" pega calçada/calçadas/calcadão
TERMOS_DO_TEMA = [
    r"calcad", r"passeio", r"pedestre", r"travessi", r"faixa", r"atravess", r"semaforo", r"guia rebaixad",
    r"rampa", r"buraco", r"piso", r"desnivel", r"obstacul", r"entulho", r"acessib", r"cadeira de rodas",
    r"deficien", r"mobilidade reduzida", r"idos", r"carrinho de bebe", r"estacion", r"\bcarro", r"\bmoto",
    r"bicicleta", r"\bbike", r"patinete", r"ciclov", r"veiculo", r"\b156\b", r"sp156", r"subprefeitura",
    r"prefeitura", r"multa", r"infra[cç]", r"\bcet\b", r"transito", r"\bctb\b", r"arvore", r"raiz",
    r"poste", r"vistori", r"fiscaliza", r"denunci", r"reclam", r"conserto", r"consert", r"reform", r"arrum",
]
_RE_TEMA = re.compile("|".join(TERMOS_DO_TEMA))

# perguntas sobre o próprio assistente ("o que você sabe?"): resposta fixa, sem passar pela busca
_RE_SOBRE_O_ASSISTENTE = re.compile(
    r"(o ?que|quais?|sobre o que).{0,30}(voce|vc|tu).{0,30}(sabe|pode|responde|informa|ajuda|faz|tem)|"
    r"(o ?que|quais?).{0,20}(tem|ha) na (sua|tua) base|como (voce|vc) (funciona|pode ajudar)|^(ajuda|help)\??$"
)


def sobre_o_tema(pergunta: str) -> bool:
    return bool(_RE_TEMA.search(normalizar(pergunta)))


def sobre_o_assistente(pergunta: str) -> bool:
    return bool(_RE_SOBRE_O_ASSISTENTE.search(normalizar(pergunta)))
