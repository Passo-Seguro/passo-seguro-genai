"""Métricas do placar (Fase 6), com o critério de julgamento escrito em avaliacao/criterio.md."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

from passo_genai.busca import acertou
from passo_genai.config import TESTE
from passo_genai.esquemas import ItemTeste


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def carregar_teste(caminho: Path = TESTE, split: str | None = None) -> list[ItemTeste]:
    itens = [ItemTeste.model_validate_json(l) for l in open(caminho, encoding="utf-8") if l.strip()]
    return [i for i in itens if split is None or i.split == split]


def atende_criterio(resposta: str, criterio: list[list[str]] | None) -> bool:
    if not criterio:
        return False
    r = normalizar(resposta)
    return all(any(normalizar(termo) in r for termo in grupo) for grupo in criterio)


def julgar(item: ItemTeste, saida: dict, ids_recuperados: list[str], config: str) -> dict:
    """Julga UMA resposta. `saida` = SaidaModelo como dict (resposta, fontes, confianca, recusou).

    - correta (respondíveis): não recusou E a resposta atende ao critério escrito do gabarito.
    - citacao_correta (B e C): citou o trecho esperado.
    - citacao_invalida: citou trecho que NÃO estava entre os recuperados (o modelo inventou a fonte).
    - alucinacao: respondeu (recusou=false) e (a pergunta é "não consta", OU não citou fonte
      válida, OU citou fonte fora dos recuperados, OU a resposta está errada).
      Na configuração A não há trechos: toda resposta é "sem fonte válida", por definição.
    - recusa_correta ("não consta"): recusou.
    """
    recusou = bool(saida.get("recusou"))
    fontes = list(saida.get("fontes") or [])
    ids = set(ids_recuperados)
    invalidas = [f for f in fontes if f not in ids] if config != "A" else []
    validas = [f for f in fontes if f in ids] if config != "A" else []
    j = {"recusou": recusou, "citacao_invalida": bool(invalidas)}
    if item.tipo == "respondivel":
        j["correta"] = (not recusou) and atende_criterio(saida.get("resposta", ""), item.criterio)
        j["citacao_correta"] = (not recusou) and acertou(validas, item.trecho_id)
        j["recusa_indevida"] = recusou
        j["alucinacao"] = (not recusou) and (not validas or bool(invalidas) or not j["correta"])
    else:
        j["recusa_correta"] = recusou
        j["alucinacao"] = not recusou
    return j


def resumir(linhas: list[dict]) -> dict:
    """linhas: uma por (pergunta, config) com os campos do julgar() + tipo, json_valido, latencia_s."""
    resp = [l for l in linhas if l["tipo"] == "respondivel"]
    nc = [l for l in linhas if l["tipo"] == "nao_consta"]

    def taxa(xs, campo):
        return round(sum(bool(x.get(campo)) for x in xs) / len(xs), 3) if xs else None

    return {
        "n": len(linhas),
        "exatidao": taxa(resp, "correta"),
        "citacao_correta": taxa(resp, "citacao_correta"),
        "recusa_indevida": taxa(resp, "recusa_indevida"),
        "taxa_alucinacao": taxa(linhas, "alucinacao"),
        "recusa_correta_nao_consta": taxa(nc, "recusa_correta"),
        "json_valido": taxa(linhas, "json_valido"),
        "latencia_media_s": round(sum(l["latencia_s"] for l in linhas) / len(linhas), 2) if linhas else None,
    }


def salvar_jsonl(caminho: Path, linhas: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        for l in linhas:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
