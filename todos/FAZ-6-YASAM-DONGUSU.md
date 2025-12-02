# 🔄 FAZ 6: Yaşam Döngüsü - Sync/Async Otomasyon (The Loop)

**Durum:** ⬜ Başlanmadı  
**Tahmini Süre:** 2-3 gün  
**Öncelik:** 🟡 Orta  
**Bağımlılık:** Faz 0-5 tamamlanmış olmalı

---

## 🎯 Faz Hedefi

Sistemin kendi kendini güncelleyebilmesini sağlayan otomasyon katmanını oluşturmak. "Gündüz Modu" (gerçek zamanlı sohbet) ve "Gece Modu" (log analizi, hafıza güncelleme, self-improvement) ayrımı ile biyolojik bir öğrenme döngüsü simüle edilecek.

---

## 🏗️ Mimari Genel Bakış

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YAŞAM DÖNGÜSÜ (24 SAAT)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     GÜNDÜZ MODU (SYNC)                              │    │
│  │                     08:00 - 00:00                                   │    │
│  │                                                                     │    │
│  │   ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐ │    │
│  │   │  Kullanıcı│───▶│  Router   │───▶│  Inference│───▶│  Response │ │    │
│  │   │  Mesajı   │    │           │    │           │    │           │ │    │
│  │   └───────────┘    └───────────┘    └───────────┘    └───────────┘ │    │
│  │         │                                                  │       │    │
│  │         ▼                                                  ▼       │    │
│  │   ┌─────────────────────────────────────────────────────────────┐ │    │
│  │   │                      LOG DOSYASI                            │ │    │
│  │   │  logs/conversations/2024-12-02.jsonl                        │ │    │
│  │   │                                                             │ │    │
│  │   │  {"timestamp": "...", "user": "...", "response": "...", ... }│ │    │
│  │   └─────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      GECE MODU (ASYNC)                              │    │
│  │                      00:00 - 08:00 (veya manuel)                    │    │
│  │                                                                     │    │
│  │   ┌─────────────────────────────────────────────────────────────┐   │    │
│  │   │                   GECE SCRIPTİ                              │   │    │
│  │   │                                                             │   │    │
│  │   │  1. LOG ANALİZİ                                             │   │    │
│  │   │     - Günlük logları oku                                    │   │    │
│  │   │     - Başarısız yanıtları tespit et                         │   │    │
│  │   │     - Pattern analizi yap                                   │   │    │
│  │   │                                                             │   │    │
│  │   │  2. BİLGİ ÇIKARIMI                                          │   │    │
│  │   │     - NER (Named Entity Recognition)                        │   │    │
│  │   │     - Keyword extraction                                    │   │    │
│  │   │     - Önemli bilgileri işaretle                             │   │    │
│  │   │                                                             │   │    │
│  │   │  3. HAFIZA GÜNCELLEMESİ                                     │   │    │
│  │   │     - ChromaDB'ye yeni bilgiler ekle                        │   │    │
│  │   │     - Eski/yanlış bilgileri güncelle                        │   │    │
│  │   │     - Duplicate temizliği                                   │   │    │
│  │   │                                                             │   │    │
│  │   │  4. RAPOR OLUŞTURMA                                         │   │    │
│  │   │     - Günlük özet                                           │   │    │
│  │   │     - Hata oranları                                         │   │    │
│  │   │     - İyileştirme önerileri                                 │   │    │
│  │   └─────────────────────────────────────────────────────────────┘   │    │
│  │                                      │                              │    │
│  │                                      ▼                              │    │
│  │   ┌─────────────────────────────────────────────────────────────┐   │    │
│  │   │              (İLERİ SEVİYE) ÖZ-EĞİTİM                       │   │    │
│  │   │                                                             │   │    │
│  │   │  - Hata yapılan konuları tespit et                          │   │    │
│  │   │  - Yeni eğitim verisi öner                                  │   │    │
│  │   │  - LoRA re-training tetikle (manuel onay)                   │   │    │
│  │   └─────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Detaylı Görev Listesi

### 6.1 Gündüz Modu Geliştirme (Sync Handler)

