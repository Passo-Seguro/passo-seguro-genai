# Critério de julgamento do placar

Este arquivo é a regra **escrita antes** de rodar o placar. Ela vale igual para as três
configurações: A (modelo sem contexto), B (RAG simples) e C (RAG + LoRA).

## Conjunto

`avaliacao/teste.jsonl` tem 60 perguntas: 40 respondíveis e 20 "não consta".

- `split = dev` (15 perguntas: 10 respondíveis e 5 não consta). Usado para ajustar o limiar
  de similaridade, o prompt e o tamanho dos trechos.
- `split = teste` (45 perguntas: 30 respondíveis e 15 não consta). Usado **só** no placar
  (`avaliacao/avaliar.py`). Nenhuma dessas perguntas, nem paráfrase delas, entra no treino do
  LoRA: o `scripts/05_gerar_exemplos.py` descarta exemplos com similaridade de 0,90 ou mais.
- `registro = formal | informal`. Serve para medir se o modelo erra mais com linguagem
  informal, que é justamente a de quem menos escreve no padrão formal.

As perguntas foram escritas como o pedestre fala, antes de ler a base em detalhe. O gabarito
(`resposta_esperada` e `trecho_id`) foi conferido depois, contra os trechos.

## Métricas

| Métrica | Sobre | Definição |
|---|---|---|
| **Exatidão** | respondíveis | Não recusou **e** a resposta contém todos os grupos de `criterio` (basta um termo de cada grupo; sem acento e sem maiúsculas). Ex.: para "qual o prazo?", o critério `[["60", "sessenta"]]` exige que a resposta diga 60 dias. |
| **Citação correta** | respondíveis, B e C | Citou o trecho do gabarito. `trecho_id` é um prefixo: `ctb-art181` casa com `ctb-art181-p2`; `a\|b` aceita qualquer um dos dois. |
| **Taxa de alucinação** | todas | Respondeu (não recusou) **e**: a pergunta é "não consta"; **ou** não citou nenhum trecho recuperado; **ou** citou trecho que não estava entre os recuperados; **ou** a resposta está errada pelo critério. Na A não há trechos, então toda resposta da A é "sem fonte válida". |
| **Recusa correta** | não consta | Recusou (`recusou: true`). |
| **Recusa indevida** | respondíveis | Recusou uma pergunta que a base responde. É o custo de ser cauteloso. |
| **JSON válido** | todas | A saída passou no Pydantic (`resposta`, `fontes`, `confianca`, `recusou`) na 1ª ou na 2ª tentativa. |
| **Latência média** | todas | Segundos por resposta, incluindo a busca, na mesma máquina para as três configurações. |

## Revisão manual

O critério automático pode errar nos dois sentidos: a resposta certa dita com outras palavras,
ou a palavra-chave aparecendo numa frase errada. `avaliacao/saidas/<config>.jsonl` traz todas
as saídas, e `avaliacao/revisao_manual.csv` tem a coluna `correta_manual`. Se você preencher
(1 ou 0), o placar usa o seu julgamento no lugar do automático e avisa quantas linhas foram
corrigidas à mão.
