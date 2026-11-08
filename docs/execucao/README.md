# Registro de execução e testes — 08/11/2026

O que foi rodado de verdade nesta máquina, com as saídas salvas nesta pasta. Serve de evidência
para o relatório e de ponto de partida para quem continuar o pipeline.

## Ambiente

| Item | Versão |
|---|---|
| Sistema | Windows 11 Pro |
| Python | 3.12.10 (venv em `.venv`) |
| GPU | NVIDIA GeForce RTX 4080, 16 GB, driver 617.14, CUDA 13.0, bf16 |
| PyTorch | 2.14.1+cu130 |
| Ollama | 0.40.15, modelo `qwen2.5:1.5b-instruct` |
| Embeddings | `intfloat/multilingual-e5-base` |

Saída completa: [`00_ambiente.txt`](00_ambiente.txt).

**Ajuste feito no guia:** o índice `cu124` do PyTorch para na versão 2.6. O passo 1 agora usa
`cu130` (driver 580 ou mais novo; `cu126` para drivers antigos).

## Testes automatizados

`python -m pytest -v` → **22 passaram, 0 falharam** ([`pytest.txt`](pytest.txt)).

| Arquivo | O que cobre |
|---|---|
| `test_api.py` | contrato do `POST /assistente`, 401, 422, contingência, log sem a pergunta, cache |
| `test_avaliacao.py` | forma do conjunto de teste, julgamento (acerto, alucinação, não consta), resumo |
| `test_base.py` | fatiamento por artigo, texto revogado removido, janelas com sobreposição |
| `test_gerador.py` | recusa por limiar sem chamar o LLM, JSON inválido com nova tentativa, citação fora dos recuperados |

## Pipeline: o que rodou

| Fase | Comando | Resultado |
|---|---|---|
| 2. Base | `01_baixar_base.py` | 7 fontes baixadas sem bloqueio (o Planalto não bloqueou). As 4 do SP156 seguem `ativo: false` |
| 2. Base | `02_fatiar.py` | **82 trechos** ([`base/tabela_base.md`](../../base/tabela_base.md)); todo `trecho_id` do gabarito existe na base |
| 3. Busca | `03_indexar.py` | índice com 82 vetores em 25 s (GPU) |
| 3. Busca | `04_avaliar_busca.py` | **recall@3 = 0,60** (meta do guia: 0,8); limiar 0,86 ([`04_avaliar_busca.txt`](04_avaliar_busca.txt)) |
| 4. Geração | `05_testar_geracao.py --config B` | 15 perguntas dev com o Ollama ([`05_geracao_B_dev.txt`](05_geracao_B_dev.txt)) |
| 8. API | `uvicorn api.app:app` | `/saude`, `/assistente` e `/metrics` testados com curl ([`api_assistente_local.txt`](api_assistente_local.txt)) |

### Fase 3: a busca ainda não passa na meta

| Conjunto | n | recall@1 | recall@3 |
|---|---|---|---|
| dev | 10 | 0,20 | 0,20 |
| todas as respondíveis | 40 | 0,30 | 0,60 |

Diagnóstico, feito com as 40 respondíveis:

- O trecho certo costuma estar logo abaixo do corte: **recall@5 = 0,70 e recall@10 = 0,875**.
- Em **8 dos 16 erros**, a página genérica `sp-subpref-calcadas` ocupa o top-3. É um texto
  amplo sobre calçadas que fica parecido com quase qualquer pergunta.
- Todas as similaridades ficam entre 0,76 e 0,93. Com o limiar calibrado no dev (0,86), as
  respondíveis do dev quase sempre são recusadas: acerto de 0,20 e recusa correta de 1,00.

Caminhos possíveis, a decidir pelo grupo (ajustar olhando só o dev):

1. Buscar top-10 e reordenar com um reranker multilíngue (ex.: `BAAI/bge-reranker-v2-m3`),
   mantendo o top-3 para o prompt.
2. Busca híbrida: BM25 sobre os mesmos trechos, somado ao score denso. Ajuda nas perguntas com
   termos exatos ("Art. 3º", "mobilidade reduzida", "prazo").
3. Rebaixar ou cortar a página `sp-subpref-calcadas` e limpar o menu de navegação que entrou nos
   trechos `sp-subpref-servicos156-*`.