#### 6.1.1 Session Manager
- [ ] `src/lifecycle/session_manager.py` oluştur:
  ```python
  """
  EVO-TR Session Yöneticisi
  
  Kullanıcı session'larını takip eder.
  """
  
  from datetime import datetime, timedelta
  from typing import Optional, Dict
  from dataclasses import dataclass, field
  import uuid
  
  
  @dataclass
  class Session:
      """Kullanıcı session'ı"""
      session_id: str
      created_at: datetime
      last_activity: datetime
      message_count: int = 0
      metadata: Dict = field(default_factory=dict)
      
      def is_expired(self, timeout_minutes: int = 30) -> bool:
          """Session süresi doldu mu?"""
          return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)
      
      def touch(self) -> None:
          """Aktiviteyi güncelle"""
          self.last_activity = datetime.now()
          self.message_count += 1
  
  
  class SessionManager:
      """Session yöneticisi"""
      
      def __init__(self, timeout_minutes: int = 30):
          self.timeout_minutes = timeout_minutes
          self.sessions: Dict[str, Session] = {}
          self.current_session_id: Optional[str] = None
      
      def create_session(self, metadata: Optional[Dict] = None) -> Session:
          """Yeni session oluştur"""
          session_id = str(uuid.uuid4())[:8]
          now = datetime.now()
          
          session = Session(
              session_id=session_id,
              created_at=now,
              last_activity=now,
              metadata=metadata or {}
          )
          
          self.sessions[session_id] = session
          self.current_session_id = session_id
          
          return session
      
      def get_current_session(self) -> Optional[Session]:
          """Mevcut session'ı getir"""
          if not self.current_session_id:
              return None
          
          session = self.sessions.get(self.current_session_id)
          
          if session and session.is_expired(self.timeout_minutes):
              self.end_session(self.current_session_id)
              return None
          
          return session
      
      def get_or_create_session(self) -> Session:
          """Session getir veya oluştur"""
          session = self.get_current_session()
          if session:
              return session
          return self.create_session()
      
      def end_session(self, session_id: str) -> Optional[Session]:
          """Session'ı sonlandır"""
          if session_id in self.sessions:
              session = self.sessions.pop(session_id)
              if self.current_session_id == session_id:
                  self.current_session_id = None
              return session
          return None
      
      def cleanup_expired(self) -> int:
          """Süresi dolmuş session'ları temizle"""
          expired = [
              sid for sid, session in self.sessions.items()
              if session.is_expired(self.timeout_minutes)
          ]
          
          for sid in expired:
              self.end_session(sid)
          
          return len(expired)
      
      def get_stats(self) -> Dict:
          """Session istatistikleri"""
          return {
              "active_sessions": len(self.sessions),
              "current_session": self.current_session_id,
              "timeout_minutes": self.timeout_minutes
          }
  
  
  # Singleton
  _session_manager: Optional[SessionManager] = None
  
  
  def get_session_manager() -> SessionManager:
      global _session_manager
      if _session_manager is None:
          _session_manager = SessionManager()
      return _session_manager
  ```

#### 6.1.2 Sync Handler
- [ ] `src/lifecycle/sync_handler.py` oluştur:
  ```python
  """
  EVO-TR Gündüz Modu (Sync Handler)
  
  Gerçek zamanlı sohbet işlemleri.
  """
  
  from typing import Optional, Callable
  from datetime import datetime
  
  from ..orchestrator import get_orchestrator, Response
  from .session_manager import get_session_manager
  from .logger import get_conversation_logger
  
  
  class SyncHandler:
      """Gerçek zamanlı sohbet handler'ı"""
      
      def __init__(
          self,
          on_response: Optional[Callable[[Response], None]] = None,
          on_error: Optional[Callable[[Exception], None]] = None
      ):
          self.orchestrator = get_orchestrator()
          self.session_manager = get_session_manager()
          self.logger = get_conversation_logger()
          
          self.on_response = on_response
          self.on_error = on_error
          
          self._running = False
      
      def start(self) -> None:
          """Handler'ı başlat"""
          self._running = True
          self.session_manager.get_or_create_session()
          print("✅ SyncHandler başlatıldı")
      
      def stop(self) -> None:
          """Handler'ı durdur"""
          self._running = False
          session = self.session_manager.get_current_session()
          if session:
              self.session_manager.end_session(session.session_id)
          print("✅ SyncHandler durduruldu")
      
      def process_message(self, user_message: str) -> Response:
          """
          Kullanıcı mesajını işle.
          
          Args:
              user_message: Kullanıcı mesajı
              
          Returns:
              Response objesi
          """
          if not self._running:
              raise RuntimeError("SyncHandler çalışmıyor")
          
          # Session güncelle
          session = self.session_manager.get_or_create_session()
          session.touch()
          
          try:
              # Orchestrator ile yanıt üret
              response = self.orchestrator.chat(user_message)
              
              # Logla
              self.logger.log_interaction(
                  user_message=user_message,
                  response_text=response.text,
                  intent=response.intent,
                  confidence=response.confidence,
                  adapter_used=response.adapter_used,
                  processing_time=response.processing_time,
                  metadata={
                      "session_id": session.session_id,
                      "message_number": session.message_count
                  }
              )
              
              # Callback
              if self.on_response:
                  self.on_response(response)
              
              return response
              
          except Exception as e:
              if self.on_error:
                  self.on_error(e)
              raise
      
      def get_session_info(self) -> dict:
          """Mevcut session bilgisi"""
          session = self.session_manager.get_current_session()
          if session:
              return {
                  "session_id": session.session_id,
                  "started": session.created_at.isoformat(),
                  "messages": session.message_count,
                  "last_activity": session.last_activity.isoformat()
              }
          return {"status": "no_active_session"}
  
  
  # Singleton
  _sync_handler: Optional[SyncHandler] = None
  
  
  def get_sync_handler() -> SyncHandler:
      global _sync_handler
      if _sync_handler is None:
          _sync_handler = SyncHandler()
      return _sync_handler
  ```

