"""Fase 5 — treina o LoRA na sua GPU (PEFT + TRL) e junta o adapter ao modelo base.

    python scripts/08_treinar_lora.py                 # rank 16, alpha 32, 3 épocas
    python scripts/08_treinar_lora.py --4bit          # QLoRA: para GPUs com 4–6 GB
    python scripts/08_treinar_lora.py --epocas 2 --max-len 1536

Modelo: MODELO_HF (padrão Qwen/Qwen2.5-1.5B-Instruct), o MESMO do Ollama na configuração B,
para o placar comparar só o efeito do LoRA. 10% dos exemplos ficam para a validação (perda).

Saídas:
    modelos/lora-adapter/   adapter (pequeno, ~35 MB) + curva de perda
    modelos/mesclado/       modelo base + adapter juntos (safetensors), entrada do 09_exportar_ollama.py
    treino/treino_lora.json resumo (perda de treino e validação, tempo, GPU, hiperparâmetros)
"""

import argparse
import json
import math
import random
import sys
import time

import _comum  # noqa: F401
from _comum import titulo
from passo_genai.config import MODELOS, TREINO, Config


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--epocas", type=float, default=3)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--acumulacao", type=int, default=8, help="batch efetivo = batch × acumulação")
    ap.add_argument("--max-len", type=int, default=2048)
    ap.add_argument("--4bit", dest="quatro_bits", action="store_true", help="QLoRA (bitsandbytes)")
    ap.add_argument("--sem-mesclar", action="store_true")
    args = ap.parse_args()

    import torch
    from datasets import Dataset
    from peft import LoraConfig, PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available():
        print("Sem GPU CUDA. Treinar LoRA em CPU leva horas/dias: use o notebook no Colab (README.md, seção 7.5).")
        if input("Continuar mesmo assim? [s/N] ").strip().lower() != "s":
            return 1

    cfg = Config()
    exemplos = [json.loads(l) for l in open(TREINO / "treino.jsonl", encoding="utf-8") if l.strip()]
    random.Random(42).shuffle(exemplos)
    n_val = max(1, len(exemplos) // 10)
    val, treino = exemplos[:n_val], exemplos[n_val:]
    ds_treino = Dataset.from_list([{"prompt": e["prompt"], "completion": e["completion"]} for e in treino])
    ds_val = Dataset.from_list([{"prompt": e["prompt"], "completion": e["completion"]} for e in val])
    titulo(f"{len(treino)} exemplos de treino, {len(val)} de validação — {cfg.modelo_hf}")

    bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    dtype = torch.bfloat16 if bf16 else torch.float16
    kwargs = {"torch_dtype": dtype}
    if args.quatro_bits:
        from transformers import BitsAndBytesConfig

        kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                           bnb_4bit_compute_dtype=dtype, bnb_4bit_use_double_quant=True)
    tokenizador = AutoTokenizer.from_pretrained(cfg.modelo_hf)
    if tokenizador.pad_token is None:
        tokenizador.pad_token = tokenizador.eos_token
    modelo = AutoModelForCausalLM.from_pretrained(cfg.modelo_hf, device_map="auto", **kwargs)

    lora = LoraConfig(r=args.rank, lora_alpha=args.alpha, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    saida = MODELOS / "lora-adapter"
    sft = SFTConfig(
        output_dir=str(MODELOS / "lora-checkpoints"),
        num_train_epochs=args.epocas,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch,
        gradient_accumulation_steps=args.acumulacao,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        # 5% dos passos; inteiro porque o transformers 5 tirou o warmup_ratio
        warmup_steps=max(1, round(0.05 * math.ceil(len(treino) / (args.batch * args.acumulacao)) * args.epocas)),
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        bf16=bf16,
        fp16=not bf16,
        gradient_checkpointing=True,
        max_length=args.max_len,
        report_to="none",
        seed=42,
    )
    trainer = SFTTrainer(model=modelo, args=sft, train_dataset=ds_treino, eval_dataset=ds_val,
                         peft_config=lora, processing_class=tokenizador)
    inicio = time.time()
    trainer.train()
    duracao = (time.time() - inicio) / 60
    trainer.save_model(str(saida))
    tokenizador.save_pretrained(str(saida))

    historico = trainer.state.log_history
    perdas = [h["loss"] for h in historico if "loss" in h]
    val_perdas = [h["eval_loss"] for h in historico if "eval_loss" in h]
    resumo = {"modelo_hf": cfg.modelo_hf, "rank": args.rank, "alpha": args.alpha, "epocas": args.epocas, "lr": args.lr,
              "batch_efetivo": args.batch * args.acumulacao, "qlora_4bit": args.quatro_bits, "n_treino": len(treino),
              "n_validacao": len(val), "perda_treino_final": perdas[-1] if perdas else None,
              "perda_validacao_por_epoca": val_perdas, "duracao_min": round(duracao, 1),
              "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"}
    (TREINO / "treino_lora.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")
    (saida / "log_history.json").write_text(json.dumps(historico, indent=2), encoding="utf-8")
    titulo("Treino concluído")
    print(json.dumps(resumo, indent=2, ensure_ascii=False))
    if len(val_perdas) >= 2 and val_perdas[-1] > min(val_perdas) * 1.05:
        print("AVISO: a perda de validação subiu na última época (sobreajuste). Considere --epocas 2.")

    if args.sem_mesclar:
        return 0
    titulo("Juntando adapter + modelo base (pesos completos em fp16)")
    del modelo, trainer
    torch.cuda.empty_cache()
    base = AutoModelForCausalLM.from_pretrained(cfg.modelo_hf, torch_dtype=torch.float16, device_map="cpu")
    mesclado = PeftModel.from_pretrained(base, str(saida)).merge_and_unload()
    destino = MODELOS / "mesclado"
    mesclado.save_pretrained(str(destino), safe_serialization=True)
    tokenizador.save_pretrained(str(destino))
    print(f"{destino}\nPróximo: python scripts/09_exportar_ollama.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