4. Ativar as 4 páginas do SP156 (`fontes.yaml`). As perguntas r25 e r26 dependem delas.

### Fase 4: geração no dev (configuração B, limiar 0,86)

| | n | Resultado |
|---|---|---|
| "Não consta" | 5 | 5 recusas corretas, todas já na busca |
| Respondíveis | 10 | 3 recusas indevidas na busca; das 7 que chegaram ao LLM, 4 corretas e 4 com alucinação ou citação inválida (uma das corretas também teve citação inválida) |

O JSON veio válido em todas; uma resposta precisou da segunda tentativa. O caminho até o LLM
leva de 0,4 s a 5 s depois que o modelo está carregado. A primeira chamada levou 46 s, que é o
tempo de carregar o modelo.

A guarda de citação funcionou numa pergunta rodada com limiar 0,80
([`05_geracao_B_pergunta_limiar080.txt`](05_geracao_B_pergunta_limiar080.txt)). O modelo
respondeu "30 dias" sem citar fonte. O gabarito é 60 dias (Lei 15.442, art. 11), e a busca não
tinha trazido esse artigo. Como não havia fonte, o contrato transformou a resposta em recusa.

### Fase 8: API local

| Chamada | Esperado | Obtido |
|---|---|---|
| `GET /saude` | 200, base carregada | 200, 82 trechos, limiar 0,86 |
| `POST` sem token / token errado | 401 `nao_autenticado` | 401 |
| `POST` pergunta vazia | 422 `dados_invalidos` | 422 |
| "Quem tem prioridade na faixa de pedestre?" | resposta com fonte | CTB art. 70 (e 68, 214), 2,6 s |
| "Qual a melhor ação para investir este mês?" | recusa | recusa na busca, 34 ms |
| mesma pergunta repetida | cache | servida do cache (`tipo="cache"` = 1) |
| log | sem o texto da pergunta | nenhuma ocorrência da pergunta no log |

Dois pontos para corrigir:

- "carro na calçada pode?", a pergunta usada de exemplo no guia, é recusada: o score foi
  0,855, abaixo do limiar de 0,86. É o mesmo problema da busca.
- Um corpo que não é JSON válido (ex.: acento enviado fora de UTF-8 pelo curl do Git Bash) volta
  como 400 `{"detail": ...}`, o formato padrão do FastAPI, e não `{codigo, mensagem}`. O
  `exception_handler` cobre a validação dos campos, mas não o erro de parse do corpo.

### Fase 8: container (`api/Dockerfile`)

O primeiro build gerou uma imagem de **11,7 GB**. Tinha dois problemas, os dois corrigidos:

- No estágio `deps`, o segundo `pip install --prefix=/install` não via o torch CPU já instalado
  em `/install`. Por isso o `sentence-transformers` puxava o torch com CUDA do PyPI, com 3 GB só
  de bibliotecas NVIDIA. Agora o comando roda com `PYTHONPATH` apontando para `/install`.
- Não havia `.dockerignore`, então o `.venv` inteiro ia no contexto do build. O novo
  `.dockerignore` deixa passar só o que os Dockerfiles copiam.

Depois disso: **3,96 GB**, torch `2.15.0+cpu`, contexto de 2,7 kB. O container rodou com
`OLLAMA_URL=http://host.docker.internal:11434`. Resultado: `/saude` 200, 401 sem token, resposta
com CTB art. 70 em 4 s e healthcheck `healthy`
([`api_assistente_docker.txt`](api_assistente_docker.txt)).

## O que falta, e por quê não foi rodado aqui

| Fase | Bloqueio |
|---|---|
| 3. Busca | recall@3 abaixo de 0,8. O guia pede corrigir antes de seguir |
| 5. LoRA (06–09) | `07_revisar_exemplos.py` exige revisão humana dos ~300 exemplos. O treino (`08`) roda na RTX 4080 sem `--4bit` |
| 6. Placar | depende do modelo `passo-seguro-lora` (configuração C) |
| 7. Cinco erros | depende do placar |
| Railway | `Dockerfile.railway` precisa do `.gguf` gerado pelo `09_exportar_ollama.py` |
| Notebooks | não foram executados. O guia pede salvá-los com as saídas |

Para repetir esta execução, siga o [PASSO_A_PASSO.md](../../PASSO_A_PASSO.md), passos 1 a 5 e 9.
