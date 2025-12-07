"""
EVO-TR History Expert Testleri

FAZ 7.3: Tarih uzmanı adapter testleri
"""

import pytest
import json
from pathlib import Path


class TestHistoryDataPreparation:
    """Tarih veri seti hazırlık testleri."""
    
    def test_history_data_dir_exists(self):
        """History data dizini var mı?"""
        data_dir = Path("data/training/history")
        assert data_dir.exists(), "History data dizini bulunamadı"
    
    def test_train_file_exists(self):
        """Train dosyası var mı?"""
        train_file = Path("data/training/history/train.jsonl")
        assert train_file.exists(), "Train dosyası bulunamadı"
    
    def test_valid_file_exists(self):
        """Validation dosyası var mı?"""
        valid_file = Path("data/training/history/valid.jsonl")
        assert valid_file.exists(), "Validation dosyası bulunamadı"
    
    def test_train_data_format(self):
        """Train verisi doğru formatta mı?"""
        train_file = Path("data/training/history/train.jsonl")
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
        train_file = Path("data/training/history/train.jsonl")
        count = sum(1 for _ in open(train_file, encoding="utf-8"))
        assert count >= 20, f"Yetersiz train verisi: {count}"
    
    def test_valid_data_count(self):
        """Yeterli validation verisi var mı?"""
        valid_file = Path("data/training/history/valid.jsonl")
        count = sum(1 for _ in open(valid_file, encoding="utf-8"))
        assert count >= 2, f"Yetersiz validation verisi: {count}"
    
    def test_turkish_history_exists(self):
        """Türkçe tarih örnekleri var mı?"""
        turkish_file = Path("data/training/history/turkish_history.jsonl")
        assert turkish_file.exists(), "Türkçe tarih dosyası bulunamadı"
        
        count = sum(1 for _ in open(turkish_file, encoding="utf-8"))
        assert count >= 10, f"Yetersiz Türkçe örnek: {count}"


class TestHistoryIntent:
    """History intent testleri."""
    
    def test_intent_mapping_has_history(self):
        """intent_mapping.json'da history var mı?"""
        with open("configs/intent_mapping.json", "r", encoding="utf-8") as f:
            mapping = json.load(f)
        
        assert "history" in mapping["intent_to_adapter"], "history intent yok"
        assert mapping["intent_to_adapter"]["history"] == "adapter_history_expert"
    
    def test_intent_dataset_has_history(self):
        """intent_dataset.json'da history örnekleri var mı?"""
        with open("data/intents/intent_dataset.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
        
        assert "history" in dataset["intent_distribution"], "history intent dağılımı yok"
        assert dataset["intent_distribution"]["history"] >= 20, "Yetersiz history örneği"
        
        # History intent'li örnekler var mı?
        history_samples = [i for i in dataset["intents"] if i["intent"] == "history"]
        assert len(history_samples) >= 20, f"Yetersiz history örneği: {len(history_samples)}"


class TestHistoryAdapterConfig:
    """Adapter konfigürasyon testleri."""
    
    def test_lora_config_exists(self):
        """LoRA config dosyası var mı?"""
        config_file = Path("configs/lora_history_config.yaml")
        assert config_file.exists(), "LoRA config dosyası bulunamadı"
    
    def test_adapter_dir_ready(self):
        """Adapter dizini hazır mı?"""
        adapters_dir = Path("adapters")
        assert adapters_dir.exists(), "Adapters dizini bulunamadı"


class TestHistoryLoRAManager:
    """LoRA Manager history testleri."""
    
    def test_lora_manager_has_history(self):
        """LoRAManager history_expert biliyor mu?"""
        import sys
        sys.path.insert(0, str(Path.cwd() / "src"))
        
        from experts.lora_manager import LoRAManager
        
        assert "history" in LoRAManager.ADAPTER_REGISTRY, "history intent registry'de yok"
        assert LoRAManager.ADAPTER_REGISTRY["history"] == "history_expert"


class TestHistoryInference:
    """MLXInference history testleri."""
    
    def test_inference_has_history_prompt(self):
        """MLXInference history system prompt var mı?"""
        import sys
        sys.path.insert(0, str(Path.cwd() / "src"))
        
        from inference.mlx_inference import MLXInference
        
        assert "history" in MLXInference.SYSTEM_PROMPTS, "history system prompt yok"
        
        prompt = MLXInference.SYSTEM_PROMPTS["history"]
        assert "tarih" in prompt.lower(), "tarih kelimesi yok"


class TestHistoryIntentSamples:
    """History intent örnek testleri."""
    
    def test_history_samples_file_exists(self):
        """history.json dosyası var mı?"""
        samples_file = Path("data/intents/samples/history.json")
        assert samples_file.exists(), "history.json bulunamadı"
    
    def test_history_samples_content(self):
        """history.json doğru içeriğe sahip mi?"""
        samples_file = Path("data/intents/samples/history.json")
        with open(samples_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert "intent" in data, "intent alanı yok"
        assert data["intent"] == "history", "intent değeri yanlış"
        assert "samples" in data, "samples alanı yok"
        assert len(data["samples"]) >= 20, f"Yetersiz örnek: {len(data['samples'])}"
    
    def test_history_samples_languages(self):
        """Hem Türkçe hem İngilizce örnekler var mı?"""
        samples_file = Path("data/intents/samples/history.json")
        with open(samples_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        languages = set(s.get("language", "tr") for s in data["samples"])
        assert "tr" in languages, "Türkçe örnekler yok"
        assert "en" in languages, "İngilizce örnekler yok"


class TestHistoryAdapterPost:
    """Eğitim sonrası adapter testleri."""
    
    @pytest.mark.skipif(
        not Path("adapters/history_expert/adapters.safetensors").exists(),
        reason="History adapter henüz eğitilmemiş"
    )
    def test_adapter_file_exists(self):
        """Adapter dosyası var mı?"""
        adapter_file = Path("adapters/history_expert/adapters.safetensors")
        assert adapter_file.exists(), "Adapter dosyası bulunamadı"
    
    @pytest.mark.skipif(
        not Path("adapters/history_expert/adapter_config.json").exists(),
        reason="History adapter config henüz oluşturulmamış"
    )
    def test_adapter_config_exists(self):
        """Adapter config var mı?"""
        config_file = Path("adapters/history_expert/adapter_config.json")
        assert config_file.exists(), "Adapter config bulunamadı"
        
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        assert "lora_parameters" in config or "rank" in config, "LoRA parametreleri yok"
    
    @pytest.mark.skipif(
        not Path("adapters/history_expert/adapters.safetensors").exists(),
        reason="History adapter henüz eğitilmemiş"
    )
    def test_adapter_size_reasonable(self):
        """Adapter boyutu makul mü?"""
        adapter_file = Path("adapters/history_expert/adapters.safetensors")
        size_mb = adapter_file.stat().st_size / (1024 * 1024)
        
        # 1MB - 100MB arası olmalı
        assert 1 < size_mb < 100, f"Adapter boyutu şüpheli: {size_mb:.1f}MB"
