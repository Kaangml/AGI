#!/usr/bin/env python3
"""
Bilim Veri Seti İndirici

SciQ dataset'inden bilim soruları toplar ve
MLX LoRA formatına dönüştürür.
"""

import json
from pathlib import Path
from datasets import load_dataset
import random

# Bilim kategorileri için anahtar kelimeler
PHYSICS_KEYWORDS = [
    'force', 'energy', 'motion', 'velocity', 'acceleration', 'gravity',
    'electricity', 'magnetism', 'wave', 'light', 'heat', 'temperature',
    'pressure', 'mass', 'weight', 'momentum', 'newton', 'joule', 'watt',
    'circuit', 'voltage', 'current', 'resistance', 'magnetic', 'electric',
    'nuclear', 'atom', 'proton', 'neutron', 'electron', 'photon', 'quantum'
]

CHEMISTRY_KEYWORDS = [
    'chemical', 'reaction', 'element', 'compound', 'molecule', 'atom',
    'bond', 'acid', 'base', 'ph', 'oxidation', 'reduction', 'ion',
    'solution', 'solvent', 'solute', 'concentration', 'catalyst',
    'periodic table', 'electron', 'proton', 'neutron', 'isotope',
    'organic', 'inorganic', 'polymer', 'metal', 'gas', 'liquid', 'solid'
]

BIOLOGY_KEYWORDS = [
    'cell', 'dna', 'rna', 'gene', 'protein', 'organism', 'species',
    'evolution', 'natural selection', 'mutation', 'chromosome',
    'photosynthesis', 'respiration', 'metabolism', 'enzyme',
    'bacteria', 'virus', 'plant', 'animal', 'ecosystem', 'food chain',
    'mitosis', 'meiosis', 'tissue', 'organ', 'nervous', 'blood',
    'immune', 'hormone', 'reproduction', 'heredity', 'ecology'
]

def categorize_question(question: str, support: str = "") -> str:
    """Soruyu bilim dalına göre kategorize et."""
    text = (question + " " + support).lower()
    
    physics_score = sum(1 for kw in PHYSICS_KEYWORDS if kw in text)
    chemistry_score = sum(1 for kw in CHEMISTRY_KEYWORDS if kw in text)
    biology_score = sum(1 for kw in BIOLOGY_KEYWORDS if kw in text)
    
    max_score = max(physics_score, chemistry_score, biology_score)
    
    if max_score == 0:
        return "general_science"
    elif physics_score == max_score:
        return "physics"
    elif chemistry_score == max_score:
        return "chemistry"
    else:
        return "biology"


def format_science_qa(question: str, answer: str, support: str = "", category: str = "") -> dict:
    """Bilim Q&A'yı chat formatına dönüştür."""
    
    # Kategori bazlı system prompt
    category_prompts = {
        "physics": "You are an expert physics tutor. Explain concepts clearly with examples.",
        "chemistry": "You are an expert chemistry tutor. Explain reactions and concepts step by step.",
        "biology": "You are an expert biology tutor. Explain life sciences concepts clearly.",
        "general_science": "You are an expert science tutor. Explain scientific concepts clearly."
    }
    
    system = category_prompts.get(category, category_prompts["general_science"])
    
    # Açıklama varsa cevaba ekle
    if support and len(support) > 50:
        response = f"{answer}\n\nExplanation: {support}"
    else:
        response = answer
    
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
            {"role": "assistant", "content": response}
        ]
    }


def download_sciq() -> list:
    """SciQ dataset'i indir ve işle."""
    print("📥 SciQ dataset indiriliyor...")
    
    ds = load_dataset("allenai/sciq", split="train")
    print(f"   ✓ {len(ds)} örnek indirildi")
    
    examples = []
    category_counts = {"physics": 0, "chemistry": 0, "biology": 0, "general_science": 0}
    
    for item in ds:
        question = item["question"]
        answer = item["correct_answer"]
        support = item.get("support", "")
        
        # Kategorize et
        category = categorize_question(question, support)
        category_counts[category] += 1
        
        # Format
        formatted = format_science_qa(question, answer, support, category)
        formatted["category"] = category
        examples.append(formatted)
    
    print(f"\n📊 Kategori Dağılımı:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count}")
    
    return examples


