# Erros candidatos — configuração B

20 erros em 45 perguntas: {'trecho_mal_cortado': 8, 'busca_nao_achou': 5, 'recusa_por_limiar': 4, 'modelo_inventou': 3}

## r06 — busca_nao_achou
- **Pergunta:** se o dono não arrumar a calçada ele leva multa? de quanto?
- **Esperado:** Sim. A multa é de R$ 300,00 por metro linear da testada (ou do trecho danificado), corrigida anualmente pelo IPCA. (`sp-lei15442-anexo|sp-lei15442-art15`)
- **Saída:** Sim, o dono da calçada pode ser multado se não realizar a manutenção adequada. A multa é de R$ 10,00 por metro quadrado da calçada, desde que a largura seja inferior a 1,20m. Se houver reincidência, a multa pode aumentar para R$ 20,00 por metro quadrado.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p2', 'sp-dec59671-art1-p1'] · recusou=False · nível=None
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
- **Saída:** A responsabilidade pela segurança do pedestre no trânsito é da autoridade competente, conforme o Código de Trânsito Brasileiro (Lei nº 9.503/1997), Art. 68.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p1', 'ctb-art68-p1'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p2', 0.6335], ['ctb-art68-p1', 0.5251], ['sp-subpref-calcadas-s01-p1', 0.2066]]

## r26 — busca_nao_achou
- **Pergunta:** E se a calçada danificada for de uma praça ou prédio público?
- **Esperado:** O serviço 'Calçada pública - solicitar manutenção', pelo 156. (`sp-subpref-servicos156`)
- **Saída:** A calçada de uma praça ou prédio público também precisa ser reformada e manutida de acordo com as normas municipais. A Prefeitura deve executar as reformas e as multas devem ser pagas pelos responsáveis, como proprietários ou usuários. Se não for feita a manutenção adequada, pode ser multado.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p4', 'sp-dec59671-art1-p1'] · recusou=False · nível=None
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
- **Saída:** A Prefeitura tem prazo de 30 dias para regularizar a calçada pública após a reforma. Se o serviço não for feito dentro desse período, os responsáveis precisarão arcar com as multas, desde que comuniquem à Subprefeitura local sobre os devidos reparos ou que os servidores públicos identifiquem a reforma.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p2', 'sp-dec59671-art32-p1'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p4', 0.5959], ['sp-dec59671-art32-p1', 0.5485], ['sp-subpref-calcadas-s01-p2', 0.1055]]

## n08 — modelo_inventou
- **Pergunta:** Qual o horário de atendimento da Subprefeitura da Sé?
- **Esperado:** Recusa: a base não traz essa informação. (`None`)
- **Saída:** A Subprefeitura da Sé não tem um horário específico de atendimento. O atendimento é feito através do Portal 156, que pode ser acessado online. Para obter informações mais detalhadas sobre o atendimento, é recomendável consultar diretamente a Secretaria Municipal das Subprefeituras.
- **Fontes citadas:** ['sp-subpref-servicos156-s01-p1', 'sp-subpref-servicos156-s01-p2', 'sp-subpref-servicos156-s01-p3'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-servicos156-s01-p2', 0.2432], ['sp-subpref-servicos156-s01-p3', 0.1033], ['sp-subpref-servicos156-s01-p1', 0.023]]

## n18 — modelo_inventou
- **Pergunta:** se eu mesmo consertar a calçada da praça a prefeitura me reembolsa?
- **Esperado:** Recusa: a base não traz essa informação. (`None`)
- **Saída:** A Prefeitura de São Paulo é responsável por reformar as calçadas das vias estruturais e das Rotas Estratégicas e de Segurança, conforme determinado no Plano Diretor. No entanto, após a reforma, a manutenção dessas calçadas continua sob responsabilidade do cidadão. É importante manter a calçada em bom estado para garantir a segurança e a acessibilidade para todos os pedestres.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p4', 'sp-subpref-calcadas-s01-p2'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p2', 0.2595], ['sp-subpref-calcadas-s01-p4', 0.2201], ['sp-cartilha-calcadas-s01-p1', 0.109]]

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

## r03 — trecho_mal_cortado
- **Pergunta:** moto andando na calçada pra fugir do trânsito, é proibido?
- **Esperado:** Sim. Transitar com veículo em calçadas e passeios é infração gravíssima, com multa multiplicada por três. (`ctb-art193`)
- **Saída:** Sim, transitando com o veículo em calçadas, passeios, passarelas, ciclovias, ciclofaixas, ilhas, refúgios, ajardinamentos, canteiros centrais e divisores de pista de rolamento, é proibido ao pedestre, como demonstrado no trecho Art. 193 da Lei nº 9.503/1997.
- **Fontes citadas:** [] · recusou=False · nível=None
- **Recuperados:** [['ctb-art68-p1', 0.2918], ['ctb-art193-p1', 0.1391], ['ctb-art254-p1', 0.0971]]

## r15 — trecho_mal_cortado
- **Pergunta:** posso atravessar a rua fora da faixa?
- **Esperado:** O pedestre deve usar a faixa ou passagem se houver uma a até 50 metros; andar fora da faixa própria é proibido e é infração leve. (`ctb-art69|ctb-art254`)
- **Saída:** Não, não é permitido atravessar a rua fora da faixa. De acordo com o Código de Trânsito Brasileiro (Lei nº 9.503/1997), Art. 254, o pedestre deve permanecer na faixa própria, exceto para cruzar as pistas de rolamento, que deve ser feito em sentido perpendicular ao de seu eixo, observando as disposições deste Código.
- **Fontes citadas:** ['ctb-art254-p1', 'ctb-art70-p1', 'ctb-art69-p1'] · recusou=False · nível=None
- **Recuperados:** [['ctb-art254-p1', 0.3997], ['ctb-art70-p1', 0.3837], ['ctb-art69-p1', 0.3181]]

