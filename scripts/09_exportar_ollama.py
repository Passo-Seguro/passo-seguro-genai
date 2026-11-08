"""Fase 5 — importa o modelo mesclado no Ollama, quantizado (q4_K_M), e extrai o arquivo GGUF.

    python scripts/09_exportar_ollama.py

1. Copia o TEMPLATE e os PARAMETER do modelo base no Ollama (`ollama show <base> --modelfile`),
   para o modelo ajustado usar o mesmo formato de chat.
2. `ollama create passo-seguro-lora --quantize q4_K_M -f modelos/Modelfile` (lê os safetensors
   de modelos/mesclado/ e quantiza na mesma precisão do modelo base; comparação justa no placar).
3. Copia o GGUF gerado pelo Ollama para modelos/passo-seguro-lora-q4_K_M.gguf, que é o arquivo
   que vai para o container do assistente (Dockerfile.railway).

Se o seu Ollama não importar safetensors (versão antiga), use o llama.cpp:
    git clone https://github.com/ggml-org/llama.cpp && pip install -r llama.cpp/requirements.txt
    python llama.cpp/convert_hf_to_gguf.py modelos/mesclado --outtype f16 --outfile modelos/mesclado-f16.gguf
    llama.cpp/build/bin/llama-quantize modelos/mesclado-f16.gguf modelos/passo-seguro-lora-q4_K_M.gguf Q4_K_M
e troque o FROM do Modelfile pelo .gguf. Depois: ollama create passo-seguro-lora -f modelos/Modelfile
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import _comum  # noqa: F401
from _comum import titulo
from passo_genai.config import MODELOS, Config


def rodar(cmd: list[str]) -> str:
    print("$ " + " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit(f"falhou: {' '.join(cmd)}")
    return r.stdout


def main() -> int:
    cfg = Config()
    mesclado = MODELOS / "mesclado"
    if not (mesclado / "config.json").exists():
        print("modelos/mesclado/ não existe. Rode o 08_treinar_lora.py.")
        return 1
    if not shutil.which("ollama"):
        print("ollama não está no PATH.")
        return 1

    titulo(f"Template do modelo base ({cfg.modelo_base})")
    try:
        mf_base = rodar(["ollama", "show", cfg.modelo_base, "--modelfile"])
    except SystemExit:
        rodar(["ollama", "pull", cfg.modelo_base])
        mf_base = rodar(["ollama", "show", cfg.modelo_base, "--modelfile"])
    template = re.search(r'TEMPLATE\s+"""(.*?)"""', mf_base, re.S)
    params = re.findall(r"^PARAMETER .+$", mf_base, re.M)
    linhas = [f"FROM {mesclado.resolve().as_posix()}"]
    if template:
        linhas.append(f'TEMPLATE """{template.group(1)}"""')
    linhas += params
    linhas += ["PARAMETER temperature 0.1"]
    modelfile = MODELOS / "Modelfile"
    modelfile.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"{modelfile} escrito ({len(params)} PARAMETER copiados)")

    titulo("ollama create (quantizando para q4_K_M, alguns minutos)")
    rodar(["ollama", "create", cfg.modelo_lora, "--quantize", "q4_K_M", "-f", str(modelfile)])

    titulo("Extraindo o GGUF")
    mf_novo = rodar(["ollama", "show", cfg.modelo_lora, "--modelfile"])
    m = re.search(r"^FROM (.+)$", mf_novo, re.M)
    blob = Path(m.group(1).strip()) if m else None
    destino = MODELOS / "passo-seguro-lora-q4_K_M.gguf"
    if blob and blob.exists():
        shutil.copy2(blob, destino)
        print(f"{destino} ({destino.stat().st_size / 1e9:.2f} GB)")
        # Modelfile "portátil" para o container: aponta para o .gguf ao lado
        portatil = ["FROM ./passo-seguro-lora-q4_K_M.gguf"] + linhas[1:]
        (MODELOS / "Modelfile.gguf").write_text("\n".join(portatil) + "\n", encoding="utf-8")
    else:
        print("Não achei o blob do modelo (normal se o Ollama roda em outra máquina/container).")

    titulo("Teste rápido")
    print(rodar(["ollama", "run", cfg.modelo_lora, "Responda só com o JSON pedido: a calçada é de quem?"])[:500])
    print(f"\nPronto: o modelo '{cfg.modelo_lora}' está no Ollama. Próximo: python avaliacao/avaliar.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
