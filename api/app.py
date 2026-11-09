"""Serviço do assistente: `POST /assistente`, no contrato do openapi.yaml do repositório principal.

- corpo `{"pergunta": "..."}` (1 a 500 caracteres);
- resposta `{resposta, fontes: [{titulo, url}], confianca, recusou}`;
- Bearer token (`ASSISTENTE_TOKEN`, o mesmo configurado na API principal);
- se o LLM não responder dentro do prazo, devolve 200 com a recusa padrão e o link do SP156
  (a API principal faz o mesmo do lado dela, com timeout de 15 s);
- LOG SEM O TEXTO DA PERGUNTA: só tempo, recusa e número de fontes. A pergunta nunca é ligada a
  um id de pessoa (a API principal nem envia o autor).

    uvicorn api.app:app --port 8002
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import sys
import time
from collections import OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.responses import JSONResponse as _JSONResponse, PlainTextResponse  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402


class JSONResponse(_JSONResponse):
    # sem o charset, o Invoke-RestMethod do Windows PowerShell 5.1 lê o corpo como latin-1 ("calÃ§ada")
    media_type = "application/json; charset=utf-8"

from passo_genai.avaliacao import normalizar  # noqa: E402
from passo_genai.config import Config  # noqa: E402
from passo_genai.esquemas import PerguntaAssistente, RespostaAssistente  # noqa: E402
from passo_genai.gerador import (Assistente, ClienteOllama, LLMIndisponivel, para_contrato, recusa_padrao,  # noqa: E402
                                  resposta_sobre_o_assistente)
from passo_genai.tema import sobre_o_assistente  # noqa: E402

log = logging.getLogger("passo_seguro.assistente")


def contingencia() -> RespostaAssistente:
    return RespostaAssistente(
        resposta=("O assistente não está disponível agora. Você ainda pode registrar o problema aqui no Passo "
                  "Seguro e, para falar com a Prefeitura, ligue 156 ou acesse o SP156: https://sp156.prefeitura.sp.gov.br/"),
        fontes=[], confianca=0.0, recusou=True)


class Cache:
    """Cache em memória das perguntas frequentes (plano B do risco "LLM lento")."""

    def __init__(self, tamanho: int):
        self.tamanho, self.dados = tamanho, OrderedDict()

    def obter(self, chave):
        if chave in self.dados:
            self.dados.move_to_end(chave)
            return self.dados[chave]
        return None

    def guardar(self, chave, valor):
        self.dados[chave] = valor
        self.dados.move_to_end(chave)
        while len(self.dados) > self.tamanho:
            self.dados.popitem(last=False)


def criar_app(assistente: Assistente | None = None, token: str | None = None, config_vencedora: str | None = None) -> FastAPI:
    token = os.getenv("ASSISTENTE_TOKEN", "") if token is None else token
    config_vencedora = config_vencedora or os.getenv("CONFIG_VENCEDORA", "C")
    estado = {"assistente": assistente, "erro": None}
    cache = Cache(int(os.getenv("CACHE_TAMANHO", "256")))
    contadores = {"total": 0, "recusas": 0, "contingencias": 0, "cache": 0}
    latencias: list[float] = []

    @asynccontextmanager
    async def ciclo(app):
        # stdout: o Railway (e outros) marca tudo o que sai no stderr como erro
        logging.basicConfig(level=os.getenv("NIVEL_LOG", "INFO"), format="%(message)s", stream=sys.stdout)
        if estado["assistente"] is None:
            try:
                from passo_genai.busca import Buscador

                cfg = Config()
                # o LLM tem até TIMEOUT_LLM_S (padrão 12 s aqui) para caber nos 15 s da API principal
                cfg.timeout_s = float(os.getenv("TIMEOUT_LLM_S", "12"))
                estado["assistente"] = Assistente(Buscador.carregar(), cfg, ClienteOllama(cfg.ollama_url, cfg.timeout_s))
                log.info(json.dumps({"evento": "pronto", "config": config_vencedora, "limiar": cfg.limiar,
                                     "modelo": estado["assistente"].modelo_da_config(config_vencedora)}))
            except Exception as e:
                estado["erro"] = type(e).__name__
                log.error(json.dumps({"evento": "falha_ao_carregar", "tipo_erro": type(e).__name__}))
        if not token:
            log.warning(json.dumps({"evento": "sem_token", "aviso": "ASSISTENTE_TOKEN vazio: endpoint sem autenticação"}))
        yield

    app = FastAPI(title="Passo Seguro — Assistente", version="1.0.0", lifespan=ciclo, redoc_url=None,
                  default_response_class=JSONResponse)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request, exc):
        # ex.: corpo que não decodifica (acento fora de UTF-8) -> 400 do FastAPI; mantém o formato {codigo, mensagem}
        codigos = {400: ("requisicao_invalida", "O corpo da requisição não é um JSON válido em UTF-8."),
                   404: ("nao_encontrado", "Rota não encontrada."), 405: ("metodo_nao_permitido", "Método não permitido.")}
        codigo, mensagem = codigos.get(exc.status_code, ("erro_http", str(exc.detail)))
        return JSONResponse(status_code=exc.status_code, content={"codigo": codigo, "mensagem": mensagem})

    @app.exception_handler(RequestValidationError)
    async def _validacao(request, exc):
        detalhes = [{"campo": str(e["loc"][-1]), "problema": e["msg"]} for e in exc.errors()]
        return JSONResponse(status_code=422, content={"codigo": "dados_invalidos", "mensagem": "Os dados enviados não são válidos.",
                                                      "detalhes": detalhes})

    def autorizado(request: Request) -> bool:
        if not token:
            return True
        cab = request.headers.get("authorization", "")
        return cab.lower().startswith("bearer ") and hmac.compare_digest(cab[7:].strip().encode(), token.encode())

    @app.get("/saude")
    async def saude():
        a = estado["assistente"]
        ok = a is not None
        return JSONResponse(status_code=200 if ok else 503, content={
            "status": "ok" if ok else "sem_base", "erro": estado["erro"], "config": config_vencedora,
            "modelo": a.modelo_da_config(config_vencedora) if ok else None,
            "limiar": a.config.limiar if ok else None, "trechos": len(a.buscador.trechos) if ok and a.buscador else None})

    @app.get("/metrics")
    async def metrics():
        linhas = [f'assistente_respostas_total{{tipo="{k}"}} {v}' for k, v in contadores.items()]
        if latencias:
            o = sorted(latencias)
            linhas += [f'assistente_latencia_segundos{{quantil="{q}"}} {o[min(int(q * len(o)), len(o) - 1)]:.3f}' for q in (0.5, 0.95)]
        return PlainTextResponse("\n".join(linhas) + "\n")

    @app.post("/assistente", response_model=RespostaAssistente)
    async def perguntar(corpo: PerguntaAssistente, request: Request):
        if not autorizado(request):
            return JSONResponse(status_code=401, content={"codigo": "nao_autenticado", "mensagem": "Token ausente ou inválido."})
        inicio = time.perf_counter()
        contadores["total"] += 1
        chave = normalizar(corpo.pergunta)
        if (em_cache := cache.obter(chave)) is not None:
            contadores["cache"] += 1
            return em_cache
        a = estado["assistente"]
        evento = {"evento": "resposta"}
        if a is None:
            resposta = contingencia()
            contadores["contingencias"] += 1
            evento["contingencia"] = "sem_base"
        elif sobre_o_assistente(corpo.pergunta):
            resposta = resposta_sobre_o_assistente(a.buscador.por_id)
            evento["tipo"] = "sobre_o_assistente"
        else:
            try:
                r = a.responder(corpo.pergunta, config_vencedora)
                resposta = para_contrato(r, a.buscador.por_id)
                evento.update({"nivel_recusa": r.nivel_recusa, "json_valido": r.json_valido,
                               "citacoes_invalidas": len(r.citacoes_invalidas), "score_max": r.score_max})
                if r.nivel_recusa != "json":
                    cache.guardar(chave, resposta)
            except LLMIndisponivel as e:
                resposta = contingencia()
                contadores["contingencias"] += 1
                evento["contingencia"] = str(e)[:40]
        if resposta.recusou:
            contadores["recusas"] += 1
        dur = time.perf_counter() - inicio
        latencias.append(dur)
        del latencias[:-2000]
        evento.update({"ms": round(dur * 1000), "recusou": resposta.recusou, "n_fontes": len(resposta.fontes)})
        log.info(json.dumps(evento))  # sem o texto da pergunta
        return resposta

    return app


app = criar_app()
