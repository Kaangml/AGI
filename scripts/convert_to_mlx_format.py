#!/usr/bin/env python3
"""
EVO-TR: Veri Formatı Dönüştürme

Alpaca formatından MLX-LM chat formatına dönüştürür.
"""

import json
from pathlib import Path
from rich.console import Console

console = Console()

# Giriş dosyaları
TRAIN_INPUT = Path("data/training/tr_chat_train.jsonl")
VAL_INPUT = Path("data/training/tr_chat_val.jsonl")

# Çıkış dizini (MLX-LM formatında)
OUTPUT_DIR = Path("data/training/mlx_format")


def convert_to_chat_format(sample: dict) -> dict:
    """Alpaca formatından chat formatına dönüştür"""
    instruction = sample.get("instruction", "")
    input_text = sample.get("input", "")
    output = sample.get("output", "")
    
    # Input varsa instruction'a ekle
    if input_text:
        user_content = f"{instruction}\n\n{input_text}"
    else:
        user_content = instruction
    
    return {
        "messages": [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": output}
        ]
    }


def convert_file(input_path: Path, output_path: Path) -> int:
    """Tek bir dosyayı dönüştür"""
    samples = []
    
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            sample = json.loads(line)
            chat_sample = convert_to_chat_format(sample)
            samples.append(chat_sample)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    return len(samples)


def main():
    console.print("\n[bold blue]🔄 Veri Formatı Dönüştürme (Alpaca -> MLX Chat)[/bold blue]\n")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Train dosyasını dönüştür
    train_output = OUTPUT_DIR / "train.jsonl"
    train_count = convert_file(TRAIN_INPUT, train_output)
    console.print(f"✅ Train: {train_count} örnek -> {train_output}")
    
    # Val dosyasını dönüştür
    val_output = OUTPUT_DIR / "valid.jsonl"
    val_count = convert_file(VAL_INPUT, val_output)
    console.print(f"✅ Valid: {val_count} örnek -> {val_output}")
    
    # Örnek göster
    console.print(f"\n📋 [yellow]Örnek dönüştürülmüş veri:[/yellow]")
    with open(train_output, "r", encoding="utf-8") as f:
        sample = json.loads(f.readline())
        console.print(json.dumps(sample, ensure_ascii=False, indent=2))
    
    console.print(f"\n✅ [bold green]Dönüştürme tamamlandı![/bold green]")
    console.print(f"\n[cyan]Eğitim için kullanılacak dizin:[/cyan] {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
