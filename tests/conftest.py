import json
import zlib
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ))

from passo_genai.avaliacao import normalizar  # noqa: E402
from passo_genai.busca import Buscador  # noqa: E402
from passo_genai.config import Config  # noqa: E402
from passo_genai.esquemas import Trecho  # noqa: E402

HTML_LEI = """<html><head><meta charset="utf-8"><title>Lei</title></head><body>
<p>LEI Nº 1.234, DE 1º DE JANEIRO DE 2020</p>
<p>O PREFEITO faz saber que a Câmara aprovou e ele promulga a seguinte lei:</p>
<p>Art. 1º Esta lei trata das calçadas.</p>
<p>Art. 7º Os responsáveis por imóveis lindeiros a vias com guias e sarjetas são obrigados a executar, manter e conservar os passeios na extensão da testada.</p>
<p>§ 1º Excetuam-se as rotas estratégicas.</p>
<p><strike>Art. 11. O prazo é de 30 (trinta) dias.</strike></p>
<p>Art. 11. O prazo para regularização é de 60 (sessenta) dias, improrrogáveis.</p>
<p>Art. 10-A. Antes das penalidades será expedida Notificação Orientativa.</p>
<p>ANEXO ÚNICO</p>
<p>Passeio em mau estado: R$ 300,00 por metro linear.</p>
</body></html>"""


class EmbeddingsFalsas:
    """Bag-of-words com hashing: determinístico, sem baixar modelo."""

    nome = "falso"

    def _vet(self, texto):
        v = np.zeros(256, dtype=np.float32)
        for p in normalizar(texto).replace(".", " ").replace(",", " ").split():
            if len(p) > 3:
                v[zlib.crc32(p.encode()) % 256] += 1
        n = np.linalg.norm(v)
        return v / n if n else v

    def documentos(self, textos):
        return np.stack([self._vet(t) for t in textos])

    def consultas(self, textos):
        return np.stack([self._vet(t) for t in textos])


def trecho(tid, texto, fonte="ctb", artigo="Art. 181"):
    return Trecho(trecho_id=tid, fonte=fonte, titulo="Código de Trânsito Brasileiro", url="https://exemplo.gov.br/ctb",
                  artigo=artigo, licenca="domínio público", data_acesso="2026-11-08", texto=texto)


@pytest.fixture
def buscador():
    ts = [
        trecho("ctb-art181-p1", "Estacionar o veículo no passeio ou sobre faixa destinada a pedestre: infração grave, multa, remoção do veículo"),
        trecho("ctb-art70-p1", "Os pedestres que estiverem atravessando a via sobre as faixas terão prioridade de passagem", artigo="Art. 70"),
        trecho("sp-lei15442-art11-p1", "O prazo para regularização da calçada é de 60 dias improrrogáveis", fonte="sp-lei15442", artigo="Art. 11"),
    ]
    emb = EmbeddingsFalsas()
    return Buscador(ts, emb.documentos([t.texto for t in ts]), emb)


class LLMFalso:
    """Devolve, em ordem, as respostas programadas (str) e registra as chamadas."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def chat(self, modelo, mensagens, temperatura, max_tokens, schema=None):
        self.chamadas.append({"modelo": modelo, "mensagens": mensagens})
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)


@pytest.fixture
def config():
    c = Config()
    c.limiar = 0.05  # embeddings falsos dão scores baixos; o teste de recusa por limiar usa 0.99
    c.top_k = 2
    return c
