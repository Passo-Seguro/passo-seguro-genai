# Guia de uso: assistente do pedestre (`POST /assistente`)

O assistente responde dúvidas de pedestres de São Paulo sobre calçadas, travessias e como
reclamar. A resposta cita a lei ou a página oficial de onde saiu. Quando a base não cobre a
pergunta, ele recusa e indica o SP156.

> **Situação em 08/11/2026:** o modelo da configuração C (`passo-seguro-lora`) ainda não está no
> Ollama ([por quê](execucao/README.md#5d-exportação-para-o-ollama-09_exportar_ollamapy-bloqueada)).
> Até lá, suba com `CONFIG_VENCEDORA=B`. Com C sem o modelo, toda pergunta que passa do limiar
> cai na resposta de contingência. Leia também o
> [aviso sobre "carro na calçada"](execucao/README.md#8-api) antes de usar B em produção.

- [Como funciona](#como-funciona)
- [Subir o serviço](#subir-o-serviço)
- [Contrato](#contrato)
- [Exemplos de chamada](#exemplos-de-chamada)
- [Exemplos de respostas](#exemplos-de-respostas)
- [Erros e contingência](#erros-e-contingência)
- [Saúde e métricas](#saúde-e-métricas)
- [Configuração](#configuração)
- [Usar como biblioteca Python](#usar-como-biblioteca-python)
- [Linha de comando](#linha-de-comando)

## Como funciona

1. **Busca.** O `multilingual-e5-base` encontra os 10 trechos oficiais mais parecidos com a
   pergunta. O reranker `mmarco-mMiniLMv2` relê cada par pergunta–trecho e reordena. Os 3
   melhores seguem adiante.
2. **Recusa pela busca.** Se o melhor trecho tiver score abaixo do limiar (`avaliacao/limiar.json`,
   calibrado no dev), o serviço recusa **sem chamar o LLM**.
3. **Geração.** O LLM local (Qwen2.5-1.5B no Ollama: o modelo base na configuração B, o ajustado
   com LoRA na C) responde só com base nos trechos. A saída é JSON forçado pelo schema.
4. **Validação.** O Pydantic valida o JSON. Se vier inválido, tenta mais uma vez; se falhar de
   novo, recusa.
5. **Citação.** Fonte citada que não está entre os trechos recuperados é descartada. Se não
   sobrar nenhuma fonte, a resposta vira recusa: o app sempre mostra de onde veio a informação.

## Subir o serviço

Pré-requisitos: o Ollama rodando, com o modelo da configuração escolhida (`qwen2.5:1.5b-instruct`
para B, `passo-seguro-lora` para C), e a base indexada (`base/trechos.jsonl`, `base/indice/`).

**Local (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
$env:ASSISTENTE_TOKEN="token-local"; $env:CONFIG_VENCEDORA="C"
uvicorn api.app:app --port 8002
```

**Docker, só a API** (o Ollama fica no host):

```powershell
docker build -f api/Dockerfile -t ghcr.io/passo-seguro/passo-seguro-genai:local .
docker run --rm -p 8002:8000 -e ASSISTENTE_TOKEN=token-local -e CONFIG_VENCEDORA=C `
  -e OLLAMA_URL=http://host.docker.internal:11434 ghcr.io/passo-seguro/passo-seguro-genai:local
```

**Docker Compose** (Ollama e API juntos):

```powershell
docker compose up --build
docker compose exec ollama ollama pull qwen2.5:1.5b-instruct
docker compose exec ollama ollama create passo-seguro-lora -f /modelos/Modelfile.gguf
```

**Imagem única para o Railway** (Ollama + modelo GGUF + API):

```powershell
docker build -f Dockerfile.railway -t passo-seguro-assistente .
docker run --rm -p 8000:8000 -e ASSISTENTE_TOKEN=troque passo-seguro-assistente
```

A documentação interativa (Swagger) fica em <http://localhost:8002/docs>.

## Contrato

**Requisição:** `POST /assistente`, `Content-Type: application/json`, cabeçalho
`Authorization: Bearer <ASSISTENTE_TOKEN>`.

```json
{"pergunta": "carro estacionado em cima da calçada pode?"}
```

`pergunta` é obrigatória e tem de 1 a 500 caracteres.

**Resposta 200** (exemplo ilustrativo do formato; as respostas reais estão em
[Exemplos de respostas](#exemplos-de-respostas)):

```json
{
  "resposta": "Não pode. Estacionar no passeio é infração grave, com multa e remoção do veículo.",
  "fontes": [
    {"titulo": "Código de Trânsito Brasileiro (Lei nº 9.503/1997), Art. 181",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm"}
  ],
  "confianca": 0.9,
  "recusou": false
}
```

| Campo | Tipo | Significado |
|---|---|---|
| `resposta` | string | texto para o pedestre. Na recusa, a mensagem padrão com o link do SP156 |
| `fontes` | lista | `{titulo, url}` de cada fonte usada. Vazia na recusa |
| `confianca` | número 0..1 | confiança declarada pelo modelo. Na recusa, no máximo 0,3 |
| `recusou` | booleano | `true` quando a base não sustenta a resposta |

O app deve **sempre** mostrar as fontes e, quando `recusou` for `true`, oferecer o registro do
problema no próprio Passo Seguro.

## Exemplos de chamada

Saídas reais destas chamadas estão em [`execucao/`](execucao/).

**curl (bash):**

```bash
curl -X POST http://localhost:8002/assistente \
  -H "Authorization: Bearer token-local" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"pergunta": "Quem tem prioridade na faixa de pedestre?"}'
```

**curl no PowerShell:** o `curl.exe` do Windows pode mandar os acentos fora de UTF-8. Grave o
corpo num arquivo e envie com `--data-binary`:

```powershell
'{"pergunta": "carro na calçada pode?"}' | Out-File -Encoding utf8NoBOM corpo.json   # PowerShell 7
curl.exe -X POST http://localhost:8002/assistente -H "Authorization: Bearer token-local" `
  -H "Content-Type: application/json" --data-binary "@corpo.json"
```

**PowerShell nativo:**

```powershell
$corpo = @{ pergunta = "carro na calçada pode?" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8002/assistente `
  -Headers @{ Authorization = "Bearer token-local" } `
  -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($corpo))
```

**Python (httpx):**

```python
import httpx

r = httpx.post(
    "http://localhost:8002/assistente",
    headers={"Authorization": "Bearer token-local"},
    json={"pergunta": "a raiz da árvore levantou a calçada, de quem é a culpa?"},
    timeout=15,
)
r.raise_for_status()
dados = r.json()
print(dados["resposta"])
for f in dados["fontes"]:
    print("-", f["titulo"], f["url"])
```

**JavaScript:**

```js
const r = await fetch("http://localhost:8002/assistente", {
  method: "POST",
  headers: { Authorization: "Bearer token-local", "Content-Type": "application/json" },
  body: JSON.stringify({ pergunta: "bike pode andar na calçada?" }),
  signal: AbortSignal.timeout(15000),
});
const { resposta, fontes, recusou } = await r.json();
```

## Exemplos de respostas

**Respondida, com fonte:**

```json
{"resposta": "Os pedestres que estiverem atravessando a via sobre as faixas delimitadas para esse fim terão prioridade de passagem, exceto nos locais com sinalização semafórica...",
 "fontes": [{"titulo": "Código de Trânsito Brasileiro (Lei nº 9.503/1997), Art. 70",
             "url": "https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm"}],
 "confianca": 1.0, "recusou": false}
```

**Recusa (fora da base):** pergunta "Qual a melhor ação para investir este mês?"

```json
{"resposta": "Não encontrei isso nas fontes oficiais que eu consulto. Para falar com a Prefeitura, ligue 156 ou acesse o SP156: https://sp156.prefeitura.sp.gov.br/ — e você pode registrar o problema aqui no Passo Seguro.",
 "fontes": [], "confianca": 0.0, "recusou": true}
```

## Erros e contingência

| Status | `codigo` | Quando |
|---|---|---|
| 401 | `nao_autenticado` | sem o cabeçalho `Authorization` ou com o token errado |
| 422 | `dados_invalidos` | `pergunta` ausente, vazia ou com mais de 500 caracteres |
| 400 | `requisicao_invalida` | o corpo não é JSON válido em UTF-8 (ex.: acento enviado em latin-1) |
| 200 com `recusou: true` | — | o LLM não respondeu no prazo (`TIMEOUT_LLM_S`, 12 s) ou a base não carregou: volta a resposta de contingência, com o link do SP156 |

A API principal tem timeout de 15 s. O serviço desiste do LLM aos 12 s para sempre responder
dentro desse prazo.

## Saúde e métricas

`GET /saude` devolve 200 com a base carregada e 503 (`"status": "sem_base"`) sem ela:

```json
{"status": "ok", "erro": null, "config": "C", "modelo": "passo-seguro-lora", "limiar": 0.17, "trechos": 82}
```

`GET /metrics` responde no formato do Prometheus:

```
assistente_respostas_total{tipo="total"} 4
assistente_respostas_total{tipo="recusas"} 2
assistente_respostas_total{tipo="contingencias"} 0
assistente_respostas_total{tipo="cache"} 1
assistente_latencia_segundos{quantil="0.95"} 2.584
```

O log é JSON, uma linha por resposta, e **nunca traz o texto da pergunta**:

```json
{"evento": "resposta", "nivel_recusa": null, "json_valido": true, "citacoes_invalidas": 0, "score_max": 0.87, "ms": 2584, "recusou": false, "n_fontes": 3}
```

## Configuração

Todas as variáveis podem ir no `.env` (ver [`.env.exemplo`](../.env.exemplo)).

| Variável | Padrão | Para quê |
|---|---|---|
| `ASSISTENTE_TOKEN` | vazio | token Bearer, o mesmo da API principal. Vazio desliga a autenticação |
| `CONFIG_VENCEDORA` | C | `B` (modelo base) ou `C` (modelo com LoRA), a que ganhou no placar |
| `OLLAMA_URL` | `http://localhost:11434` | onde está o Ollama |
| `OLLAMA_MODELO_BASE` | `qwen2.5:1.5b-instruct` | modelo das configurações A e B |
| `OLLAMA_MODELO_LORA` | `passo-seguro-lora` | modelo da configuração C |
| `MODELO_EMBEDDINGS` | `intfloat/multilingual-e5-base` | trocar exige reindexar (`03_indexar.py`) |
| `MODELO_RERANKER` | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | vazio = só a busca densa. Trocar exige recalibrar o limiar (`04_avaliar_busca.py`) |
| `CANDIDATOS` | 10 | quantos trechos o reranker relê |
| `TOP_K` | 3 | quantos trechos vão para o prompt |
| `LIMIAR` | de `avaliacao/limiar.json` | score mínimo do melhor trecho para chamar o LLM |
| `TIMEOUT_LLM_S` | 12 na API, 60 nos scripts | tempo máximo esperando o LLM |
| `CACHE_TAMANHO` | 256 | perguntas repetidas guardadas em memória (chave normalizada) |
| `NIVEL_LOG` | INFO | nível do log |

## Usar como biblioteca Python

```python
import sys; sys.path.insert(0, "src")
from passo_genai.busca import Buscador
from passo_genai.gerador import Assistente, para_contrato

buscador = Buscador.carregar()            # índice + reranker
assistente = Assistente(buscador)         # usa o Ollama de OLLAMA_URL

r = assistente.responder("quem conserta a calçada na frente de casa?", config="C")
print(r.nivel_recusa, r.score_max, r.ids_recuperados, f"{r.latencia_s:.1f}s")
print(para_contrato(r, buscador.por_id).model_dump())

# só a busca
for res in buscador.buscar("bike pode andar na calçada?", 3):
    print(f"{res.score:.3f}  {res.trecho.trecho_id}")
```

## Linha de comando

```powershell
python scripts/05_testar_geracao.py --pergunta "o carro tá em cima da calçada, pode?"           # configuração B
python scripts/05_testar_geracao.py --config C --pergunta "quem conserta a calçada?"            # com LoRA
python scripts/05_testar_geracao.py --config A                                                  # sem contexto, 15 perguntas dev
```

A saída mostra o top-3 com os scores, o nível da recusa (busca, modelo ou JSON), o JSON e o
julgamento contra o gabarito.
