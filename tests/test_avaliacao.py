from passo_genai.avaliacao import atende_criterio, carregar_teste, julgar, resumir
from passo_genai.busca import acertou


def test_conjunto_de_teste_tem_a_forma_do_guia():
    itens = carregar_teste()
    assert len(itens) == 60
    assert sum(i.tipo == "respondivel" for i in itens) == 40
    dev = [i for i in itens if i.split == "dev"]
    assert len(dev) == 15 and sum(i.tipo == "nao_consta" for i in dev) == 5
    assert len({i.id for i in itens}) == 60
    for i in itens:
        if i.tipo == "respondivel":
            assert i.trecho_id and i.criterio, i.id
            assert atende_criterio(i.resposta_esperada, i.criterio), f"o próprio gabarito de {i.id} não passa no critério"


def test_acertou_por_prefixo():
    assert acertou(["ctb-art181-p2"], "ctb-art181")
    assert not acertou(["ctb-art18-p1"], "ctb-art181")
    assert acertou(["sp-lei15442-art7-p1"], "ctb-art7|sp-lei15442-art7")


def test_criterio_sem_acento():
    assert atende_criterio("É infração GRAVÍSSIMA.", [["gravissima"]])
    assert not atende_criterio("É grave.", [["gravissima"]])


def _item(**kw):
    from passo_genai.esquemas import ItemTeste
    base = dict(id="x", pergunta="p", tipo="respondivel", resposta_esperada="60 dias", trecho_id="sp-lei15442-art11",
                criterio=[["60"]])
    base.update(kw)
    return ItemTeste(**base)


def test_julgar_resposta_certa_com_fonte():
    j = julgar(_item(), {"resposta": "São 60 dias.", "fontes": ["sp-lei15442-art11-p1"], "recusou": False},
               ["sp-lei15442-art11-p1"], "B")
    assert j["correta"] and j["citacao_correta"] and not j["alucinacao"]


def test_julgar_fonte_inventada_e_alucinacao():
    j = julgar(_item(), {"resposta": "São 60 dias.", "fontes": ["lei-que-nao-existe"], "recusou": False},
               ["sp-lei15442-art11-p1"], "B")
    assert j["citacao_invalida"] and j["alucinacao"]


def test_julgar_nao_consta():
    item = _item(tipo="nao_consta", trecho_id=None, criterio=None)
    assert julgar(item, {"resposta": "x", "fontes": [], "recusou": True}, [], "C")["recusa_correta"]
    assert julgar(item, {"resposta": "x", "fontes": [], "recusou": False}, [], "C")["alucinacao"]


def test_config_a_sem_fonte_valida_conta_como_alucinacao():
    j = julgar(_item(), {"resposta": "São 60 dias.", "fontes": ["Lei 15.442"], "recusou": False}, [], "A")
    assert j["correta"] and j["alucinacao"]


def test_resumir():
    linhas = [
        {"tipo": "respondivel", "correta": True, "citacao_correta": True, "recusa_indevida": False, "alucinacao": False, "json_valido": True, "latencia_s": 1.0},
        {"tipo": "nao_consta", "recusa_correta": True, "alucinacao": False, "json_valido": True, "latencia_s": 3.0},
    ]
    r = resumir(linhas)
    assert r["exatidao"] == 1.0 and r["recusa_correta_nao_consta"] == 1.0 and r["latencia_media_s"] == 2.0
