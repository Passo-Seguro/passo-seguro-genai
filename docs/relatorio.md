# Relatório — Assistente do pedestre (Generative AI for Engineering)

**Repositório:** https://github.com/Passo-Seguro/passo-seguro-genai ·
**API no ar:** https://assistente-production-307b.up.railway.app ([como usar](../README.md#61-api-no-ar-railway)) ·
**Vídeo:** [link do vídeo]

## 01. Integrantes

Guilherme Morais (RM 551981) · Júlia Marques (RM 98680) · Matheus Gusmão (RM 550826)

## 02. Ficha Técnica: o que a IA resolve

**Tarefa:** responder dúvidas de pedestres de São Paulo sobre calçadas, travessias e como
reclamar, citando a fonte, em JSON.

**Problema.** As solicitações de calçada no SP156 cresceram mais de 200% entre 2020 e 2025 e
chegaram a 49.215 (levantamento apresentado na Câmara Municipal de São Paulo, agosto de 2026).
Mesmo assim, o pedestre não sabe se o conserto é do dono do imóvel, da Prefeitura ou de uma
concessionária, nem qual serviço do 156 pedir. As respostas existem, mas estão espalhadas entre
o CTB, leis e decretos municipais e páginas da Prefeitura.

**Para quem:** idosos, pessoas com deficiência ou mobilidade reduzida, quem empurra carrinho de
bebê: quem mais sofre com a calçada ruim. **Restrição da disciplina:** mobilidade e segurança.

**Solução:** um LLM local pequeno (Qwen2.5-1.5B-Instruct, Apache 2.0) com RAG sobre 82 trechos de
fontes oficiais e especializado com LoRA. Ele responde em linguagem simples, **sempre cita a lei
ou a página de onde tirou a resposta** e **recusa** quando a base não sustenta a resposta,
indicando o SP156. O app (PWA) chama o assistente pela API principal, em `POST /assistente`.

## 03. Pipeline

```mermaid
flowchart LR
    P[Pergunta do pedestre] --> E[Embeddings e5<br/>query]
    E --> F[(FAISS<br/>84 trechos oficiais)]
    F --> RR[Reranker cross-encoder<br/>10 candidatos → top-3]
    RR --> T{score >= 0,17<br/>OU pergunta do tema?}
    T -- não --> R1[Recusa padrão<br/>+ link SP156]
    T -- sim --> L[Qwen2.5-1.5B + LoRA<br/>Ollama, JSON forçado]
    L --> V{JSON válido?<br/>Pydantic}
    V -- não, 2x --> R1
    V -- sim --> C{fontes citadas estão<br/>entre os recuperados?}
    C -- não --> R1
    C -- sim --> S[resposta, fontes,<br/>confianca, recusou]
```

A pergunta vira um vetor (`intfloat/multilingual-e5-base`), e o FAISS traz os 10 trechos mais
parecidos. O reranker `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` relê cada par pergunta–trecho
e fica com os 3 melhores. Se o melhor tiver score abaixo do limiar **e** a pergunta for fora do
assunto (checagem de tema por termos como calçada, pedestre, faixa, 156, buraco), o serviço
**recusa sem chamar o LLM**. Pergunta do tema sempre chega ao modelo, mesmo com score baixo: na
versão 1, o limiar recusava perguntas informais do próprio tema (seção 05). Senão, o modelo responde só com base nos trechos, com a saída presa a um schema JSON. O
Pydantic valida o JSON (uma nova tentativa e, se falhar de novo, recusa), e a checagem de citação
descarta fontes que não estavam entre os trechos recuperados; sem nenhuma fonte válida, a
resposta vira recusa. O contrato final é `{resposta, fontes: [{titulo, url}], confianca, recusou}`.

## 04. Base de conhecimento