---

### 6.2 Gece Modu Geliştirme (Async Processor)

#### 6.2.1 Log Analyzer
- [ ] `src/lifecycle/log_analyzer.py` oluştur:
  ```python
  """
  EVO-TR Log Analiz Modülü
  
  Günlük logları analiz eder ve içgörüler çıkarır.
  """
  
  import json
  from datetime import datetime, timedelta
  from pathlib import Path
  from typing import List, Dict, Optional
  from collections import Counter
  from dataclasses import dataclass
  
  
  @dataclass
  class DailyStats:
      """Günlük istatistikler"""
      date: str
      total_messages: int
      unique_sessions: int
      avg_processing_time: float
      intent_distribution: Dict[str, int]
      adapter_usage: Dict[str, int]
      avg_confidence: float
      low_confidence_count: int  # < 0.7
      error_count: int
  
  
  @dataclass
  class FailedInteraction:
      """Başarısız etkileşim"""
      timestamp: str
      user_message: str
      response: str
      intent: str
      confidence: float
      reason: str  # low_confidence, empty_response, error
  
  
  class LogAnalyzer:
      """Log analiz aracı"""
      
      def __init__(self, log_dir: str = "./logs/conversations"):
          self.log_dir = Path(log_dir)
      
      def load_logs(self, date: str) -> List[Dict]:
          """Belirli bir günün loglarını yükle"""
          log_file = self.log_dir / f"{date}.jsonl"
          
          if not log_file.exists():
              return []
          
          logs = []
          with open(log_file, "r", encoding="utf-8") as f:
              for line in f:
                  try:
                      logs.append(json.loads(line))
                  except json.JSONDecodeError:
                      continue
          
          return logs
      
      def analyze_day(self, date: Optional[str] = None) -> DailyStats:
          """Günlük analiz"""
          if date is None:
              date = datetime.now().strftime("%Y-%m-%d")
          
          logs = self.load_logs(date)
          
          if not logs:
              return DailyStats(
                  date=date,
                  total_messages=0,
                  unique_sessions=0,
                  avg_processing_time=0,
                  intent_distribution={},
                  adapter_usage={},
                  avg_confidence=0,
                  low_confidence_count=0,
                  error_count=0
              )
          
          # İstatistikleri hesapla
          sessions = set()
          intents = Counter()
          adapters = Counter()
          processing_times = []
          confidences = []
          low_confidence = 0
          errors = 0
          
          for log in logs:
              # Session
              session_id = log.get("metadata", {}).get("session_id")
              if session_id:
                  sessions.add(session_id)
              
              # Intent
              intent = log.get("intent", "unknown")
              intents[intent] += 1
              
              # Adapter
              adapter = log.get("adapter", "unknown")
              adapters[adapter] += 1
              
              # Metrics
              if "processing_time" in log:
                  processing_times.append(log["processing_time"])
              
              confidence = log.get("confidence", 0)
              confidences.append(confidence)
              
              if confidence < 0.7:
                  low_confidence += 1
              
              if log.get("error"):
                  errors += 1
          
          return DailyStats(
              date=date,
              total_messages=len(logs),
              unique_sessions=len(sessions),
              avg_processing_time=sum(processing_times) / len(processing_times) if processing_times else 0,
              intent_distribution=dict(intents),
              adapter_usage=dict(adapters),
              avg_confidence=sum(confidences) / len(confidences) if confidences else 0,
              low_confidence_count=low_confidence,
              error_count=errors
          )
      
      def find_failed_interactions(
          self, 
          date: Optional[str] = None,
          confidence_threshold: float = 0.7
      ) -> List[FailedInteraction]:
          """Başarısız etkileşimleri bul"""
          if date is None:
              date = datetime.now().strftime("%Y-%m-%d")
          
          logs = self.load_logs(date)
          failed = []
          
          for log in logs:
              reason = None
              
              # Düşük confidence
              if log.get("confidence", 0) < confidence_threshold:
                  reason = "low_confidence"
              
              # Boş yanıt
              elif not log.get("response") or len(log.get("response", "")) < 10:
                  reason = "empty_response"
              
              # Hata
              elif log.get("error"):
                  reason = "error"
              
              if reason:
                  failed.append(FailedInteraction(
                      timestamp=log.get("timestamp", ""),
                      user_message=log.get("user_message", ""),
                      response=log.get("response", ""),
                      intent=log.get("intent", ""),
                      confidence=log.get("confidence", 0),
                      reason=reason
                  ))
          
          return failed
      
      def extract_patterns(self, date: Optional[str] = None) -> Dict:
          """Konuşma pattern'larını çıkar"""
          if date is None:
              date = datetime.now().strftime("%Y-%m-%d")
          
          logs = self.load_logs(date)
          
          # Sık kullanılan kelimeler
          word_freq = Counter()
          for log in logs:
              words = log.get("user_message", "").lower().split()
              word_freq.update(words)
          
          # Stop words filtrele
          stop_words = {"bir", "bu", "şu", "ne", "nasıl", "mi", "mı", "mu", "mü", "ve", "için", "ile"}
          word_freq = {k: v for k, v in word_freq.items() if k not in stop_words and len(k) > 2}
          
          # En sık 20 kelime
          top_words = dict(Counter(word_freq).most_common(20))
          
          return {
              "date": date,
              "top_keywords": top_words,
              "total_unique_words": len(word_freq)
          }
  
  
  # Singleton
  _log_analyzer: Optional[LogAnalyzer] = None
  
  
  def get_log_analyzer() -> LogAnalyzer:
      global _log_analyzer
      if _log_analyzer is None:
          _log_analyzer = LogAnalyzer()
      return _log_analyzer
  ```

