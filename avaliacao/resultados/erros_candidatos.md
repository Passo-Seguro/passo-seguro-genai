# Erros candidatos — configuração C

20 erros em 45 perguntas: {'busca_nao_achou': 5, 'recusa_por_limiar': 4, 'trecho_mal_cortado': 8, 'modelo_recusou_com_base': 1, 'modelo_inventou': 2}

## r06 — busca_nao_achou
- **Pergunta:** se o dono não arrumar a calçada ele leva multa? de quanto?
- **Esperado:** Sim. A multa é de R$ 300,00 por metro linear da testada (ou do trecho danificado), corrigida anualmente pelo IPCA. (`sp-lei15442-anexo|sp-lei15442-art15`)
- **Saída:** Sim. A multa é aplicável à pessoa que tem responsabilidade pela calçada, seja ela proprietária ou responsável pelo imóvel.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p2'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p4', 0.3912], ['sp-subpref-calcadas-s01-p2', 0.1181], ['sp-dec59671-art1-p1', 0.0232]]

## r12 — busca_nao_achou
- **Pergunta:** a raiz da árvore levantou a calçada, o dono é obrigado a consertar?
- **Esperado:** O responsável fica temporariamente dispensado da manutenção enquanto a árvore que causou o dano não for removida. (`sp-dec59671-art32`)
- **Saída:** Não encontrei isso nas fontes oficiais que eu consulto. Para falar com a Prefeitura, ligue 156 ou acesse o SP156: https://sp156.prefeitura.sp.gov.br/ — e você pode registrar o problema aqui no Passo Seguro.
- **Fontes citadas:** [] · recusou=True · nível=busca
- **Recuperados:** [['sp-dec59671-art34-p1', 0.0305], ['sp-subpref-calcadas-s01-p4', 0.0228], ['sp-dec59671-art1-p1', 0.0175]]

## r21 — busca_nao_achou
- **Pergunta:** de quem é a responsabilidade pela segurança do pedestre no trânsito?
- **Esperado:** Os veículos maiores respondem pelos menores, os motorizados pelos não motorizados e, juntos, pela segurança dos pedestres. (`ctb-art29`)
- **Saída:** É assegurada ao pedestre a utilização dos passeios ou passagens apropriadas das vias urbanas e dos acostamentos das vias rurais para circulação, podendo a autoridade competente permitir a utilização de parte da calçada para outros fins, desde que não seja prejudicial ao fluxo de pedestres.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p2'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p2', 0.6335], ['ctb-art68-p1', 0.5251], ['sp-subpref-calcadas-s01-p1', 0.2066]]

## r26 — busca_nao_achou
- **Pergunta:** E se a calçada danificada for de uma praça ou prédio público?
- **Esperado:** O serviço 'Calçada pública - solicitar manutenção', pelo 156. (`sp-subpref-servicos156`)
- **Saída:** A calçada da praça ou prédio público é responsabilidade do responsável pelo imóvel, seja ele proprietário ou usuário.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p4'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p2', 0.5587], ['sp-subpref-calcadas-s01-p4', 0.3234], ['sp-dec59671-art1-p1', 0.1666]]

## r34 — busca_nao_achou
- **Pergunta:** a rampa da garagem do vizinho deixou a calçada torta, pode isso?
- **Esperado:** Não. O rebaixamento para acesso de veículos não pode obstruir a faixa livre nem alterar a sua inclinação transversal. (`sp-dec59671-art10`)
- **Saída:** Não encontrei isso nas fontes oficiais que eu consulto. Para falar com a Prefeitura, ligue 156 ou acesse o SP156: https://sp156.prefeitura.sp.gov.br/ — e você pode registrar o problema aqui no Passo Seguro.
- **Fontes citadas:** [] · recusou=True · nível=busca
- **Recuperados:** [['sp-cartilha-calcadas-s04-p1', 0.0185], ['sp-cartilha-calcadas-s05-p1', 0.0136], ['sp-dec59671-art1-p1', 0.0047]]

## n03 — modelo_inventou
- **Pergunta:** Quantos dias a Prefeitura leva para consertar uma calçada pública?
- **Esperado:** Recusa: a base não traz essa informação. (`None`)
- **Saída:** A Prefeitura tem 30 dias para regularizar as calçadas que foram feitas pela empresa concessionária.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p4'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p4', 0.5959], ['sp-dec59671-art32-p1', 0.5485], ['sp-subpref-calcadas-s01-p2', 0.1055]]

## n18 — modelo_inventou
- **Pergunta:** se eu mesmo consertar a calçada da praça a prefeitura me reembolsa?
- **Esperado:** Recusa: a base não traz essa informação. (`None`)
- **Saída:** Sim, o cidadão é responsável pela manutenção após reforma. A Prefeitura executa as reformas e paga, mas depois fica sob responsabilidade do cidadão.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p4'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p2', 0.2595], ['sp-subpref-calcadas-s01-p4', 0.2201], ['sp-cartilha-calcadas-s01-p1', 0.109]]

