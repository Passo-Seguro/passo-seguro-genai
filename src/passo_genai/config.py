"""Configuração central. Tudo pode ser trocado por variável de ambiente (ou pelo arquivo .env)."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from passo_genai import RAIZ

BASE = RAIZ / "base"
BRUTOS = BASE / "brutos"
TRECHOS = BASE / "trechos.jsonl"
INDICE = BASE / "indice"
AVALIACAO = RAIZ / "avaliacao"
TESTE = AVALIACAO / "teste.jsonl"
TREINO = RAIZ / "treino"
MODELOS = RAIZ / "modelos"
ARQ_LIMIAR = AVALIACAO / "limiar.json"
RESULTADOS = AVALIACAO / "resultados"  # placar, saídas, erros (gerados pelos scripts)

MENSAGEM_RECUSA = (
    "Não encontrei isso nas fontes oficiais que eu consulto. Para falar com a Prefeitura, "
    "ligue 156 ou acesse o SP156: https://sp156.prefeitura.sp.gov.br/ — e você pode registrar "
    "o problema aqui no Passo Seguro."
)


def _carregar_env():
    """Lê RAIZ/.env (CHAVE=valor) sem depender de pacote extra. Variáveis já definidas ganham."""
    arq = RAIZ / ".env"
    if not arq.exists():
        return
    for linha in arq.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        k, v = linha.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_carregar_env()


def _limiar_salvo() -> float:
    if ARQ_LIMIAR.exists():
        return float(json.loads(ARQ_LIMIAR.read_text(encoding="utf-8"))["limiar"])
    return 0.80  # provisório até rodar scripts/04_calibrar_limiar.py


@dataclass
class Config:
    # embeddings multilíngues (e5 exige os prefixos "query: " e "passage: ")
    modelo_embeddings: str = field(default_factory=lambda: os.getenv("MODELO_EMBEDDINGS", "intfloat/multilingual-e5-base"))
    top_k: int = field(default_factory=lambda: int(os.getenv("TOP_K", "3")))
    # reranker (cross-encoder): reordena os CANDIDATOS do e5; o limiar passa a valer sobre o score dele.
    # MODELO_RERANKER vazio = só a busca densa
    modelo_reranker: str = field(default_factory=lambda: os.getenv("MODELO_RERANKER", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"))
    candidatos: int = field(default_factory=lambda: int(os.getenv("CANDIDATOS", "10")))
    limiar: float = field(default_factory=lambda: float(os.getenv("LIMIAR", _limiar_salvo())))
    # Ollama
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434"))
    modelo_base: str = field(default_factory=lambda: os.getenv("OLLAMA_MODELO_BASE", "qwen2.5:1.5b-instruct"))
    modelo_lora: str = field(default_factory=lambda: os.getenv("OLLAMA_MODELO_LORA", "passo-seguro-lora"))
    # Hugging Face (treino do LoRA): o MESMO modelo do Ollama, em pesos completos
    modelo_hf: str = field(default_factory=lambda: os.getenv("MODELO_HF", "Qwen/Qwen2.5-1.5B-Instruct"))
    temperatura: float = field(default_factory=lambda: float(os.getenv("TEMPERATURA", "0.1")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "350")))
    timeout_s: float = field(default_factory=lambda: float(os.getenv("TIMEOUT_LLM_S", "60")))
