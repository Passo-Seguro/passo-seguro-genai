| Configuração | Exatidão | Citação correta | Alucinação | Recusa correta (não consta) | Recusa indevida | JSON válido | Latência média (s) |
|---|---|---|---|---|---|---|---|
| A — modelo sem contexto | 23% | 0% | 100% | 0% | 0% | 100% | 0.29 |
| B — RAG simples | 50% | 67% | 29% | 80% | 20% | 100% | 0.32 |

45 perguntas do split `teste`; limiar 0.17; top-3; 0 julgamentos corrigidos à mão.

## Interpretação

- **A → B (efeito do RAG):** a exatidão sobe de 23% para 50% e a alucinação cai de 100% para 29%.
  Sem contexto, o modelo nunca cita uma fonte válida, então toda resposta de A conta como
  alucinação. Com os trechos, 67% das respostas citam o trecho certo. O custo são 20% de recusas
  indevidas.
- **Formal × informal:** B acerta 67% das formais e só 39% das informais. As recusas indevidas
  (33%) aparecem só nas informais: o reranker dá notas baixas a perguntas com "tá", "pra" e
  "a gente", que ficam abaixo do limiar. É o viés mais importante a corrigir, porque o pedestre
  fala assim.
- **C (LoRA):** pendente. O adapter foi treinado, mas não pôde ser importado no Ollama 0.40 (ver
  `docs/execucao/README.md`, fase 5d).
