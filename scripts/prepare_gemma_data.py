"""
EVO-TR V2: Gemma Verilerini Eğitime Hazırla
=============================================
Gemma 3 27B ile üretilen verileri mevcut verilerle birleştir ve train/val olarak böl.
"""

import json
import random
from pathlib import Path
from datetime import datetime


def load_jsonl(filepath: Path) -> list:
    """JSONL dosyasını yükle."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def save_jsonl(data: list, filepath: Path):
    """JSONL dosyasına kaydet."""
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"   Kaydedildi: {filepath} ({len(data)} örnek)")


def split_data(data: list, val_ratio: float = 0.1) -> tuple:
    """Veriyi train/val olarak böl."""
    random.shuffle(data)
    val_size = int(len(data) * val_ratio)
    return data[val_size:], data[:val_size]


def prepare_turkish_chat():
    """Türkçe sohbet verilerini hazırla."""
    print("\n📚 Türkçe Sohbet Verileri Hazırlanıyor...")
    
    # Yeni Gemma verileri
    gemma_files = list(Path("data/generated/turkish_chat").glob("turkish_chat_*.jsonl"))
    gemma_files = [f for f in gemma_files if "checkpoint" not in f.name]
    
    new_data = []
    for f in gemma_files:
        new_data.extend(load_jsonl(f))
    print(f"   Yeni Gemma verisi: {len(new_data)} örnek")
    
    # Mevcut veriler
    existing_file = Path("data/training/tr_chat_combined.jsonl")
    if existing_file.exists():
        existing_data = load_jsonl(existing_file)
        print(f"   Mevcut veri: {len(existing_data)} örnek")
    else:
        existing_data = []
    
    # Birleştir
    all_data = existing_data + new_data
    print(f"   Toplam: {len(all_data)} örnek")
    
    # Train/Val böl
    train_data, val_data = split_data(all_data, val_ratio=0.1)
    print(f"   Train: {len(train_data)}, Val: {len(val_data)}")
    
    # Kaydet
    output_dir = Path("data/training")
    save_jsonl(all_data, output_dir / "tr_chat_combined_v2.jsonl")
    save_jsonl(train_data, output_dir / "tr_chat_train_v2.jsonl")
    save_jsonl(val_data, output_dir / "tr_chat_val_v2.jsonl")
    
    return len(train_data), len(val_data)


def prepare_python_code():
    """Python kod verilerini hazırla."""
    print("\n🐍 Python Kod Verileri Hazırlanıyor...")
    
    # Yeni Gemma verileri
    gemma_files = list(Path("data/generated/python_code").glob("python_code_*.jsonl"))
    gemma_files = [f for f in gemma_files if "checkpoint" not in f.name]
    
    new_data = []
    for f in gemma_files:
        new_data.extend(load_jsonl(f))
    print(f"   Yeni Gemma verisi: {len(new_data)} örnek")
    
    # Mevcut veriler
    existing_file = Path("data/training/python_coder_combined.jsonl")
    if existing_file.exists():
        existing_data = load_jsonl(existing_file)
        print(f"   Mevcut veri: {len(existing_data)} örnek")
    else:
        existing_data = []
    
    # Birleştir
    all_data = existing_data + new_data
    print(f"   Toplam: {len(all_data)} örnek")
    
    # Train/Val böl
    train_data, val_data = split_data(all_data, val_ratio=0.1)
    print(f"   Train: {len(train_data)}, Val: {len(val_data)}")
    
    # Kaydet
    output_dir = Path("data/training")
    save_jsonl(all_data, output_dir / "python_coder_combined_v2.jsonl")
    save_jsonl(train_data, output_dir / "python_coder_train_v2.jsonl")
    save_jsonl(val_data, output_dir / "python_coder_val_v2.jsonl")
    
    return len(train_data), len(val_data)


def main():
    print("=" * 50)
    print("EVO-TR V2: Veri Hazırlama")
    print("=" * 50)
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    random.seed(42)  # Reproducibility
    
    # Türkçe sohbet
    tr_train, tr_val = prepare_turkish_chat()
    
    # Python kod
    py_train, py_val = prepare_python_code()
    
    print("\n" + "=" * 50)
    print("📊 Özet")
    print("=" * 50)
    print(f"   Türkçe Sohbet: {tr_train} train + {tr_val} val")
    print(f"   Python Kod: {py_train} train + {py_val} val")
    print(f"   Toplam: {tr_train + py_train} train + {tr_val + py_val} val")
    print("\n✅ Veri hazırlama tamamlandı!")
    print("\nSonraki adım: LoRA eğitimi")
    print("   python -m mlx_lm.lora --config configs/lora_tr_config_v2.yaml")


if __name__ == "__main__":
    main()
