#!/usr/bin/env python3
"""EVO-TR Kurulum Doğrulama Script'i"""

import sys
import os
from rich.console import Console
from rich.table import Table

console = Console()

def check_import(module_name):
    try:
        __import__(module_name)
        return True, "✅"
    except ImportError as e:
        return False, f"❌ {e}"

def main():
    console.print("\n[bold blue]🔍 EVO-TR Kurulum Kontrolü[/bold blue]\n")
    
    table = Table(title="Bağımlılık Durumu")
    table.add_column("Modül", style="cyan")
    table.add_column("Durum", style="green")
    
    modules = [
        "mlx", "mlx_lm", "transformers", 
        "huggingface_hub", "chromadb", 
        "sentence_transformers", "dotenv"
    ]
    
    all_ok = True
    for mod in modules:
        ok, status = check_import(mod)
        table.add_row(mod, status)
        if not ok:
            all_ok = False
    
    console.print(table)
    
    # MLX Device Check
    try:
        import mlx.core as mx
        device = str(mx.default_device())
        console.print(f"\n[bold]MLX Device:[/bold] {device}")
        if "gpu" in device:
            console.print("[green]✅ Metal GPU aktif[/green]")
        else:
            console.print("[yellow]⚠️ CPU modunda çalışıyor[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ MLX Hatası: {e}[/red]")
    
    # .env Check
    if os.path.exists(".env"):
        console.print("\n[green]✅ .env dosyası mevcut[/green]")
        from dotenv import load_dotenv
        load_dotenv()
        if os.getenv("HF_TOKEN"):
            console.print("[green]✅ HF_TOKEN tanımlı[/green]")
        else:
            console.print("[red]❌ HF_TOKEN tanımlı değil[/red]")
            all_ok = False
    else:
        console.print("\n[red]❌ .env dosyası bulunamadı[/red]")
        all_ok = False
    
    # Model Check
    model_path = "./models/base/qwen-2.5-3b-instruct"
    if os.path.exists(model_path):
        # Model boyutunu kontrol et
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(model_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        size_gb = total_size / (1024**3)
        console.print(f"\n[green]✅ Base model mevcut: {model_path}[/green]")
        console.print(f"   Boyut: {size_gb:.2f} GB")
    else:
        console.print(f"\n[yellow]⚠️ Base model henüz indirilmemiş: {model_path}[/yellow]")
    
    # Final Status
    if all_ok:
        console.print("\n[bold green]🎉 Kurulum başarılı! Faz 1'e geçebilirsin.[/bold green]\n")
    else:
        console.print("\n[bold red]⚠️ Bazı sorunlar var. Yukarıdaki hataları düzelt.[/bold red]\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
