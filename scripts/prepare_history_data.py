#!/usr/bin/env python3
"""
Tarih Veri Seti Hazırlayıcı

Türk tarihi, dünya tarihi ve kültür verileri için
MLX LoRA eğitim formatı.
"""

import json
from pathlib import Path
import random


def create_turkish_history_samples() -> list:
    """Türk tarihi ve kültürü örnekleri oluştur."""
    print("📝 Türk tarihi örnekleri oluşturuluyor...")
    
    samples = [
        # Osmanlı Dönemi
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin. Soruları detaylı ve doğru şekilde cevapla."},
                {"role": "user", "content": "Osmanlı İmparatorluğu ne zaman kuruldu ve hangi padişah tarafından?"},
                {"role": "assistant", "content": """Osmanlı İmparatorluğu 1299 yılında Osman Bey (Osman Gazi) tarafından kurulmuştur.

**Kuruluş Süreci:**
- Söğüt ve çevresinde küçük bir beylik olarak başladı
- Osman Bey, Selçuklu Sultanı'ndan bağımsızlık aldı
- İlk başkent Söğüt, sonra Bursa oldu

**Önemli Noktalar:**
- 1299 resmi kuruluş tarihi kabul edilir
- Osmanlı adı, kurucusu Osman Bey'den gelir
- 1922'ye kadar 623 yıl sürdü
- 36 padişah tahta çıktı"""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Fatih Sultan Mehmet kimdir ve neden önemlidir?"},
                {"role": "assistant", "content": """Fatih Sultan Mehmet (II. Mehmet), Osmanlı'nın 7. padişahıdır ve İstanbul'u fetheden hükümdardır.

**Hayatı (1432-1481):**
- Babası: II. Murad
- 12 yaşında ilk kez, 19 yaşında kalıcı olarak tahta çıktı

**İstanbul'un Fethi (29 Mayıs 1453):**
- Bizans İmparatorluğu'na son verdi
- Orta Çağ'ı bitirip Yeni Çağ'ı başlattı
- Gemileri karadan yürüttü (Haliç)
- Büyük toplar (Şahi) kullandı

**Diğer Fetihleri:**
- Sırbistan, Mora, Trabzon, Kırım
- 2 imparatorluk, 4 krallık, 6 prenslik fethetti

**Mirası:**
- "Fatih" (Fetheden) unvanını aldı
- Fatih Kanunnamesi'ni hazırlattı
- İstanbul'u başkent yaptı"""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Kanuni Sultan Süleyman dönemi hakkında bilgi ver."},
                {"role": "assistant", "content": """Kanuni Sultan Süleyman (I. Süleyman), Osmanlı'nın 10. padişahı ve en uzun süre tahtta kalan hükümdarıdır.

**Saltanat Süresi:** 1520-1566 (46 yıl)

**Neden "Kanuni":**
- Osmanlı hukuk sistemini düzenledi
- Kanunname-i Al-i Osman
- Adalet sistemini güçlendirdi

**Batı'da "Muhteşem Süleyman":**
- Osmanlı'nın en güçlü dönemini yaşattı
- Topraklar 3 kıtaya yayıldı

**Önemli Seferler:**
- Belgrad (1521), Rodos (1522)
- Mohaç Meydan Muharebesi (1526)
- Viyana Kuşatması (1529)
- Zigetvar (1566) - burada vefat etti

**Kültürel Dönem:**
- Mimar Sinan'ın eserleri (Süleymaniye Camii)
- Şiir (Muhibbi mahlası)
- Hürrem Sultan ile evliliği"""}
            ]
        },
        # Cumhuriyet Dönemi
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Mustafa Kemal Atatürk kimdir?"},
                {"role": "assistant", "content": """Mustafa Kemal Atatürk (1881-1938), Türkiye Cumhuriyeti'nin kurucusu ve ilk Cumhurbaşkanı'dır.

**Hayatı:**
- 1881'de Selanik'te doğdu
- Askeri okullarda eğitim aldı
- "Kemal" adını matematik öğretmeni verdi

**Askeri Başarıları:**
- Çanakkale Savaşı (1915) - "Çanakkale geçilmez!"
- Sakarya Meydan Muharebesi
- Büyük Taarruz ve Başkomutanlık

**Kurtuluş Savaşı (1919-1922):**
- 19 Mayıs 1919: Samsun'a çıkış
- Amasya, Erzurum, Sivas Kongreleri
- TBMM'nin açılışı (23 Nisan 1920)
- Zafer ve Lozan Antlaşması

**Cumhuriyet'in Kuruluşu:**
- 29 Ekim 1923: Cumhuriyet ilan edildi
- 15 yıl Cumhurbaşkanlığı yaptı
- 10 Kasım 1938'de vefat etti

**"Atatürk" Soyadı:** 1934'te TBMM tarafından verildi."""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Atatürk ilkeleri nelerdir?"},
                {"role": "assistant", "content": """Atatürk İlkeleri (Altı Ok), Türkiye Cumhuriyeti'nin temel ilkeleridir:

**1. Cumhuriyetçilik:**
- Halkın kendi kendini yönetmesi
- Egemenlik kayıtsız şartsız milletindir
- Seçimle gelen yönetim

**2. Milliyetçilik:**
- Türk milletinin birliği
- Irk ayrımı yapmayan, kültürel birlik
- "Ne mutlu Türk'üm diyene!"

**3. Halkçılık:**
- Sınıf ayrımı yok
- Herkes kanun önünde eşit
- Halkın refahı öncelik

**4. Devletçilik:**
- Ekonomide devlet öncülüğü
- Özel sektör ile işbirliği
- Kalkınma planları

**5. Laiklik:**
- Din ve devlet işlerinin ayrılması
- Vicdan özgürlüğü
- Eğitimde birlik

**6. İnkılapçılık (Devrimcilik):**
- Çağdaşlaşma
- Yeniliklere açıklık
- Eski düzeni değiştirme"""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Atatürk devrimleri nelerdir?"},
                {"role": "assistant", "content": """Atatürk Devrimleri, Türkiye'yi çağdaş medeniyetler seviyesine çıkarmak için yapılan köklü değişikliklerdir:

**Siyasi Devrimler:**
- Saltanatın kaldırılması (1922)
- Cumhuriyetin ilanı (1923)
- Halifeliğin kaldırılması (1924)

**Hukuki Devrimler:**
- Türk Medeni Kanunu (1926) - İsviçre'den
- Türk Ceza Kanunu - İtalya'dan
- Kadınlara seçme-seçilme hakkı (1934)

**Eğitim ve Kültür:**
- Tevhid-i Tedrisat (1924) - eğitim birliği
- Harf Devrimi (1928) - Latin alfabesi
- Türk Dil ve Tarih Kurumları

**Sosyal Devrimler:**
- Şapka Kanunu (1925)
- Tekke ve zaviyelerin kapatılması
- Uluslararası saat, takvim, ölçü birimleri
- Soyadı Kanunu (1934)

**Ekonomik Devrimler:**
- Aşar vergisinin kaldırılması
- Devlet bankaları kurulması
- Demiryolları yapımı"""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Kurtuluş Savaşı nasıl başladı ve sonuçlandı?"},
                {"role": "assistant", "content": """Kurtuluş Savaşı (1919-1922), Türk Bağımsızlık Savaşı olarak da bilinir.

**Başlangıç Nedenleri:**
- Mondros Mütarekesi (30 Ekim 1918)
- İşgaller: Yunan, İngiliz, Fransız, İtalyan
- Sevr Antlaşması tehdidi

**Önemli Olaylar:**
- 19 Mayıs 1919: Mustafa Kemal Samsun'a çıktı
- Amasya Genelgesi: "Milletin istiklalini yine milletin azmi kurtaracaktır"
- Erzurum ve Sivas Kongreleri
- 23 Nisan 1920: TBMM açıldı

**Savaşlar:**
- I. İnönü (1921)
- II. İnönü (1921)
- Sakarya Meydan Muharebesi (1921)
- Büyük Taarruz (26 Ağustos 1922)
- 9 Eylül 1922: İzmir'in kurtuluşu

**Sonuçlar:**
- Mudanya Mütarekesi (11 Ekim 1922)
- Lozan Antlaşması (24 Temmuz 1923)
- Cumhuriyetin ilanı (29 Ekim 1923)
- Tam bağımsız Türkiye"""}
            ]
        },
        # Selçuklu Dönemi
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Anadolu Selçuklu Devleti hakkında bilgi ver."},
                {"role": "assistant", "content": """Anadolu Selçuklu Devleti (1077-1308), Türklerin Anadolu'yu yurt edindiği ilk büyük devlettir.

**Kuruluş:**
- Kurucusu: Süleyman Şah (Kutalmışoğlu)
- 1077'de İznik merkez olmak üzere kuruldu
- Malazgirt Zaferi (1071) ile Anadolu kapıları açıldı

**Başkentler:**
- İznik → Konya (1097'den itibaren)

**Önemli Sultanlar:**
- I. Kılıç Arslan
- I. Mesud
- II. Kılıç Arslan
- I. Alaeddin Keykubad (en parlak dönem)

**Başarılar:**
- Anadolu'nun Türkleşmesi
- Ticaret yollarının güvenliği
- Kervansaraylar ve hanlar
- Medreseler ve hastaneler

**Yıkılış:**
- Moğol istilası (1243 Kösedağ)
- Beyliklere bölünme
- 1308'de son buldu

**Miras:**
- Osmanlı'ya zemin hazırladı
- Türk-İslam mimarisi gelişti"""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Malazgirt Savaşı neden önemlidir?"},
                {"role": "assistant", "content": """Malazgirt Meydan Muharebesi (26 Ağustos 1071), Türk tarihinin dönüm noktalarından biridir.

**Taraflar:**
- Büyük Selçuklu: Sultan Alparslan
- Bizans İmparatorluğu: IV. Romanos Diogenes

**Savaşın Sebebi:**
- Selçukluların Anadolu akınları
- Bizans'ın Selçuklu tehdidine son verme isteği

**Savaşın Sonucu:**
- Selçuklu zaferi
- Bizans İmparatoru esir alındı
- Bizans ordusu dağıtıldı

**Önemi:**
1. **Anadolu'nun Kapıları Açıldı:**
   - Türkler Anadolu'ya yerleşmeye başladı
   - Anadolu Türk yurdu oldu

2. **Bizans Zayıfladı:**
   - İmparatorluk bir daha toparlanamadı
   - Anadolu toprakları kaybedildi

3. **Türk Devletleri Kuruldu:**
   - Anadolu Selçuklu Devleti
   - Türkmen beylikleri
   - Osmanlı Devleti'nin temeli atıldı

"Anadolu'nun Türk yurdu olmasının başlangıcı" olarak kabul edilir."""}
            ]
        },
        # Türk Kültürü
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi ve kültürü konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Mimar Sinan kimdir ve eserleri nelerdir?"},
                {"role": "assistant", "content": """Mimar Sinan (1489-1588), Osmanlı'nın ve dünya mimarlık tarihinin en büyük mimarlarından biridir.

**Hayatı:**
- Kayseri/Ağırnas'ta doğdu
- Devşirme olarak saraya alındı
- Yeniçeri ocağında yetişti
- 50 yıl Hassa Mimarbaşılığı yaptı

**Eserleri:**
Toplam 365+ eser: 84 cami, 52 mescit, 57 medrese, 35 hamam...

**Üç Büyük Eseri:**

1. **Şehzade Camii (1548):** "Çıraklık eserim"
2. **Süleymaniye Camii (1557):** "Kalfalık eserim"
3. **Selimiye Camii (1575):** "Ustalık eserim"

**Diğer Önemli Eserleri:**
- Rüstem Paşa Camii
- Mihrimah Sultan Camileri
- Sokollu Mehmet Paşa Camii
- Mostar Köprüsü (Bosna)

**Mimari Dehası:**
- Büyük kubbeleri taşıma tekniği
- Işık ve akustik mükemmelliği
- Depreme dayanıklılık
- 99 yaşında vefat etti"""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Çanakkale Savaşı hakkında bilgi ver."},
                {"role": "assistant", "content": """Çanakkale Savaşları (1915-1916), I. Dünya Savaşı'nın en önemli cephelerinden biridir.

**Neden Çanakkale?**
- Müttefikler İstanbul'u almak istiyordu
- Rusya'ya yardım ulaştırma amacı
- Osmanlı'yı savaş dışı bırakma planı

**Deniz Savaşları:**
- 18 Mart 1915: Müttefik donanma yenildi
- 3 savaş gemisi battı
- Mayın hatları geçilemedi

**Kara Savaşları:**
- 25 Nisan 1915: Gelibolu çıkarması
- Arıburnu, Conkbayırı, Anafartalar
- 8.5 ay süren siper savaşları

**Mustafa Kemal'in Rolü:**
- 19. Tümen Komutanı
- "Ben size taarruzu değil, ölmeyi emrediyorum!"
- Conkbayırı ve Anafartalar'da zafer

**Sonuçlar:**
- Osmanlı zaferi
- İtilaf Devletleri çekildi (Ocak 1916)
- 250.000+ Türk şehit
- "Çanakkale geçilmez!" ruhu doğdu

**Önemi:**
- Atatürk'ün tanınması
- Milli ruhun uyanışı
- Kurtuluş Savaşı'na ilham"""}
            ]
        },
        # Coğrafya
        {
            "messages": [
                {"role": "system", "content": "Sen Türkiye coğrafyası konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Türkiye'nin coğrafi bölgeleri nelerdir?"},
                {"role": "assistant", "content": """Türkiye 7 coğrafi bölgeye ayrılır:

**1. Marmara Bölgesi:**
- En kalabalık ve gelişmiş bölge
- İstanbul, Bursa, Kocaeli
- Sanayi ve ticaret merkezi

**2. Ege Bölgesi:**
- Verimli ovalar (Gediz, Küçük Menderes)
- İzmir, Manisa, Aydın
- Turizm ve tarım

**3. Akdeniz Bölgesi:**
- Toros Dağları ve kıyı ovaları
- Antalya, Mersin, Adana
- Turizm, narenciye, pamuk

**4. İç Anadolu Bölgesi:**
- Türkiye'nin ortası
- Ankara (başkent), Konya, Kayseri
- Tahıl üretimi, step iklimi

**5. Karadeniz Bölgesi:**
- Dağlık, yağışlı
- Samsun, Trabzon, Rize
- Çay, fındık, mısır

**6. Doğu Anadolu Bölgesi:**
- En büyük, en yüksek bölge
- Erzurum, Van, Kars
- Hayvancılık, sert kış

**7. Güneydoğu Anadolu Bölgesi:**
- Mezopotamya'nın bir parçası
- Gaziantep, Diyarbakır, Şanlıurfa
- GAP Projesi, pamuk, tahıl"""}
            ]
        },
        # Daha fazla tarih örnekleri
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "İstanbul ne zaman fethedildi?"},
                {"role": "assistant", "content": """İstanbul, 29 Mayıs 1453'te Fatih Sultan Mehmet tarafından fethedildi.

**Fetih Öncesi:**
- Konstantinopolis, Bizans'ın başkentiydi
- 1000 yıllık tarih
- Daha önce birçok kuşatma başarısız olmuştu

**Fetih Süreci:**
- Kuşatma: 6 Nisan - 29 Mayıs 1453
- 53 gün sürdü
- 80.000-100.000 Osmanlı askeri
- Büyük toplar (Şahi topu)
- Gemiler karadan Haliç'e taşındı

**29 Mayıs 1453:**
- Surlar yıkıldı
- Şehir ele geçirildi
- Son Bizans İmparatoru XI. Konstantin öldü

**Sonuçları:**
- Bizans İmparatorluğu son buldu
- Orta Çağ bitti, Yeni Çağ başladı
- İstanbul Osmanlı başkenti oldu
- Doğu-Batı ticareti el değiştirdi
- Coğrafi keşiflere yol açtı"""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Lozan Antlaşması nedir?"},
                {"role": "assistant", "content": """Lozan Barış Antlaşması, 24 Temmuz 1923'te imzalanan, Türkiye Cumhuriyeti'nin uluslararası alanda tanındığı antlaşmadır.

**Taraflar:**
- Türkiye: İsmet İnönü başkanlığında heyet
- İtilaf Devletleri: İngiltere, Fransa, İtalya, Japonya, Yunanistan...

**Müzakereler:**
- Lozan, İsviçre'de yapıldı
- 8 ay sürdü (Kasım 1922 - Temmuz 1923)
- Çok zorlu pazarlıklar

**Kazanımlar:**
1. **Tam Bağımsızlık:**
   - Kapitülasyonlar kaldırıldı
   - Dış borçlar düzenlendi
   - Boğazlar Türk egemenliğine geçti

2. **Toprak Bütünlüğü:**
   - Doğu Trakya, Edirne
   - İstanbul
   - Boğazlar

3. **Sevr'in İptali:**
   - Sevr Antlaşması geçersiz oldu
   - Misak-ı Milli büyük ölçüde gerçekleşti

**Önemi:**
- Türkiye'nin uluslararası tanınması
- Bağımsız dış politikanın temeli
- "Lozan'da masa başında kazandık"
- Hala geçerliliğini koruyor"""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Göktürkler hakkında bilgi ver."},
                {"role": "assistant", "content": """Göktürk Kağanlığı (552-745), Türk adını kullanan ilk devlettir.

**Kuruluş:**
- 552'de Bumin Kağan tarafından kuruldu
- Avarların yıkılmasıyla bağımsız oldu
- Ötüken merkez seçildi

**Bölünme:**
- I. Göktürk: 552-630
- Fetret Devri: 630-682 (Çin egemenliği)
- II. Göktürk: 682-745

**Önemli Kağanlar:**
- Bumin Kağan (kurucu)
- Mukan Kağan (en güçlü dönem)
- İlteriş (Kutluk) Kağan (yeniden kurucu)
- Bilge Kağan ve Kül Tigin

**Orhun Yazıtları:**
- Türkçenin ilk yazılı belgeleri
- Bilge Kağan ve Kül Tigin adına dikildi
- 732-735 yıllarına ait
- Göktürk alfabesiyle yazıldı

**Mirası:**
- "Türk" adı ilk kez kullanıldı
- Türk alfabesi (runik)
- Devlet geleneği
- Orta Asya hakimiyeti

**Yıkılış:** Uygurlar tarafından 745'te son verildi."""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Sen Türk tarihi konusunda uzman bir tarihçisin."},
                {"role": "user", "content": "Osmanlı'da divan teşkilatı nasıl çalışırdı?"},
                {"role": "assistant", "content": """Divan-ı Hümayun, Osmanlı'nın en yüksek yönetim ve yargı organıydı.

**Toplantı Yeri ve Zamanı:**
- Topkapı Sarayı'nda Kubbealtı
- Haftada 4 gün (Cumartesi-Salı)
- Sabah namazından sonra

**Üyeleri:**
1. **Vezir-i Azam (Sadrazam):**
   - Başkan, padişahın vekili
   - Mühr-ü Hümayun'u taşır

2. **Kubbealtı Vezirleri:**
   - Yardımcı vezirler
   - 3-7 kişi

3. **Kazaskerler:**
   - Anadolu ve Rumeli kazaskeri
   - Adalet ve din işleri

4. **Defterdarlar:**
   - Maliye işleri
   - Anadolu ve Rumeli defterdarı

5. **Nişancı:**
   - Tuğra çeker
   - Yazışmaları düzenler

**Görevleri:**
- Devlet politikalarını belirleme
- Şikayetleri dinleme
- Davaları karara bağlama
- Tayin ve aziller

**Tanzimat Sonrası:**
- 1838'de Meclis-i Vala kuruldu
- 1876'da Meşrutiyet ilanı
- Parlamento sistemine geçiş"""}
            ]
        },
    ]
    
    print(f"   ✓ {len(samples)} Türk tarihi örneği oluşturuldu")
    return samples