## r20 — modelo_recusou_com_base
- **Pergunta:** Quem fiscaliza e multa o estacionamento irregular na cidade?
- **Esperado:** Os órgãos executivos de trânsito do município, dentro da sua circunscrição. (`ctb-art24`)
- **Saída:** Não encontrei isso nas fontes oficiais que eu consulto. Para falar com a Prefeitura, ligue 156 ou acesse o SP156: https://sp156.prefeitura.sp.gov.br/ — e você pode registrar o problema aqui no Passo Seguro.
- **Fontes citadas:** [] · recusou=True · nível=modelo
- **Recuperados:** [['sp-subpref-servicos156-s01-p3', 0.3283], ['ctb-art24-p1', 0.2848], ['sp-lei15442-art12-p1', 0.2482]]

## r08 — recusa_por_limiar
- **Pergunta:** e se o dono nunca arrumar, a prefeitura faz a obra?
- **Esperado:** A Prefeitura pode executar a obra e cobrar o custo do responsável, além das multas. (`sp-lei15442-art17`)
- **Saída:** Não encontrei isso nas fontes oficiais que eu consulto. Para falar com a Prefeitura, ligue 156 ou acesse o SP156: https://sp156.prefeitura.sp.gov.br/ — e você pode registrar o problema aqui no Passo Seguro.
- **Fontes citadas:** [] · recusou=True · nível=busca
- **Recuperados:** [['sp-dec59671-art1-p1', 0.0645], ['sp-lei15442-art17-p1', 0.0278], ['sp-lei15442-art10-p1', 0.0212]]

## r11 — recusa_por_limiar
- **Pergunta:** a empresa de água quebrou a calçada pra mexer no cano e deixou assim, quem conserta?
- **Esperado:** Quem usa a via para instalar infraestrutura tem de reparar os danos que causou à calçada; a empresa pode ser multada se não recompor. (`sp-dec59671-art1|sp-subpref-calcadas|sp-dec59671-art16`)
- **Saída:** Não encontrei isso nas fontes oficiais que eu consulto. Para falar com a Prefeitura, ligue 156 ou acesse o SP156: https://sp156.prefeitura.sp.gov.br/ — e você pode registrar o problema aqui no Passo Seguro.
- **Fontes citadas:** [] · recusou=True · nível=busca
- **Recuperados:** [['sp-dec59671-art1-p1', 0.0034], ['sp-subpref-calcadas-s01-p2', 0.0032], ['sp-cartilha-calcadas-s01-p1', 0.0006]]

## r32 — recusa_por_limiar
- **Pergunta:** se eu arrumar dentro do prazo eu pago multa mesmo assim?
- **Esperado:** Não. Se os reparos forem feitos no prazo de 60 dias e comunicados à Subprefeitura, não há cobrança de multa. (`sp-subpref-calcadas|sp-lei15442-art14`)
- **Saída:** Não encontrei isso nas fontes oficiais que eu consulto. Para falar com a Prefeitura, ligue 156 ou acesse o SP156: https://sp156.prefeitura.sp.gov.br/ — e você pode registrar o problema aqui no Passo Seguro.
- **Fontes citadas:** [] · recusou=True · nível=busca
- **Recuperados:** [['sp-lei15442-art11-p1', 0.0238], ['sp-lei15442-art17-p1', 0.0159], ['sp-lei15442-art14-p1', 0.0131]]

## r38 — recusa_por_limiar
- **Pergunta:** o motorista veio pra cima de mim quando eu tava terminando de atravessar e o sinal abriu pra ele, ele tava errado?
- **Esperado:** Sim. Com semáforo, o pedestre que não concluiu a travessia tem preferência mesmo se o sinal mudar; não dar essa preferência é infração gravíssima. (`ctb-art70|ctb-art214`)
- **Saída:** Não encontrei isso nas fontes oficiais que eu consulto. Para falar com a Prefeitura, ligue 156 ou acesse o SP156: https://sp156.prefeitura.sp.gov.br/ — e você pode registrar o problema aqui no Passo Seguro.
- **Fontes citadas:** [] · recusou=True · nível=busca
- **Recuperados:** [['ctb-art29-p2', 0.0139], ['ctb-art29-p3', 0.0137], ['ctb-art214-p1', 0.004]]

