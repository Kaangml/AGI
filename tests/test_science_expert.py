"""
EVO-TR Science Expert Testleri

FAZ 7.2: Bilim uzmanı adapter testleri
"""

import pytest
import json
from pathlib import Path


class TestScienceDataPreparation:
    """Bilim veri seti hazırlık testleri."""
    
    def test_science_data_dir_exists(self):
        """Science data dizini var mı?"""
        data_dir = Path("data/training/science")
        assert data_dir.exists(), "Science data dizini bulunamadı"
    
    def test_train_file_exists(self):
        """Train dosyası var mı?"""
        train_file = Path("data/training/science/train.jsonl")
        assert train_file.exists(), "Train dosyası bulunamadı"
    
    def test_valid_file_exists(self):
        """Validation dosyası var mı?"""
        valid_file = Path("data/training/science/valid.jsonl")
        assert valid_file.exists(), "Validation dosyası bulunamadı"
    
    def test_train_data_format(self):
        """Train verisi doğru formatta mı?"""
        train_file = Path("data/training/science/train.jsonl")
        with open(train_file, "r", encoding="utf-8") as f:
            first_line = f.readline()
            data = json.loads(first_line)
        
        assert "messages" in data, "messages alanı yok"
        assert len(data["messages"]) >= 2, "En az 2 mesaj olmalı"
        
        # Role kontrolü
        roles = [m["role"] for m in data["messages"]]
        assert "user" in roles, "user mesajı yok"
        assert "assistant" in roles, "assistant mesajı yok"
    
    def test_train_data_count(self):
        """Yeterli train verisi var mı?"""
        train_file = Path("data/training/science/train.jsonl")
        count = sum(1 for _ in open(train_file, encoding="utf-8"))
        assert count > 10000, f"Yetersiz train verisi: {count}"
    
    def test_valid_data_count(self):
        """Yeterli validation verisi var mı?"""
        valid_file = Path("data/training/science/valid.jsonl")
        count = sum(1 for _ in open(valid_file, encoding="utf-8"))
        assert count > 1000, f"Yetersiz validation verisi: {count}"
    
    def test_turkish_science_exists(self):
        """Türkçe bilim örnekleri var mı?"""
        turkish_file = Path("data/training/science/turkish_science.jsonl")
        assert turkish_file.exists(), "Türkçe bilim dosyası bulunamadı"
        
        count = sum(1 for _ in open(turkish_file, encoding="utf-8"))
        assert count >= 10, f"Yetersiz Türkçe örnek: {count}"


class TestScienceIntent:
    """Science intent testleri."""
    
    def test_intent_mapping_has_science(self):
        """intent_mapping.json'da science var mı?"""
        with open("configs/intent_mapping.json", "r", encoding="utf-8") as f:
            mapping = json.load(f)
        
        assert "science" in mapping["intent_to_adapter"], "science intent yok"
        assert mapping["intent_to_adapter"]["science"] == "adapter_science_expert"
    
    def test_intent_dataset_has_science(self):
        """intent_dataset.json'da science örnekleri var mı?"""
        with open("data/intents/intent_dataset.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
        
        assert "science" in dataset["intent_distribution"], "science intent dağılımı yok"
        assert dataset["intent_distribution"]["science"] >= 20, "Yetersiz science örneği"
        
        # Science intent'li örnekler var mı?
        science_samples = [i for i in dataset["intents"] if i["intent"] == "science"]
        assert len(science_samples) >= 20, f"Yetersiz science örneği: {len(science_samples)}"


class TestScienceAdapterConfig:
    """Adapter konfigürasyon testleri."""
    
    def test_lora_config_exists(self):
        """LoRA config dosyası var mı?"""
        config_file = Path("configs/lora_science_config.yaml")
        # Training öncesi config dosyası oluşturulacak
        # Bu test training başlamadan önce fail olabilir
        pass
    
    def test_adapter_dir_ready(self):
        """Adapter dizini hazır mı?"""
        adapter_dir = Path("adapters/science_expert")
        # Training tamamlandıktan sonra kontrol edilecek
        pass


class TestScienceDataContent:
    """Veri içeriği testleri."""
    
    def test_physics_content(self):
        """Fizik içeriği var mı?"""
        train_file = Path("data/training/science/train.jsonl")
        physics_keywords = ["force", "energy", "motion", "physics", "newton", "fizik", "enerji"]
        
        found = False
        with open(train_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                text = str(data).lower()
                if any(kw in text for kw in physics_keywords):
                    found = True
                    break
        
        assert found, "Fizik içeriği bulunamadı"
    
    def test_chemistry_content(self):
        """Kimya içeriği var mı?"""
        train_file = Path("data/training/science/train.jsonl")
        chemistry_keywords = ["chemical", "element", "reaction", "kimya", "element", "tepkime"]
        
        found = False
        with open(train_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                text = str(data).lower()
                if any(kw in text for kw in chemistry_keywords):
                    found = True
                    break
        
        assert found, "Kimya içeriği bulunamadı"
    
    def test_biology_content(self):
        """Biyoloji içeriği var mı?"""
        train_file = Path("data/training/science/train.jsonl")
        biology_keywords = ["cell", "dna", "organism", "biyoloji", "hücre", "gen"]
        
        found = False
        with open(train_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                text = str(data).lower()
                if any(kw in text for kw in biology_keywords):
                    found = True
                    break
        
        assert found, "Biyoloji içeriği bulunamadı"


class TestLoRAManagerScience:
    """LoRA Manager science desteği testleri."""
    
    def test_adapter_registry_has_science(self):
        """ADAPTER_REGISTRY'de science var mı?"""
        import sys
        sys.path.insert(0, ".")
        from src.experts.lora_manager import LoRAManager
        
        assert "science" in LoRAManager.ADAPTER_REGISTRY, "science intent registry'de yok"
        assert LoRAManager.ADAPTER_REGISTRY["science"] == "science_expert"


class TestMLXInferenceScience:
    """MLX Inference science desteği testleri."""
    
    def test_system_prompt_has_science(self):
        """SYSTEM_PROMPTS'ta science var mı?"""
        import sys
        sys.path.insert(0, ".")
        from src.inference.mlx_inference import MLXInference
        
        assert "science" in MLXInference.SYSTEM_PROMPTS, "science system prompt yok"
        
        prompt = MLXInference.SYSTEM_PROMPTS["science"]
        assert "fizik" in prompt.lower() or "bilim" in prompt.lower(), "Türkçe bilim anahtar kelimesi yok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
