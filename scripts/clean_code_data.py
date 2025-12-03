#!/usr/bin/env python3
"""
Python Kod Verisi Temizleme ve Birleştirme Script'i
FAZ 3: Python Uzman LoRA için veri hazırlığı

Veri Kaynakları:
- HumanEval: 164 örnek
- MBPP: 964 örnek
- CodeAlpaca: 9208 örnek
- Code-Instructions: 5000 örnek
- Manuel: ~54 örnek

Temizlik İşlemleri:
1. Format standardizasyonu (instruction-input-output)
2. Duplikat temizleme
3. Çok kısa/uzun örnekleri filtreleme
4. Boş veya hatalı örnekleri çıkarma
5. Python odaklı olmayan örnekleri filtreleme
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "training"
PYTHON_CODE_DIR = DATA_DIR / "python_code"
MANUAL_PYTHON_DIR = DATA_DIR / "manual_python"
OUTPUT_FILE = DATA_DIR / "python_coder_combined.jsonl"

# Config
MIN_OUTPUT_LENGTH = 20  # Minimum output karakteri
MAX_OUTPUT_LENGTH = 4000  # Maximum output karakteri (token limiti için)
MIN_INSTRUCTION_LENGTH = 10  # Minimum instruction karakteri


def load_jsonl(file_path: Path) -> List[Dict]:
    """JSONL dosyasını yükle."""
    data = []
    if not file_path.exists():
        print(f"⚠️ Dosya bulunamadı: {file_path}")
        return data
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                data.append(item)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON hatası {file_path.name}:{i}: {e}")
    return data


def create_content_hash(item: Dict) -> str:
    """İçerik için unique hash oluştur (duplikat tespiti için)."""
    content = f"{item.get('instruction', '')}{item.get('output', '')}"
    return hashlib.md5(content.encode()).hexdigest()


def is_python_focused(item: Dict) -> bool:
    """Örneğin Python odaklı olup olmadığını kontrol et."""
    instruction = item.get('instruction', '').lower()
    output = item.get('output', '')
    
    # Python keywords ve patterns
    python_indicators = [
        'python', 'def ', 'class ', 'import ', 'from ', 
        'print(', 'return ', 'if __name__', 'lambda',
        'list', 'dict', 'tuple', 'set(', 'range(',
        '# ', 'self.', '__init__', 'async ', 'await ',
        '.py', 'pip ', 'venv', 'pytest', 'unittest'
    ]
    
    # Diğer diller (filtrelenecek)
    other_languages = [
        'javascript', 'java ', 'c++', 'c#', 'ruby', 
        'rust', 'go ', 'golang', 'swift', 'kotlin',
        'php', 'perl', 'scala', 'haskell', 'sql',
        'function()', 'console.log', 'System.out',
        'public static void', '#include', 'fn main'
    ]
    
    # Diğer dil varsa filtrele
    for lang in other_languages:
        if lang.lower() in instruction.lower() or lang.lower() in output.lower():
            # Ama "python vs javascript" gibi karşılaştırmalara izin ver
            if 'python' not in instruction.lower():
                return False
    
    # Python indicator varsa kabul et
    for indicator in python_indicators:
        if indicator in instruction.lower() or indicator in output:
            return True
    
    # Genel programlama sorusu da kabul (örn: "sort an array")
    programming_terms = [
        'algorithm', 'function', 'write a', 'create a', 
        'implement', 'code', 'program', 'write code'
    ]
    for term in programming_terms:
        if term in instruction.lower():
            return True
    
    return False


def clean_item(item: Dict) -> Dict:
    """Tek bir örneği temizle ve standardize et."""
    # Standart alanları çıkar
    instruction = item.get('instruction', item.get('prompt', item.get('question', ''))).strip()
    input_text = item.get('input', item.get('context', '')).strip()
    output = item.get('output', item.get('response', item.get('completion', item.get('answer', '')))).strip()
    
    # None değerleri string'e çevir
    instruction = instruction if instruction else ''
    input_text = input_text if input_text else ''
    output = output if output else ''
    
    return {
        'instruction': instruction,
        'input': input_text,
        'output': output
    }


def is_valid_item(item: Dict) -> bool:
    """Örneğin geçerli olup olmadığını kontrol et."""
    instruction = item.get('instruction', '')
    output = item.get('output', '')
    
    # Boş kontrol
    if not instruction or not output:
        return False
    
    # Uzunluk kontrolleri
    if len(instruction) < MIN_INSTRUCTION_LENGTH:
        return False
    
    if len(output) < MIN_OUTPUT_LENGTH:
        return False
    
    if len(output) > MAX_OUTPUT_LENGTH:
        return False
    
    # Çok kısa çıktılar (sadece "Yes", "No", sayı vb.)
    if len(output.split()) < 3 and not any(c in output for c in ['def ', 'class ', '=']):
        return False
    
    return True


def load_all_datasets() -> Dict[str, List[Dict]]:
    """Tüm veri setlerini yükle."""
    datasets = {}
    
    # HuggingFace datasets
    hf_files = {
        'humaneval': PYTHON_CODE_DIR / 'humaneval.jsonl',
        'mbpp': PYTHON_CODE_DIR / 'mbpp.jsonl',
        'code_alpaca': PYTHON_CODE_DIR / 'code_alpaca_python.jsonl',
        'code_instructions': PYTHON_CODE_DIR / 'code_instructions_python.jsonl',
    }
    
    for name, path in hf_files.items():
        print(f"📂 Yükleniyor: {name}...")
        datasets[name] = load_jsonl(path)
        print(f"   → {len(datasets[name])} örnek")
    
    # Manuel örnekler
    print(f"📂 Yükleniyor: manual_examples...")
    manual_data = []
    for jsonl_file in MANUAL_PYTHON_DIR.glob('*.jsonl'):
        manual_data.extend(load_jsonl(jsonl_file))
    datasets['manual'] = manual_data
    print(f"   → {len(datasets['manual'])} örnek")
    
    return datasets


def process_and_combine(datasets: Dict[str, List[Dict]]) -> List[Dict]:
    """Tüm verileri işle ve birleştir."""
    combined = []
    seen_hashes: Set[str] = set()
    
    stats = {
        'total_raw': 0,
        'invalid': 0,
        'duplicates': 0,
        'non_python': 0,
        'accepted': 0
    }
    
    for source, data in datasets.items():
        source_accepted = 0
        
        for item in data:
            stats['total_raw'] += 1
            
            # Temizle
            cleaned = clean_item(item)
            
            # Geçerlilik kontrol
            if not is_valid_item(cleaned):
                stats['invalid'] += 1
                continue
            
            # Python odaklı mı?
            if not is_python_focused(cleaned):
                stats['non_python'] += 1
                continue
            
            # Duplikat kontrol
            content_hash = create_content_hash(cleaned)
            if content_hash in seen_hashes:
                stats['duplicates'] += 1
                continue
            
            seen_hashes.add(content_hash)
            cleaned['source'] = source
            combined.append(cleaned)
            stats['accepted'] += 1
            source_accepted += 1
        
        print(f"✅ {source}: {source_accepted}/{len(data)} örnek kabul edildi")
    
    print("\n📊 İstatistikler:")
    print(f"   Ham toplam: {stats['total_raw']}")
    print(f"   Geçersiz: {stats['invalid']}")
    print(f"   Non-Python: {stats['non_python']}")
    print(f"   Duplikat: {stats['duplicates']}")
    print(f"   Kabul edilen: {stats['accepted']}")
    
    return combined


def save_combined(data: List[Dict], output_path: Path):
    """Birleştirilmiş veriyi kaydet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            # source alanını kaldır (training için gerekmez)
            save_item = {
                'instruction': item['instruction'],
                'input': item['input'],
                'output': item['output']
            }
            f.write(json.dumps(save_item, ensure_ascii=False) + '\n')
    
    print(f"\n💾 Kaydedildi: {output_path}")
    print(f"   Toplam: {len(data)} örnek")


def main():
    print("=" * 60)
    print("🐍 Python Kod Verisi Temizleme ve Birleştirme")
    print("=" * 60 + "\n")
    
    # Veri setlerini yükle
    datasets = load_all_datasets()
    
    print("\n" + "-" * 60)
    print("🔄 Veriler işleniyor ve birleştiriliyor...")
    print("-" * 60 + "\n")
    
    # İşle ve birleştir
    combined = process_and_combine(datasets)
    
    # Kaydet
    save_combined(combined, OUTPUT_FILE)
    
    # Kaynak dağılımı
    print("\n📈 Kaynak Dağılımı:")
    source_counts = {}
    for item in combined:
        source = item.get('source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        percentage = (count / len(combined)) * 100
        print(f"   {source}: {count} ({percentage:.1f}%)")
    
    print("\n" + "=" * 60)
    print("🎉 Tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    main()
