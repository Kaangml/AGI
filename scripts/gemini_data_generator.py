"""
EVO-TR V2: Gemini Data Generator
==================================
Gemini 2.5 Flash ile kaliteli eğitim verisi üretimi.

Kullanım:
    python scripts/gemini_data_generator.py --domain turkish_chat --count 100
    python scripts/gemini_data_generator.py --domain python_code --count 50
"""

import os
import json
import asyncio
import aiohttp
import argparse
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# .env'den API key yükle
load_dotenv()


def get_api_keys() -> list:
    """Tüm mevcut API key'leri döndür."""
    keys = []
    primary = os.getenv("GOOGLE_API_KEY")
    secondary = os.getenv("GOOGLE_API_KEY_2")
    
    if primary:
        keys.append(primary)
    if secondary:
        keys.append(secondary)
    
    return keys


class APIKeyRotator:
    """Rate limit'e takılınca key değiştiren rotator."""
    
    def __init__(self):
        self.keys = get_api_keys()
        self.current_index = 0
        self.rate_limited_until = {}  # key -> datetime
        
    def get_current_key(self) -> str:
        """Aktif key'i döndür, rate limited ise diğerine geç."""
        if not self.keys:
            raise ValueError("Hiç API key bulunamadı!")
        
        now = datetime.now()
        
        # Tüm key'leri dene
        for _ in range(len(self.keys)):
            key = self.keys[self.current_index]
            
            # Bu key rate limited mı?
            if key in self.rate_limited_until:
                if now < self.rate_limited_until[key]:
                    # Hala rate limited, sonraki key'e geç
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    continue
                else:
                    # Rate limit süresi dolmuş
                    del self.rate_limited_until[key]
            
            return key
        
        # Tüm key'ler rate limited - en kısa sürede açılacak olanı bekle
        wait_times = {k: v for k, v in self.rate_limited_until.items()}
        if wait_times:
            min_wait = min(wait_times.values())
            wait_seconds = (min_wait - now).total_seconds()
            print(f"⏳ Tüm API key'ler rate limited. {wait_seconds:.0f} saniye bekleniyor...")
            return None
        
        return self.keys[0]
    
    def mark_rate_limited(self, key: str, wait_seconds: int = 60):
        """Bir key'i rate limited olarak işaretle."""
        self.rate_limited_until[key] = datetime.now() + timedelta(seconds=wait_seconds)
        print(f"🔄 API key rate limited, {wait_seconds}s sonra tekrar denenecek")
        self.current_index = (self.current_index + 1) % len(self.keys)


@dataclass
class GenerationConfig:
    """Veri üretim konfigürasyonu."""
    domain: str
    count: int
    output_dir: str = "./data/generated"
    batch_size: int = 1  # Sıralı üretim için 1
    delay_between_batches: float = 4.0  # RPM=30 -> 60/30=2s, +2s buffer = 4s
    max_retries: int = 3
    
    # Token limitleri (Qwen 2.5 3B eğitimi için optimize)
    # Hedef: Toplam konuşma ~600-800 token (eğitim için ideal)
    # Gemma 3 27B: input=131K, output=8192
    # TPM=15K -> istek başına ~1K token güvenli
    max_input_tokens: int = 400   # Prompt token limiti
    max_output_tokens: int = 600  # Response token limiti
    
    # Gemma 3 27B Rate limits
    rpm_limit: int = 30    # Dakikada max istek
    tpm_limit: int = 15000 # Dakikada max token
    rpd_limit: int = 14400 # Günde max istek


