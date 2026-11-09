| Configuração | Exatidão | Citação correta | Alucinação | Recusa correta (não consta) | Recusa indevida | JSON válido | Latência média (s) |
|---|---|---|---|---|---|---|---|
| A — modelo sem contexto | 23% | 0% | 100% | 0% | 0% | 100% | 0.38 |
| B — RAG simples | 50% | 73% | 56% | 47% | 0% | 98% | 0.5 |
| C — RAG + LoRA | 50% | 47% | 33% | 80% | 10% | 100% | 0.36 |

45 perguntas do split `teste`; limiar 0.17; top-3; 0 julgamentos corrigidos à mão.

Versão 2 (09/11/2026): base limpa e com a carta de serviços do SP156 (84 trechos), checagem de
tema (pergunta do tema sempre vai ao modelo) e LoRA v2. Ver README, seção 9.7.

## Interpretação

- **A → B (efeito do RAG):** a exatidão vai de 23% para 50%, e a alucinação cai de 100% para 56%.
  Sem contexto, o modelo nunca cita uma fonte válida.
- **B → C (efeito do LoRA):** mesma exatidão (50%), mas C alucina bem menos (56% → 33%) e recusa
  80% do que a base não responde, contra 47% de B. Com a checagem de tema, B responde quase tudo e
  inventa quando a busca acha pouco; C recusa esses casos. B variou de 50% a 63% entre rodadas.
- **Formal × informal:** C acerta 50% nos dois registros e não recusa nenhuma informal; na v1,
  acertava 22% das informais e recusava 33% delas. O viés vinha do limiar do reranker.
- **Custo:** C ainda recusa 10% das respondíveis com o trecho certo no contexto (todas formais).
- **Configuração escolhida: C (LoRA v2).**

| Versão 1 (08/11, base de 82 trechos, sem checagem de tema) | Exatidão | Alucinação | Recusa correta | Recusa indevida |
|---|---|---|---|---|
| B | 43% | 36% | 80% | 23% |
| C (LoRA v1) | 40% | 29% | 87% | 23% |