## r16 — trecho_mal_cortado
- **Pergunta:** O pedestre pode ser multado?
- **Esperado:** Sim. O CTB lista condutas proibidas ao pedestre; é infração leve, com multa de 50% do valor da infração leve. (`ctb-art254`)
- **Saída:** Sim, o pedestre pode ser multado. A Lei nº 15.442/2011 estendeu a obrigatoriedade da manutenção do passeio público ao responsável pelo imóvel, seja ele proprietário ou usuário. Se os serviços forem feitos dentro do prazo de 60 dias, os responsáveis não precisarão arcar com o valor das multas, desde que comuniquem à Subprefeitura local, responsável pela região, sobre os devidos reparos. Se não for cumprido o prazo, a empresa pode ter sua permissão de prestação de serviços suspensa.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p4', 'ctb-art254-p1', 'sp-lei15442-art8-p1'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p4', 0.566], ['ctb-art254-p1', 0.5072], ['sp-lei15442-art8-p1', 0.3644]]

## r27 — trecho_mal_cortado
- **Pergunta:** tem um trambolho bloqueando a calçada, qual serviço do 156?
- **Esperado:** O serviço 'Acessibilidade - solicitar avaliação de obstáculo na calçada'. (`sp-subpref-servicos156|sp156-obstaculo`)
- **Saída:** Denunciar calçada danificada ou inexistente
- **Fontes citadas:** ['sp-subpref-servicos156-s01-p1', 'sp-subpref-servicos156-s01-p2', 'sp-subpref-servicos156-s01-p3'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-servicos156-s01-p2', 0.6161], ['sp-subpref-servicos156-s01-p3', 0.4644], ['sp-subpref-servicos156-s01-p1', 0.3421]]

## r35 — trecho_mal_cortado
- **Pergunta:** a empresa remendou a calçada depois da obra, pode ficar remendo?
- **Esperado:** Não. Na recomposição, a faixa livre deve ser refeita em toda a seção transversal, sem remendos longitudinais. (`sp-dec59671-art16`)
- **Saída:** Sim, a empresa pode ficar remendando a calçada. A lei nº 15.442, de 2011, estendeu a obrigatoriedade pela manutenção do passeio ao responsável pelo imóvel, seja ele proprietário ou usuário. Por meio dela, tornou-se obrigatório deixar a largura de 1,20m livre para a circulação de pedestres, ficou estabelecido prazo de 30 dias para adequação da calçada, sob pena de nova multa e, ainda, foi redefinida a forma de aplicação de multas com base na metragem linear (antes havia valor fixo para a sanção, independentemente do tamanho da calçada). Portanto, mesmo que a empresa tenha remendado a calçada, é necessário que o responsável pelo imóvel faça as adequações necessárias para garantir a segurança e a acessibilidade dos pedestres.
- **Fontes citadas:** ['sp-subpref-calcadas-s01-p4', 'sp-dec59671-art16-p1', 'sp-dec59671-art17-p1'] · recusou=False · nível=None
- **Recuperados:** [['sp-subpref-calcadas-s01-p4', 0.4868], ['sp-dec59671-art17-p1', 0.1564], ['sp-dec59671-art16-p1', 0.1153]]

## r36 — trecho_mal_cortado
- **Pergunta:** Qual a altura livre mínima sobre a calçada para placas e toldos?
- **Esperado:** 2,10 m para instalações como placas e toldos; 3,00 m para interferências construtivas. (`sp-dec59671-art4`)
- **Saída:** A altura livre mínima sobre a calçada para placas e toldos deve ser de no mínimo 3,00 metros (três metros) do nível da calçada.
- **Fontes citadas:** ['sp-dec59671-art4-p1', 'sp-cartilha-calcadas-s05-p1'] · recusou=False · nível=None
- **Recuperados:** [['sp-dec59671-art4-p1', 0.9954], ['sp-cartilha-calcadas-s03-p1', 0.9537], ['sp-cartilha-calcadas-s05-p1', 0.8652]]

## r39 — trecho_mal_cortado
- **Pergunta:** Qual a inclinação transversal máxima da faixa livre?
- **Esperado:** 3%, e ela deve ser constante. (`sp-dec59671-art4`)
- **Saída:** A inclinação transversal máxima da faixa livre é de 2% (dois por cento). Essa norma é mencionada no trecho 24 do Decreto Municipal nº 59.671/2020, que trata das calçadas e situações atípicas. A referência é clara e direta, indicando que a faixa livre deve ter uma inclinação máxima de 2% para as situações atípicas descritas no trecho 1 e 2.
- **Fontes citadas:** [] · recusou=False · nível=None
- **Recuperados:** [['sp-dec59671-art24-p1', 0.8556], ['sp-dec59671-art4-p3', 0.8354], ['sp-cartilha-calcadas-s05-p1', 0.8215]]

## r40 — trecho_mal_cortado
- **Pergunta:** carro parado em cima da faixa de pedestre também dá multa?
- **Esperado:** Sim. Estacionar sobre faixa destinada a pedestre é infração grave, com multa e remoção do veículo. (`ctb-art181`)
- **Saída:** Sim, o Código de Trânsito Brasileiro (Lei nº 9.503/1997) estabelece multas para o estacionamento de veículos em áreas proibidas, incluindo as faixas de pedestres. Portanto, um carro estacionado em cima da faixa de pedestres também pode ser punido com multa.
- **Fontes citadas:** ['ctb-art181-p1', 'ctb-art181-p2'] · recusou=False · nível=None
- **Recuperados:** [['ctb-art214-p1', 0.3931], ['ctb-art181-p2', 0.178], ['ctb-art181-p1', 0.1469]]
