"""Geração fundamentada (Fase 4): busca -> recusa por limiar -> LLM com JSON forçado -> validação.

Três configurações (Fase 6):
    A = modelo base SEM contexto
    B = RAG simples (modelo base + busca)
    C = RAG + LoRA (modelo ajustado + busca)

Recusa em dois níveis:
    1. similaridade do melhor trecho abaixo do limiar -> recusa SEM chamar o modelo;
    2. o modelo também pode recusar (recusou: true).
JSON inválido: tenta de novo uma vez; se falhar de novo, recusa.
Checagem de citação: fonte citada que não está entre os trechos recuperados = alucinação.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

import httpx
from pydantic import ValidationError

from passo_genai.busca import Buscador, Resultado
from passo_genai.config import MENSAGEM_RECUSA, Config
from passo_genai.esquemas import SCHEMA_SAIDA, FonteCitada, RespostaAssistente, SaidaModelo
from passo_genai.prompts import mensagens_rag, mensagens_sem_contexto


class LLMIndisponivel(Exception):
    pass


class ClienteOllama:
    def __init__(self, url: str, timeout_s: float = 60.0, cliente: httpx.Client | None = None):
        self.url = url.rstrip("/")
        self.cliente = cliente or httpx.Client(timeout=timeout_s)
        self.timeout_s = timeout_s

    def chat(self, modelo: str, mensagens: list[dict], temperatura: float, max_tokens: int,
             schema: dict | None = SCHEMA_SAIDA) -> str:
        corpo = {"model": modelo, "messages": mensagens, "stream": False,
                 "options": {"temperature": temperatura, "num_predict": max_tokens, "seed": 42}}
        if schema is not None:
            corpo["format"] = schema  # saída estruturada do Ollama (>= 0.5)
        try:
            r = self.cliente.post(f"{self.url}/api/chat", json=corpo, timeout=self.timeout_s)
        except httpx.HTTPError as e:
            raise LLMIndisponivel(type(e).__name__) from None
        if r.status_code != 200:
            raise LLMIndisponivel(f"status {r.status_code}: {r.text[:200]}")
        return r.json()["message"]["content"]


@dataclass
class RespostaGerada:
    saida: SaidaModelo
    config: str
    recuperados: list[Resultado] = field(default_factory=list)
    score_max: float | None = None
    nivel_recusa: str | None = None  # "busca" | "modelo" | "json" | None
    json_valido: bool = True
    tentativas: int = 0
    citacoes_invalidas: list[str] = field(default_factory=list)
    bruto: str = ""
    latencia_s: float = 0.0

    @property
    def ids_recuperados(self) -> list[str]:
        return [r.trecho.trecho_id for r in self.recuperados]


def recusa_padrao(confianca: float = 0.0) -> SaidaModelo:
    return SaidaModelo(resposta=MENSAGEM_RECUSA, fontes=[], confianca=confianca, recusou=True)


def _parse(texto: str) -> SaidaModelo:
    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.strip("`").removeprefix("json").strip()
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio < 0 or fim < 0:
        raise ValueError("sem objeto JSON")
    return SaidaModelo.model_validate(json.loads(texto[inicio:fim + 1]))


class Assistente:
    def __init__(self, buscador: Buscador | None, config: Config | None = None, llm: ClienteOllama | None = None):
        self.config = config or Config()
        self.buscador = buscador
        self.llm = llm or ClienteOllama(self.config.ollama_url, self.config.timeout_s)

    def modelo_da_config(self, config: str) -> str:
        return self.config.modelo_lora if config == "C" else self.config.modelo_base

    def responder(self, pergunta: str, config: str = "C", limiar: float | None = None,
                  recuperados: list[Resultado] | None = None) -> RespostaGerada:
        """Responde a pergunta na configuração A, B ou C. `recuperados` permite reaproveitar a
        busca (o placar busca uma vez e usa o mesmo contexto em B e C)."""
        inicio = time.perf_counter()
        limiar = self.config.limiar if limiar is None else limiar
        if config == "A":
            mensagens = mensagens_sem_contexto(pergunta)
            recuperados = []
        else:
            if recuperados is None:
                recuperados = self.buscador.buscar(pergunta, self.config.top_k)
            score = recuperados[0].score if recuperados else 0.0
            if score < limiar:
                return RespostaGerada(recusa_padrao(), config, recuperados, score, nivel_recusa="busca",
                                  latencia_s=time.perf_counter() - inicio)
            mensagens = mensagens_rag(pergunta, [r.trecho for r in recuperados])

        modelo = self.modelo_da_config(config)
        bruto, saida, tentativas = "", None, 0
        for tentativas in (1, 2):
            bruto = self.llm.chat(modelo, mensagens, self.config.temperatura, self.config.max_tokens)
            try:
                saida = _parse(bruto)
                break
            except (ValueError, ValidationError, json.JSONDecodeError):
                continue
        res = RespostaGerada(saida or recusa_padrao(), config, recuperados,
                         recuperados[0].score if recuperados else None,
                         json_valido=saida is not None, tentativas=tentativas, bruto=bruto)
        if saida is None:
            res.nivel_recusa = "json"
        elif saida.recusou:
            res.nivel_recusa = "modelo"
        elif config != "A":
            ids = set(res.ids_recuperados)
            res.citacoes_invalidas = [f for f in saida.fontes if f not in ids]
        res.latencia_s = time.perf_counter() - inicio
        return res


def para_contrato(res: RespostaGerada, por_id: dict) -> RespostaAssistente:
    """Converte para o contrato público. No PRODUTO, citação fora dos trechos recuperados é
    descartada; se nenhuma fonte válida sobrar, vira recusa (o app sempre mostra as fontes)."""
    s = res.saida
    if s.recusou:
        return RespostaAssistente(resposta=s.resposta or MENSAGEM_RECUSA, fontes=[], confianca=min(s.confianca, 0.3), recusou=True)
    validas = [f for f in s.fontes if f in por_id and f not in res.citacoes_invalidas]
    if not validas:
        r = recusa_padrao()
        return RespostaAssistente(resposta=r.resposta, fontes=[], confianca=0.0, recusou=True)
    fontes, vistos = [], set()
    for f in validas:
        t = por_id[f]
        titulo = f"{t.titulo}, {t.artigo}" if t.artigo and t.artigo.lower().startswith(("art", "anexo")) else t.titulo
        if titulo in vistos:
            continue
        vistos.add(titulo)
        fontes.append(FonteCitada(titulo=titulo, url=t.url))
    return RespostaAssistente(resposta=s.resposta, fontes=fontes, confianca=round(s.confianca, 3), recusou=False)