#### 6.2.2 Information Extractor
- [ ] `src/lifecycle/info_extractor.py` oluştur:
  ```python
  """
  EVO-TR Bilgi Çıkarım Modülü
  
  Konuşmalardan önemli bilgileri çıkarır.
  """
  
  import re
  from typing import List, Dict, Optional
  from dataclasses import dataclass
  
  
  @dataclass
  class ExtractedInfo:
      """Çıkarılan bilgi"""
      info_type: str  # user_name, project_name, preference, fact
      value: str
      source_text: str
      confidence: float
  
  
  class InformationExtractor:
      """Bilgi çıkarım aracı"""
      
      # Pattern'lar
      PATTERNS = {
          "user_name": [
              r"benim ad[ıi]m (\w+)",
              r"ad[ıi]m (\w+)",
              r"ben (\w+)[,\.]",
              r"(\w+) olarak çağır"
          ],
          "project_name": [
              r"proje(?:nin)? ad[ıi] (\w+)",
              r"(\w+) projes[ıi]",
              r"(\w+) (?:isimli|adlı) proje"
          ],
          "preference": [
              r"(\w+) sever[ıi]m",
              r"(\w+) tercih eder[ıi]m",
              r"(\w+) kullan[ıi]yor[u]?m",
              r"(\w+) favorim"
          ],
          "location": [
              r"(\w+)'(?:da|de|ta|te) yaşıyorum",
              r"(\w+)'(?:da|de|ta|te) oturuyorum",
              r"(\w+) şehrind[ea]"
          ]
      }
      
      def extract_from_text(self, text: str) -> List[ExtractedInfo]:
          """Metinden bilgi çıkar"""
          extracted = []
          text_lower = text.lower()
          
          for info_type, patterns in self.PATTERNS.items():
              for pattern in patterns:
                  matches = re.finditer(pattern, text_lower)
                  for match in matches:
                      value = match.group(1).title()
                      
                      # Basit confidence hesaplama
                      confidence = 0.8 if len(value) > 2 else 0.5
                      
                      extracted.append(ExtractedInfo(
                          info_type=info_type,
                          value=value,
                          source_text=text,
                          confidence=confidence
                      ))
          
          return extracted
      
      def extract_from_logs(self, logs: List[Dict]) -> List[ExtractedInfo]:
          """Log listesinden bilgi çıkar"""
          all_extracted = []
          
          for log in logs:
              user_msg = log.get("user_message", "")
              response = log.get("response", "")
              
              # Kullanıcı mesajından çıkar
              extracted = self.extract_from_text(user_msg)
              all_extracted.extend(extracted)
              
              # Yanıttan da çıkar (daha düşük priority)
              response_extracted = self.extract_from_text(response)
              for info in response_extracted:
                  info.confidence *= 0.8  # Yanıttan çıkarılan daha az güvenilir
              all_extracted.extend(response_extracted)
          
          # Duplicate'ları kaldır
          unique = {}
          for info in all_extracted:
              key = (info.info_type, info.value)
              if key not in unique or info.confidence > unique[key].confidence:
                  unique[key] = info
          
          return list(unique.values())
  
  
  # Singleton
  _extractor: Optional[InformationExtractor] = None
  
  
  def get_info_extractor() -> InformationExtractor:
      global _extractor
      if _extractor is None:
          _extractor = InformationExtractor()
      return _extractor
  ```

