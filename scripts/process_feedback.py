#!/usr/bin/env python3
"""
EVO-TR: Feedback İşleme ve Lifecycle Başlatıcı

Bu script feedback veritabanındaki verileri analiz eder ve
gerektiğinde incremental training başlatır.

Kullanım:
    python scripts/process_feedback.py --analyze    # Sadece analiz
    python scripts/process_feedback.py --train      # Eğitim başlat
    python scripts/process_feedback.py --stats      # İstatistikler
"""

import sys
sys.path.insert(0, ".")

import argparse
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table

from src.lifecycle.feedback import FeedbackDatabase
from src.lifecycle.preference_learning import PreferenceCollector, PreferenceLearningPipeline


console = Console()


def show_stats():
    """Feedback istatistiklerini göster."""
    db = FeedbackDatabase("./data/feedback.db")
    
    # Genel istatistikler
    stats = db.get_stats()
    
    table = Table(title="📊 Feedback İstatistikleri")
    table.add_column("Metrik", style="cyan")
    table.add_column("Değer", style="white")
    
    table.add_row("Toplam Feedback", str(stats.get("total", 0)))
    table.add_row("👍 Pozitif (thumbs_up)", str(stats.get("thumbs_up", 0)))
    table.add_row("👎 Negatif (thumbs_down)", str(stats.get("thumbs_down", 0)))
    table.add_row("✏️ Düzeltme (edit)", str(stats.get("edit", 0)))
    table.add_row("İşlenmemiş", str(stats.get("unprocessed", 0)))
    table.add_row("Eğitimde Kullanılmayan", str(stats.get("unused_for_training", 0)))
    
    console.print(table)
    
    # Düzeltmeleri göster
    corrections = db.get_corrected_responses(limit=10)
    if corrections:
        console.print(f"\n[green]✏️ Son {len(corrections)} Düzeltme:[/green]")
        for i, entry in enumerate(corrections, 1):
            console.print(f"\n[dim]{i}. {entry.timestamp}[/dim] [{entry.adapter_used}]")
            console.print(f"   [cyan]Soru:[/cyan] {entry.user_message[:80]}...")
            console.print(f"   [red]Yanlış:[/red] {entry.assistant_response[:80]}...")
            console.print(f"   [green]Doğru:[/green] {entry.corrected_response[:80]}...")


def analyze_feedback():
    """Feedback'leri analiz et ve eğitim için hazır olanları göster."""
    db = FeedbackDatabase("./data/feedback.db")
    
    # Düzeltilmiş yanıtlar (en değerli)
    corrections = db.get_corrected_responses(limit=100)
    console.print(f"\n[green]✏️ Eğitime Hazır Düzeltme: {len(corrections)} adet[/green]")
    
    # Negatif feedback'ler
    negatives = db.get_negative_feedback(limit=100)
    console.print(f"[yellow]👎 Negatif Feedback: {len(negatives)} adet[/yellow]")
    
    # İşlenmemiş feedback'ler
    unprocessed = db.get_unprocessed_feedback(limit=100)
    console.print(f"[cyan]📋 İşlenmemiş: {len(unprocessed)} adet[/cyan]")
    
    # Eğitim için yeterli veri var mı?
    min_corrections_for_training = 10
    if len(corrections) >= min_corrections_for_training:
        console.print(f"\n[bold green]✅ Yeterli düzeltme var! Eğitim başlatılabilir.[/bold green]")
        console.print(f"[dim]   Komut: python scripts/process_feedback.py --train[/dim]")
    else:
        needed = min_corrections_for_training - len(corrections)
        console.print(f"\n[yellow]⚠️ Eğitim için {needed} düzeltme daha gerekli.[/yellow]")
        console.print(f"[dim]   CLI'da /correct komutu ile düzeltme yapabilirsiniz.[/dim]")
    
    return {
        "corrections": len(corrections),
        "negatives": len(negatives),
        "unprocessed": len(unprocessed),
        "ready_for_training": len(corrections) >= min_corrections_for_training
    }


def prepare_training_data():
    """Feedback'lerden DPO eğitim verisi hazırla."""
    db = FeedbackDatabase("./data/feedback.db")
    collector = PreferenceCollector(storage_path="./data/preferences")
    
    # Düzeltmeleri al
    corrections = db.get_corrected_responses(limit=100)
    
    if not corrections:
        console.print("[yellow]⚠️ Düzeltilmiş yanıt bulunamadı.[/yellow]")
        return None
    
    console.print(f"[cyan]📋 {len(corrections)} düzeltme işleniyor...[/cyan]")
    
    # Preference pair'ler oluştur
    pairs = []
    for entry in corrections:
        pair = collector.create_from_feedback(
            prompt=entry.user_message,
            response=entry.assistant_response,
            feedback_type="edit",
            adapter=entry.adapter_used,
            corrected_response=entry.corrected_response
        )
        if pair:
            pairs.append(pair)
    
    console.print(f"[green]✅ {len(pairs)} preference pair oluşturuldu.[/green]")
    
    # DPO formatında kaydet
    if pairs:
        collector.save()
        dpo_data = collector.export_for_dpo()
        
        output_dir = Path("./data/training/dpo_from_feedback")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"dpo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            for item in dpo_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        console.print(f"[green]✅ DPO verisi kaydedildi: {output_file}[/green]")
        
        # Feedback'leri işlenmiş olarak işaretle
        feedback_ids = [entry.id for entry in corrections if entry.id]
        db.mark_as_used_for_training(feedback_ids)
        console.print(f"[dim]   {len(feedback_ids)} feedback eğitimde kullanıldı olarak işaretlendi.[/dim]")
        
        return output_file
    
    return None


def run_incremental_training(dpo_file: Path):
    """DPO verisi ile incremental training başlat."""
    console.print(f"\n[yellow]🚀 Incremental Training başlatılıyor...[/yellow]")
    console.print(f"[dim]   Veri: {dpo_file}[/dim]")
    
    # TODO: mlx_lm DPO training entegrasyonu
    # Şimdilik sadece mesaj yazdır
    console.print("[yellow]⚠️ DPO training henüz entegre edilmedi.[/yellow]")
    console.print("[dim]   Manuel olarak şu komutu çalıştırabilirsiniz:[/dim]")
    console.print(f"[dim]   mlx_lm.lora --data {dpo_file.parent} --model models/base/qwen-2.5-3b-instruct[/dim]")


def main():
    parser = argparse.ArgumentParser(description="EVO-TR Feedback İşleme")
    parser.add_argument("--stats", action="store_true", help="İstatistikleri göster")
    parser.add_argument("--analyze", action="store_true", help="Feedback'leri analiz et")
    parser.add_argument("--train", action="store_true", help="Eğitim verisi hazırla ve başlat")
    
    args = parser.parse_args()
    
    console.print("\n[bold blue]🔄 EVO-TR Feedback İşleyici[/bold blue]\n")
    
    if args.stats:
        show_stats()
    elif args.analyze:
        analyze_feedback()
    elif args.train:
        analysis = analyze_feedback()
        if analysis["ready_for_training"]:
            dpo_file = prepare_training_data()
            if dpo_file:
                run_incremental_training(dpo_file)
        else:
            console.print("[yellow]⚠️ Eğitim için yeterli veri yok.[/yellow]")
    else:
        # Varsayılan: stats + analyze
        show_stats()
        console.print()
        analyze_feedback()


if __name__ == "__main__":
    main()
