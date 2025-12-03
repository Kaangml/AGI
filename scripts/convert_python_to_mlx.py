#!/usr/bin/env python3
"""
Python Kod Verisini MLX Training Formatına Dönüştürme
FAZ 3: Python Uzman LoRA için format dönüşümü

Giriş: python_coder_combined.jsonl (instruction-input-output format)
Çıkış: train.jsonl, valid.jsonl (MLX chat format)

MLX Chat Format:
{
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ]
}
"""

import json
import random
from pathlib import Path
from typing import List, Dict
import hashlib

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "training"
INPUT_FILE = DATA_DIR / "python_coder_combined.jsonl"
OUTPUT_DIR = DATA_DIR / "python_coder_mlx"

# Config
TRAIN_RATIO = 0.9  # %90 train, %10 validation
RANDOM_SEED = 42

# System prompts (çeşitlilik için rotation)
SYSTEM_PROMPTS = [
    "Sen deneyimli bir Python geliştiricisisin. Temiz, okunabilir ve iyi belgelenmiş kod yazarsın.",
    "Sen uzman bir Python programcısısın. Best practice'lere uygun, verimli kod üretirsin.",
    "Sen bir Python kod asistanısın. Kullanıcının isteklerini Python kodu ile çözersin.",
    "Sen senior bir Python mühendisisin. Modern Python standartlarına uygun kod yazarsın.",
    "Sen bir Python tutorüsün. Açıklayıcı yorumlarla birlikte kod örnekleri verirsin.",
    "You are an expert Python developer. You write clean, efficient, and well-documented code.",
    "You are a Python programming assistant. You help users with Python coding tasks."
]


def load_jsonl(file_path: Path) -> List[Dict]:
    """JSONL dosyasını yükle."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def get_system_prompt(index: int) -> str:
    """Index'e göre system prompt döndür (deterministic)."""
    return SYSTEM_PROMPTS[index % len(SYSTEM_PROMPTS)]


def convert_to_mlx_chat(item: Dict, index: int) -> Dict:
    """Instruction formatını MLX chat formatına dönüştür."""
    instruction = item.get('instruction', '')
    input_text = item.get('input', '')
    output = item.get('output', '')
    
    # User message oluştur
    if input_text:
        user_content = f"{instruction}\n\n{input_text}"
    else:
        user_content = instruction
    
    # System prompt seç
    system_prompt = get_system_prompt(index)
    
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": output}
        ]
    }


def split_train_valid(data: List[Dict], train_ratio: float = 0.9, seed: int = 42) -> tuple:
    """Veriyi train ve validation olarak böl."""
    random.seed(seed)
    
    # Karıştır
    shuffled = data.copy()
    random.shuffle(shuffled)
    
    # Böl
    split_index = int(len(shuffled) * train_ratio)
    train_data = shuffled[:split_index]
    valid_data = shuffled[split_index:]
    
    return train_data, valid_data


def save_jsonl(data: List[Dict], file_path: Path):
    """JSONL olarak kaydet."""
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def analyze_data(data: List[Dict]) -> Dict:
    """Veri setini analiz et."""
    stats = {
        'total': len(data),
        'avg_user_len': 0,
        'avg_assistant_len': 0,
        'max_user_len': 0,
        'max_assistant_len': 0,
        'min_user_len': float('inf'),
        'min_assistant_len': float('inf')
    }
    
    user_lens = []
    assistant_lens = []
    
    for item in data:
        messages = item.get('messages', [])
        for msg in messages:
            if msg['role'] == 'user':
                length = len(msg['content'])
                user_lens.append(length)
                stats['max_user_len'] = max(stats['max_user_len'], length)
                stats['min_user_len'] = min(stats['min_user_len'], length)
            elif msg['role'] == 'assistant':
                length = len(msg['content'])
                assistant_lens.append(length)
                stats['max_assistant_len'] = max(stats['max_assistant_len'], length)
                stats['min_assistant_len'] = min(stats['min_assistant_len'], length)
    
    if user_lens:
        stats['avg_user_len'] = sum(user_lens) / len(user_lens)
    if assistant_lens:
        stats['avg_assistant_len'] = sum(assistant_lens) / len(assistant_lens)
    
    return stats


def main():
    print("=" * 60)
    print("🔄 Python Kod Verisi MLX Format Dönüşümü")
    print("=" * 60 + "\n")
    
    # Veriyi yükle
    print(f"📂 Yükleniyor: {INPUT_FILE}")
    raw_data = load_jsonl(INPUT_FILE)
    print(f"   → {len(raw_data)} örnek yüklendi\n")
    
    # MLX formatına dönüştür
    print("🔄 MLX chat formatına dönüştürülüyor...")
    mlx_data = []
    for i, item in enumerate(raw_data):
        mlx_data.append(convert_to_mlx_chat(item, i))
    print(f"   → {len(mlx_data)} örnek dönüştürüldü\n")
    
    # Train/Valid böl
    print(f"✂️ Train/Valid bölünüyor (ratio: {TRAIN_RATIO})...")
    train_data, valid_data = split_train_valid(mlx_data, TRAIN_RATIO, RANDOM_SEED)
    print(f"   → Train: {len(train_data)} örnek")
    print(f"   → Valid: {len(valid_data)} örnek\n")
    
    # Klasör oluştur
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Kaydet
    train_path = OUTPUT_DIR / "train.jsonl"
    valid_path = OUTPUT_DIR / "valid.jsonl"
    
    save_jsonl(train_data, train_path)
    save_jsonl(valid_data, valid_path)
    
    print(f"💾 Kaydedildi:")
    print(f"   → {train_path}")
    print(f"   → {valid_path}\n")
    
    # Analiz
    print("📊 Train Set Analizi:")
    train_stats = analyze_data(train_data)
    print(f"   Toplam: {train_stats['total']}")
    print(f"   User avg/min/max: {train_stats['avg_user_len']:.0f}/{train_stats['min_user_len']}/{train_stats['max_user_len']}")
    print(f"   Assistant avg/min/max: {train_stats['avg_assistant_len']:.0f}/{train_stats['min_assistant_len']}/{train_stats['max_assistant_len']}")
    
    print("\n📊 Valid Set Analizi:")
    valid_stats = analyze_data(valid_data)
    print(f"   Toplam: {valid_stats['total']}")
    print(f"   User avg/min/max: {valid_stats['avg_user_len']:.0f}/{valid_stats['min_user_len']}/{valid_stats['max_user_len']}")
    print(f"   Assistant avg/min/max: {valid_stats['avg_assistant_len']:.0f}/{valid_stats['min_assistant_len']}/{valid_stats['max_assistant_len']}")
    
    # Örnek göster
    print("\n" + "-" * 60)
    print("📝 Örnek Dönüşüm (ilk örnek):")
    print("-" * 60)
    if mlx_data:
        example = mlx_data[0]
        for msg in example['messages']:
            role = msg['role'].upper()
            content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
            print(f"\n[{role}]")
            print(content)
    
    print("\n" + "=" * 60)
    print("🎉 Dönüşüm tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    main()
