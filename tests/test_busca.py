import numpy as np

from passo_genai.busca import Buscador


class RerankerFalso:
    """Dá nota alta ao trecho que tem a palavra-chave, como um cross-encoder faria."""

    def __init__(self, chave):
        self.chave = chave
        self.chamadas = 0

    def pontuar(self, pergunta, textos):
        self.chamadas += 1
        return np.array([0.9 if self.chave in t else 0.1 for t in textos], dtype=np.float32)


def test_sem_reranker_o_score_e_o_cosseno(buscador):
    r = buscador.buscar("estacionar o veículo no passeio", 2)
    assert r[0].trecho.trecho_id == "ctb-art181-p1"
    assert r[0].score == r[0].score_denso


def test_reranker_reordena_os_candidatos_e_o_score_passa_a_ser_o_dele(buscador):
    rr = RerankerFalso("60 dias")
    b = Buscador(buscador.trechos, buscador.vetores, buscador.emb, reranker=rr, candidatos=3)
    r = b.buscar("estacionar o veículo no passeio", 2)
    # o e5 põe o art. 181 em 1º; o reranker manda o trecho do prazo para o topo
    assert r[0].trecho.trecho_id == "sp-lei15442-art11-p1"
    assert r[0].score == np.float32(0.9) and r[0].score_denso is not None
    assert len(r) == 2 and rr.chamadas == 1


def test_lote_usa_o_reranker_em_cada_pergunta(buscador):
    rr = RerankerFalso("prioridade")
    b = Buscador(buscador.trechos, buscador.vetores, buscador.emb, reranker=rr, candidatos=3)
    lotes = b.buscar_lote(["faixa de pedestre", "prazo da calçada"], 1)
    assert [l[0].trecho.trecho_id for l in lotes] == ["ctb-art70-p1", "ctb-art70-p1"]
    assert rr.chamadas == 2
