from passo_genai.base import dividir_artigos, html_para_linhas, janelas
from tests.conftest import HTML_LEI


def test_divide_por_artigo_e_tira_texto_revogado():
    arts = dict(dividir_artigos(html_para_linhas(HTML_LEI)))
    assert set(arts) == {"1", "7", "11", "10-A", "anexo"}
    assert "60 (sessenta) dias" in arts["11"]
    assert "30 (trinta)" not in arts["11"]  # <strike> é redação revogada
    assert "§ 1º" in arts["7"]  # parágrafos ficam no artigo
    assert "300,00" in arts["anexo"]
    assert all("PREFEITO" not in t for t in arts.values())  # preâmbulo descartado


def test_anexo_em_tabela_nao_e_cortado_pelas_celulas_art():
    html = ("<p>Art. 1º Texto.</p><p>ANEXO ÚNICO</p><table><tr><td>a) falta de limpeza</td><td>Art. 1º</td>"
            "<td>R$ 4,00 por metro quadrado</td></tr><tr><td>c) passeio em mau estado</td><td>Art. 7º</td>"
            "<td>R$ 300,00 por metro linear</td></tr></table><p>Este texto não substitui o original</p>")
    arts = dict(dividir_artigos(html_para_linhas(html)))
    assert "R$ 4,00" in arts["anexo"] and "R$ 300,00" in arts["anexo"]
    assert "Este texto" not in arts["anexo"]
    assert arts["1"] == "Art. 1º Texto."


def test_janelas_com_sobreposicao():
    linhas = [f"inciso {i} " + "palavra " * 40 for i in range(40)]
    partes = janelas("\n".join(linhas), max_tokens=200, sobreposicao=50)
    assert len(partes) > 1
    # a última linha de uma janela reaparece no início da próxima
    assert partes[0].split("\n")[-1] in partes[1]
