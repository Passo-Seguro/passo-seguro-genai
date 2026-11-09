| Configuração | Exatidão | Citação correta | Alucinação | Recusa correta (não consta) | Recusa indevida | JSON válido | Latência média (s) |
|---|---|---|---|---|---|---|---|
| B — RAG simples | 69% | 85% | 25% | 67% | 8% | 100% | 0.7 |
| C — RAG + LoRA | 62% | 77% | 12% | 100% | 23% | 100% | 0.33 |

16 perguntas do split `app`; limiar 0.17; top-3; 0 julgamentos corrigidos à mão.

Interpretação (2–3 frases por diferença): onde o LoRA ganhou, onde não ganhou e por quê; o efeito do RAG sobre a alucinação; o custo em recusas indevidas; formal × informal (ver placar_por_registro_app.csv).