#### 6.2.3 Night Processor (Gece Script'i)
- [ ] `src/lifecycle/async_processor.py` oluştur:
  ```python
  """
  EVO-TR Gece Modu (Async Processor)
  
  Günlük logları analiz eder ve sistemi günceller.
  """
  
  from datetime import datetime, timedelta
  from typing import Dict, List, Optional
  from pathlib import Path
  import json
  
  from .log_analyzer import get_log_analyzer, DailyStats
  from .info_extractor import get_info_extractor, ExtractedInfo
  from ..memory.chromadb_handler import get_memory_handler
  
  
  class AsyncProcessor:
      """Gece işlem motoru"""
      
      def __init__(self, report_dir: str = "./logs/reports"):
          self.log_analyzer = get_log_analyzer()
          self.info_extractor = get_info_extractor()
          self.memory = get_memory_handler()
          self.report_dir = Path(report_dir)
          self.report_dir.mkdir(parents=True, exist_ok=True)
      
      def process_day(self, date: Optional[str] = None) -> Dict:
          """
          Bir günün verilerini işle.
          
          Args:
              date: İşlenecek tarih (YYYY-MM-DD). None ise dün.
              
          Returns:
              İşlem raporu
          """
          if date is None:
              yesterday = datetime.now() - timedelta(days=1)
              date = yesterday.strftime("%Y-%m-%d")
          
          print(f"\n🌙 Gece işlemi başlıyor: {date}")
          
          report = {
              "date": date,
              "processed_at": datetime.now().isoformat(),
              "steps": {}
          }
          
          # 1. Log Analizi
          print("📊 1/4 Log analizi yapılıyor...")
          stats = self.log_analyzer.analyze_day(date)
          report["steps"]["log_analysis"] = {
              "total_messages": stats.total_messages,
              "unique_sessions": stats.unique_sessions,
              "avg_confidence": round(stats.avg_confidence, 3),
              "low_confidence_count": stats.low_confidence_count
          }
          print(f"   ✅ {stats.total_messages} mesaj, {stats.unique_sessions} session analiz edildi")
          
          # 2. Başarısız etkileşimler
          print("⚠️ 2/4 Başarısız etkileşimler bulunuyor...")
          failed = self.log_analyzer.find_failed_interactions(date)
          report["steps"]["failed_interactions"] = {
              "count": len(failed),
              "reasons": {}
          }
          for f in failed:
              reason = f.reason
              report["steps"]["failed_interactions"]["reasons"][reason] = \
                  report["steps"]["failed_interactions"]["reasons"].get(reason, 0) + 1
          print(f"   ✅ {len(failed)} başarısız etkileşim bulundu")
          
          # 3. Bilgi çıkarımı
          print("🧠 3/4 Bilgi çıkarımı yapılıyor...")
          logs = self.log_analyzer.load_logs(date)
          extracted = self.info_extractor.extract_from_logs(logs)
          report["steps"]["info_extraction"] = {
              "count": len(extracted),
              "types": {}
          }
          
          # Hafızaya ekle
          added_to_memory = 0
          for info in extracted:
              if info.confidence >= 0.7:  # Sadece yüksek güvenilirliktekileri ekle
                  self.memory.add_memory(
                      text=f"{info.info_type}: {info.value}",
                      metadata={
                          "extracted_from": "night_process",
                          "date": date,
                          "confidence": info.confidence
                      },
                      memory_type=info.info_type
                  )
                  added_to_memory += 1
                  
                  report["steps"]["info_extraction"]["types"][info.info_type] = \
                      report["steps"]["info_extraction"]["types"].get(info.info_type, 0) + 1
          
          print(f"   ✅ {len(extracted)} bilgi çıkarıldı, {added_to_memory} hafızaya eklendi")
          report["steps"]["info_extraction"]["added_to_memory"] = added_to_memory
          
          # 4. Pattern analizi
          print("🔍 4/4 Pattern analizi yapılıyor...")
          patterns = self.log_analyzer.extract_patterns(date)
          report["steps"]["patterns"] = {
              "top_keywords": list(patterns["top_keywords"].keys())[:10],
              "unique_words": patterns["total_unique_words"]
          }
          print(f"   ✅ {patterns['total_unique_words']} unique kelime analiz edildi")
          
          # Raporu kaydet
          report_file = self.report_dir / f"{date}_report.json"
          with open(report_file, "w", encoding="utf-8") as f:
              json.dump(report, f, ensure_ascii=False, indent=2)
          
          print(f"\n✅ Gece işlemi tamamlandı!")
          print(f"📄 Rapor: {report_file}")
          
          return report
      
      def generate_improvement_suggestions(self, date: Optional[str] = None) -> List[Dict]:
          """
          İyileştirme önerileri oluştur.
          
          Args:
              date: Analiz edilecek tarih
              
          Returns:
              Öneri listesi
          """
          if date is None:
              yesterday = datetime.now() - timedelta(days=1)
              date = yesterday.strftime("%Y-%m-%d")
          
          suggestions = []
          
          stats = self.log_analyzer.analyze_day(date)
          failed = self.log_analyzer.find_failed_interactions(date)
          
          # Düşük confidence oranı yüksekse
          if stats.total_messages > 0:
              low_conf_ratio = stats.low_confidence_count / stats.total_messages
              if low_conf_ratio > 0.2:  # %20'den fazla
                  suggestions.append({
                      "type": "router_improvement",
                      "priority": "high",
                      "description": f"Router güvenilirliği düşük (%{low_conf_ratio*100:.0f} düşük confidence). "
                                     "Intent veri setine daha fazla örnek eklenebilir.",
                      "metric": f"{stats.low_confidence_count}/{stats.total_messages}"
                  })
          
          # Belirli intent'te çok hata varsa
          for intent, count in stats.intent_distribution.items():
              intent_fails = sum(1 for f in failed if f.intent == intent)
              if count > 5 and intent_fails / count > 0.3:
                  suggestions.append({
                      "type": "adapter_improvement",
                      "priority": "medium",
                      "description": f"'{intent}' intent'inde yüksek hata oranı (%{intent_fails/count*100:.0f}). "
                                     f"İlgili LoRA adapter eğitim verisi artırılabilir.",
                      "metric": f"{intent_fails}/{count}"
                  })
          
          # Processing time yüksekse
          if stats.avg_processing_time > 5.0:  # 5 saniyeden fazla
              suggestions.append({
                  "type": "performance",
                  "priority": "low",
                  "description": f"Ortalama yanıt süresi yüksek ({stats.avg_processing_time:.1f}s). "
                                 "Model quantization veya cache optimizasyonu düşünülebilir.",
                  "metric": f"{stats.avg_processing_time:.1f}s"
              })
          
          return suggestions
  
  
  # Singleton
  _async_processor: Optional[AsyncProcessor] = None
  
  
  def get_async_processor() -> AsyncProcessor:
      global _async_processor
      if _async_processor is None:
          _async_processor = AsyncProcessor()
      return _async_processor
  ```

