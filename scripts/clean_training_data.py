#!/usr/bin/env python3
"""
EVO-TR: Eğitim Verisi Temizleme ve Birleştirme

Aya dataset ve manuel verileri temizler, birleştirir.
"""

import json
import re
from pathlib import Path
from typing import List, Dict
from collections import Counter
from rich.console import Console
from rich.table import Table

console = Console()

INPUT_DIRS = [
    Path("data/training/aya_tr"),
    Path("data/training/manual_tr"),
]
OUTPUT_FILE = Path("data/training/tr_chat_combined.jsonl")


def clean_text(text: str) -> str:
    """Metni temizle"""
    if not text:
        return ""
    # Fazla boşlukları kaldır
    text = re.sub(r'\s+', ' ', text)
    # Başta ve sondaki boşlukları kaldır
    text = text.strip()
    return text


def is_valid_sample(sample: Dict) -> bool:
    """Örneğin geçerli olup olmadığını kontrol et"""
    instruction = sample.get("instruction", "")
    output = sample.get("output", "")
    
    # Boş kontrolleri
    if not instruction or not output:
        return False
    
    # Minimum uzunluk
    if len(instruction) < 3 or len(output) < 5:
        return False
    
    # Maximum uzunluk (token limiti için)
    if len(instruction) > 2000 or len(output) > 4000:
        return False
    
    return True


def remove_duplicates(samples: List[Dict]) -> List[Dict]:
    """Duplicate'ları kaldır"""
    seen = set()
    unique = []
    
    for sample in samples:
        key = (sample["instruction"].lower().strip(), sample["output"].lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(sample)
    
    return unique


def main():
    console.print("\n[bold blue]🧹 Eğitim Verisi Temizleme ve Birleştirme[/bold blue]\n")
    
    all_samples = []
    source_counts = {}
    
    for input_dir in INPUT_DIRS:
        if not input_dir.exists():
            console.print(f"[yellow]⚠️ Dizin bulunamadı: {input_dir}[/yellow]")
            continue
        
        dir_count = 0
        for file in input_dir.glob("*.jsonl"):
            console.print(f"📖 Okunuyor: [cyan]{file}[/cyan]")
            file_count = 0
            
            with open(file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        sample = json.loads(line)
                        sample["instruction"] = clean_text(sample.get("instruction", ""))
                        sample["input"] = clean_text(sample.get("input", ""))
                        sample["output"] = clean_text(sample.get("output", ""))
                        
                        if is_valid_sample(sample):
                            all_samples.append(sample)
                            file_count += 1
                    except json.JSONDecodeError as e:
                        console.print(f"[red]   ❌ JSON hatası (satır {line_num}): {e}[/red]")
                        continue
            
            console.print(f"   ✅ {file_count} geçerli örnek")
            dir_count += file_count
        
        source_counts[input_dir.name] = dir_count
    
    console.print(f"\n📊 [bold]Toplam örnek (temizleme öncesi):[/bold] {len(all_samples)}")
    
    # Kaynak dağılımı
    table = Table(title="Kaynak Dağılımı")
    table.add_column("Kaynak", style="cyan")
    table.add_column("Örnek Sayısı", style="green")
    
    for source, count in source_counts.items():
        table.add_row(source, str(count))
    console.print(table)
    
    # Duplicate kaldır
    original_count = len(all_samples)
    all_samples = remove_duplicates(all_samples)
    removed_count = original_count - len(all_samples)
    console.print(f"\n🔄 Kaldırılan duplicate: {removed_count}")
    console.print(f"📊 [bold]Toplam örnek (duplicate sonrası):[/bold] {len(all_samples)}")
    
    # Kaydet
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for sample in all_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    file_size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
    console.print(f"\n💾 [green]Kaydedildi:[/green] {OUTPUT_FILE}")
    console.print(f"📊 Dosya boyutu: {file_size_mb:.2f} MB")
    
    # İstatistikler
    if all_samples:
        instruction_lengths = [len(s["instruction"]) for s in all_samples]
        output_lengths = [len(s["output"]) for s in all_samples]
        
        stats_table = Table(title="Veri İstatistikleri")
        stats_table.add_column("Metrik", style="cyan")
        stats_table.add_column("Değer", style="green")
        
        stats_table.add_row("Instruction Min", str(min(instruction_lengths)))
        stats_table.add_row("Instruction Max", str(max(instruction_lengths)))
        stats_table.add_row("Instruction Ortalama", f"{sum(instruction_lengths)/len(instruction_lengths):.0f}")
        stats_table.add_row("Output Min", str(min(output_lengths)))
        stats_table.add_row("Output Max", str(max(output_lengths)))
        stats_table.add_row("Output Ortalama", f"{sum(output_lengths)/len(output_lengths):.0f}")
        
        console.print(stats_table)
    
    console.print(f"\n✅ [bold green]Temizleme tamamlandı![/bold green]")


if __name__ == "__main__":
    main()