def create_world_history_samples() -> list:
    """Dünya tarihi örnekleri oluştur."""
    print("📝 Dünya tarihi örnekleri oluşturuluyor...")
    
    samples = [
        {
            "messages": [
                {"role": "system", "content": "You are an expert historian. Answer questions accurately and in detail."},
                {"role": "user", "content": "What was the French Revolution?"},
                {"role": "assistant", "content": """The French Revolution (1789-1799) was a period of radical political and social change in France.

**Causes:**
- Financial crisis and debt
- Social inequality (Three Estates)
- Enlightenment ideas
- Food shortages

**Key Events:**
- Storming of the Bastille (July 14, 1789)
- Declaration of Rights of Man
- Reign of Terror (1793-1794)
- Rise of Napoleon Bonaparte

**Outcomes:**
- End of absolute monarchy
- Rise of nationalism
- Spread of democratic ideals
- Inspiration for other revolutions

The revolution's ideals of "Liberty, Equality, Fraternity" continue to influence politics worldwide."""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are an expert historian."},
                {"role": "user", "content": "When did World War I begin and end?"},
                {"role": "assistant", "content": """World War I (The Great War) lasted from July 28, 1914 to November 11, 1918.

**Start:** 
- Assassination of Archduke Franz Ferdinand (June 28, 1914)
- Austria-Hungary declared war on Serbia (July 28, 1914)

**Major Powers:**
- Allied Powers: France, Britain, Russia, Italy, USA (1917)
- Central Powers: Germany, Austria-Hungary, Ottoman Empire

**Key Battles:**
- Battle of the Marne
- Battle of Verdun
- Battle of the Somme
- Gallipoli Campaign

**End:**
- Armistice signed November 11, 1918
- Treaty of Versailles (1919)

**Casualties:** Over 17 million dead, 20 million wounded"""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are an expert historian."},
                {"role": "user", "content": "Who was Alexander the Great?"},
                {"role": "assistant", "content": """Alexander the Great (356-323 BCE) was a Macedonian king who created one of history's largest empires.

**Early Life:**
- Born in Pella, Macedonia
- Son of King Philip II
- Tutored by Aristotle

**Conquests (336-323 BCE):**
- Conquered Persian Empire
- Egypt (founded Alexandria)
- Central Asia to India
- Never lost a battle

**Major Battles:**
- Battle of Granicus (334 BCE)
- Battle of Issus (333 BCE)
- Battle of Gaugamela (331 BCE)

**Empire:**
- Stretched from Greece to India
- Over 5 million square kilometers
- Spread Greek culture (Hellenism)

**Death:**
- Died in Babylon at age 32
- Possibly fever, poison, or alcohol
- Empire divided among generals

Legacy: Spread of Greek culture, founding of cities, opening of East-West trade routes."""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are an expert historian."},
                {"role": "user", "content": "What was the Renaissance?"},
                {"role": "assistant", "content": """The Renaissance (14th-17th century) was a cultural and intellectual movement that began in Italy.

**Meaning:** "Rebirth" - revival of classical Greek and Roman culture

**Origins:**
- Started in Florence, Italy
- Wealthy merchant families (Medici)
- Fall of Constantinople (1453) brought scholars west

**Key Features:**
1. **Humanism:** Focus on human potential and achievements
2. **Art:** Perspective, realism, human form
3. **Science:** Observation and experimentation
4. **Literature:** Vernacular languages

**Famous Figures:**
- Leonardo da Vinci (artist, inventor)
- Michelangelo (sculptor, painter)
- Galileo Galilei (astronomer)
- William Shakespeare (playwright)
- Niccolò Machiavelli (political philosopher)

**Spread:**
- Northern Renaissance (Netherlands, Germany)
- England, France, Spain

**Impact:**
- Scientific Revolution
- Protestant Reformation
- Age of Exploration
- Modern thinking began"""}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are an expert historian."},
                {"role": "user", "content": "What caused World War II?"},
                {"role": "assistant", "content": """World War II (1939-1945) was caused by multiple interconnected factors:

**1. Treaty of Versailles (1919):**
- Harsh terms on Germany
- War guilt clause
- Massive reparations
- Territory losses

**2. Rise of Fascism:**
- Hitler in Germany (1933)
- Mussolini in Italy (1922)
- Militarism in Japan

**3. Great Depression (1929):**
- Economic collapse
- Unemployment
- Political extremism grew

**4. Appeasement Policy:**
- Britain and France avoided conflict
- Munich Agreement (1938)
- Allowed Nazi expansion

**5. Nazi Aggression:**
- Remilitarization of Rhineland (1936)
- Anschluss with Austria (1938)
- Annexation of Czechoslovakia (1939)

**Immediate Trigger:**
- Germany invaded Poland (September 1, 1939)
- Britain and France declared war (September 3, 1939)

**Result:** Deadliest conflict in history - 70-85 million deaths"""}
            ]
        },
    ]
    
    print(f"   ✓ {len(samples)} dünya tarihi örneği oluşturuldu")
    return samples


def main():
    """Ana fonksiyon."""
    output_dir = Path("data/training/history")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Türk tarihi örnekleri
    turkish_history = create_turkish_history_samples()
    
    # Dünya tarihi örnekleri
    world_history = create_world_history_samples()
    
    # Birleştir
    all_samples = turkish_history + world_history
    random.seed(42)
    random.shuffle(all_samples)
    
    # Train/Val split (%90/%10)
    split_idx = int(len(all_samples) * 0.9)
    train_data = all_samples[:split_idx]
    val_data = all_samples[split_idx:]
    
    # Türk tarihi örneklerini train'e ekstra ekle (önemli!)
    train_data.extend(turkish_history)
    random.shuffle(train_data)
    
    print(f"\n📊 Split:")
    print(f"   Train: {len(train_data)} örnek")
    print(f"   Validation: {len(val_data)} örnek")
    
    # Kaydet
    def save_jsonl(data, path):
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    save_jsonl(train_data, output_dir / "train.jsonl")
    save_jsonl(val_data, output_dir / "valid.jsonl")
    
    # Tüm örnekleri de kaydet
    save_jsonl(turkish_history, output_dir / "turkish_history.jsonl")
    save_jsonl(world_history, output_dir / "world_history.jsonl")
    
    print(f"\n💾 Dosyalar kaydedildi:")
    print(f"   {output_dir}/train.jsonl ({len(train_data)} örnek)")
    print(f"   {output_dir}/valid.jsonl ({len(val_data)} örnek)")
    print(f"   {output_dir}/turkish_history.jsonl ({len(turkish_history)} örnek)")
    print(f"   {output_dir}/world_history.jsonl ({len(world_history)} örnek)")


if __name__ == "__main__":
    main()