| Fonte | Formato | Licença | Trechos | Acesso |
|---|---|---|---|---|
| [Código de Trânsito Brasileiro (Lei nº 9.503/1997)](https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm) | HTML | ato oficial, domínio público (Lei 9.610/98, art. 8º, IV) | 18 | 08/11/2026 |
| [Lei Brasileira de Inclusão (Lei nº 13.146/2015)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm) | HTML | ato oficial, domínio público | 11 | 08/11/2026 |
| [Lei municipal nº 15.442/2011 (limpeza de imóveis e passeios), com alterações](http://legislacao.prefeitura.sp.gov.br/leis/lei-15442-de-09-de-setembro-de-2011) | HTML | ato oficial, domínio público | 11 | 08/11/2026 |
| [Decreto municipal nº 59.671/2020 (padronização das calçadas)](http://legislacao.prefeitura.sp.gov.br/leis/decreto-59671-de-7-de-agosto-de-2020) | HTML | ato oficial, domínio público | 16 | 08/11/2026 |
| [Subprefeituras — Calçadas: o direito de ir e vir…](https://prefeitura.sp.gov.br/subprefeituras/w/noticias/36935) | HTML | publicação oficial da Prefeitura; fonte citada | 4 | 08/11/2026 |
| [Subprefeituras — Serviços do Portal 156](https://prefeitura.sp.gov.br/web/subprefeituras/w/pracas_de_atendimento/335674) | HTML | publicação oficial da Prefeitura; fonte citada | 3 | 08/11/2026 |
| [SP156 — Calçada particular: denunciar calçada danificada ou inexistente](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=906) | HTML | publicação oficial da Prefeitura; fonte citada | 2 | 08/11/2026 |
| [SP156 — Calçada pública: solicitar manutenção](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=931) | HTML | publicação oficial da Prefeitura; fonte citada | 2 | 08/11/2026 |
| [SP156 — Acessibilidade: solicitar avaliação de obstáculo na calçada](https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?servico=2634) | HTML | publicação oficial da Prefeitura; fonte citada | 1 | 08/11/2026 |
| [Cartilha de Calçadas 2023 (SMPED/CPA)](https://www.prefeitura.sp.gov.br/cidade/secretarias/upload/pessoa_com_deficiencia/2023_08_11%20-%20Livreto%20Cartilha%20de%20Cal%C3%A7adas%202023%20-%20Vrs%20NOVA%20NORMA%20-%20V9.pdf) | PDF | publicação oficial da Prefeitura; fonte citada | 16 | 08/11/2026 |
| **Total** | | | **84** | |

Fatiamento: leis por artigo e páginas por seção, com 300 a 500 tokens e sobreposição de 50.
Removemos a redação revogada (texto riscado no Planalto). A NBR 9050 ficou de fora por direitos
autorais.

O fatiamento tinha um bug, achado na análise de erros (seção 06): o **Anexo Único da Lei
15.442**, que tem os valores das multas, entrava só com o cabeçalho da tabela. A célula "Art. 1º"
da coluna "Dispositivos violados" era lida como início de um artigo novo, e as linhas com
R$ 4,00/m², R$ 200 e R$ 300 por metro linear se perdiam. Corrigimos em `dividir_artigos`, com
teste automatizado.

Na versão 2 (09/11), a base ganhou a **carta de serviços do SP156** (calçada particular, calçada
pública e obstáculo): o que é cada serviço, quando pedir, o prazo (60 e 120 dias), os canais e as
etapas. Sem elas, a base sabia de quem é a obrigação, mas não **como pedir** o conserto. As
páginas das Subprefeituras também perderam o menu do portal e o aviso de cookies, que tinham
entrado nos trechos.

**Busca:** recall@1 = **0,475** e recall@3 = **0,775** nas 40 respondíveis, com o reranker. Só com
o e5, o recall@3 era 0,60: em 8 dos 16 erros, uma página genérica da Subprefeitura ocupava o
top-3, e o trecho certo vinha logo abaixo (recall@10 = 0,875). Por isso adicionamos o reranker,
em vez de mexer de novo nos trechos. Na base v2, o recall@3 continua 0,775 e o recall@1 cai para
0,425, porque as páginas do SP156 às vezes ocupam o 1º lugar.

| Busca | recall@1 (40) | recall@3 (40) | s/pergunta em CPU |
|---|---|---|---|
| só e5 | 0,30 | 0,60 | 0,01 |
| e5 + `mmarco-mMiniLMv2` (**adotado**) | 0,475 | **0,775** | ~1,1 |
| e5 + `bge-reranker-v2-m3` | 0,625 | 0,80 | ~11,5 |

O `bge-reranker-v2-m3` chega a 0,80, mas leva 11,5 s por pergunta em CPU e estoura o prazo de
12 s da API. O `mmarco` empata com ele no critério do dev e cabe no prazo. Ficamos 0,025 abaixo
da meta de 0,8 e **não** alteramos o gabarito para fechá-la.

**Limiar:** **0,17** (score do reranker, entre 0 e 1).

![curva do limiar](prints/06_curva_limiar_reranker.png)

O limiar foi escolhido **só no dev** (15 perguntas), maximizando o equilíbrio entre acertar as
respondíveis e recusar as "não consta": em 0,17, 60% das respondíveis passam do limiar com o trecho certo no top-3, e 100% das
"não consta" são recusadas (equilíbrio 0,8). Com o e5 sozinho, o limiar era um cosseno de 0,86:
no e5, os scores do dev ficam espremidos entre 0,76 e 0,93, então a varredura começava acima de
0,8 e separava mal as perguntas (só 20% de acerto nas respondíveis, equilíbrio 0,6). O reranker
espalha os scores de 0 a 1, e a escolha fica mais estável. Com a checagem de tema, o limiar só
filtra perguntas fora do assunto; por isso ficou 0,17 na versão 2.

## 05. Performance das três configurações

Placar das **45 perguntas de teste** (30 respondíveis, 15 "não consta"), nunca usadas para ajustar
nada, executado pelo notebook `05_placar.ipynb` na mesma máquina para as três configurações.

| Configuração | Exatidão | Citação correta | Alucinação | Recusa correta (não consta) | Recusa indevida | JSON válido | Latência média (s) |
|---|---|---|---|---|---|---|---|
| A — modelo sem contexto | 23% | 0% | 100% | 0% | 0% | 100% | 0,38 |
| B — RAG simples | 50% | **73%** | 56% | 47% | **0%** | 98% | 0,50 |
| **C — RAG + LoRA v2** | **50%** | 47% | **33%** | **80%** | 10% | **100%** | **0,36** |

Versão 2 (09/11): base com o SP156, checagem de tema e LoRA v2. Na versão 1 (08/11), B teve 43%
de exatidão e 23% de recusa indevida, e C (LoRA v1) teve 40% e 23%. Latência medida na RTX 4080;
na API publicada no Railway, em CPU (8 vCPUs), as respostas levam de 1 a 11 s.

Critério de julgamento ([`avaliacao/criterio.md`](../avaliacao/criterio.md), escrito **antes** de
rodar o placar): uma resposta é **exata** quando não recusa e contém todos os grupos de termos do
gabarito (por exemplo, "60" ou "sessenta" para o prazo da intimação), sem acento e sem
maiúsculas. Há **alucinação** quando o modelo responde a uma "não consta", não cita nenhum trecho
recuperado, cita um trecho que não foi recuperado ou dá uma resposta errada pelo critério. Nenhum
julgamento foi corrigido à mão.

Interpretação:

- **A → B (efeito do RAG):** a exatidão vai de 23% para 50%, e a alucinação cai de 100% para
  56%. Sem contexto, o modelo nunca cita uma fonte válida e inventa com segurança. O RAG é o que
  torna a resposta verificável.
- **B → C (efeito do LoRA):** mesma exatidão (50%), mas C alucina bem menos (56% → 33%), recusa
  80% do que não está na base (B, 47%) e devolve JSON válido em 100% dos casos. Com a checagem de
  tema, B responde quase tudo e inventa quando a busca acha pouco ("pode processar a Prefeitura",
  "a pena por atropelamento é multa"); C recusa esses casos. B variou de 50% a 63% de exatidão
  entre rodadas. O LoRA ensinou **formato, citação e recusa**, mas não acrescentou conhecimento.
  **Escolhemos C** por ser a configuração mais segura.
- **Custo:** C ainda recusa 10% das respondíveis com o trecho certo no contexto. A latência não
  pesa: na GPU, as três ficam abaixo de 0,4 s por resposta.
- **IA responsável — linguagem informal.** Na versão 1, o modelo errava muito mais com quem escreve
  fora do padrão formal: C acertava 22% das informais e recusava 33% delas, porque o reranker dava
  notas baixas a "tá", "pra" e "a gente" e o limiar recusava antes de chamar o modelo. A checagem de
  tema e o LoRA v2 corrigiram isso:

  | | Exatidão formal | Exatidão informal | Recusa indevida formal | Recusa indevida informal |
  |---|---|---|---|---|
  | B (v2) | 67% | 39% | 0% | 0% |
  | C v1 | 67% | 22% | 8% | 33% |
  | **C v2** | 50% | **50%** | 25% | **0%** |

  O custo apareceu do outro lado: C v2 recusa 25% das formais com resposta na base.

**Perguntas no estilo do app.** O placar não tinha as perguntas de "como fazer" que o app recebe
("como peço o conserto de um buraco?", "quanto custa denunciar?"); elas falharam no teste real e
viraram um conjunto de 16 perguntas ([`perguntas_app.jsonl`](../avaliacao/perguntas_app.jsonl)),
fora do placar oficial porque foram escritas depois de ver a base. C v2 acerta 62% pelo critério
(lendo as respostas, 6 das 13 respondíveis saem certas e úteis), alucina 12% e recusa as 3 fora
do tema; ainda recusa "como reclamar de carro na calçada", "quanto custa denunciar" e "calçada de
prédio público". Com os mesmos trechos, o `qwen2.5:7b-instruct` acerta 92%, mas leva 35 s por
resposta em CPU, contra 7,9 s do 1,5B: o limite que sobra é o tamanho do modelo.

Treino do LoRA (v2): **346 exemplos** (25% recusas: 258 respostas, 26 fora de escopo, 62 sem
base), divididos em 312 de treino e 34 de validação. Foram **3 épocas**, rank 16, alpha 32 e lr
2e-4, com perda de validação de 0,277 → 0,254 → **0,250** (sem sobreajuste), em **10,6 min na
RTX 4080** ([`treino/treino_lora.json`](../treino/treino_lora.json)). Os exemplos foram gerados por
um modelo professor (`qwen2.5:7b-instruct`) a partir dos trechos, e um filtro descartou os
parecidos demais com as perguntas de teste. A revisão exemplo a exemplo foi feita pelo **Claude
(assistente de IA)**, a pedido da equipe, e está registrada com o motivo de cada decisão em
[`treino/revisao_ia.json`](../treino/revisao_ia.json). Da v1 para a v2, saíram 3 recusas com
rótulo errado (o contexto respondia a pergunta) e 8 respostas que vinham de ruído do portal, e
entraram 33 exemplos de "como pedir" gerados das páginas do SP156. Para rodar no Ollama, o modelo
mesclado foi convertido para GGUF Q4_K_M com o llama.cpp, a mesma quantização do modelo base, para
a comparação ser justa.

## 06. Os cinco erros

Erros reais da configuração B no placar oficial da versão 1, escolhidos para cobrir etapas diferentes. Os
detalhes, com os trechos recuperados e os scores, estão em
[`avaliacao/resultados/cinco_erros.md`](../avaliacao/resultados/cinco_erros.md).

| # | Pergunta | Saída | Causa | Correção |
|---|---|---|---|---|
| 1 | "moto andando na calçada pra fugir do trânsito, é proibido?" | "Sim, transitando com o veículo em calçadas…", sem `fontes` | a busca trouxe o art. 193, mas o modelo base não preencheu a fonte, e o produto transformou a resposta em recusa | é o que o LoRA treina: **em C, a resposta saiu correta**, citando só o art. 193 |
| 2 | "se o dono não arrumar a calçada ele leva multa? de quanto?" | "A multa é de R$ 10,00 por metro quadrado" (**inventado**; o certo é R$ 300 por metro linear) | bug no fatiamento do Anexo Único, corrigido; mesmo assim, a busca não leva "de quanto?" até a tabela | reescrever cada linha do anexo como frase completa; recusar resposta com número que não aparece nos trechos citados |
| 3 | "e se o dono nunca arrumar, a prefeitura faz a obra?" | recusa pelo limiar | o art. 17 veio, mas o reranker deu nota baixa à pergunta coloquial (0,03 < 0,17) | calibrar o limiar com mais perguntas informais; recusar só se o reranker **e** o e5 estiverem baixos |
| 4 | "Quantos dias a Prefeitura leva para consertar uma calçada pública?" (não consta) | "A Prefeitura tem prazo de 30 dias…" | juntou dois trechos parecidos (o prazo do dono do imóvel e a concessionária) numa regra que não existe; como cita trechos recuperados, a checagem não pega | recusas "sem base" no LoRA; perguntas "não consta" parecidas com artigos reais no dev |
| 5 | "a empresa de água quebrou a calçada pra mexer no cano e deixou assim, quem conserta?" | recusa pelo limiar | nada liga "empresa de água" e "cano" a "concessionária" e "intervenção"; o trecho certo nem chegou ao top-3 | glossário de expansão de consulta e um trecho de perguntas frequentes com linguagem popular |

**E a configuração C?** O LoRA v1 resolveu o erro 1 e parou de inventar o valor da multa no
erro 2; os erros 3 e 5 continuavam, porque o limiar agia antes do modelo. Na versão 2, com a
checagem de tema e o LoRA v2: o erro 1 continua correto; o **erro 3 foi resolvido** (a pergunta
chega ao modelo, que responde com o art. 1 do Decreto); o erro 5 chega ao modelo, mas a resposta
("a Subprefeitura é responsável pela manutenção das calçadas públicas") ainda está errada, porque
o trecho das concessionárias não vem no top-3; no erro 2, C não inventa valor, mas também não diz
"de quanto". O erro 4 mudou de natureza: a base nova traz o prazo máximo de 120 dias do serviço de
calçada pública, e C responde isso, mas o gabarito continua "não consta".

## 07. Conclusão técnica e links

**O que funciona.** O assistente responde com a fonte oficial e o link, e recusa o que não está
na base: na configuração C, 80% das perguntas "não consta" foram recusadas, e o JSON sai válido
em 100% dos casos. Responde as perguntas de "como pedir" com a carta de serviços do SP156
(canais, prazo, o que informar) e trata igual quem escreve de modo formal ou informal. Ele está publicado no Railway, cumpre o contrato da API (11 de 11 checagens
de ponta a ponta, com 401, 422 e 400 no formato combinado) e responde dentro do prazo de 15 s da
API principal, porque desiste do LLM aos 12 s e devolve a recusa com o SP156. A privacidade foi
tratada no código: o log nunca guarda o texto da pergunta, e há um teste para isso.

**Limites.**

- A exatidão é de 50%: com 84 trechos e um modelo de 1,5B, de cada dez perguntas, cinco saem
  certas, uma é recusada com a resposta na base e o resto sai errado ou incompleto. As respostas
  são curtas e às vezes não dizem o essencial ("quem eu chamo?").
- A alucinação de 33% ainda é alta para um tema legal. O caso mais perigoso é o número plausível e
  errado (erro 2), por isso o app sempre mostra a fonte, para o pedestre conferir.
- O tamanho do modelo é o limite principal: o 7B acerta 92% das perguntas do app com os mesmos
  trechos, mas não cabe no prazo de 15 s em CPU.
- O CTB não traz o valor das multas em reais, só a gravidade, e a base não responde "de quanto".
  Também falta a página do serviço do 156 para veículo estacionado na calçada.
- As páginas do SP156 e das Subprefeituras mudam de endereço: a base precisa ser baixada de novo
  periodicamente (`scripts/01_baixar_base.py`).
- A revisão dos exemplos do LoRA foi feita por IA e precisa ser conferida por uma pessoa.

**Próximos passos.**

1. Servidor com GPU para usar o `qwen2.5:7b-instruct` (ou treinar o LoRA nele): é o maior ganho
   de qualidade medido.
2. Página do serviço do 156 para veículo sobre a calçada e um glossário de linguagem popular
   ("empresa de água" → concessionária), contra os erros 5 e de "como reclamar de carro".
3. Reescrever o anexo de multas como frases e recusar números que não estão nos trechos (erro 2).
4. Mais exemplos de resposta completa no LoRA, para reduzir as recusas de perguntas formais.
5. Rodar o `bge-reranker-v2-m3` (recall@3 de 0,80) quando houver GPU no servidor.

**Links**

- Repositório: https://github.com/Passo-Seguro/passo-seguro-genai
- API no ar: https://assistente-production-307b.up.railway.app (Swagger em `/docs`)
- Modelo (GGUF Q4_K_M): [release `modelo-v2`](https://github.com/Passo-Seguro/passo-seguro-genai/releases/tag/modelo-v2)
- Vídeo: [link do vídeo]
- Documentação completa, testes e registro da execução: [README](../README.md)
