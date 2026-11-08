"""Esquemas Pydantic.

- `SaidaModelo`: o JSON que o LLM tem de produzir (interno). `fontes` traz os `trecho_id`.
- `RespostaAssistente` / `FonteCitada`: o contrato público de POST /assistente (openapi.yaml do
  repositório principal). Lá as fontes são {titulo, url}; o serviço converte os trecho_id.
"""

from pydantic import BaseModel, ConfigDict, Field


class SaidaModelo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    resposta: str = Field(min_length=1, max_length=1500)
    fontes: list[str] = Field(default_factory=list, description="trecho_id dos trechos usados")
    confianca: float = Field(ge=0, le=1)
    recusou: bool


# JSON Schema enviado ao Ollama em `format` (saída estruturada): o modelo é forçado a segui-lo.
SCHEMA_SAIDA = {
    "type": "object",
    "properties": {
        "resposta": {"type": "string"},
        "fontes": {"type": "array", "items": {"type": "string"}},
        "confianca": {"type": "number", "minimum": 0, "maximum": 1},
        "recusou": {"type": "boolean"},
    },
    "required": ["resposta", "fontes", "confianca", "recusou"],
}


class PerguntaAssistente(BaseModel):
    pergunta: str = Field(min_length=1, max_length=500)


class FonteCitada(BaseModel):
    titulo: str
    url: str | None = None


class RespostaAssistente(BaseModel):
    resposta: str
    fontes: list[FonteCitada]
    confianca: float = Field(ge=0, le=1)
    recusou: bool


class Trecho(BaseModel):
    trecho_id: str
    fonte: str
    titulo: str
    url: str
    artigo: str | None = None
    licenca: str
    data_acesso: str
    texto: str


class ItemTeste(BaseModel):
    id: str
    pergunta: str
    tipo: str  # respondivel | nao_consta
    resposta_esperada: str
    trecho_id: str | None = None  # prefixo: "ctb-art181" casa com "ctb-art181-p2"
    registro: str = "informal"  # formal | informal (para medir o viés com linguagem informal)
    split: str = "teste"  # dev (15, para ajustar) | teste (45, só no placar)
    # critério de julgamento escrito: TODOS os grupos precisam aparecer na resposta (basta um
    # termo de cada grupo). Comparação sem acento e sem maiúsculas. Ver avaliacao/criterio.md.
    criterio: list[list[str]] | None = None