#### 6.2.4 Night Process CLI
- [ ] `scripts/night_processor.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """
  EVO-TR Gece İşlem Script'i
  
  Kullanım:
      python scripts/night_processor.py                    # Dünü işle
      python scripts/night_processor.py --date 2024-12-01  # Belirli tarihi işle
      python scripts/night_processor.py --days 7           # Son 7 günü işle
  """
  
  import argparse
  from datetime import datetime, timedelta
  from rich.console import Console
  from rich.table import Table
  from rich.panel import Panel
  
  import sys
  sys.path.append(".")
  
  from src.lifecycle.async_processor import get_async_processor
  
  console = Console()
  
  
  def main():
      parser = argparse.ArgumentParser(description="EVO-TR Gece İşlem Script'i")
      parser.add_argument("--date", type=str, help="İşlenecek tarih (YYYY-MM-DD)")
      parser.add_argument("--days", type=int, default=1, help="Son N günü işle")
      parser.add_argument("--suggestions", action="store_true", help="İyileştirme önerilerini göster")
      args = parser.parse_args()
      
      console.print(Panel(
          "[bold blue]🌙 EVO-TR Gece İşlemi[/bold blue]\n"
          "Log analizi ve hafıza güncelleme",
          expand=False
      ))
      
      processor = get_async_processor()
      
      # İşlenecek tarihleri belirle
      if args.date:
          dates = [args.date]
      else:
          dates = []
          for i in range(args.days):
              date = datetime.now() - timedelta(days=i+1)
              dates.append(date.strftime("%Y-%m-%d"))
      
      # Her tarihi işle
      all_reports = []
      for date in dates:
          report = processor.process_day(date)
          all_reports.append(report)
      
      # Özet tablo
      console.print("\n")
      
      table = Table(title="İşlem Özeti")
      table.add_column("Tarih", style="cyan")
      table.add_column("Mesaj", style="green")
      table.add_column("Session", style="yellow")
      table.add_column("Başarısız", style="red")
      table.add_column("Hafızaya Eklenen", style="magenta")
      
      for report in all_reports:
          la = report["steps"]["log_analysis"]
          fi = report["steps"]["failed_interactions"]
          ie = report["steps"]["info_extraction"]
          
          table.add_row(
              report["date"],
              str(la["total_messages"]),
              str(la["unique_sessions"]),
              str(fi["count"]),
              str(ie["added_to_memory"])
          )
      
      console.print(table)
      
      # İyileştirme önerileri
      if args.suggestions:
          console.print("\n[bold]📋 İyileştirme Önerileri:[/bold]\n")
          
          for date in dates:
              suggestions = processor.generate_improvement_suggestions(date)
              
              if suggestions:
                  console.print(f"[cyan]{date}:[/cyan]")
                  for s in suggestions:
                      priority_color = {
                          "high": "red",
                          "medium": "yellow",
                          "low": "green"
                      }.get(s["priority"], "white")
                      
                      console.print(f"  [{priority_color}][{s['priority'].upper()}][/{priority_color}] {s['description']}")
                  console.print()
              else:
                  console.print(f"[cyan]{date}:[/cyan] ✅ Öneri yok, her şey yolunda!\n")
  
  
  if __name__ == "__main__":
      main()
  ```

---

### 6.3 Zamanlama ve Otomasyon

