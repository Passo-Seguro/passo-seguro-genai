# Passo a passo: do zero ao placar e ao `/assistente`, rodando no seu PC

Tudo roda no seu computador, no VS Code. A GPU NVIDIA é usada no treino do LoRA (passo 7); o
resto roda bem em CPU. Cada passo também é uma **tarefa do VS Code**: `Ctrl+Shift+P` →
**Tasks: Run Task** → escolha pelo número.

Os comandos estão em PowerShell (Windows). No Linux ou no Mac, troque
`.venv\Scripts\Activate.ps1` por `source .venv/bin/activate`.

| Data | Fase | Comando / tarefa | Sai daqui | Pontos |
|---|---|---|---|---|
| 07/11 | 1. Tarefa e teste | já pronto: `avaliacao/teste.jsonl` (revisar) | 60 perguntas | 0,5 |
| 07–08/11 | 2. Base | `01_baixar_base.py`, `02_fatiar.py` | `base/trechos.jsonl`, `base/tabela_base.md` | 1,0 |
| 08–09/11 | 3. Busca | `03_indexar.py`, `04_avaliar_busca.py` | recall@k, `curva_limiar.png` | 1,0 |
| 09–10/11 | 4. Geração | `05_testar_geracao.py` | JSON validado, recusa em 2 níveis | 2,0 |
| 10–13/11 | 5. LoRA | `06`, `07` (revisão), `08` (GPU), `09` (Ollama) | `passo-seguro-lora` no Ollama | 2,0 |
| 13–14/11 | 6. Placar | `avaliacao/avaliar.py` | `placar.csv`, `placar.md` | 2,0 |
| 14/11 | 7. Cinco erros | `10_erros.py` + texto seu | `avaliacao/cinco_erros.md` | 1,0 |
| 12–14/11 | 8. API | Docker / Railway | `POST /assistente` no ar | – |
| 15–16/11 | 9. README e relatório | `docs/relatorio.md` | entrega | 0,5 |

---

## 1. Ambiente (uma vez)

