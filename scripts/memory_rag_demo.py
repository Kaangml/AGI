#!/usr/bin/env python3
"""
EVO-TR: Memory & RAG Demo

Hafıza sisteminin LLM ile entegre çalışmasını gösterir.
"""

import sys
sys.path.insert(0, ".")

from mlx_lm import load, generate
from src.memory.memory_manager import MemoryManager
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


def main():
    console.print("\n[bold blue]🧠 EVO-TR: Memory & RAG Demo[/bold blue]\n")
    
    # Memory Manager başlat
    console.print("📦 Memory Manager başlatılıyor...")
    memory = MemoryManager(
        persist_path="./data/chromadb/demo",
        collection_name="demo_memory",
        max_context_messages=10,
        max_context_tokens=1500,
        system_prompt="Sen EVO-TR, Türkçe konuşan ve kod yazabilen akıllı bir asistansın. Önceki konuşmaları hatırlayabilirsin.",
        auto_save=True
    )
    console.print("✅ Memory Manager hazır!\n")
    
    # Model yükle
    console.print("🤖 LLM yükleniyor...")
    model, tokenizer = load("./models/base/qwen-2.5-3b-instruct")
    console.print("✅ LLM hazır!\n")
    
    # Bazı örnek hatıralar ekle
    console.print("[yellow]📚 Örnek hafızalar ekleniyor...[/yellow]")
    
    memory.add_fact("Kullanıcının adı Kaan.", topic="user_info")
    memory.add_fact("Kaan'ın favori programlama dili Python.", topic="preferences")
    memory.add_fact("Kaan Mac Mini M4 kullanıyor.", topic="user_info")
    memory.add_preference("Kaan kod örneklerini Türkçe açıklamalarla tercih ediyor.")
    
    console.print("✅ Hafızalar eklendi!\n")
    console.print(memory.get_status_summary())
    console.print()
    
    # Demo konuşmalar
    demo_queries = [
        "Merhaba! Beni hatırlıyor musun?",
        "Hangi bilgisayarı kullanıyorum?",
        "Python'da bir sayının asal olup olmadığını kontrol eden fonksiyon yaz.",
        "Az önce yazdığın kodu açıklar mısın?"
    ]
    
    console.print("[bold green]💬 Demo konuşma başlıyor...[/bold green]\n")
    console.print("─" * 60)
    
    for query in demo_queries:
        console.print(Panel(f"[cyan]👤 Kullanıcı:[/cyan] {query}", expand=False))
        
        # Mesajı hafızaya ekle
        memory.add_user_message(query)
        
        # RAG: İlgili bağlam al
        rag_context = memory.get_augmented_context(query, long_term_top_k=2)
        
        if rag_context:
            console.print(f"\n[dim]📚 RAG Context bulundu:\n{rag_context[:200]}...[/dim]\n")
        
        # System prompt'a bağlamı ekle
        enhanced_system = memory.short_term.system_prompt
        if rag_context:
            enhanced_system += f"\n\nKullanıcı hakkında bildiklerin:\n{rag_context}"
        
        # Chat mesajlarını hazırla
        messages = [{"role": "system", "content": enhanced_system}]
        
        # Son mesajları ekle (current query hariç - zaten ekledik)
        for msg in memory.short_term.get_messages()[:-1]:  # Son mesaj current query
            messages.append(msg.to_chat_format())
        
        # Current query'yi ekle
        messages.append({"role": "user", "content": query})
        
        # Prompt oluştur
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Yanıt üret
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=400,
            verbose=False
        )
        
        console.print(f"\n[green]🤖 EVO-TR:[/green] {response}\n")
        
        # Yanıtı hafızaya ekle
        memory.add_assistant_message(response)
        
        console.print("─" * 60)
    
    # Final durum
    console.print("\n[bold blue]📊 Final Hafıza Durumu[/bold blue]")
    console.print(memory.get_status_summary())
    
    # Hafıza arama testi
    console.print("\n[bold yellow]🔍 Hafıza Arama Testi: 'Python kod'[/bold yellow]")
    results = memory.search_memory("Python kod", top_k=3)
    for r in results:
        text_preview = r['text'][:100] + "..." if len(r['text']) > 100 else r['text']
        console.print(f"  [{r['similarity']:.0%}] {text_preview}")
    
    console.print("\n✅ Demo tamamlandı!")


if __name__ == "__main__":
    main()