#### 6.3.1 Launchd Plist (macOS)
- [ ] `scripts/com.evo-tr.night-processor.plist` oluştur:
  ```xml
  <?xml version="1.0" encoding="UTF-8"?>
  <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
  <plist version="1.0">
  <dict>
      <key>Label</key>
      <string>com.evo-tr.night-processor</string>
      
      <key>ProgramArguments</key>
      <array>
          <string>/Users/kaan/Desktop/Kaan/Personal/agı-llm/.venv/bin/python</string>
          <string>/Users/kaan/Desktop/Kaan/Personal/agı-llm/scripts/night_processor.py</string>
          <string>--suggestions</string>
      </array>
      
      <key>WorkingDirectory</key>
      <string>/Users/kaan/Desktop/Kaan/Personal/agı-llm</string>
      
      <key>StartCalendarInterval</key>
      <dict>
          <key>Hour</key>
          <integer>3</integer>
          <key>Minute</key>
          <integer>0</integer>
      </dict>
      
      <key>StandardOutPath</key>
      <string>/Users/kaan/Desktop/Kaan/Personal/agı-llm/logs/night_processor.log</string>
      
      <key>StandardErrorPath</key>
      <string>/Users/kaan/Desktop/Kaan/Personal/agı-llm/logs/night_processor.error.log</string>
      
      <key>EnvironmentVariables</key>
      <dict>
          <key>PATH</key>
          <string>/usr/local/bin:/usr/bin:/bin</string>
      </dict>
  </dict>
  </plist>
  ```

#### 6.3.2 Launchd Kurulum
- [ ] Kurulum script'i oluştur:
  ```bash
  # Plist'i kopyala
  cp scripts/com.evo-tr.night-processor.plist ~/Library/LaunchAgents/
  
  # Yükle
  launchctl load ~/Library/LaunchAgents/com.evo-tr.night-processor.plist
  
  # Durumu kontrol et
  launchctl list | grep evo-tr
  
  # Manuel çalıştır (test için)
  launchctl start com.evo-tr.night-processor
  
  # Kaldır
  # launchctl unload ~/Library/LaunchAgents/com.evo-tr.night-processor.plist
  ```

---

### 6.4 Self-Improvement Pipeline (İleri Seviye)

#### 6.4.1 Training Data Generator
- [ ] `src/lifecycle/training_data_generator.py` oluştur:
  ```python
  """
  EVO-TR Eğitim Verisi Üretici
  
  Başarısız etkileşimlerden yeni eğitim verisi önerir.
  """
  
  from typing import List, Dict
  from pathlib import Path
  import json
  
  from .log_analyzer import get_log_analyzer, FailedInteraction
  
  
  class TrainingDataGenerator:
      """Eğitim verisi üretici"""
      
      def __init__(self, output_dir: str = "./data/training/generated"):
          self.output_dir = Path(output_dir)
          self.output_dir.mkdir(parents=True, exist_ok=True)
          self.log_analyzer = get_log_analyzer()
      
      def generate_from_failed(
          self, 
          date: str,
          manual_corrections: Dict[str, str] = None
      ) -> List[Dict]:
          """
          Başarısız etkileşimlerden eğitim verisi üret.
          
          Args:
              date: Analiz edilecek tarih
              manual_corrections: {user_message: corrected_response} dict'i
              
          Returns:
              Üretilen eğitim verileri
          """
          failed = self.log_analyzer.find_failed_interactions(date)
          
          training_data = []
          
          for interaction in failed:
              # Manuel düzeltme varsa
              if manual_corrections and interaction.user_message in manual_corrections:
                  corrected = manual_corrections[interaction.user_message]
                  training_data.append({
                      "instruction": interaction.user_message,
                      "input": "",
                      "output": corrected,
                      "metadata": {
                          "source": "manual_correction",
                          "original_response": interaction.response,
                          "original_confidence": interaction.confidence
                      }
                  })
              else:
                  # Düzeltme için işaretle (TODO olarak)
                  training_data.append({
                      "instruction": interaction.user_message,
                      "input": "",
                      "output": "[NEEDS_CORRECTION]",
                      "metadata": {
                          "source": "failed_interaction",
                          "original_response": interaction.response,
                          "failure_reason": interaction.reason,
                          "original_confidence": interaction.confidence
                      }
                  })
          
          return training_data
      
      def save_for_review(self, data: List[Dict], filename: str) -> Path:
          """İnceleme için kaydet"""
          output_file = self.output_dir / filename
          
          with open(output_file, "w", encoding="utf-8") as f:
              json.dump(data, f, ensure_ascii=False, indent=2)
          
          return output_file
      
      def get_pending_corrections(self) -> List[Dict]:
          """Düzeltme bekleyen verileri getir"""
          pending = []
          
          for file in self.output_dir.glob("*.json"):
              with open(file, "r", encoding="utf-8") as f:
                  data = json.load(f)
                  for item in data:
                      if item.get("output") == "[NEEDS_CORRECTION]":
                          pending.append({
                              "file": str(file),
                              "data": item
                          })
          
          return pending
  
  
  # Singleton
  _generator: Optional[TrainingDataGenerator] = None
  
  
  def get_training_data_generator() -> TrainingDataGenerator:
      global _generator
      if _generator is None:
          _generator = TrainingDataGenerator()
      return _generator
  ```

---

### 6.5 Dashboard ve Monitoring

