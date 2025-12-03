#!/usr/bin/env python3
"""
EVO-TR: Türkçe Adapter Testi

Base model ve adapter ile yanıtları karşılaştırır.
"""

from mlx_lm import load, generate
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

MODEL_PATH = "./models/base/qwen-2.5-3b-instruct"
ADAPTER_PATH = "./adapters/tr_chat"

TEST_PROMPTS = [
    "Merhaba! Nasılsın?",
    "Türk kahvesi nasıl yapılır?",
    "'Damlaya damlaya göl olur' ne demek?",
    "Atatürk hakkında kısa bilgi ver.",
    "Bana bir Türk atasözü söyle ve anlamını açıkla.",
    "İstanbul'un tarihi önemi nedir?",
    "Türk misafirperverliği hakkında ne söylersin?",
    "Canım sıkılıyor, ne yapmalıyım?",
]


def main():
    console.print("\n[bold blue]🧪 Türkçe Adapter Testi[/bold blue]\n")
    
    # Adapter ile model yükle
    console.print("📥 Model yükleniyor (adapter ile)...")
    model, tokenizer = load(MODEL_PATH, adapter_path=ADAPTER_PATH)
    console.print("✅ Model hazır!\n")
    
    for i, prompt in enumerate(TEST_PROMPTS, 1):
        console.print(Panel(f"[cyan]Soru {i}:[/cyan] {prompt}", expand=False))
        
        # Chat formatında prompt oluştur
        messages = [{"role": "user", "content": prompt}]
        formatted_prompt = tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Yanıt üret
        response = generate(
            model, 
            tokenizer, 
            prompt=formatted_prompt, 
            max_tokens=200,
            verbose=False
        )
        
        console.print(f"\n[green]Yanıt:[/green] {response}\n")
        console.print("─" * 60 + "\n")
        
        if i < len(TEST_PROMPTS):
            try:
                input("Enter'a basarak devam et...")
            except EOFError:
                pass
    
    console.print("\n✅ [bold green]Test tamamlandı![/bold green]")


if __name__ == "__main__":
    main()