## r15 — trecho_mal_cortado
- **Pergunta:** posso atravessar a rua fora da faixa?
- **Esperado:** O pedestre deve usar a faixa ou passagem se houver uma a até 50 metros; andar fora da faixa própria é proibido e é infração leve. (`ctb-art69|ctb-art254`)
- **Saída:** Sim. O Código de Trânsito proíbe o pedestre de andar fora da faixa própria, passarela, passagem aérea ou subterrânea.
- **Fontes citadas:** ['ctb-art254-p1'] · recusou=False · nível=None
- **Recuperados:** [['ctb-art254-p1', 0.3997], ['ctb-art70-p1', 0.3837], ['ctb-art69-p1', 0.3181]]

## r16 — trecho_mal_cortado
- **Pergunta:** O pedestre pode ser multado?
- **Esperado:** Sim. O CTB lista condutas proibidas ao pedestre; é infração leve, com multa de 50% do valor da infração leve. (`ctb-art254`)
- **Saída:** Sim. A multa é aplicável para infrações como permanecer nas pistas, cruzar viadutos sem permissão e desobedecer à sinalização.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p4'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p4', 0.566], ['ctb-art254-p1', 0.5072], ['sp-lei15442-art8-p1', 0.3644]]

## r19 — trecho_mal_cortado
- **Pergunta:** bike pode andar na calçada?
- **Esperado:** Só se for autorizado e sinalizado pelo órgão responsável pela via; andar de bicicleta onde não é permitido é infração média. (`ctb-art59|ctb-art255`)
- **Saída:** Sim. A bicicleta desmontada empurrando a bicicleta equipara-se ao pedestre em direitos e deveres.
- **Fontes citadas:** ['ctb-art68-p1'] · recusou=False · nível=None
- **Recuperados:** [['ctb-art68-p1', 0.7381], ['ctb-art59-p1', 0.346], ['ctb-art193-p1', 0.1348]]

## r27 — trecho_mal_cortado
- **Pergunta:** tem um trambolho bloqueando a calçada, qual serviço do 156?
- **Esperado:** O serviço 'Acessibilidade - solicitar avaliação de obstáculo na calçada'. (`sp-subpref-servicos156|sp156-obstaculo`)
- **Saída:** Aqui está o serviço para denunciar o trambolho bloqueando a calçada.
- **Fontes citadas:** ['sp-subpref-servicos156-s01-p2'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-servicos156-s01-p2', 0.6161], ['sp-subpref-servicos156-s01-p3', 0.4644], ['sp-subpref-servicos156-s01-p1', 0.3421]]

## r28 — trecho_mal_cortado
- **Pergunta:** largaram material de obra na calçada, como denuncio?
- **Esperado:** Pelo 156, no serviço 'Denunciar material de construção depositado em vias públicas'. (`sp-subpref-servicos156|sp156-entulho`)
- **Saída:** Denunciar janela ou abertura a menos de 1,50m do vizinho.
- **Fontes citadas:** ['sp-dec59671-art1-p1'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-servicos156-s01-p3', 0.3133], ['sp-dec59671-art16-p1', 0.0367], ['sp-dec59671-art1-p1', 0.0336]]

## r30 — trecho_mal_cortado
- **Pergunta:** a prefeitura reformou a calçada da minha rua, agora a manutenção é com ela?
- **Esperado:** Não. Depois da reforma nas rotas estratégicas, a manutenção continua com o responsável pelo imóvel, que pode ser multado. (`sp-subpref-calcadas|sp-dec59671-art35`)
- **Saída:** Sim. A Prefeitura reformou as calçadas das vias estruturais e das Rotas Estratégicas, que são os principais serviços oferecidos nas Subprefeituras da cidade.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p4'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p2', 0.9665], ['sp-subpref-calcadas-s01-p4', 0.8572], ['sp-subpref-calcadas-s01-p3', 0.6139]]

## r35 — trecho_mal_cortado
- **Pergunta:** a empresa remendou a calçada depois da obra, pode ficar remendo?
- **Esperado:** Não. Na recomposição, a faixa livre deve ser refeita em toda a seção transversal, sem remendos longitudinais. (`sp-dec59671-art16`)
- **Saída:** Sim. A empresa que fez as obras tem que fazer o anexo ou registro de responsabilidade técnica para ser punida pela legislação.
- **Fontes citadas:** ['sp-dec59671-art16-p1'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p4', 0.4868], ['sp-dec59671-art17-p1', 0.1564], ['sp-dec59671-art16-p1', 0.1153]]

## r39 — trecho_mal_cortado
- **Pergunta:** Qual a inclinação transversal máxima da faixa livre?
- **Esperado:** 3%, e ela deve ser constante. (`sp-dec59671-art4`)
- **Saída:** A largura total das calçadas é medida a partir do alinhamento do lote até o bordo externo da guia.
- **Fontes citadas:** ['sp-dec59671-art4-p3'] · recusou=False · nível=None
- **Recuperados:** [['sp-dec59671-art24-p1', 0.8556], ['sp-dec59671-art4-p3', 0.8354], ['sp-cartilha-calcadas-s05-p1', 0.8215]]