class GeminiClient:
    """Gemini/Gemma API async client."""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    MODEL = "gemma-3-27b-it"  # Gemma 3 27B Instruct - RPM=30, TPM=15K, RPD=14.4K
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.8,
        max_tokens: int = 800  # Output token limiti
    ) -> tuple[Optional[str], dict]:
        """Tek bir prompt için yanıt üret. Token kullanımını da döndür."""
        url = f"{self.BASE_URL}/{self.MODEL}:generateContent?key={self.api_key}"
        
        token_usage = {"input": 0, "output": 0, "total": 0}
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Token kullanımını çıkar
                    usage = data.get("usageMetadata", {})
                    token_usage["input"] = usage.get("promptTokenCount", 0)
                    token_usage["output"] = usage.get("candidatesTokenCount", 0)
                    token_usage["total"] = usage.get("totalTokenCount", 0)
                    
                    # Gemini response parsing
                    if "candidates" in data and data["candidates"]:
                        content = data["candidates"][0].get("content", {})
                        parts = content.get("parts", [])
                        if parts:
                            return parts[0].get("text", ""), token_usage
                elif response.status == 429:
                    # Rate limit - özel işaretle
                    token_usage["rate_limited"] = True
                    print(f"⚠️ Rate limit aşıldı!")
                    return None, token_usage
                else:
                    error_text = await response.text()
                    print(f"⚠️ API Error {response.status}: {error_text[:100]}")
                    return None, token_usage
        except Exception as e:
            print(f"⚠️ Request error: {e}")
            return None, token_usage
        
        return None, token_usage


class TurkishChatGenerator:
    """Türkçe sohbet verisi üretici."""
    
    # Konu kategorileri
    TOPICS = {
        "selamlama": [
            "Sabah selamlaşması",
            "Akşam selamlaşması", 
            "Resmi selamlama",
            "Samimi selamlama",
            "Vedalaşma",
        ],
        "gunluk_sohbet": [
            "Hava durumu hakkında sohbet",
            "Hafta sonu planları",
            "İş/okul stresi",
            "Yemek önerileri",
            "Film/dizi tavsiyeleri",
            "Müzik sohbeti",
            "Spor haberleri",
            "Tatil planları",
        ],
        "turk_kulturu": [
            "Türk mutfağı (yemekler, tarifler)",
            "Türk kahvesi ve çay kültürü",
            "Bayramlar ve kutlamalar",
            "Türk müziği",
            "Tarihi yerler",
            "Gelenekler ve görenekler",
            "Türk edebiyatı",
        ],
        "duygusal_destek": [
            "Motivasyon ve cesaret verme",
            "Stres yönetimi tavsiyeleri",
            "Empati gösterme",
            "Başarısızlıkla başa çıkma",
            "Olumlu düşünce",
        ],
        "bilgi_soru": [
            "Genel kültür soruları",
            "Güncel olaylar hakkında",
            "Nasıl yapılır soruları",
            "Tavsiye isteme",
            "Açıklama isteme",
        ],
        "atasozleri": [
            "Atasözü açıklaması",
            "Deyim kullanımı",
            "Türkçe dil bilgisi",
        ]
    }
    
    def generate_prompt(self, topic_category: str, specific_topic: str) -> str:
        """Veri üretim promptu oluştur - Qwen 2.5 3B eğitimi için optimize."""
        return f"""Sen bir Türkçe sohbet veri seti oluşturucususun.

HEDEF MODEL: Qwen 2.5 3B (küçük dil modeli)
TOKEN LİMİTİ: Toplam konuşma ~400-600 token olmalı

Konu: {topic_category} - {specific_topic}

Bir kullanıcı ve yardımcı asistan (EVO-TR) arasında doğal bir Türkçe sohbet oluştur.

KURALLAR:
1. Yanıtlar KISA ve ÖZ olmalı (her yanıt max 2-3 cümle)
2. Doğal Türkçe kullan, çeviri gibi olmasın
3. Samimi ama profesyonel ton
4. 2 tur yeterli (user-assistant-user-assistant)
5. Asistan "EVO-TR" olarak Türkçe konuşan yardımcı bir AI

Sistem promptu dahil et:
- system: "Sen EVO-TR, Türkçe konuşan yardımcı bir yapay zeka asistanısın."

SADECE aşağıdaki JSON formatında yanıt ver:

{{
  "messages": [
    {{"role": "system", "content": "Sen EVO-TR, Türkçe konuşan yardımcı bir yapay zeka asistanısın. Kısa, net ve yararlı yanıtlar verirsin."}},
    {{"role": "user", "content": "..."}},
    {{"role": "assistant", "content": "..."}},
    {{"role": "user", "content": "..."}},
    {{"role": "assistant", "content": "..."}}
  ]
}}"""

    def get_random_topic(self) -> tuple:
        """Rastgele konu seç."""
        category = random.choice(list(self.TOPICS.keys()))
        topic = random.choice(self.TOPICS[category])
        return category, topic