Pré-requisitos: Python 3.11 ou 3.12, Git, **Ollama** (<https://ollama.com/download>) e, para o
LoRA, driver NVIDIA atualizado.

```powershell
git clone https://github.com/Passo-Seguro/passo-seguro-genai
cd passo-seguro-genai
code .
```

No terminal do VS Code:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

# PyTorch COM CUDA primeiro (senão o pip instala a versão só-CPU):
pip install torch --index-url https://download.pytorch.org/whl/cu124

pip install -r requirements-dev.txt        # RAG, avaliação, API, notebooks, testes
pip install -r requirements-treino.txt     # LoRA (transformers, peft, trl, bitsandbytes)
copy .env.exemplo .env

ollama pull qwen2.5:1.5b-instruct          # modelo base (configs A e B), ~1 GB
python scripts/00_verificar_ambiente.py
python -m pytest -q                        # 22 testes
```

**Por que Qwen2.5-1.5B-Instruct:** tem de 1 a 4 bilhões de parâmetros (pedido do guia), a licença
é Apache 2.0, ele fala português e roda em CPU em poucos segundos quando quantizado em 4 bits,
o que cabe no timeout de 15 s da API. Para trocar de modelo, mude `MODELO_HF` e
`OLLAMA_MODELO_BASE` no `.env`; os dois têm de ser o mesmo modelo. Cuidado: o Qwen2.5-3B **não**
é Apache, tem licença própria.

## 2. Fase 1 — Tarefa e conjunto de teste

**Tarefa (para o README):** responder dúvidas de pedestres de São Paulo sobre calçadas,
travessias e como reclamar, citando a fonte, em JSON.

O arquivo `avaliacao/teste.jsonl` já tem as 60 perguntas:
- 40 respondíveis e 20 "não consta";
- 15 de desenvolvimento e 45 de teste;
- marcadas como formais ou informais.

Cada respondível tem `resposta_esperada`, `trecho_id` (prefixo, ex.: `ctb-art181`) e `criterio`
(o julgamento escrito; ver `avaliacao/criterio.md`). **Revise**: troque perguntas pelas frases
reais das entrevistas da base comum, que é o melhor material possível. Depois do passo 3, o
`02_fatiar.py` avisa se algum `trecho_id` não existe na base.

Regra de ouro: as 45 de `split = teste` só rodam no placar. Ajuste prompt, limiar e trechos
olhando só as 15 de `dev`.

## 3. Fase 2 — Base de conhecimento

```powershell
python scripts/01_baixar_base.py
python scripts/02_fatiar.py
```

As fontes estão em `base/fontes.yaml`, com URL, licença e os artigos que interessam:
- CTB, partes de pedestre e de estacionar na calçada;
- Lei Brasileira de Inclusão, acessibilidade;
- Lei municipal 15.442/2011, que define o responsável pela calçada, o prazo de 60 dias e a multa;
- Decreto 59.671/2020, que padroniza as calçadas (o vigente; o 58.611/2019 foi revogado);
- páginas das Subprefeituras e a Cartilha de Calçadas 2023.

A NBR 9050 fica de fora (ABNT, direitos autorais).

- **O Planalto bloqueia download automático.** Se der `FALHOU`, abra a URL no navegador →
  `Ctrl+S` → "Página da Web, somente HTML" → salve como `base/brutos/ctb.html` (ou `lbi.html`)
  e rode o `01` de novo.
- **SP156:** as 4 entradas `sp156-*` estão com `ativo: false`. Abra
  <https://sp156.prefeitura.sp.gov.br>, busque cada serviço, cole a URL e troque para `ativo: true`.
- `base/tabela_base.md` traz fonte, formato, licença e número de trechos para o relatório.

## 4. Fase 3 — Busca

```powershell
python scripts/03_indexar.py          # 1ª vez baixa o modelo de embeddings (~1 GB)
python scripts/04_avaliar_busca.py
```

- recall@1 e recall@3 nas respondíveis. **Se recall@3 ficar abaixo de 0,8**, veja as perguntas
  listadas em "errou" e mexa no tamanho dos trechos (`MAX_TOKENS` em `src/passo_genai/base.py`)
  ou nos artigos de `fontes.yaml`, antes de seguir.
- Limiar: varre os valores de similaridade, mede acerto nas respondíveis e recusa correta nas
  "não consta", e escolhe o melhor equilíbrio **no dev**. Salva `avaliacao/limiar.json` e o
  gráfico `avaliacao/curva_limiar.png`, que vai para o relatório com a justificativa.
- Com o e5, as similaridades ficam altas (0,75 a 0,9), então a varredura vai além do intervalo
  de 0,3 a 0,8 do guia. Explique isso no relatório.

## 5. Fase 4 — Geração fundamentada

```powershell
python scripts/05_testar_geracao.py --config B
python scripts/05_testar_geracao.py --pergunta "o carro tá em cima da calçada, pode?"
```

O pipeline completo está em `src/passo_genai/gerador.py`:
1. Busca os 3 melhores trechos.
2. Se o melhor score ficar abaixo do limiar, **recusa sem chamar o modelo**.
3. Chama o LLM com o prompt de sistema (`prompts.py`) e a saída forçada em JSON (schema do Ollama).
4. Valida com Pydantic. Se o JSON vier inválido, tenta de novo uma vez; se falhar de novo, recusa.
5. Checa a citação: fonte que não está entre os recuperados conta como alucinação. No produto,
   ela é descartada, e se não sobrar fonte nenhuma a resposta vira recusa.

## 6. Fase 5 — LoRA (10–13/11)

**6a. Gerar ~300 exemplos com um modelo professor maior** (sem GPU de treino):

```powershell
ollama pull qwen2.5:7b-instruct     # professor local (~5 GB). Ou uma API no .env (PROFESSOR_URL)
python scripts/06_gerar_exemplos.py --alvo 300
```

Cerca de 25% são recusas: perguntas fora do escopo, e perguntas respondíveis acompanhadas de
trechos que não as respondem. Exemplos parecidos com qualquer pergunta do teste (similaridade de
0,90 ou mais) são descartados.

**6b. Revisar à mão** (obrigatório no guia):

```powershell
python scripts/07_revisar_exemplos.py            # a = aprovar, e = editar, r = rejeitar, q = sair
python scripts/07_revisar_exemplos.py --exportar # treino/treino.jsonl + treino/estatisticas.md
```

**7. Treinar na GPU** (a partir de 11/11, quando o YOLO da visão tiver terminado):

```powershell
python scripts/08_treinar_lora.py                                  # 8 GB de VRAM ou mais
python scripts/08_treinar_lora.py --4bit --batch 1 --acumulacao 16 # 4 a 6 GB (QLoRA)
```

São rank 16, alpha 32, 3 épocas e cerca de 10 a 25 minutos numa GPU de 8 GB. Se a perda de
validação subir na última época, use `--epocas 2`.

Sem GPU NVIDIA: abra `notebooks/04_lora.ipynb` no Google Colab (GPU T4), envie a pasta
`treino/` e `src/`, rode as células do passo 8 e baixe `modelos/mesclado/` de volta.

**8. Importar no Ollama:**

```powershell
python scripts/09_exportar_ollama.py
```

O script junta o adapter, quantiza em q4_K_M (a mesma quantização do modelo base, para a
comparação ser justa) e cria `passo-seguro-lora` no Ollama. Também extrai o
`modelos/passo-seguro-lora-q4_K_M.gguf` para o container.

**Plano B (se o LoRA não funcionar até 12/11):** veja `docs/plano-b-agente.md`.

## 7. Fase 6 — Placar (13–14/11)

```powershell
python avaliacao/avaliar.py --split dev   # ensaio
python avaliacao/avaliar.py               # PLACAR OFICIAL: 45 perguntas × A, B, C
```

Saem `avaliacao/placar.csv`, `placar.md`, `placar_por_registro.csv` (formal × informal) e
`saidas/*.jsonl`. Confira o julgamento automático em `revisao_manual.csv`: preencha
`correta_manual` com 1 ou 0 onde discordar e rode de novo. Interprete cada diferença em 2 ou 3
frases. O placar também vai para o pitch: entregue os números ao Guilherme.

## 8. Fase 7 — Cinco erros reais

```powershell
python scripts/10_erros.py --config C
```

O script classifica os erros pela causa provável (busca não achou, recusa por limiar, trecho
mal cortado, modelo inventou, JSON quebrou) e cria `avaliacao/cinco_erros.md` com 5 sugestões.
Escreva a causa e a correção de cada um.

## 9. Fase 8 — API `/assistente` e integração

**Local:**

```powershell
$env:ASSISTENTE_TOKEN="token-local"; $env:CONFIG_VENCEDORA="C"
uvicorn api.app:app --port 8002
curl.exe -X POST http://localhost:8002/assistente -H "Authorization: Bearer token-local" -H "Content-Type: application/json" -d '{\"pergunta\": \"carro na calçada pode?\"}'
```

`CONFIG_VENCEDORA` é B ou C, a que ganhou no placar.

**Container no Railway**, que é onde o Terraform da Júlia espera o assistente (`assistente_url`
e `assistente_token`):

```powershell
docker build -f Dockerfile.railway -t passo-seguro-assistente .
docker run --rm -p 8000:8000 -e ASSISTENTE_TOKEN=troque passo-seguro-assistente
```

No Railway: crie um serviço a partir deste repositório com `Dockerfile.railway` e defina
`ASSISTENTE_TOKEN`. Ele precisa de uns 3 GB de RAM; se faltar, use `MODELO_EMBEDDINGS`
`intfloat/multilingual-e5-small`, mas isso exige reindexar. Passe a URL e o token para a Júlia
pôr no `terraform.tfvars`. O `.gguf` não vai para o git: faça o build da sua máquina com
`railway up`, ou publique a imagem no GHCR.

**Contrato com a API principal:**
- A resposta tem `{resposta, fontes: [{titulo, url}], confianca, recusou}`.
- O timeout da API é de 15 s. O serviço desiste do LLM aos 12 s e devolve a recusa padrão com o link do SP156.
- O log nunca tem o texto da pergunta.

## 10. Fase 9 — README e relatório

Use o modelo em `docs/relatorio.md` e preencha os 7 itens do checklist. O diagrama do pipeline
em Mermaid já está no README.

Antes do push final:

```powershell
python -m pytest -q
git status       # .env, modelos/*.gguf e safetensors NÃO podem aparecer
```

Rode também os notebooks e salve com as saídas: o guia pede notebooks com saídas salvas.
