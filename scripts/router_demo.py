#!/usr/bin/env python3
"""
EVO-TR Router Demo

Kullanıcıdan alınan mesajları router ile sınıflandırır ve
hangi adaptere yönlendirileceğini gösterir.
"""

import sys
from pathlib import Path

# Proje kökünü ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.router.classifier import get_classifier

console = Console()


def print_result(result: dict, text: str):
    """Sonucu güzel formatta yazdır"""
    # Ana sonuç
    intent = result["intent"]
    confidence = result["confidence"]
    adapter = result["adapter_id"]
    
    # Renk seçimi
    if confidence >= 0.7:
        conf_color = "green"
    elif confidence >= 0.5:
        conf_color = "yellow"
    else:
        conf_color = "red"
    
    console.print(f"\n[bold]📝 Girdi:[/bold] \"{text}\"")
    console.print(f"   [bold cyan]🎯 Intent:[/bold cyan] {intent}")
    console.print(f"   [bold {conf_color}]📊 Confidence:[/bold {conf_color}] {confidence:.3f}")
    console.print(f"   [bold magenta]🔧 Adapter:[/bold magenta] {adapter}")
    
    # Tüm skorlar tablosu
    if result.get("all_scores"):
        table = Table(title="Tüm Skorlar", show_header=True)
        table.add_column("Intent", style="cyan")
        table.add_column("Skor", style="green", justify="right")
        
        sorted_scores = sorted(result["all_scores"].items(), key=lambda x: x[1], reverse=True)
        for intent, score in sorted_scores:
            marker = " ←" if intent == result["intent"] else ""
            table.add_row(f"{intent}{marker}", f"{score:.4f}")
        
        console.print(table)


def demo():
    """İnteraktif demo"""
    console.print(Panel.fit(
        "[bold blue]🧠 EVO-TR Router Demo[/bold blue]\n"
        "Mesaj yazın ve hangi adaptere yönlendirileceğini görün.\n"
        "[dim]Çıkmak için 'q' veya 'quit' yazın.[/dim]",
        border_style="blue"
    ))
    
    # Router'ı başlat
    console.print("\n[dim]Router yükleniyor...[/dim]")
    classifier = get_classifier()
    
    stats = classifier.get_stats()
    console.print(f"[green]✅ Router hazır! {stats['total_intents']} kategori, {stats['total_samples']} örnek[/green]\n")
    
    # Demo örnekleri
    console.print("[bold]📋 Örnek mesajlar:[/bold]")
    examples = [
        "Merhaba, nasılsın?",
        "Python ile HTTP isteği nasıl atılır?",
        "TypeError hatası alıyorum",
        "Bu atasözünün anlamı ne?",
        "Dün ne konuştuk?",
    ]
    for ex in examples:
        console.print(f"   • {ex}")
    
    console.print("\n" + "="*60 + "\n")
    
    while True:
        try:
            text = console.input("[bold green]>>> [/bold green]").strip()
            
            if not text:
                continue
            
            if text.lower() in ["q", "quit", "exit", "çık"]:
                console.print("[dim]Görüşürüz! 👋[/dim]")
                break
            
            result = classifier.predict(text)
            print_result(result, text)
            
        except KeyboardInterrupt:
            console.print("\n[dim]Görüşürüz! 👋[/dim]")
            break
        except Exception as e:
            console.print(f"[red]Hata: {e}[/red]")


if __name__ == "__main__":
    demo()
