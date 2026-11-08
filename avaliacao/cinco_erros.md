# Cinco erros reais (Fase 7)

Os erros são da **configuração B** (RAG simples, `qwen2.5:1.5b-instruct`) no placar oficial das 45
perguntas de teste ([`saidas/B.jsonl`](saidas/B.jsonl)), escolhidos entre os 20 de
[`erros_candidatos.md`](erros_candidatos.md) para cobrir causas diferentes. A configuração C
(LoRA) ainda não entrou no placar: ver o [README](../README.md#95-lora), seção 9.5.

O score é o do reranker (`mmarco-mMiniLMv2`), entre 0 e 1. O limiar é 0,17.

## Erro 1 (r03): resposta incompleta citando trechos que não a sustentam

- **Pergunta:** moto andando na calçada pra fugir do trânsito, é proibido?
- **Recuperados:** `ctb-art68` (0,29), **`ctb-art193`** (0,14), `ctb-art254` (0,10)
- **Saída:** "Sim, é proibido transitar com moto em calçadas, passeios, passarelas, ciclovias […]",
  citando os **três** trechos recuperados.
- **Causa:** a busca acertou: o art. 193 estava no contexto. O modelo copiou a lista de lugares,
  mas deixou de fora o que o pedestre precisa saber (infração gravíssima, multa multiplicada por
  três). Também citou em bloco tudo o que recebeu, inclusive os arts. 68 e 254, que não tratam de
  veículo na calçada. Por isso o julgamento marca "não exata" e conta alucinação. A classificação
  automática ("trecho mal cortado") não descreve bem esse erro. Numa execução anterior, a mesma
  pergunta saiu com `fontes` vazio.
- **Correção:** é exatamente o que o LoRA treina: os 233 exemplos de resposta citam só o trecho
  de origem e trazem a penalidade quando ela existe. No prompt, dá para pedir "cite apenas os
  trechos que sustentam a resposta".

## Erro 2 (r06): a busca não achou o valor da multa, e o modelo inventou um

- **Pergunta:** se o dono não arrumar a calçada ele leva multa? de quanto?
- **Recuperados:** `sp-subpref-calcadas-s01-p4` (0,39), `sp-subpref-calcadas-s01-p2` (0,12), `sp-dec59671-art1` (0,02)
- **Saída:** "A multa é de R$ 10,00 por metro quadrado da calçada […]"
- **Causa:** o valor certo (R$ 300 por metro linear) está no Anexo Único da Lei 15.442. Este erro
  revelou um **bug no fatiamento**: dentro da tabela do anexo, a célula "Art. 1º" (coluna
  "Dispositivos violados") era lida como início de um artigo novo, e o anexo terminava antes de
  qualquer valor. Corrigido em `src/passo_genai/base.py` (`dividir_artigos`), com o teste
  `test_anexo_em_tabela_nao_e_cortado_pelas_celulas_art`. Agora o trecho tem os cinco valores.
  Mesmo assim, a busca não leva "de quanto?" até a tabela, cujo texto é pouco parecido com a
  pergunta. Sem o anexo no contexto, o modelo base **inventou** valor e unidade. É a falha mais
  perigosa: um número plausível e errado.
- **Correção:** (1) reescrever cada linha do anexo como frase completa ("Passeio em mau estado de
  conservação: multa de R$ 300,00 por metro linear da testada"), para a busca achá-la; (2)
  checagem pós-geração que recusa a resposta quando ela traz um número que não aparece em nenhum
  trecho citado.

## Erro 3 (r08): o trecho certo veio, mas foi recusado pelo limiar

- **Pergunta:** e se o dono nunca arrumar, a prefeitura faz a obra?
- **Recuperados:** `sp-dec59671-art1` (0,06), **`sp-lei15442-art17`** (0,03), `sp-lei15442-art10` (0,02)
- **Saída:** recusa padrão (nível `busca`).
- **Causa:** o art. 17, que responde a pergunta, foi recuperado, mas o reranker deu nota baixa a
  todos os candidatos de uma pergunta coloquial ("nunca arrumar", "faz a obra"), e o melhor
  ficou abaixo de 0,17. O limiar foi calibrado com apenas 10 respondíveis do dev, então é frágil.
- **Correção:** calibrar o limiar com mais perguntas de desenvolvimento, sobretudo informais, ou
  usar um critério combinado: recusar só quando o reranker **e** o cosseno do e5 estiverem
  baixos. O `bge-reranker-v2-m3` dá notas mais altas a perguntas informais, mas só cabe no prazo
  com GPU.

## Erro 4 (n03): "não consta" que passou do limiar e virou alucinação

- **Pergunta:** Quantos dias a Prefeitura leva para consertar uma calçada pública?
- **Recuperados:** `sp-subpref-calcadas-s01-p4` (0,60), `sp-dec59671-art32` (0,55), `sp-subpref-calcadas-s01-p2` (0,11)
- **Saída:** "A Prefeitura tem 30 dias para regularizar a calçada pública após a reforma. Se o
  serviço não for feito nesse prazo, a empresa pode ter sua permissão de prestação de serviços
  suspensa.", citando `sp-subpref-calcadas-s01-p2`.
- **Causa:** a base não tem prazo de conserto pela Prefeitura. O único "30 dias" do contexto está
  no art. 32, e é o prazo **do responsável pelo imóvel**, contado do corte de uma árvore. A
  "suspensão da permissão" é da concessionária (página da Subprefeitura). O modelo juntou dois
  trechos parecidos numa regra que não existe. Como cita um trecho que de fato foi recuperado, a
  checagem de citação não pega.
- **Correção:** é o caso que as recusas "sem base" do LoRA treinam: pergunta parecida, trecho
  parecido, que não responde. Também dá para acrescentar ao dev perguntas "não consta" parecidas
  com artigos reais, para o limiar aprender esse caso.

## Erro 5 (r11): pergunta informal sem vocabulário em comum com a base

- **Pergunta:** a empresa de água quebrou a calçada pra mexer no cano e deixou assim, quem conserta?
- **Recuperados:** `sp-dec59671-art1` (0,003), `sp-subpref-calcadas-s01-p2` (0,003), `sp-cartilha-calcadas-s01-p1` (0,001)
- **Saída:** recusa padrão (nível `busca`).
- **Causa:** a resposta está em `sp-subpref-calcadas-s01-p4` ("A lei obriga as **concessionárias
  ou permissionárias** públicas a repararem as calçadas onde realizarem intervenções […]"), que
  nem chegou ao top-3. Nada liga "empresa de água" e "cano" a "concessionária" e "intervenção".
  Os scores quase nulos mostram que nenhum candidato pareceu relevante.
- **Correção:** expansão de consulta com um pequeno glossário (empresa de água, luz, gás, Sabesp,
  Enel, Comgás → concessionária; buraco, cano, obra → intervenção) antes da busca, ou um trecho de
  "perguntas frequentes" na base com essa linguagem. Exemplos de treino com esse vocabulário
  também ajudam o LoRA a responder quando o trecho vem.

## Resumo

| Erro | Etapa que falhou | Tipo |
|---|---|---|
| 1 | geração (citação) | resposta certa, sem `fontes` |
| 2 | fatiamento + geração | valor inventado |
| 3 | limiar | recusa indevida |
| 4 | limiar + geração | alucinação em "não consta" |
| 5 | busca (vocabulário) | recusa indevida |
