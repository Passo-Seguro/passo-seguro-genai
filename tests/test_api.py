"""O serviço tem de cumprir o contrato POST /assistente do openapi.yaml do repositório principal."""

import logging

from fastapi.testclient import TestClient

from api.app import criar_app
from passo_genai.gerador import Assistente, LLMIndisponivel
from tests.conftest import LLMFalso

TOKEN = "t"
CAB = {"Authorization": f"Bearer {TOKEN}"}


def cliente(buscador, config, respostas):
    app = criar_app(Assistente(buscador, config, LLMFalso(respostas)), token=TOKEN, config_vencedora="B")
    return TestClient(app)


def test_resposta_no_contrato(buscador, config):
    with cliente(buscador, config, [{"resposta": "Infração grave.", "fontes": ["ctb-art181-p1"], "confianca": 0.9, "recusou": False}]) as c:
        r = c.post("/assistente", json={"pergunta": "carro estacionado no passeio pode?"}, headers=CAB)
        assert r.status_code == 200
        corpo = r.json()
        assert set(corpo) == {"resposta", "fontes", "confianca", "recusou"}
        assert corpo["fontes"][0]["titulo"] and corpo["fontes"][0]["url"]
        assert 0 <= corpo["confianca"] <= 1


def test_llm_fora_do_ar_responde_contingencia_200(buscador, config):
    with cliente(buscador, config, [LLMIndisponivel("timeout")]) as c:
        r = c.post("/assistente", json={"pergunta": "estacionar no passeio"}, headers=CAB)
        assert r.status_code == 200
        assert r.json()["recusou"] is True and r.json()["fontes"] == [] and "156" in r.json()["resposta"]


def test_token(buscador, config):
    with cliente(buscador, config, []) as c:
        assert c.post("/assistente", json={"pergunta": "x"}).status_code == 401


def test_pergunta_vazia_ou_longa_422(buscador, config):
    with cliente(buscador, config, []) as c:
        assert c.post("/assistente", json={"pergunta": ""}, headers=CAB).status_code == 422
        assert c.post("/assistente", json={"pergunta": "a" * 501}, headers=CAB).status_code == 422


def test_log_nao_tem_o_texto_da_pergunta(buscador, config, caplog):
    segredo = "estacionar passeio meu telefone 11999990000"
    with cliente(buscador, config, [{"resposta": "x", "fontes": [], "confianca": 0.2, "recusou": True}]) as c:
        with caplog.at_level(logging.INFO, logger="passo_seguro.assistente"):
            c.post("/assistente", json={"pergunta": segredo}, headers=CAB)
    assert caplog.records and all("11999990000" not in r.getMessage() for r in caplog.records)


def test_cache_de_perguntas_repetidas(buscador, config):
    with cliente(buscador, config, [{"resposta": "Infração grave.", "fontes": ["ctb-art181-p1"], "confianca": 0.9, "recusou": False}]) as c:
        a = c.post("/assistente", json={"pergunta": "Estacionar no passeio?"}, headers=CAB).json()
        b = c.post("/assistente", json={"pergunta": "estacionar no   passeio?"}, headers=CAB).json()  # mesma após normalizar
        assert a == b  # a 2ª não chamou o LLM (a fila de respostas falsas tinha 1 só)


def test_json_declara_charset_utf8(buscador, config):
    # sem o charset, o Invoke-RestMethod do Windows PowerShell 5.1 lê o corpo como latin-1: "calÃ§ada"
    with cliente(buscador, config, [{"resposta": "Infração grave.", "fontes": ["ctb-art181-p1"], "confianca": 0.9, "recusou": False}]) as c:
        respostas = [c.post("/assistente", json={"pergunta": "carro na calçada?"}, headers=CAB),
                     c.post("/assistente", json={"pergunta": "x"}),
                     c.post("/assistente", json={"pergunta": ""}, headers=CAB),
                     c.get("/saude")]
        for r in respostas:
            assert r.headers["content-type"] == "application/json; charset=utf-8", r.request.url


def test_corpo_fora_de_utf8_vira_400_no_formato_de_erro(buscador, config):
    # é o que o curl.exe do Windows manda quando a pergunta tem acento: "calçada" em latin-1
    with cliente(buscador, config, []) as c:
        r = c.post("/assistente", content='{"pergunta": "calçada"}'.encode("latin-1"),
                   headers={**CAB, "Content-Type": "application/json"})
        assert r.status_code == 400 and r.json()["codigo"] == "requisicao_invalida"
