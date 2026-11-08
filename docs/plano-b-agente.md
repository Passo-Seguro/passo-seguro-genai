# Plano B: agente com duas ferramentas (se o LoRA não funcionar até 12/11)

O guia prevê: se o LoRA não estiver funcionando em 12/11, a especialização vira um **agente**
com duas ferramentas, comparado ao RAG simples.

| Ferramenta | O que faz | Implementação |
|---|---|---|
| `buscar_na_base(pergunta)` | Devolve os 3 trechos mais próximos com `trecho_id` | `Buscador.buscar` (já existe) |
| `status_do_relato(id)` | Consulta o andamento de um relato | `GET {API}/relatos/{id}` do repositório principal |

Como montar com o que já existe:
1. Use as *tools* do Ollama (`"tools": [...]` em `/api/chat`). O Qwen2.5 suporta chamada de ferramenta.
2. Loop: o modelo pede uma ferramenta, o código executa e devolve o resultado como mensagem
   `role: tool`. Repita até a resposta final, com no máximo 3 passos.
3. A resposta final continua no JSON de `SaidaModelo`, com a mesma checagem de citação.
4. No placar, a configuração C passa a ser "agente" em vez de "RAG + LoRA". As métricas e o
   critério não mudam.

No relatório, explique por que o plano B foi acionado: o que falhou no LoRA e qual sinal foi
visto (perda, JSON quebrado, recusa demais).
