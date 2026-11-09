from passo_genai.base import _sem_ruido, servico_sp156_para_texto
from passo_genai.tema import sobre_o_assistente, sobre_o_tema


def test_perguntas_do_tema_inclusive_informais():
    for p in ["Como peço o conserto de um buraco na calçada?", "carro parado em cima do passeio pode?",
              "tem um vaso enorme bloqueando, quem eu chamo no 156?", "bike pode andar na calcada?",
              "a faixa de pedestre tá apagada", "quem arruma a rampa de cadeira de rodas?"]:
        assert sobre_o_tema(p), p


def test_perguntas_fora_do_tema():
    for p in ["Qual a previsão do tempo para amanhã?", "qual a melhor ação para investir este mês?",
              "me indica uma receita de bolo", "quem ganhou o jogo ontem?"]:
        assert not sobre_o_tema(p), p


def test_perguntas_sobre_o_assistente():
    for p in ["Oque voce pode me informar que tem na sua base?", "o que você sabe?", "Como você pode ajudar?",
              "sobre o que vc responde?", "ajuda"]:
        assert sobre_o_assistente(p), p
    assert not sobre_o_assistente("Como peço o conserto de um buraco na calçada?")


def test_tira_menu_e_aviso_de_cookies_das_paginas():
    linhas = ["Acesso à Informação", "Notícias", "Calçadas",
              "As calçadas da cidade precisam estar adequadas aos padrões municipais definidos por legislação.",
              "Menu curto que vem depois do texto fica", "A Prefeitura de São Paulo valoriza sua privacidade!",
              "Em nosso site, utilizamos cookies para melhorar a experiência."]
    assert _sem_ruido(linhas) == linhas[3:5]


def test_extrai_a_carta_de_servicos_do_sp156():
    html = ("<html><h1>Calçada particular - denunciar</h1><nav>Início</nav><div>Compartilhe</div>"
            "<div>O QUE É</div><div>Fiscalização de calçadas com buracos.</div>"
            "<div>PRAZO MÁXIMO</div><div>60 dias.</div>"
            "<div>CANAIS PARA SOLICITAR</div><div>Telefônico</div><div>:</div><div>- Central Telefônica 156.</div>"
            "<div>MANIFESTAÇÃO SOBRE SERVIÇO</div><div>Ouvidoria</div><div>FAQ</div></html>")
    nome, texto = servico_sp156_para_texto(html)
    assert nome == "Calçada particular - denunciar"
    assert "O que é: Fiscalização de calçadas com buracos." in texto and "Prazo máximo: 60 dias." in texto
    assert "Telefônico: - Central Telefônica 156." in texto
    assert "Ouvidoria" not in texto and "Compartilhe" not in texto
