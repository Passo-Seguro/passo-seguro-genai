"""Busca semântica: embeddings multilíngues + índice vetorial (FAISS, ou numpy se não houver FAISS).

A base tem algumas centenas de trechos, então a busca exata (produto interno de vetores
normalizados = similaridade de cosseno) é instantânea mesmo sem FAISS.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from passo_genai.base import carregar_trechos
from passo_genai.config import INDICE, TRECHOS, Config
from passo_genai.esquemas import Trecho


@dataclass
class Resultado:
    trecho: Trecho
    score: float  # do reranker, se houver; senão o cosseno do e5
    score_denso: float | None = None


class Embeddings:
    """Wrapper do sentence-transformers que cuida dos prefixos do e5 ("query: "/"passage: ")."""

    def __init__(self, nome: str, device: str | None = None):
        from sentence_transformers import SentenceTransformer

        self.nome = nome
        self.modelo = SentenceTransformer(nome, device=device)
        self.e5 = "e5" in nome.lower()

    def _prefixo(self, textos, tipo):
        if not self.e5:
            return list(textos)
        return [f"{tipo}: {t}" for t in textos]

    def documentos(self, textos: list[str]) -> np.ndarray:
        return self.modelo.encode(self._prefixo(textos, "passage"), normalize_embeddings=True,
                                  batch_size=16, show_progress_bar=len(textos) > 50).astype(np.float32)

    def consultas(self, textos: list[str]) -> np.ndarray:
        return self.modelo.encode(self._prefixo(textos, "query"), normalize_embeddings=True,
                                  batch_size=32).astype(np.float32)


class Reranqueador:
    """Cross-encoder: lê pergunta e trecho juntos e devolve a relevância em 0..1 (sigmoide).
    Corrige o ponto fraco do e5 nesta base: páginas genéricas sobre calçadas ficavam parecidas
    com quase toda pergunta e tomavam o top-3 do artigo certo."""

    def __init__(self, nome: str, device: str | None = None):
        from sentence_transformers import CrossEncoder

        self.nome = nome
        self.modelo = CrossEncoder(nome, device=device, max_length=512)

    def pontuar(self, pergunta: str, textos: list[str]) -> np.ndarray:
        logits = np.asarray(self.modelo.predict([(pergunta, t) for t in textos], batch_size=16,
                                                show_progress_bar=False, activation_fn=None), dtype=np.float32)
        return 1.0 / (1.0 + np.exp(-logits))


class Buscador:
    def __init__(self, trechos: list[Trecho], vetores: np.ndarray, embeddings: Embeddings,
                 reranker: Reranqueador | None = None, candidatos: int = 10):
        self.trechos = trechos
        self.vetores = vetores
        self.emb = embeddings
        self.reranker = reranker
        self.candidatos = candidatos
        self.por_id = {t.trecho_id: t for t in trechos}
        self._faiss = None
        try:
            import faiss

            self._faiss = faiss.IndexFlatIP(vetores.shape[1])
            self._faiss.add(vetores)
        except ImportError:
            pass

    # ------------------------------------------------------------------ construção e disco
    @classmethod
    def construir(cls, config: Config | None = None, caminho_trechos: Path = TRECHOS) -> "Buscador":
        config = config or Config()
        trechos = carregar_trechos(caminho_trechos)
        emb = Embeddings(config.modelo_embeddings)
        return cls(trechos, emb.documentos([t.texto for t in trechos]), emb)

    def salvar(self, pasta: Path = INDICE) -> None:
        pasta.mkdir(parents=True, exist_ok=True)
        np.save(pasta / "vetores.npy", self.vetores)
        (pasta / "ids.json").write_text(json.dumps([t.trecho_id for t in self.trechos]), encoding="utf-8")
        (pasta / "info.json").write_text(json.dumps({
            "modelo_embeddings": self.emb.nome, "n_trechos": len(self.trechos), "dim": int(self.vetores.shape[1]),
            "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}, indent=2), encoding="utf-8")

    @classmethod
    def carregar(cls, pasta: Path = INDICE, caminho_trechos: Path = TRECHOS, embeddings: Embeddings | None = None,
                 config: Config | None = None) -> "Buscador":
        config = config or Config()
        info = json.loads((pasta / "info.json").read_text(encoding="utf-8"))
        ids = json.loads((pasta / "ids.json").read_text(encoding="utf-8"))
        por_id = {t.trecho_id: t for t in carregar_trechos(caminho_trechos)}
        faltando = [i for i in ids if i not in por_id]
        if faltando:
            raise RuntimeError(f"índice desatualizado: {len(faltando)} trechos sumiram. Rode scripts/03_indexar.py")
        emb = embeddings or Embeddings(info["modelo_embeddings"])
        reranker = Reranqueador(config.modelo_reranker) if config.modelo_reranker else None
        return cls([por_id[i] for i in ids], np.load(pasta / "vetores.npy"), emb, reranker, config.candidatos)

    # ------------------------------------------------------------------ busca
    def buscar_vetor(self, q: np.ndarray, k: int) -> list[Resultado]:
        k = min(k, len(self.trechos))
        if self._faiss is not None:
            scores, idx = self._faiss.search(q.reshape(1, -1), k)
            pares = zip(idx[0], scores[0])
        else:
            sims = self.vetores @ q.reshape(-1)
            idx = np.argsort(-sims)[:k]
            pares = zip(idx, sims[idx])
        return [Resultado(self.trechos[int(i)], float(s), float(s)) for i, s in pares]

    def _reordenar(self, pergunta: str, q: np.ndarray, k: int) -> list[Resultado]:
        if self.reranker is None:
            return self.buscar_vetor(q, k)
        cands = self.buscar_vetor(q, max(k, self.candidatos))
        scores = self.reranker.pontuar(pergunta, [c.trecho.texto for c in cands])
        for c, s in zip(cands, scores):
            c.score = float(s)
        return sorted(cands, key=lambda c: -c.score)[:k]

    def buscar(self, pergunta: str, k: int = 3) -> list[Resultado]:
        return self._reordenar(pergunta, self.emb.consultas([pergunta])[0], k)

    def buscar_lote(self, perguntas: list[str], k: int = 3) -> list[list[Resultado]]:
        qs = self.emb.consultas(perguntas)
        return [self._reordenar(p, q, k) for p, q in zip(perguntas, qs)]


def acertou(recuperados: list[str], esperado: str | None) -> bool:
    """O trecho esperado do gabarito é um PREFIXO (ex.: 'ctb-art181' casa com 'ctb-art181-p2')."""
    if not esperado:
        return False
    esperados = [e.strip() for e in esperado.split("|")]  # aceita mais de um: "a|b"
    return any(r == e or r.startswith(e + "-") for r in recuperados for e in esperados)
