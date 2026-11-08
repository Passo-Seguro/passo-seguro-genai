| Configuração | Exatidão | Citação correta | Alucinação | Recusa correta (não consta) | Recusa indevida | JSON válido | Latência média (s) |
|---|---|---|---|---|---|---|---|
| A — modelo sem contexto | 23% | 0% | 100% | 0% | 0% | 100% | 0.3 |
| B — RAG simples | 43% | 50% | 36% | 80% | 23% | 98% | 0.35 |
| C — RAG + LoRA | 40% | 53% | 29% | 87% | 23% | 100% | 0.23 |

45 perguntas do split `teste`; limiar 0.17; top-3; 0 julgamentos corrigidos à mão.

## Interpretação

- **A → B (efeito do RAG):** a exatidão quase dobra (23% → 43%) e a alucinação cai de 100% para
  36%. Sem contexto, o modelo nunca cita uma fonte válida. O custo são 23% de recusas indevidas.
- **B → C (efeito do LoRA):** a exatidão fica praticamente igual (43% → 40%; entre execuções, B
  variou de 43% a 50% e C de 37% a 40%), mas C alucina menos (36% → 29%), recusa melhor o que não
  está na base (80% → 87%), devolve JSON válido em 100% dos casos e responde mais rápido
  (0,35 s → 0,23 s). Nas perguntas formais, a alucinação cai à metade (47% → 24%). O LoRA ensinou
  formato, citação e recusa, mas não acrescentou conhecimento: os erros de busca continuam.
- **Formal × informal:** nas três configurações, as perguntas informais acertam bem menos (B 28%,
  C 22%) e concentram as recusas indevidas (B 39%, C 33%), porque o reranker dá notas baixas a
  "tá", "pra" e "a gente". É o maior ponto de melhoria.
- **Configuração escolhida: C.** Empata com B em exatidão, dentro da variação entre execuções, e
  é mais segura (menos alucinação, mais recusas corretas, JSON sempre válido).
