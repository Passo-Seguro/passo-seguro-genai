#!/bin/sh
# Sobe o Ollama, registra o modelo ajustado (rápido: só aponta para o .gguf) e sobe a API.
set -e
# threads pela cota de CPU do container (cgroup), não pelos núcleos da máquina física: no Railway o
# nproc mostra dezenas de núcleos e torch + llama.cpp disputando todos eles deixam tudo lento
if [ -z "$NUM_THREADS" ]; then
    read -r cota periodo < /sys/fs/cgroup/cpu.max 2>/dev/null || cota=max
    if [ "$cota" != "max" ] && [ -n "$periodo" ]; then NUM_THREADS=$(( (cota + periodo - 1) / periodo )); else NUM_THREADS=$(nproc); fi
fi
export OMP_NUM_THREADS="$NUM_THREADS" MKL_NUM_THREADS="$NUM_THREADS"
echo "threads: $NUM_THREADS (nproc $(nproc), cpu.max $(cat /sys/fs/cgroup/cpu.max 2>/dev/null || echo '?'))"
ollama serve &
for i in $(seq 1 60); do ollama list >/dev/null 2>&1 && break; sleep 1; done
cd /app/modelos && { cat Modelfile.gguf; echo "PARAMETER num_thread $NUM_THREADS"; } > Modelfile.run \
    && ollama create "${OLLAMA_MODELO_LORA:-passo-seguro-lora}" -f Modelfile.run
# aquece o modelo (a 1ª resposta carrega os pesos na RAM)
python -c "import json,os,urllib.request as u; u.urlopen(u.Request('http://127.0.0.1:11434/api/generate', json.dumps({'model': os.getenv('OLLAMA_MODELO_LORA','passo-seguro-lora'), 'prompt': 'ok', 'stream': False}).encode(), {'Content-Type': 'application/json'}), timeout=120)" || true
cd /app && exec uvicorn api.app:app --host 0.0.0.0 --port "${PORT:-8000}"