class PythonCodeGenerator:
    """Python kod verisi üretici."""
    
    TOPICS = {
        "temel_kavramlar": [
            "Değişken tanımlama ve veri tipleri",
            "Liste, tuple, dictionary kullanımı",
            "String işlemleri",
            "Koşullu ifadeler (if/else)",
            "Döngüler (for, while)",
            "Fonksiyon tanımlama",
            "Lambda fonksiyonları",
        ],
        "orta_seviye": [
            "List comprehension",
            "Dictionary comprehension",
            "File işlemleri (okuma/yazma)",
            "Exception handling (try/except)",
            "Class ve OOP temelleri",
            "Decorators",
            "Generators",
        ],
        "algoritmalar": [
            "Sıralama algoritmaları",
            "Arama algoritmaları",
            "Recursion örnekleri",
            "String manipülasyonu",
            "Array/liste problemleri",
            "Matematik problemleri",
        ],
        "debugging": [
            "Hata bulma ve düzeltme",
            "Kod optimizasyonu",
            "Best practices",
            "Clean code önerileri",
        ],
        "pratik_ornekler": [
            "API istekleri (requests)",
            "JSON işleme",
            "Tarih/saat işlemleri",
            "Regex kullanımı",
            "Unit test yazma",
        ]
    }
    
    def generate_prompt(self, topic_category: str, specific_topic: str) -> str:
        """Python kod veri üretim promptu - Qwen 2.5 3B için optimize."""
        return f"""Sen bir Python programlama eğitim verisi oluşturucususun.

HEDEF MODEL: Qwen 2.5 3B (küçük dil modeli)
TOKEN LİMİTİ: Toplam konuşma ~500-700 token olmalı

Konu: {topic_category} - {specific_topic}

KURALLAR:
1. Soru ve yanıt Türkçe olmalı
2. Kod KISA ve ÖZ olmalı (max 15-20 satır)
3. Açıklama 2-3 cümle ile sınırlı
4. Çalışır, doğru Python kodu
5. Asistan "EVO-TR" olarak Python uzmanı bir AI

SADECE aşağıdaki JSON formatında yanıt ver:

{{
  "messages": [
    {{"role": "system", "content": "Sen EVO-TR, Python programlama konusunda uzman bir yapay zeka asistanısın. Kısa, çalışır kod örnekleri ve net açıklamalar verirsin."}},
    {{"role": "user", "content": "..."}},
    {{"role": "assistant", "content": "..."}}
  ]
}}"""

    def get_random_topic(self) -> tuple:
        """Rastgele konu seç."""
        category = random.choice(list(self.TOPICS.keys()))
        topic = random.choice(self.TOPICS[category])
        return category, topic


