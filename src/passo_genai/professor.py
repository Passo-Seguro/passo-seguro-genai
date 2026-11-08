"""Cliente do "modelo professor" (maior) que gera os exemplos de treino do LoRA (Fase 5).

Duas opções, por variável de ambiente:
- Ollama local (padrão): PROFESSOR_MODELO=qwen2.5:7b-instruct   (precisa de ~6 GB de VRAM/RAM)
- API compatível com OpenAI: PROFESSOR_URL=https://.../v1  PROFESSOR_CHAVE=...  PROFESSOR_MODELO=...
  (ex.: Groq, OpenRouter, Together). A chave fica no .env, que o git ignora.
"""

from __future__ import annotations

import json
import os

import httpx


class Professor:
    def __init__(self):
        self.url = os.getenv("PROFESSOR_URL", "").rstrip("/")
        self.chave = os.getenv("PROFESSOR_CHAVE", "")
        self.modelo = os.getenv("PROFESSOR_MODELO", "qwen2.5:7b-instruct")
        self.ollama = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        self.cliente = httpx.Client(timeout=180)

    @property
    def descricao(self) -> str:
        return f"{self.modelo} via {'API ' + self.url if self.url else 'Ollama ' + self.ollama}"

    def json(self, sistema: str, usuario: str, temperatura: float = 0.7) -> dict:
        mensagens = [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]
        if self.url:
            r = self.cliente.post(f"{self.url}/chat/completions",
                                  headers={"Authorization": f"Bearer {self.chave}"},
                                  json={"model": self.modelo, "messages": mensagens, "temperature": temperatura,
                                        "response_format": {"type": "json_object"}})
            r.raise_for_status()
            texto = r.json()["choices"][0]["message"]["content"]
        else:
            r = self.cliente.post(f"{self.ollama}/api/chat",
                                  json={"model": self.modelo, "messages": mensagens, "stream": False,
                                        "format": "json", "options": {"temperature": temperatura}})
            r.raise_for_status()
            texto = r.json()["message"]["content"]
        inicio, fim = texto.find("{"), texto.rfind("}")
        return json.loads(texto[inicio:fim + 1])
