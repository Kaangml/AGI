#!/usr/bin/env python3
"""Intent veri setini sample dosyalarından oluşturur."""

import json
import os
from datetime import datetime
from pathlib import Path

def load_samples(samples_dir: str) -> dict:
    """Her sample dosyasından örnekleri yükler."""
    intents = []
    samples_path = Path(samples_dir)
    
    intent_mapping = {
        "general_chat.txt": "general_chat",
        "turkish_culture.txt": "turkish_culture",
        "code_python.txt": "code_python",
        "code_debug.txt": "code_debug",
        "code_explain.txt": "code_explain",
        "code_math.json": "code_math",
        "memory_recall.txt": "memory_recall",
        "general_knowledge.txt": "general_knowledge"
    }
    
    for filename, intent in intent_mapping.items():
        filepath = samples_path / filename
        if filepath.exists():
            if filename.endswith('.json'):
                # JSON formatı
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        intents.append({
                            "text": item["text"],
                            "intent": item["intent"],
                            "language": "tr"
                        })
                print(f"✅ {filename}: {len(data)} örnek yüklendi")
            else:
                # TXT formatı
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()]
                    for text in lines:
                        intents.append({
                            "text": text,
                            "intent": intent,
                            "language": "tr"
                        })
                print(f"✅ {filename}: {len(lines)} örnek yüklendi")
        else:
            print(f"⚠️ {filename} bulunamadı")
    
    return intents

def create_dataset(samples_dir: str, output_file: str):
    """Ana dataset dosyasını oluşturur."""
    intents = load_samples(samples_dir)
    
    dataset = {
        "version": "1.0",
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "total_samples": len(intents),
        "intent_distribution": {},
        "intents": intents
    }
    
    # Intent dağılımını hesapla
    for intent in intents:
        intent_type = intent["intent"]
        dataset["intent_distribution"][intent_type] = \
            dataset["intent_distribution"].get(intent_type, 0) + 1
    
    # JSON olarak kaydet
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 Dataset oluşturuldu: {output_file}")
    print(f"   Toplam örnek: {len(intents)}")
    print(f"   Intent dağılımı:")
    for intent, count in sorted(dataset["intent_distribution"].items()):
        print(f"     - {intent}: {count}")

if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent
    samples_dir = base_dir / "data" / "intents" / "samples"
    output_file = base_dir / "data" / "intents" / "intent_dataset.json"
    
    create_dataset(str(samples_dir), str(output_file))
