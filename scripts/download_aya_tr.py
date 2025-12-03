#!/usr/bin/env python3
"""
EVO-TR: Aya Dataset Türkçe Subset İndirme

Cohere'ın Aya multilingual instruction dataset'inden
Türkçe örnekleri filtreler ve Alpaca formatında kaydeder.
"""

from datasets import load_dataset
from pathlib import Path
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
OUTPUT_DIR = Path("data/training/aya_tr")


def main():
    console.print("\n[bold blue]📥 Aya Dataset (Türkçe) İndirici[/bold blue]\n")
    
    # Çıktı dizinini oluştur
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Dataset'i yükle
        task = progress.add_task("Aya Dataset yükleniyor...", total=None)
        
        try:
            dataset = load_dataset("CohereForAI/aya_dataset", trust_remote_code=True)
            progress.update(task, description="✅ Dataset yüklendi")
        except Exception as e:
            console.print(f"[red]❌ Dataset yüklenemedi: {e}[/red]")
            return
        
        # Bilgi göster
        console.print(f"\n📊 Dataset yapısı:")
        console.print(f"   Splits: {list(dataset.keys())}")
        
        if "train" in dataset:
            console.print(f"   Train: {len(dataset['train'])} örnek")
            console.print(f"   Sütunlar: {dataset['train'].column_names}")
    
    # Türkçe filtrele
    console.print("\n🔍 Türkçe örnekler filtreleniyor...")
    
    tr_samples = []
    total = len(dataset["train"])
    
    with Progress() as progress:
        task = progress.add_task("Filtreleniyor...", total=total)
        
        for item in dataset["train"]:
            progress.advance(task)
            
            # Language alanını kontrol et
            lang = item.get("language", "").lower()
            lang_code = item.get("language_code", "").lower()
            
            if "turkish" in lang or "tr" in lang_code or lang == "tr":
                # Alpaca formatına dönüştür
                instruction = item.get("inputs", "")
                output = item.get("targets", "")
                
                if instruction and output:
                    tr_samples.append({
                        "instruction": instruction.strip(),
                        "input": "",
                        "output": output.strip()
                    })
    
    console.print(f"\n✅ Türkçe örnek sayısı: [green]{len(tr_samples)}[/green]")
    
    if len(tr_samples) == 0:
        console.print("[yellow]⚠️ Türkçe örnek bulunamadı. Dataset yapısı kontrol ediliyor...[/yellow]")
        
        # İlk 5 örneği göster
        console.print("\n📋 İlk 5 örnek:")
        for i, item in enumerate(dataset["train"].select(range(min(5, len(dataset["train"]))))):
            console.print(f"\n--- Örnek {i+1} ---")
            console.print(item)
        
        # Dil dağılımını göster
        console.print("\n🌍 Dil dağılımı (ilk 1000):")
        from collections import Counter
        
        languages = []
        for item in dataset["train"].select(range(min(1000, len(dataset["train"])))):
            lang = item.get("language", "unknown")
            languages.append(lang)
        
        for lang, count in Counter(languages).most_common(20):
            console.print(f"   {lang}: {count}")
        
        return
    
    # JSONL olarak kaydet
    output_file = OUTPUT_DIR / "aya_tr.jsonl"
    
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in tr_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    # İstatistikler
    file_size_mb = output_file.stat().st_size / 1024 / 1024
    
    console.print(f"\n💾 [green]Kaydedildi:[/green] {output_file}")
    console.print(f"📊 Dosya boyutu: {file_size_mb:.2f} MB")
    
    # Örnek göster
    console.print(f"\n📋 [yellow]Örnek veri (ilk 3):[/yellow]")
    for i, sample in enumerate(tr_samples[:3]):
        console.print(f"\n[cyan]--- Örnek {i+1} ---[/cyan]")
        console.print(f"[bold]Instruction:[/bold] {sample['instruction'][:100]}...")
        console.print(f"[bold]Output:[/bold] {sample['output'][:100]}...")
    
    console.print(f"\n✅ [bold green]İndirme tamamlandı![/bold green]")


if __name__ == "__main__":
    main()
