"""
EVO-TR Router: Intent Sınıflandırıcı

Gelen kullanıcı mesajını analiz edip doğru adapter'a yönlendirir.
Similarity-based yaklaşım kullanır.
"""

import json
from pathlib import Path
from typing import Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer


class IntentClassifier:
    """Similarity-based intent sınıflandırıcı"""
    
    def __init__(
        self,
        model_path: str = "./models/router/sentence_transformer",
        dataset_path: str = "./data/intents/intent_dataset.json",
        mapping_path: str = "./configs/intent_mapping.json"
    ):
        """
        Intent sınıflandırıcıyı başlat.
        
        Args:
            model_path: Sentence transformer model dizini
            dataset_path: Intent veri seti yolu
            mapping_path: Intent-adapter mapping dosyası
        """
        print(f"🔄 Router modeli yükleniyor: {model_path}")
        self.model = SentenceTransformer(model_path)
        self.dataset = self._load_dataset(dataset_path)
        self.mapping = self._load_mapping(mapping_path)
        self.intent_embeddings = self._build_intent_embeddings()
        print(f"✅ Router hazır! {len(self.intent_embeddings)} intent kategorisi")
    
    def _load_dataset(self, path: str) -> dict:
        """Veri setini yükle"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _load_mapping(self, path: str) -> dict:
        """Intent mapping'i yükle"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _build_intent_embeddings(self) -> Dict[str, np.ndarray]:
        """Her intent için ortalama embedding hesapla"""
        print("📊 Intent embedding'leri hesaplanıyor...")
        
        intent_texts = {}
        for sample in self.dataset["intents"]:
            intent = sample["intent"]
            if intent not in intent_texts:
                intent_texts[intent] = []
            intent_texts[intent].append(sample["text"])
        
        intent_embeddings = {}
        for intent, texts in intent_texts.items():
            embeddings = self.model.encode(texts, show_progress_bar=False)
            intent_embeddings[intent] = np.mean(embeddings, axis=0)
            print(f"  ✓ {intent}: {len(texts)} örnek")
        
        return intent_embeddings
    
    def predict(self, text: str) -> Dict:
        """
        Metin için intent tahmini yap
        
        Args:
            text: Kullanıcı mesajı
            
        Returns:
            {
                "intent": str,
                "confidence": float,
                "adapter_id": str,
                "all_scores": dict
            }
        """
        # Girdi embedding'i
        query_embedding = self.model.encode([text], show_progress_bar=False)[0]
        
        # Tüm intent'lerle benzerlik hesapla
        scores = {}
        for intent, intent_emb in self.intent_embeddings.items():
            similarity = self._cosine_similarity(query_embedding, intent_emb)
            scores[intent] = float(similarity)
        
        # En yüksek skoru bul
        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent]
        
        # Confidence threshold kontrolü
        threshold = self.mapping.get("confidence_threshold", 0.7)
        if confidence < threshold:
            adapter_id = self.mapping.get("fallback_adapter", "base_model")
        else:
            adapter_id = self.mapping["intent_to_adapter"].get(
                best_intent, 
                self.mapping.get("fallback_adapter", "base_model")
            )
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "adapter_id": adapter_id,
            "all_scores": scores
        }
    
    def predict_batch(self, texts: list) -> list:
        """Birden fazla metin için tahmin yap"""
        return [self.predict(text) for text in texts]
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """İki vektör arasındaki cosine benzerliğini hesapla"""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def get_stats(self) -> Dict:
        """Model istatistiklerini döndür"""
        intent_counts = {}
        for sample in self.dataset["intents"]:
            intent = sample["intent"]
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
        return {
            "total_intents": len(self.intent_embeddings),
            "intents": list(self.intent_embeddings.keys()),
            "sample_counts": intent_counts,
            "total_samples": sum(intent_counts.values()),
            "confidence_threshold": self.mapping.get("confidence_threshold"),
            "fallback_adapter": self.mapping.get("fallback_adapter")
        }


# Singleton instance
_classifier: Optional[IntentClassifier] = None


def get_classifier(force_reload: bool = False) -> IntentClassifier:
    """Global classifier instance döndür"""
    global _classifier
    if _classifier is None or force_reload:
        _classifier = IntentClassifier()
    return _classifier


def classify(text: str) -> Dict:
    """Kısa yol: Doğrudan sınıflandırma yap"""
    return get_classifier().predict(text)


def route(text: str) -> str:
    """Mesaj için adapter ID döndür"""
    result = classify(text)
    return result["adapter_id"]
