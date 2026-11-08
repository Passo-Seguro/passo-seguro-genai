# Serviço POST /assistente (sem o LLM: ele chama o Ollama em OLLAMA_URL).
# Build a partir da RAIZ do repositório:
#   docker build -f api/Dockerfile -t ghcr.io/passo-seguro/passo-seguro-genai:local .
FROM python:3.12-slim AS deps
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install --prefix=/install torch --index-url https://download.pytorch.org/whl/cpu
COPY api/requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/app/.cache/hf TOKENIZERS_PARALLELISM=false
ARG MODELO_EMBEDDINGS=intfloat/multilingual-e5-base
ENV MODELO_EMBEDDINGS=${MODELO_EMBEDDINGS}
RUN useradd --create-home --uid 10001 assistente
COPY --from=deps /install /usr/local
WORKDIR /app
# o modelo de embeddings entra na imagem: nada é baixado na partida
RUN python -c "import os; from sentence_transformers import SentenceTransformer; SentenceTransformer(os.environ['MODELO_EMBEDDINGS'])" \
    && chown -R assistente /app/.cache
COPY src/ src/
COPY api/ api/
COPY base/trechos.jsonl base/trechos.jsonl
COPY base/indice/ base/indice/
COPY avaliacao/limiar.json avaliacao/limiar.json
USER assistente
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/saude', timeout=2).status==200 else 1)"
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
