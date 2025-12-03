#!/usr/bin/env python3
"""
EVO-TR: Python Adapter Testi

Python kod üretimi için adapter ile model testleri.
"""

from mlx_lm import load, generate
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

MODEL_PATH = "./models/base/qwen-2.5-3b-instruct"
ADAPTER_PATH = "./adapters/python_coder"

TEST_PROMPTS = [
    # Temel Python
    "Write a Python function to check if a number is prime.",
    "Write a Python function that reverses a string without using built-in reverse methods.",
    "Create a Python function to find the factorial of a number using recursion.",
    
    # Algoritmalar
    "Implement binary search in Python.",
    "Write a Python function to merge two sorted lists into one sorted list.",
    "Implement a Python function for bubble sort algorithm.",
    
    # Veri yapıları
    "Create a Python class for a simple stack with push, pop, and peek methods.",
    "Write a Python function to remove duplicates from a list while preserving order.",
    
    # Debug/Best practices
    "This code has a bug: def add(a, b): return a - b. Fix it.",
    "Write a Python function to read a JSON file safely with proper error handling.",
    
    # Türkçe promptlar
    "Bir Python fonksiyonu yaz: verilen listede en büyük ve en küçük sayıyı bul.",
    "Python'da bir sayının palindrom olup olmadığını kontrol eden fonksiyon yaz.",
]


def extract_code(response: str) -> str:
    """Yanıttan kod bloğunu çıkar."""
    if "```python" in response:
        start = response.find("```python") + 9
        end = response.find("```", start)
        if end != -1:
            return response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        if end != -1:
            return response[start:end].strip()
    return response


def test_with_adapter():
    """Adapter ile test."""
    console.print("\n[bold blue]🧪 Python Adapter Testi[/bold blue]\n")
    
    # Adapter ile model yükle
    console.print("📥 Model yükleniyor (Python adapter ile)...")
    model, tokenizer = load(MODEL_PATH, adapter_path=ADAPTER_PATH)
    console.print("✅ Model hazır!\n")
    
    for i, prompt in enumerate(TEST_PROMPTS, 1):
        console.print(Panel(f"[cyan]Prompt {i}/{len(TEST_PROMPTS)}:[/cyan] {prompt}", expand=False))
        
        # System prompt ile chat formatı
        messages = [
            {"role": "system", "content": "Sen deneyimli bir Python geliştiricisisin. Kod yaz, açıkla ve debug yap."},
            {"role": "user", "content": prompt}
        ]
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
            max_tokens=400,
            verbose=False
        )
        
        # Kodu çıkar ve syntax highlight
        code = extract_code(response)
        if code != response:
            console.print("\n[green]Kod:[/green]")
            syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            console.print(f"\n[green]Yanıt:[/green] {response}")
        
        console.print("\n" + "─" * 70 + "\n")
        
        if i < len(TEST_PROMPTS):
            try:
                input("Enter'a basarak devam et...")
            except EOFError:
                pass
    
    console.print("\n✅ [bold green]Test tamamlandı![/bold green]")


def test_code_execution():
    """Üretilen kodu çalıştırarak doğruluk testi."""
    console.print("\n[bold yellow]🔬 Kod Çalıştırma Testi[/bold yellow]\n")
    
    # Adapter ile model yükle
    model, tokenizer = load(MODEL_PATH, adapter_path=ADAPTER_PATH)
    
    # Test case'ler - (prompt, test_code)
    test_cases = [
        (
            "Write a Python function called 'is_prime' that checks if a number is prime.",
            """
# Test is_prime function
assert is_prime(2) == True
assert is_prime(17) == True
assert is_prime(1) == False
assert is_prime(4) == False
assert is_prime(97) == True
print("✅ is_prime tests passed!")
"""
        ),
        (
            "Write a Python function called 'factorial' that calculates factorial of a number.",
            """
# Test factorial function
assert factorial(0) == 1
assert factorial(1) == 1
assert factorial(5) == 120
assert factorial(10) == 3628800
print("✅ factorial tests passed!")
"""
        ),
        (
            "Write a Python function called 'reverse_string' that reverses a string.",
            """
# Test reverse_string function
assert reverse_string("hello") == "olleh"
assert reverse_string("Python") == "nohtyP"
assert reverse_string("") == ""
assert reverse_string("a") == "a"
print("✅ reverse_string tests passed!")
"""
        ),
    ]
    
    passed = 0
    for prompt, test_code in test_cases:
        console.print(Panel(f"[cyan]Test:[/cyan] {prompt}", expand=False))
        
        messages = [
            {"role": "system", "content": "Sen deneyimli bir Python geliştiricisisin. Sadece fonksiyonu yaz, açıklama yapma."},
            {"role": "user", "content": prompt}
        ]
        formatted_prompt = tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        response = generate(
            model, 
            tokenizer, 
            prompt=formatted_prompt, 
            max_tokens=300,
            verbose=False
        )
        
        code = extract_code(response)
        console.print(Syntax(code, "python", theme="monokai"))
        
        # Kodu çalıştır
        try:
            exec_globals = {}
            exec(code + "\n" + test_code, exec_globals)
            passed += 1
            console.print("[green]✅ Test geçti![/green]\n")
        except Exception as e:
            console.print(f"[red]❌ Test başarısız: {e}[/red]\n")
    
    console.print(f"\n📊 [bold]Sonuç: {passed}/{len(test_cases)} test geçti[/bold]\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--exec":
        test_code_execution()
    else:
        test_with_adapter()
