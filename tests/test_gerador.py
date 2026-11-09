from passo_genai.gerador import Assistente, para_contrato
from tests.conftest import LLMFalso


def test_recusa_pela_busca_nao_chama_o_modelo(buscador, config):
    config.limiar = 0.99
    llm = LLMFalso([])
    r = Assistente(buscador, config, llm).responder("qual a previsão do tempo?", "B")
    assert r.saida.recusou and r.nivel_recusa == "busca" and llm.chamadas == []


def test_resposta_valida_vira_contrato_com_titulo_e_url(buscador, config):
    llm = LLMFalso([{"resposta": "Não pode: é infração grave.", "fontes": ["ctb-art181-p1"], "confianca": 0.9, "recusou": False}])
    a = Assistente(buscador, config, llm)
    r = a.responder("estacionar o veículo no passeio pode?", "B")
    assert r.json_valido and not r.citacoes_invalidas
    c = para_contrato(r, buscador.por_id)
    assert not c.recusou and c.fontes[0].titulo.endswith("Art. 181") and c.fontes[0].url.startswith("https://")
    # o prompt levou os trechos com o trecho_id
    assert "trecho_id: ctb-art181-p1" in llm.chamadas[0]["mensagens"][1]["content"]


def test_json_invalido_tenta_de_novo_e_depois_recusa(buscador, config):
    llm = LLMFalso(["isto não é json", "nem isto"])
    r = Assistente(buscador, config, llm).responder("estacionar no passeio", "B")
    assert r.nivel_recusa == "json" and r.tentativas == 2 and r.saida.recusou and not r.json_valido


def test_json_invalido_na_primeira_e_valido_na_segunda(buscador, config):
    llm = LLMFalso(["{quebrado", {"resposta": "60 dias.", "fontes": ["sp-lei15442-art11-p1"], "confianca": 0.8, "recusou": False}])
    r = Assistente(buscador, config, llm).responder("prazo regularização calçada", "B")
    assert r.json_valido and r.tentativas == 2


def test_citacao_fora_dos_recuperados_vira_recusa_no_produto(buscador, config):
    llm = LLMFalso([{"resposta": "Pode sim.", "fontes": ["lei-inventada-art1"], "confianca": 0.9, "recusou": False}])
    r = Assistente(buscador, config, llm).responder("estacionar no passeio", "B")
    assert r.citacoes_invalidas == ["lei-inventada-art1"]
    assert para_contrato(r, buscador.por_id).recusou


def test_config_c_usa_o_modelo_lora_e_a_sem_contexto(buscador, config):
    llm = LLMFalso([{"resposta": "a", "fontes": [], "confianca": 0.5, "recusou": True}] * 2)
    a = Assistente(buscador, config, llm)
    a.responder("estacionar no passeio", "C")
    a.responder("estacionar no passeio", "A")
    assert llm.chamadas[0]["modelo"] == config.modelo_lora
    assert llm.chamadas[1]["modelo"] == config.modelo_base
    assert "TRECHOS" not in llm.chamadas[1]["mensagens"][1]["content"]


def test_pergunta_do_tema_abaixo_do_limiar_vai_ao_modelo(buscador, config):
    # o reranker dá nota baixa a pergunta informal do tema; ela não pode ser recusada antes do modelo
    config.limiar = 0.99
    llm = LLMFalso([{"resposta": "Peça no SP156.", "fontes": ["ctb-art181-p1"], "confianca": 0.8, "recusou": False}])
    r = Assistente(buscador, config, llm).responder("tem um vaso enorme bloqueando a calçada, quem eu chamo?", "B")
    assert r.nivel_recusa is None and len(llm.chamadas) == 1


def test_sem_portao_de_tema_volta_a_recusar_pelo_limiar(buscador, config):
    config.limiar, config.portao_tema = 0.99, False
    llm = LLMFalso([])
    r = Assistente(buscador, config, llm).responder("tem um vaso bloqueando a calçada", "B")
    assert r.nivel_recusa == "busca" and llm.chamadas == []
