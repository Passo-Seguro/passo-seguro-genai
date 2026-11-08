# modelos/ (fora do git, exceto este README e o Modelfile.gguf)

- `lora-adapter/`: adapter LoRA (08_treinar_lora.py). Pode publicar no Hugging Face e pôr o link no README.
- `mesclado/`: modelo base + adapter em safetensors (~3 GB).
- `Modelfile`, `Modelfile.gguf`, `passo-seguro-lora-q4_K_M.gguf`: import no Ollama (09_exportar_ollama.py).