def create_turkish_science_samples() -> list:
    """Türkçe bilim örnekleri oluştur."""
    print("\n📝 Türkçe bilim örnekleri oluşturuluyor...")
    
    turkish_samples = [
        # Fizik
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir fizik öğretmenisin. Kavramları örneklerle açıkla."},
                {"role": "user", "content": "Newton'un hareket yasaları nelerdir?"},
                {"role": "assistant", "content": """Newton'un üç hareket yasası:

1. **Birinci Yasa (Eylemsizlik):** Bir cisim üzerine net kuvvet etki etmedikçe durağan kalır veya düzgün doğrusal hareket yapar.

2. **İkinci Yasa (F=ma):** Bir cisme uygulanan net kuvvet, cismin kütlesi ile ivmesinin çarpımına eşittir. F = m × a

3. **Üçüncü Yasa (Etki-Tepki):** Her etkiye eşit ve zıt yönde bir tepki vardır. Örneğin, yere bastığınızda yer size eşit kuvvetle basar."""}
            ],
            "category": "physics"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir fizik öğretmenisin."},
                {"role": "user", "content": "Enerji korunumu yasası ne demektir?"},
                {"role": "assistant", "content": """Enerji korunumu yasası, enerjinin yok edilemeyeceğini veya yoktan var edilemeyeceğini, yalnızca bir formdan diğerine dönüşebileceğini belirtir.

**Örnek:** Bir sarkacı salladığınızda:
- En yüksek noktada: Maksimum potansiyel enerji, sıfır kinetik enerji
- En alçak noktada: Maksimum kinetik enerji, minimum potansiyel enerji

Toplam enerji (potansiyel + kinetik) her zaman sabit kalır."""}
            ],
            "category": "physics"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir fizik öğretmenisin."},
                {"role": "user", "content": "Işık hızı nedir ve neden önemlidir?"},
                {"role": "assistant", "content": """Işık hızı (c), vakumda yaklaşık **299,792,458 m/s** veya yaklaşık **3 × 10⁸ m/s**'dir.

**Önemi:**
1. Evrendeki en yüksek hızdır - hiçbir madde veya bilgi daha hızlı hareket edemez
2. Einstein'ın E=mc² formülünde kritik rol oynar
3. Elektromanyetik dalgaların hızını belirler
4. Uzaklıkları ölçmede kullanılır (ışık yılı)

Güneş ışığının Dünya'ya ulaşması yaklaşık 8 dakika 20 saniye sürer."""}
            ],
            "category": "physics"
        },
        # Kimya
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir kimya öğretmenisin. Tepkimeleri ve kavramları adım adım açıkla."},
                {"role": "user", "content": "Periyodik tablo nasıl düzenlenmiştir?"},
                {"role": "assistant", "content": """Periyodik tablo elementlerin düzenli bir şekilde sıralandığı tablodur:

**Satırlar (Periyotlar):** 7 periyot vardır. Her periyot, elektronların yerleştiği enerji seviyesini gösterir.

**Sütunlar (Gruplar):** 18 grup vardır. Aynı gruptaki elementler benzer kimyasal özelliklere sahiptir.

**Bölgeler:**
- **s-bloğu:** 1-2. gruplar (alkali ve toprak alkali metaller)
- **p-bloğu:** 13-18. gruplar (halojenler, soy gazlar)
- **d-bloğu:** 3-12. gruplar (geçiş metalleri)
- **f-bloğu:** Lantanitler ve aktinitler

Elementler artan atom numarasına göre sıralanır."""}
            ],
            "category": "chemistry"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir kimya öğretmenisin."},
                {"role": "user", "content": "Asit ve baz nedir? Nasıl ayırt edilir?"},
                {"role": "assistant", "content": """**Asitler:**
- H⁺ iyonu verirler
- Turnusolu kırmızıya çevirirler
- pH < 7
- Örnek: HCl (tuz ruhu), H₂SO₄ (sülfürik asit), sirke

**Bazlar:**
- OH⁻ iyonu verirler
- Turnusolu maviye çevirirler
- pH > 7
- Örnek: NaOH (kostik), Ca(OH)₂ (sönmüş kireç), sabun

**Nötrleşme:** Asit + Baz → Tuz + Su
Örnek: HCl + NaOH → NaCl + H₂O

pH ölçeği 0-14 arasındadır, 7 nötrdür."""}
            ],
            "category": "chemistry"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir kimya öğretmenisin."},
                {"role": "user", "content": "Kimyasal bağ türleri nelerdir?"},
                {"role": "assistant", "content": """Üç ana kimyasal bağ türü vardır:

**1. İyonik Bağ:**
- Metal ve ametal arasında oluşur
- Elektron transferi ile gerçekleşir
- Örnek: NaCl (sofra tuzu) - Na elektron verir, Cl alır

**2. Kovalent Bağ:**
- Ametaller arasında oluşur
- Elektronlar paylaşılır
- Örnek: H₂O, CO₂, O₂
- Polar ve apolar olabilir

**3. Metalik Bağ:**
- Metaller arasında oluşur
- Elektronlar "deniz" gibi serbest hareket eder
- İletkenlik ve parlaklık sağlar
- Örnek: Cu, Fe, Au

Bağ türü, elementlerin elektronegatiflik farkına bağlıdır."""}
            ],
            "category": "chemistry"
        },
        # Biyoloji
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir biyoloji öğretmenisin. Yaşam bilimlerini açık şekilde anlat."},
                {"role": "user", "content": "DNA nedir ve nasıl çalışır?"},
                {"role": "assistant", "content": """DNA (Deoksiribonükleik Asit), canlıların genetik bilgisini taşıyan moleküldür.

**Yapısı:**
- Çift sarmal (double helix) şeklinde
- Nükleotidlerden oluşur: şeker + fosfat + baz
- 4 baz: Adenin (A), Timin (T), Guanin (G), Sitozin (C)
- Eşleşme: A-T ve G-C

**İşlevleri:**
1. **Replikasyon:** DNA kendini kopyalar (hücre bölünmesinde)
2. **Transkripsiyon:** DNA'dan RNA sentezi
3. **Translasyon:** RNA'dan protein sentezi

**Genetik Kod:** Her 3 baz (kodon) bir aminoasiti kodlar. Bu kod evrenseldir - tüm canlılarda aynıdır."""}
            ],
            "category": "biology"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir biyoloji öğretmenisin."},
                {"role": "user", "content": "Fotosentez nasıl gerçekleşir?"},
                {"role": "assistant", "content": """Fotosentez, bitkilerin güneş enerjisini kimyasal enerjiye dönüştürdüğü süreçtir.

**Genel Denklem:**
6CO₂ + 6H₂O + Işık → C₆H₁₂O₆ + 6O₂

**Aşamalar:**

**1. Işık Tepkimeleri (Tilakoidlerde):**
- Klorofil ışığı emer
- Su parçalanır (fotoliz): 2H₂O → O₂ + 4H⁺ + 4e⁻
- ATP ve NADPH üretilir

**2. Karbon Tepkimeleri (Stromada):**
- Calvin döngüsü
- CO₂ tutulur ve şekere dönüşür
- ATP ve NADPH kullanılır

**Önemi:**
- Oksijen üretir
- Besin zincirinin temelidir
- Karbon döngüsünde kritik rol oynar"""}
            ],
            "category": "biology"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir biyoloji öğretmenisin."},
                {"role": "user", "content": "Evrim teorisi ne anlatır?"},
                {"role": "assistant", "content": """Darwin'in Evrim Teorisi, türlerin zaman içinde değiştiğini ve ortak atalardan geldiğini açıklar.

**Temel Mekanizmalar:**

**1. Doğal Seçilim:**
- Çevreye uyum sağlayanlar hayatta kalır
- Avantajlı özellikler sonraki nesillere aktarılır
- "En güçlü değil, en uyumlu" hayatta kalır

**2. Mutasyon:**
- DNA'da rastgele değişiklikler
- Varyasyonun kaynağı
- Nadiren faydalı, çoğunlukla nötr veya zararlı

**3. Genetik Sürüklenme:**
- Küçük popülasyonlarda rastgele gen frekansı değişimi

**Kanıtlar:**
- Fosil kayıtları
- Karşılaştırmalı anatomi
- DNA benzerlikleri
- Embriyoloji

Tüm canlılar ortak atalardan evrilmiştir."""}
            ],
            "category": "biology"
        },
        # Daha fazla Türkçe örnek
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir fizik öğretmenisin."},
                {"role": "user", "content": "Elektrik akımı nedir?"},
                {"role": "assistant", "content": """Elektrik akımı, yüklü parçacıkların (genellikle elektronların) bir iletken içinde düzenli hareketidir.

**Temel Kavramlar:**
- **Akım (I):** Birim zamanda geçen yük miktarı. Birimi Amper (A)
- **Gerilim (V):** Elektrik potansiyel farkı. Birimi Volt (V)
- **Direnç (R):** Akıma karşı direnç. Birimi Ohm (Ω)

**Ohm Yasası:** V = I × R

**Akım Türleri:**
- **DC (Doğru Akım):** Tek yönlü akar (piller)
- **AC (Alternatif Akım):** Yön değiştirir (ev elektriği, 50 Hz)

Türkiye'de ev elektriği 220V AC'dir."""}
            ],
            "category": "physics"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir kimya öğretmenisin."},
                {"role": "user", "content": "Su molekülü neden özeldir?"},
                {"role": "assistant", "content": """Su (H₂O), eşsiz özelliklere sahip özel bir moleküldür:

**1. Polar Yapı:**
- Oksijen kısmen negatif, hidrojenler kısmen pozitif
- Bu sayede birçok maddeyi çözer ("evrensel çözücü")

**2. Hidrojen Bağları:**
- Moleküller arası güçlü çekim
- Yüksek kaynama noktası (100°C)
- Yüksek yüzey gerilimi

**3. Anomali Genleşme:**
- 4°C'de en yoğun
- Buz sudan hafif → göller yüzeyden donar
- Bu sayede canlılar kış boyunca yaşar

**4. Yüksek Özgül Isı:**
- Isıyı iyi depolar
- İklimi dengeler
- Vücut sıcaklığını düzenler

Su, yaşam için vazgeçilmezdir."""}
            ],
            "category": "chemistry"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir biyoloji öğretmenisin."},
                {"role": "user", "content": "Hücre nedir ve türleri nelerdir?"},
                {"role": "assistant", "content": """Hücre, yaşamın en küçük yapı ve işlev birimidir.

**İki Ana Tip:**

**1. Prokaryot Hücre:**
- Zarla çevrili çekirdeği yok
- DNA sitoplazmada serbest
- Organel yok (ribozom hariç)
- Örnek: Bakteriler, arkeler
- Boyut: 1-10 μm

**2. Ökaryot Hücre:**
- Zarla çevrili çekirdek var
- Organeller var: mitokondri, ER, golgi...
- Hayvan, bitki, mantar, protist
- Boyut: 10-100 μm

**Temel Organeller:**
- **Çekirdek:** DNA'yı barındırır
- **Mitokondri:** Enerji üretir (ATP)
- **Ribozom:** Protein sentezi
- **ER:** Madde taşınması
- **Golgi:** Paketleme ve salgılama

Bitki hücrelerinde ayrıca hücre duvarı ve kloroplast bulunur."""}
            ],
            "category": "biology"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir fizik öğretmenisin."},
                {"role": "user", "content": "Termodinamik yasaları nelerdir?"},
                {"role": "assistant", "content": """Termodinamik, ısı ve enerjinin davranışını inceler. Dört temel yasa vardır:

**0. Yasa (Termal Denge):**
İki sistem üçüncü bir sistemle termal dengedeyse, birbirleriyle de dengededir. (Termometre ilkesi)

**1. Yasa (Enerjinin Korunumu):**
Enerji yoktan var edilemez, var olan yok edilemez. Sadece form değiştirir.
ΔU = Q - W

**2. Yasa (Entropi):**
Kapalı bir sistemde entropi (düzensizlik) her zaman artar veya sabit kalır, asla azalmaz.
- Isı kendiliğinden soğuktan sıcağa akmaz
- Mükemmel verimli makine yapılamaz

**3. Yasa (Mutlak Sıfır):**
Mutlak sıfıra (0 K = -273.15°C) ulaşmak imkansızdır. Sıcaklık azaldıkça entropi sıfıra yaklaşır."""}
            ],
            "category": "physics"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir kimya öğretmenisin."},
                {"role": "user", "content": "Organik kimya nedir?"},
                {"role": "assistant", "content": """Organik kimya, karbon bileşiklerinin incelendiği kimya dalıdır.

**Neden Karbon Özel?**
- 4 bağ yapabilir
- Uzun zincirler ve halkalar oluşturur
- Yaşamın temeli

**Temel Organik Bileşik Sınıfları:**

1. **Hidrokarbonlar:** Sadece C ve H
   - Alkanlar (C-C): Metan, propan
   - Alkenler (C=C): Etilen
   - Alkinler (C≡C): Asetilen

2. **Fonksiyonel Gruplar:**
   - -OH (Alkol): Etanol
   - -COOH (Karboksil): Sirke asidi
   - -NH₂ (Amin): Proteinlerin yapı taşı
   - -CHO (Aldehit): Formaldehit

3. **Biyomoleküller:**
   - Karbonhidratlar (şekerler)
   - Lipitler (yağlar)
   - Proteinler
   - Nükleik asitler (DNA, RNA)"""}
            ],
            "category": "chemistry"
        },
        {
            "messages": [
                {"role": "system", "content": "Sen uzman bir biyoloji öğretmenisin."},
                {"role": "user", "content": "Sinir sistemi nasıl çalışır?"},
                {"role": "assistant", "content": """Sinir sistemi, vücudun iletişim ve kontrol merkezidir.

**Yapısı:**

**1. Merkezi Sinir Sistemi (MSS):**
- Beyin: Düşünme, bellek, duygu
- Omurilik: Refleksler, sinyal iletimi

**2. Çevresel Sinir Sistemi:**
- Somatik: İstemli hareketler
- Otonom: İstemsiz (kalp, sindirim)

**Sinir Hücresi (Nöron):**
- Dendrit: Sinyal alır
- Akson: Sinyal iletir
- Sinaps: Nöronlar arası bağlantı

**Sinyal İletimi:**
1. Elektriksel (aksiyon potansiyeli): Nöron içinde
2. Kimyasal (nörotransmitter): Nöronlar arasında

**Nörotransmitterler:**
- Dopamin: Ödül, motivasyon
- Serotonin: Ruh hali
- Asetilkolin: Kas hareketi
- GABA: Sakinleştirici"""}
            ],
            "category": "biology"
        },
    ]
    
    print(f"   ✓ {len(turkish_samples)} Türkçe örnek oluşturuldu")
    return turkish_samples


