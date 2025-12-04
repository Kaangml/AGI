#!/usr/bin/env python3
"""
Matematik verilerini birleştir ve train/val olarak böl
"""

import json
import random
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "training" / "math"

def load_jsonl(filepath: Path) -> list:
    """JSONL dosyasını yükle"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def save_jsonl(data: list, filepath: Path):
    """JSONL olarak kaydet"""
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def main():
    print("=" * 50)
    print("🧮 Matematik Veri Seti Hazırlayıcı")
    print("=" * 50)
    
    # 1. Verileri yükle
    all_data = []
    
    # GSM8K train
    gsm8k_train = DATA_DIR / "gsm8k_train.jsonl"
    if gsm8k_train.exists():
        data = load_jsonl(gsm8k_train)
        print(f"📥 GSM8K train: {len(data)} örnek")
        all_data.extend(data)
    
    # Turkish math
    turkish_math = DATA_DIR / "turkish_math.jsonl"
    if turkish_math.exists():
        data = load_jsonl(turkish_math)
        print(f"📥 Turkish math: {len(data)} örnek")
        all_data.extend(data)
    
    print(f"\n📊 Toplam: {len(all_data)} örnek")
    
    # 2. Karıştır
    random.seed(42)
    random.shuffle(all_data)
    
    # 3. Train/Val split (%90/%10)
    split_idx = int(len(all_data) * 0.9)
    train_data = all_data[:split_idx]
    val_data = all_data[split_idx:]
    
    print(f"\n📈 Bölme:")
    print(f"  - Train: {len(train_data)} örnek")
    print(f"  - Val: {len(val_data)} örnek")
    
    # 4. Kaydet
    save_jsonl(train_data, DATA_DIR / "math_combined_train.jsonl")
    save_jsonl(val_data, DATA_DIR / "math_combined_val.jsonl")
    
    print(f"\n💾 Kaydedildi:")
    print(f"  - {DATA_DIR / 'math_combined_train.jsonl'}")
    print(f"  - {DATA_DIR / 'math_combined_val.jsonl'}")
    
    print("\n✅ Tamamlandı!")

if __name__ == "__main__":
    main()
