#!/usr/bin/env python3
"""
Bilim Veri Seti Hazırlayıcı

SciQ ve Türkçe bilim verilerini birleştirip
MLX LoRA eğitimi için train/val split oluşturur.
"""

import json
import random
from pathlib import Path


def load_jsonl(path: str) -> list:
    """JSONL dosyasını yükle."""
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def save_jsonl(data: list, path: str):
    """JSONL olarak kaydet."""
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    data_dir = Path("data/training/science")
    
    # Verileri yükle
    print("📂 Veri dosyaları yükleniyor...")
    
    sciq_data = load_jsonl(data_dir / "sciq_data.jsonl")
    turkish_data = load_jsonl(data_dir / "turkish_science.jsonl")
    
    print(f"   SciQ: {len(sciq_data)} örnek")
    print(f"   Türkçe: {len(turkish_data)} örnek")
    
    # Birleştir ve karıştır
    all_data = sciq_data + turkish_data
    random.seed(42)
    random.shuffle(all_data)
    
    # Train/Val split (%90/%10)
    split_idx = int(len(all_data) * 0.9)
    train_data = all_data[:split_idx]
    val_data = all_data[split_idx:]
    
    # Türkçe örnekleri train'e ekle (önemli!)
    # Küçük Türkçe set'i hem train hem val'de olsun
    train_data.extend(turkish_data)
    random.shuffle(train_data)
    
    print(f"\n📊 Split:")
    print(f"   Train: {len(train_data)} örnek")
    print(f"   Validation: {len(val_data)} örnek")
    
    # Kaydet
    save_jsonl(train_data, data_dir / "train.jsonl")
    save_jsonl(val_data, data_dir / "valid.jsonl")
    
    print(f"\n💾 Dosyalar kaydedildi:")
    print(f"   {data_dir}/train.jsonl")
    print(f"   {data_dir}/valid.jsonl")
    
    # Örnek göster
    print(f"\n📝 Örnek train verisi:")
    sample = random.choice(train_data)
    for msg in sample["messages"][:2]:
        print(f"   [{msg['role']}]: {msg['content'][:100]}...")


if __name__ == "__main__":
    main()