def main():
    """Ana fonksiyon."""
    output_dir = Path("data/training/science")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # SciQ indir
    sciq_examples = download_sciq()
    
    # Türkçe örnekler
    turkish_examples = create_turkish_science_samples()
    
    # SciQ'yu kaydet (İngilizce)
    sciq_path = output_dir / "sciq_data.jsonl"
    with open(sciq_path, "w", encoding="utf-8") as f:
        for example in sciq_examples:
            # Kategori bilgisini kaldır (sadece messages gerekli)
            output = {"messages": example["messages"]}
            f.write(json.dumps(output, ensure_ascii=False) + "\n")
    print(f"\n💾 SciQ kaydedildi: {sciq_path} ({len(sciq_examples)} örnek)")
    
    # Türkçe örnekleri kaydet
    turkish_path = output_dir / "turkish_science.jsonl"
    with open(turkish_path, "w", encoding="utf-8") as f:
        for example in turkish_examples:
            output = {"messages": example["messages"]}
            f.write(json.dumps(output, ensure_ascii=False) + "\n")
    print(f"💾 Türkçe bilim kaydedildi: {turkish_path} ({len(turkish_examples)} örnek)")
    
    # İstatistikler
    print(f"\n📊 Toplam:")
    print(f"   SciQ (İngilizce): {len(sciq_examples)}")
    print(f"   Türkçe: {len(turkish_examples)}")
    print(f"   Genel Toplam: {len(sciq_examples) + len(turkish_examples)}")


if __name__ == "__main__":
    main()
