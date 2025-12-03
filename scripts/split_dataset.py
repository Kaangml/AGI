#!/usr/bin/env python3
"""
EVO-TR: Veri Seti Bölme (Train/Validation)

Birleştirilmiş veriyi train ve validation setlerine böler.
"""

import json
import random
from pathlib import Path
from rich.console import Console

console = Console()

INPUT_FILE = Path("data/training/tr_chat_combined.jsonl")
TRAIN_FILE = Path("data/training/tr_chat_train.jsonl")
VAL_FILE = Path("data/training/tr_chat_val.jsonl")

TRAIN_RATIO = 0.9
RANDOM_SEED = 42


def main():
    console.print("\n[bold blue]📊 Veri Seti Bölme (Train/Val)[/bold blue]\n")
    
    # Veriyi yükle
    console.print(f"📖 Yükleniyor: {INPUT_FILE}")
    samples = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            samples.append(json.loads(line))
    
    console.print(f"   Toplam örnek: {len(samples)}")
    
    # Karıştır
    random.seed(RANDOM_SEED)
    random.shuffle(samples)
    console.print(f"🔀 Veri karıştırıldı (seed={RANDOM_SEED})")
    
    # Böl
    split_idx = int(len(samples) * TRAIN_RATIO)
    train_samples = samples[:split_idx]
    val_samples = samples[split_idx:]
    
    console.print(f"\n📈 Bölme oranı: {TRAIN_RATIO*100:.0f}% train / {(1-TRAIN_RATIO)*100:.0f}% val")
    
    # Kaydet
    with open(TRAIN_FILE, "w", encoding="utf-8") as f:
        for sample in train_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    with open(VAL_FILE, "w", encoding="utf-8") as f:
        for sample in val_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    # Sonuçları göster
    train_size = TRAIN_FILE.stat().st_size / 1024
    val_size = VAL_FILE.stat().st_size / 1024
    
    console.print(f"\n✅ [green]Train:[/green] {len(train_samples)} örnek ({train_size:.1f} KB) -> {TRAIN_FILE}")
    console.print(f"✅ [green]Val:[/green] {len(val_samples)} örnek ({val_size:.1f} KB) -> {VAL_FILE}")
    
    console.print(f"\n✅ [bold green]Bölme tamamlandı![/bold green]")


if __name__ == "__main__":
    main()
