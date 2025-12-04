#!/usr/bin/env python3
"""
GSM8K Dataset Downloader
Grade School Math 8K - Matematik problemi veri seti

Bu script:
1. GSM8K veri setini indirir
2. Türkçe'ye çevirir (temel seviye)
3. MLX LoRA eğitimine uygun formata dönüştürür
"""

import json
import os
from pathlib import Path
from datasets import load_dataset

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "training" / "math"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_gsm8k():
    """GSM8K veri setini indir"""
    print("📥 GSM8K veri seti indiriliyor...")
    
    dataset = load_dataset("openai/gsm8k", "main")
    
    train_data = dataset["train"]
    test_data = dataset["test"]
    
    print(f"✅ Train: {len(train_data)} örnek")
    print(f"✅ Test: {len(test_data)} örnek")
    
    return train_data, test_data


def format_answer(answer_text: str) -> tuple[str, str]:
    """
    GSM8K cevabını parçala
    Returns: (solution_steps, final_answer)
    """
    # #### işaretinden sonrası final cevap
    if "####" in answer_text:
        parts = answer_text.split("####")
        solution = parts[0].strip()
        final = parts[1].strip()
        return solution, final
    return answer_text, ""


def create_math_prompt(question: str, solution: str, final_answer: str) -> dict:
    """MLX LoRA formatında matematik promptu oluştur"""
    
    system_msg = "Sen matematik problemlerini adım adım çözen bir asistansın. Her adımı açıkça göster ve sonucu ver."
    
    user_msg = f"Bu matematik problemini çöz:\n\n{question}"
    
    assistant_msg = f"{solution}\n\nSonuç: {final_answer}"
    
    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg}
        ]
    }


def save_dataset(data: list, filename: str):
    """JSONL formatında kaydet"""
    filepath = DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"💾 Kaydedildi: {filepath} ({len(data)} örnek)")


def main():
    print("=" * 50)
    print("🧮 GSM8K Matematik Veri Seti Hazırlayıcı")
    print("=" * 50)
    
    # 1. İndir
    train_data, test_data = download_gsm8k()
    
    # 2. Format dönüşümü
    print("\n🔄 Format dönüşümü yapılıyor...")
    
    train_formatted = []
    for item in train_data:
        solution, final = format_answer(item["answer"])
        formatted = create_math_prompt(item["question"], solution, final)
        train_formatted.append(formatted)
    
    test_formatted = []
    for item in test_data:
        solution, final = format_answer(item["answer"])
        formatted = create_math_prompt(item["question"], solution, final)
        test_formatted.append(formatted)
    
    # 3. Kaydet
    print("\n💾 Kaydediliyor...")
    save_dataset(train_formatted, "gsm8k_train.jsonl")
    save_dataset(test_formatted, "gsm8k_test.jsonl")
    
    # 4. İstatistikler
    print("\n📊 İstatistikler:")
    print(f"  - Train: {len(train_formatted)} örnek")
    print(f"  - Test: {len(test_formatted)} örnek")
    print(f"  - Toplam: {len(train_formatted) + len(test_formatted)} örnek")
    
    # 5. Örnek göster
    print("\n📝 Örnek veri:")
    sample = train_formatted[0]
    print(f"  Question: {sample['messages'][1]['content'][:100]}...")
    print(f"  Answer: {sample['messages'][2]['content'][:100]}...")
    
    print("\n✅ Tamamlandı!")


if __name__ == "__main__":
    main()
