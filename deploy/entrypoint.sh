#!/bin/sh
# Sobe o Ollama, registra o modelo ajustado (rápido: só aponta para o .gguf) e sobe a API.
set -e
ollama serve &
for i in $(seq 1 60); do ollama list >/dev/null 2>&1 && break; sleep 1; done
cd /app/modelos && ollama create "${OLLAMA_MODELO_LORA:-passo-seguro-lora}" -f Modelfile.gguf
# aquece o modelo (a 1ª resposta carrega os pesos na RAM)
python -c "import json,os,urllib.request as u; u.urlopen(u.Request('http://127.0.0.1:11434/api/generate', json.dumps({'model': os.getenv('OLLAMA_MODELO_LORA','passo-seguro-lora'), 'prompt': 'ok', 'stream': False}).encode(), {'Content-Type': 'application/json'}), timeout=120)" || true
cd /app && exec uvicorn api.app:app --host 0.0.0.0 --port "${PORT:-8000}"
