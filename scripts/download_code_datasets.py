#!/usr/bin/env python3
"""
EVO-TR: Python Kod Eğitim Veri Setlerini İndir

HumanEval, MBPP ve CodeAlpaca dataset'lerini indirir ve Alpaca formatına dönüştürür.
"""

from datasets import load_dataset
from pathlib import Path
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
OUTPUT_DIR = Path("data/training/python_code")


def download_humaneval():
    """HumanEval dataset'ini indir"""
    console.print("\n📥 [bold]HumanEval[/bold] indiriliyor...")
    
    try:
        dataset = load_dataset("openai_humaneval", trust_remote_code=True)
    except Exception as e:
        console.print(f"[yellow]⚠️ openai_humaneval bulunamadı, alternatif deneniyor...[/yellow]")
        try:
            dataset = load_dataset("openai/openai_humaneval", trust_remote_code=True)
        except:
            console.print(f"[red]❌ HumanEval indirilemedi: {e}[/red]")
            return 0
    
    samples = []
    for item in dataset["test"]:
        # Prompt zaten fonksiyon başlangıcını içeriyor
        prompt = item["prompt"]
        solution = item["canonical_solution"]
        
        samples.append({
            "instruction": f"Complete the following Python function:\n\n{prompt}",
            "input": "",
            "output": solution
        })
    
    output_file = OUTPUT_DIR / "humaneval.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    console.print(f"   ✅ HumanEval: {len(samples)} örnek -> {output_file}")
    return len(samples)


def download_mbpp():
    """MBPP dataset'ini indir"""
    console.print("\n📥 [bold]MBPP[/bold] indiriliyor...")
    
    try:
        dataset = load_dataset("google-research-datasets/mbpp", "full", trust_remote_code=True)
    except Exception as e:
        console.print(f"[red]❌ MBPP indirilemedi: {e}[/red]")
        return 0
    
    samples = []
    
    # Train ve test split'lerini birleştir
    for split in ["train", "test", "validation"]:
        if split not in dataset:
            continue
        
        for item in dataset[split]:
            instruction = item["text"]
            code = item["code"]
            
            # Test case'leri de ekle
            test_list = item.get("test_list", [])
            if test_list:
                tests = "\n".join(test_list[:3])  # İlk 3 test
                instruction = f"{instruction}\n\nExample test cases:\n{tests}"
            
            samples.append({
                "instruction": instruction,
                "input": "",
                "output": code
            })
    
    output_file = OUTPUT_DIR / "mbpp.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    console.print(f"   ✅ MBPP: {len(samples)} örnek -> {output_file}")
    return len(samples)


def download_code_alpaca():
    """CodeAlpaca dataset'ini indir (Python filtreli)"""
    console.print("\n📥 [bold]CodeAlpaca[/bold] indiriliyor...")
    
    try:
        dataset = load_dataset("sahil2801/CodeAlpaca-20k", trust_remote_code=True)
    except Exception as e:
        console.print(f"[red]❌ CodeAlpaca indirilemedi: {e}[/red]")
        return 0
    
    # Python filtre kelimeleri
    python_keywords = [
        "python", "def ", "class ", "import ", "print(", 
        "lambda", "list", "dict", "tuple", ".py", "pip install",
        "pandas", "numpy", "flask", "django", "pytest"
    ]
    
    samples = []
    total = 0
    
    for item in dataset["train"]:
        total += 1
        instruction = item.get("instruction", "").lower()
        output = item.get("output", "").lower()
        inp = item.get("input", "")
        
        # Python ile ilgili mi kontrol et
        is_python = any(kw in instruction or kw in output for kw in python_keywords)
        
        if is_python and len(output) > 50:
            samples.append({
                "instruction": item["instruction"],
                "input": inp if inp else "",
                "output": item["output"]
            })
    
    output_file = OUTPUT_DIR / "code_alpaca_python.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    console.print(f"   ✅ CodeAlpaca (Python): {len(samples)}/{total} örnek -> {output_file}")
    return len(samples)


def download_code_instructions():
    """Code-Instructions dataset'ini indir (ek kaynak)"""
    console.print("\n📥 [bold]Code-Instructions[/bold] deneniyor...")
    
    try:
        dataset = load_dataset("iamtarun/code_instructions_120k_alpaca", trust_remote_code=True)
    except Exception as e:
        console.print(f"[yellow]⚠️ Code-Instructions bulunamadı, atlanıyor[/yellow]")
        return 0
    
    python_keywords = ["python", "def ", "class ", "import ", "print("]
    samples = []
    
    for item in dataset["train"]:
        instruction = item.get("instruction", "").lower()
        output = item.get("output", "").lower()
        
        is_python = any(kw in instruction or kw in output for kw in python_keywords)
        
        if is_python and len(output) > 50:
            samples.append({
                "instruction": item["instruction"],
                "input": item.get("input", ""),
                "output": item["output"]
            })
        
        # Maksimum 5000 örnek al
        if len(samples) >= 5000:
            break
    
    if samples:
        output_file = OUTPUT_DIR / "code_instructions_python.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        
        console.print(f"   ✅ Code-Instructions (Python): {len(samples)} örnek -> {output_file}")
    
    return len(samples)


def main():
    console.print("\n[bold blue]🐍 Python Kod Dataset'leri İndirici[/bold blue]\n")
    
    # Çıktı dizinini oluştur
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total = 0
    
    # Dataset'leri indir
    total += download_humaneval()
    total += download_mbpp()
    total += download_code_alpaca()
    total += download_code_instructions()
    
    console.print(f"\n🎉 [bold green]Toplam: {total} Python kod örneği indirildi![/bold green]")
    console.print(f"📁 Konum: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