#### 6.5.1 Status Dashboard Script
- [ ] `scripts/dashboard.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """EVO-TR Status Dashboard"""
  
  from datetime import datetime, timedelta
  from rich.console import Console
  from rich.table import Table
  from rich.panel import Panel
  from rich.layout import Layout
  from rich.live import Live
  import time
  
  import sys
  sys.path.append(".")
  
  from src.lifecycle.log_analyzer import get_log_analyzer
  from src.lifecycle.session_manager import get_session_manager
  from src.memory.chromadb_handler import get_memory_handler
  from src.experts.lora_manager import get_lora_manager
  
  console = Console()
  
  
  def generate_dashboard():
      """Dashboard içeriği oluştur"""
      layout = Layout()
      
      # Sistem durumu
      memory = get_memory_handler()
      memory_stats = memory.get_stats()
      
      lora = get_lora_manager()
      lora_stats = lora.get_stats()
      
      session = get_session_manager()
      session_stats = session.get_stats()
      
      # Bugünün logları
      analyzer = get_log_analyzer()
      today = datetime.now().strftime("%Y-%m-%d")
      today_stats = analyzer.analyze_day(today)
      
      # Ana panel
      status_text = f"""
  [bold cyan]📊 Sistem Durumu[/bold cyan]
  
  [yellow]Hafıza:[/yellow]
    • Toplam kayıt: {memory_stats['total_memories']}
    • Tip dağılımı: {memory_stats['type_distribution']}
  
  [yellow]LoRA Manager:[/yellow]
    • Base model: {'✅ Yüklü' if lora_stats['base_model_loaded'] else '❌ Yüklenmedi'}
    • Aktif adapter: {lora_stats['current_adapter'] or 'Yok'}
    • Cache: {lora_stats['cache_size']}/{lora_stats['max_cache_size']}
  
  [yellow]Session:[/yellow]
    • Aktif session: {session_stats['active_sessions']}
    • Mevcut: {session_stats['current_session'] or 'Yok'}
  
  [bold cyan]📈 Bugün ({today})[/bold cyan]
  
    • Toplam mesaj: {today_stats.total_messages}
    • Session sayısı: {today_stats.unique_sessions}
    • Ortalama confidence: {today_stats.avg_confidence:.2%}
    • Düşük confidence: {today_stats.low_confidence_count}
    • Ortalama süre: {today_stats.avg_processing_time:.2f}s
  
  [dim]Son güncelleme: {datetime.now().strftime('%H:%M:%S')}[/dim]
      """
      
      return Panel(status_text, title="🤖 EVO-TR Dashboard", expand=False)
  
  
  def main():
      console.print("\n[bold]🤖 EVO-TR Dashboard başlatılıyor...[/bold]\n")
      console.print("[dim]Çıkmak için Ctrl+C[/dim]\n")
      
      try:
          with Live(generate_dashboard(), refresh_per_second=0.5, console=console) as live:
              while True:
                  time.sleep(2)
                  live.update(generate_dashboard())
      except KeyboardInterrupt:
          console.print("\n[yellow]Dashboard kapatıldı.[/yellow]")
  
  
  if __name__ == "__main__":
      main()
  ```

---

## ✅ Faz Tamamlanma Kriterleri

1. [ ] Session Manager çalışıyor
2. [ ] Sync Handler gerçek zamanlı işliyor
3. [ ] Log Analyzer istatistik çıkarıyor
4. [ ] Info Extractor bilgi çıkarıyor
5. [ ] Async Processor gece işlemi yapıyor
6. [ ] Hafızaya otomatik bilgi ekleniyor
7. [ ] İyileştirme önerileri üretiliyor
8. [ ] Dashboard çalışıyor
9. [ ] (Opsiyonel) Launchd scheduler kurulu

---

## ⏭️ Proje Tamamlandı! 🎉

Tüm fazlar tamamlandıktan sonra:
- [ ] Uçtan uca test yap
- [ ] Dokümantasyonu güncelle
- [ ] Performans optimizasyonu yap
- [ ] README.md oluştur

---

## 🐛 Olası Sorunlar ve Çözümleri

### Launchd Çalışmıyor
**Çözüm:**
```bash
# Log kontrol
tail -f ~/Library/Logs/com.evo-tr.night-processor.log

# Manuel test
launchctl start com.evo-tr.night-processor
```

### Çok Fazla Memory Kullanımı
**Çözüm:** Log dosyalarını periyodik olarak temizle, arşivle

### Yanlış Bilgi Hafızaya Ekleniyor
**Çözüm:** Confidence threshold'u artır (0.8+)

---

## 📊 Zaman Takibi

| Görev | Başlangıç | Bitiş | Süre |
|-------|-----------|-------|------|
| 6.1 Session & Sync | | | |
| 6.2 Log Analyzer | | | |
| 6.3 Async Processor | | | |
| 6.4 Self-Improvement | | | |
| 6.5 Dashboard | | | |
| **TOPLAM** | | | |

---

*Bu faz tamamlandığında, "✅ FAZ 6 TAMAMLANDI - PROJE TAMAMLANDI! 🎉" olarak işaretle.*
