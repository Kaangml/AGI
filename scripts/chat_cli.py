#!/usr/bin/env python3
"""
EVO-TR: Terminal Chat Interface

Interaktif terminal arayüzü.
"""

import sys
sys.path.insert(0, ".")

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
import re

from src.orchestrator import EvoTR


console = Console()


def print_banner():
    """Banner yazdır."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗██╗   ██╗ ██████╗    ████████╗██████╗               ║
║   ██╔════╝██║   ██║██╔═══██╗   ╚══██╔══╝██╔══██╗              ║
║   █████╗  ██║   ██║██║   ██║█████╗██║   ██████╔╝              ║
║   ██╔══╝  ╚██╗ ██╔╝██║   ██║╚════╝██║   ██╔══██╗              ║
║   ███████╗ ╚████╔╝ ╚██████╔╝      ██║   ██║  ██║              ║
║   ╚══════╝  ╚═══╝   ╚═════╝       ╚═╝   ╚═╝  ╚═╝              ║
║                                                               ║
║   Türkçe & Python Uzman AI - Multi-LoRA System                ║
║   Mac Mini M4 | MLX | Qwen-2.5-3B                             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold blue")


def print_help():
    """Yardım mesajı yazdır."""
    help_table = Table(title="🔧 Komutlar", show_header=True)
    help_table.add_column("Komut", style="cyan")
    help_table.add_column("Açıklama", style="white")
    
    commands = [
        ("/help, /h", "Bu yardım mesajını göster"),
        ("/clear, /c", "Konuşma geçmişini temizle"),
        ("/status, /s", "Sistem durumunu göster"),
        ("/memory <query>", "Hafızada ara"),
        ("/fact <bilgi>", "Yeni bilgi ekle"),
        ("/adapter <name>", "Adapter değiştir (python_coder, tr_chat)"),
        ("/base", "Base modele geç"),
        ("/rag on|off", "RAG'ı aç/kapat"),
        ("/history", "Konuşma geçmişini göster"),
        ("/quit, /q, exit", "Programdan çık"),
    ]
    
    for cmd, desc in commands:
        help_table.add_row(cmd, desc)
    
    console.print(help_table)


def format_response(text: str) -> str:
    """Yanıtı formatla (kod blokları için syntax highlighting)."""
    # Kod blokları bul
    code_pattern = r"```(\w+)?\n(.*?)```"
    
    def replace_code(match):
        lang = match.group(1) or "python"
        code = match.group(2)
        return f"\n[CODE:{lang}]\n{code}[/CODE]\n"
    
    formatted = re.sub(code_pattern, replace_code, text, flags=re.DOTALL)
    return formatted


def print_response(text: str):
    """Yanıtı güzel formatta yazdır."""
    # Kod blokları varsa ayır
    parts = re.split(r'\[CODE:(\w+)\]\n(.*?)\[/CODE\]', format_response(text), flags=re.DOTALL)
    
    i = 0
    while i < len(parts):
        if i + 2 < len(parts) and parts[i+1] in ['python', 'javascript', 'bash', 'json']:
            # Önceki metin
            if parts[i].strip():
                console.print(parts[i].strip())
            
            # Kod bloğu
            lang = parts[i+1]
            code = parts[i+2].strip()
            syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
            console.print(syntax)
            i += 3
        else:
            if parts[i].strip():
                console.print(parts[i].strip())
            i += 1


def main():
    """Ana program."""
    print_banner()
    
    console.print("\n[yellow]🔄 Sistem başlatılıyor...[/yellow]\n")
    
    # EVO-TR başlat
    try:
        evo = EvoTR(verbose=False)
    except Exception as e:
        console.print(f"[red]❌ Hata: {e}[/red]")
        return
    
    console.print("[green]✅ EVO-TR hazır![/green]")
    console.print("[dim]Yardım için /help yazın. Çıkmak için /quit yazın.[/dim]\n")
    
    # Ana döngü
    while True:
        try:
            # Kullanıcı girişi al
            user_input = Prompt.ask("\n[bold cyan]👤 Sen[/bold cyan]")
            
            if not user_input.strip():
                continue
            
            # Komutları işle
            if user_input.startswith("/"):
                cmd_parts = user_input.split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                arg = cmd_parts[1] if len(cmd_parts) > 1 else ""
                
                if cmd in ["/quit", "/q", "/exit"]:
                    console.print("\n[yellow]👋 Görüşmek üzere![/yellow]")
                    break
                
                elif cmd in ["/help", "/h"]:
                    print_help()
                
                elif cmd in ["/clear", "/c"]:
                    evo.clear_conversation()
                    console.print("[green]🧹 Konuşma temizlendi.[/green]")
                
                elif cmd in ["/status", "/s"]:
                    status = evo.get_status()
                    table = Table(title="📊 Sistem Durumu")
                    table.add_column("Özellik", style="cyan")
                    table.add_column("Değer", style="white")
                    
                    table.add_row("Mevcut Adapter", status["current_adapter"] or "base_model")
                    table.add_row("Mevcut Intent", status["current_intent"] or "-")
                    table.add_row("Konuşma Turları", str(status["conversation_turns"]))
                    table.add_row("RAG Aktif", "✅" if status["use_rag"] else "❌")
                    table.add_row("Auto-Adapter", "✅" if status["auto_adapter"] else "❌")
                    table.add_row("Mevcut Adapter'lar", ", ".join(status["available_adapters"]))
                    
                    if status["inference_stats"]["total_generations"] > 0:
                        table.add_row("Toplam Generation", str(status["inference_stats"]["total_generations"]))
                        table.add_row("Ort. Token/s", str(status["inference_stats"]["avg_tokens_per_second"]))
                    
                    console.print(table)
                
                elif cmd == "/memory":
                    if not arg:
                        console.print("[yellow]Kullanım: /memory <arama sorgusu>[/yellow]")
                    else:
                        results = evo.search_memory(arg, top_k=5)
                        if results:
                            console.print(f"\n[green]🔍 '{arg}' için {len(results)} sonuç:[/green]")
                            for r in results:
                                text_preview = r['text'][:100] + "..." if len(r['text']) > 100 else r['text']
                                console.print(f"  [{r['similarity']:.0%}] {text_preview}")
                        else:
                            console.print("[yellow]Sonuç bulunamadı.[/yellow]")
                
                elif cmd == "/fact":
                    if not arg:
                        console.print("[yellow]Kullanım: /fact <eklenecek bilgi>[/yellow]")
                    else:
                        doc_id = evo.add_fact(arg)
                        console.print(f"[green]✅ Bilgi eklendi (ID: {doc_id})[/green]")
                
                elif cmd == "/adapter":
                    if not arg:
                        adapters = list(evo.lora_manager.list_adapters().keys())
                        console.print(f"[cyan]Mevcut adapter'lar: {', '.join(adapters)}[/cyan]")
                    else:
                        try:
                            evo.lora_manager.load_adapter(arg)
                            console.print(f"[green]✅ Adapter değiştirildi: {arg}[/green]")
                        except ValueError as e:
                            console.print(f"[red]❌ {e}[/red]")
                
                elif cmd == "/base":
                    evo.lora_manager.load_base_model()
                    console.print("[green]✅ Base modele geçildi.[/green]")
                
                elif cmd == "/rag":
                    if arg.lower() == "on":
                        evo.use_rag = True
                        console.print("[green]✅ RAG açıldı.[/green]")
                    elif arg.lower() == "off":
                        evo.use_rag = False
                        console.print("[yellow]⚠️ RAG kapatıldı.[/yellow]")
                    else:
                        console.print(f"[cyan]RAG durumu: {'Açık' if evo.use_rag else 'Kapalı'}[/cyan]")
                
                elif cmd == "/history":
                    history = evo.get_conversation_history()
                    if not history:
                        console.print("[yellow]Henüz konuşma yok.[/yellow]")
                    else:
                        console.print(f"\n[cyan]📜 Son {min(5, len(history))} konuşma:[/cyan]")
                        for turn in history[-5:]:
                            console.print(f"\n[dim]{turn.timestamp.strftime('%H:%M:%S')}[/dim] [{turn.intent}]")
                            console.print(f"  👤 {turn.user_message[:50]}...")
                            console.print(f"  🤖 {turn.assistant_response[:50]}...")
                
                else:
                    console.print(f"[red]❓ Bilinmeyen komut: {cmd}[/red]")
                
                continue
            
            # Normal mesaj - yanıt üret
            console.print()
            with console.status("[bold green]🤔 Düşünüyor..."):
                response = evo.chat(user_input)
            
            # Yanıtı göster
            status = evo.get_status()
            adapter_info = f"[dim][{status['current_adapter'] or 'base'}][/dim]"
            
            console.print(f"\n[bold green]🤖 EVO-TR[/bold green] {adapter_info}")
            print_response(response)
            
        except KeyboardInterrupt:
            console.print("\n\n[yellow]👋 Görüşmek üzere![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Hata: {e}[/red]")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