class DataGenerator:
    """Ana veri üretici sınıfı."""
    
    def __init__(self, config: GenerationConfig, api_key_choice: str = None):
        self.config = config
        self.api_key_choice = api_key_choice
        
        # API key seçimi
        keys = get_api_keys()
        if not keys:
            raise ValueError("GOOGLE_API_KEY bulunamadı! .env dosyasını kontrol edin.")
        
        if api_key_choice in ["primary", "1"]:
            self.api_key = keys[0] if len(keys) > 0 else None
            print(f"🔑 Primary API key kullanılıyor")
        elif api_key_choice in ["secondary", "2"]:
            self.api_key = keys[1] if len(keys) > 1 else keys[0]
            print(f"🔑 Secondary API key kullanılıyor")
        else:
            # Rotator kullan
            self.api_key = None
            self.key_rotator = APIKeyRotator()
        
        if api_key_choice and not self.api_key:
            raise ValueError(f"Seçilen API key bulunamadı: {api_key_choice}")
        
        # Domain'e göre generator seç
        if config.domain == "turkish_chat":
            self.generator = TurkishChatGenerator()
        elif config.domain == "python_code":
            self.generator = PythonCodeGenerator()
        else:
            raise ValueError(f"Bilinmeyen domain: {config.domain}")
        
        # Output dizini oluştur
        self.output_dir = Path(config.output_dir) / config.domain
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # İstatistikler
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "start_time": None,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0
        }
    
    async def generate_single(
        self,
        client: GeminiClient,
        index: int
    ) -> Optional[Dict[str, Any]]:
        """Tek bir örnek üret."""
        category, topic = self.generator.get_random_topic()
        prompt = self.generator.generate_prompt(category, topic)
        
        self.stats["total_requests"] += 1
        
        for attempt in range(self.config.max_retries):
            response, token_usage = await client.generate(prompt)
            
            # Rate limit kontrolü
            if token_usage.get("rate_limited"):
                self.key_rotator.mark_rate_limited(client.api_key, wait_seconds=60)
                await asyncio.sleep(5)  # Kısa bekle ve tekrar dene
                continue
            
            # Token kullanımını kaydet
            self.stats["total_input_tokens"] += token_usage["input"]
            self.stats["total_output_tokens"] += token_usage["output"]
            self.stats["total_tokens"] += token_usage["total"]
            
            if response:
                # JSON parse et
                try:
                    # JSON bloğunu bul
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = response[json_start:json_end]
                        data = json.loads(json_str)
                        
                        # Validasyon
                        if "messages" in data and len(data["messages"]) >= 2:
                            data["_meta"] = {
                                "category": category,
                                "topic": topic,
                                "index": index,
                                "generated_at": datetime.now().isoformat()
                            }
                            self.stats["successful"] += 1
                            return data
                            
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON parse error ({index}): {e}")
            
            # Retry delay
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(1)
        
        self.stats["failed"] += 1
        return None
    
    async def generate_batch(
        self,
        client: GeminiClient,
        start_index: int,
        batch_size: int
    ) -> List[Dict[str, Any]]:
        """Bir batch veri üret."""
        tasks = [
            self.generate_single(client, start_index + i)
            for i in range(batch_size)
        ]
        
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
    
    async def generate_all(self) -> List[Dict[str, Any]]:
        """Tüm verileri üret."""
        self.stats["start_time"] = datetime.now()
        all_data = []
        consecutive_fails = 0
        max_consecutive_fails = 5
        
        # Tek API key mi yoksa rotator mı?
        using_single_key = self.api_key is not None
        
        print(f"\n🚀 Veri üretimi başlıyor...")
        print(f"   Domain: {self.config.domain}")
        print(f"   Hedef: {self.config.count} örnek")
        print(f"   Batch size: {self.config.batch_size}")
        print(f"   Delay: {self.config.delay_between_batches}s")
        if using_single_key:
            print(f"   API Key: Tek key (sabit)")
        else:
            print(f"   API Keys: {len(self.key_rotator.keys)} adet (rotator)")
        print()
        
        generated = 0
        batch_num = 0
        
        while generated < self.config.count:
            # Aktif API key'i al
            if using_single_key:
                api_key = self.api_key
            else:
                api_key = self.key_rotator.get_current_key()
            
            if api_key is None:
                # Tüm key'ler rate limited
                consecutive_fails += 1
                if consecutive_fails >= max_consecutive_fails:
                    print(f"\n⏳ API key rate limited. 5 dakika bekleniyor...")
                    print(f"   Şu anki ilerleme: {len(all_data)}/{self.config.count}")
                    await asyncio.sleep(300)  # 5 dakika bekle
                    consecutive_fails = 0
                else:
                    await asyncio.sleep(60)
                continue
            
            async with GeminiClient(api_key) as client:
                remaining = self.config.count - generated
                batch_size = min(self.config.batch_size, remaining)
                
                print(f"📦 Batch {batch_num + 1}: {generated}/{self.config.count}", end="", flush=True)
                
                batch_data = await self.generate_batch(client, generated, batch_size)
                
                if batch_data:
                    all_data.extend(batch_data)
                    consecutive_fails = 0
                else:
                    consecutive_fails += 1
                
                generated += batch_size
                batch_num += 1
                
                print(f" -> {len(batch_data)} başarılı")
                
                # Her 10 batch'te bir kaydet (checkpoint)
                if len(all_data) > 0 and batch_num % 10 == 0:
                    self._save_checkpoint(all_data)
                
                # Rate limiting
                if generated < self.config.count:
                    await asyncio.sleep(self.config.delay_between_batches)
        
        return all_data
    
    def _save_checkpoint(self, data: List[Dict[str, Any]]):
        """Ara kayıt (checkpoint) oluştur."""
        filepath = self.output_dir / f"{self.config.domain}_checkpoint.jsonl"
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                clean_item = {"messages": item["messages"]}
                f.write(json.dumps(clean_item, ensure_ascii=False) + "\n")
        print(f"   💾 Checkpoint: {len(data)} örnek kaydedildi")
    
    def save_data(self, data: List[Dict[str, Any]]) -> Path:
        """Veriyi kaydet."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.domain}_{timestamp}.jsonl"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                # Meta bilgiyi çıkar, sadece messages'ı kaydet
                clean_item = {"messages": item["messages"]}
                f.write(json.dumps(clean_item, ensure_ascii=False) + "\n")
        
        return filepath
    
    def print_stats(self, output_path: Path):
        """İstatistikleri yazdır."""
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        print("\n" + "=" * 50)
        print("📊 Üretim İstatistikleri")
        print("=" * 50)
        print(f"   Domain: {self.config.domain}")
        print(f"   Toplam istek: {self.stats['total_requests']}")
        print(f"   Başarılı: {self.stats['successful']}")
        print(f"   Başarısız: {self.stats['failed']}")
        print(f"   Başarı oranı: {self.stats['successful']/max(1,self.stats['total_requests'])*100:.1f}%")
        print(f"   Süre: {elapsed:.1f} saniye ({elapsed/60:.1f} dakika)")
        print(f"   Hız: {self.stats['successful']/max(1,elapsed)*60:.1f} örnek/dakika")
        print()
        print("   📈 Token Kullanımı:")
        print(f"      Input tokens: {self.stats['total_input_tokens']:,}")
        print(f"      Output tokens: {self.stats['total_output_tokens']:,}")
        print(f"      Toplam tokens: {self.stats['total_tokens']:,}")
        print(f"\n   📁 Çıktı: {output_path}")
        print("=" * 50)


async def main():
    parser = argparse.ArgumentParser(description="Gemini ile eğitim verisi üret")
    parser.add_argument(
        "--domain",
        type=str,
        choices=["turkish_chat", "python_code"],
        required=True,
        help="Veri domain'i"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Üretilecek örnek sayısı"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Batch başına istek sayısı (rate limit için 1 önerilir)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/generated",
        help="Çıktı dizini"
    )
    parser.add_argument(
        "--overnight",
        action="store_true",
        help="Gece modu - rate limit'e uygun yavaş üretim"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=4.0,
        help="İstekler arası bekleme süresi (saniye) - Gemma 3 27B için 4s önerilir"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        choices=["primary", "secondary", "1", "2"],
        default=None,
        help="Kullanılacak API key: primary/1 veya secondary/2"
    )
    
    args = parser.parse_args()
    
    # Overnight mode: Daha güvenli delay
    delay = args.delay
    if args.overnight:
        delay = max(5.0, args.delay)
        print(f"🌙 Gece modu aktif - {delay} saniye delay ile çalışıyor")
    
    config = GenerationConfig(
        domain=args.domain,
        count=args.count,
        batch_size=args.batch_size,
        output_dir=args.output_dir,
        delay_between_batches=delay
    )
    
    # Belirli API key seçildiyse sadece onu kullan
    generator = DataGenerator(config, api_key_choice=args.api_key)
    
    # Veri üret
    data = await generator.generate_all()
    
    if data:
        # Kaydet
        output_path = generator.save_data(data)
        
        # İstatistikler
        generator.print_stats(output_path)
    else:
        print("❌ Veri üretilemedi!")


if __name__ == "__main__":
    asyncio.run(main())
