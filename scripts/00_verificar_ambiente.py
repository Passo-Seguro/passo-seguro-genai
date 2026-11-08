"""Confere Python, GPU (CUDA), pacotes e o Ollama.

    python scripts/00_verificar_ambiente.py
"""

import shutil
import sys

import _comum  # noqa: F401
from _comum import titulo


def main() -> int:
    titulo("Python")
    print(sys.version.split()[0])
    titulo("GPU")
    try:
        import torch

        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            vram = p.total_memory / 1024**3
            print(f"{p.name}: {vram:.1f} GB, CUDA {torch.version.cuda}, bf16={torch.cuda.is_bf16_supported()}")
            if vram < 6:
                print("Com menos de 6 GB, treine o LoRA com --4bit (QLoRA) e --batch 1.")
        else:
            print("Sem CUDA. O RAG roda em CPU; o LoRA em CPU é inviável (use o Colab, ver README.md, seção 7.5).")
    except ImportError:
        print("PyTorch não instalado (só é obrigatório para o LoRA). Ver passo 1.")
    titulo("Pacotes")
    for mod in ("pydantic", "httpx", "bs4", "pypdf", "sentence_transformers", "faiss", "pandas", "matplotlib",
                "transformers", "peft", "trl", "datasets", "fastapi"):
        try:
            m = __import__(mod)
            print(f"ok    {mod} {getattr(m, '__version__', '')}")
        except ImportError:
            print(f"falta {mod}")
    titulo("Ollama")
    if not shutil.which("ollama"):
        print("ollama não encontrado no PATH. Instale em https://ollama.com/download")
    try:
        import httpx

        from passo_genai.config import Config

        cfg = Config()
        modelos = [m["name"] for m in httpx.get(f"{cfg.ollama_url}/api/tags", timeout=5).json().get("models", [])]
        print(f"Ollama no ar em {cfg.ollama_url}. Modelos: {modelos or 'nenhum'}")
        for nome in (cfg.modelo_base, cfg.modelo_lora):
            print(f"  {'ok ' if any(m.startswith(nome) for m in modelos) else 'FALTA'} {nome}")
        if not any(m.startswith(cfg.modelo_base) for m in modelos):
            print(f"  -> ollama pull {cfg.modelo_base}")
    except Exception as e:
        print(f"Ollama não respondeu ({type(e).__name__}). Abra o app do Ollama ou rode `ollama serve`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
