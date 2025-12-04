#!/usr/bin/env python3
"""
Test Math Expert Module - FAZ 7
Tests for math intent classification and data preparation
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Test data directory
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "training" / "math"
INTENT_DIR = BASE_DIR / "data" / "intents" / "samples"
CONFIG_DIR = BASE_DIR / "configs"


class TestMathDataPreparation:
    """Matematik veri hazırlığı testleri"""
    
    def test_gsm8k_train_exists(self):
        """GSM8K train dosyası mevcut mu?"""
        filepath = DATA_DIR / "gsm8k_train.jsonl"
        assert filepath.exists(), f"GSM8K train dosyası bulunamadı: {filepath}"
    
    def test_gsm8k_test_exists(self):
        """GSM8K test dosyası mevcut mu?"""
        filepath = DATA_DIR / "gsm8k_test.jsonl"
        assert filepath.exists(), f"GSM8K test dosyası bulunamadı: {filepath}"
    
    def test_turkish_math_exists(self):
        """Türkçe matematik verisi mevcut mu?"""
        filepath = DATA_DIR / "turkish_math.jsonl"
        assert filepath.exists(), f"Turkish math dosyası bulunamadı: {filepath}"
    
    def test_combined_train_exists(self):
        """Birleştirilmiş train dosyası mevcut mu?"""
        filepath = DATA_DIR / "math_combined_train.jsonl"
        assert filepath.exists(), f"Combined train dosyası bulunamadı: {filepath}"
    
    def test_combined_val_exists(self):
        """Birleştirilmiş val dosyası mevcut mu?"""
        filepath = DATA_DIR / "math_combined_val.jsonl"
        assert filepath.exists(), f"Combined val dosyası bulunamadı: {filepath}"
    
    def test_gsm8k_format(self):
        """GSM8K verisi doğru formatta mı?"""
        filepath = DATA_DIR / "gsm8k_train.jsonl"
        with open(filepath, 'r') as f:
            first_line = f.readline()
            data = json.loads(first_line)
        
        assert "messages" in data
        assert len(data["messages"]) == 3
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"
        assert data["messages"][2]["role"] == "assistant"
    
    def test_turkish_math_format(self):
        """Türkçe matematik verisi doğru formatta mı?"""
        filepath = DATA_DIR / "turkish_math.jsonl"
        with open(filepath, 'r') as f:
            first_line = f.readline()
            data = json.loads(first_line)
        
        assert "messages" in data
        assert len(data["messages"]) == 3
        # Türkçe içerik kontrolü
        user_msg = data["messages"][1]["content"]
        assert any(char in user_msg for char in "ğüşıöçĞÜŞİÖÇ") or "matematik" in user_msg.lower()
    
    def test_combined_count(self):
        """Birleştirilmiş veri sayısı doğru mu?"""
        train_count = 0
        val_count = 0
        
        with open(DATA_DIR / "math_combined_train.jsonl", 'r') as f:
            train_count = sum(1 for _ in f)
        
        with open(DATA_DIR / "math_combined_val.jsonl", 'r') as f:
            val_count = sum(1 for _ in f)
        
        total = train_count + val_count
        assert total > 7000, f"Toplam veri sayısı beklenenden az: {total}"
        
        # %90 train, %10 val oranı kontrolü
        train_ratio = train_count / total
        assert 0.85 <= train_ratio <= 0.95, f"Train oranı beklenmiyor: {train_ratio}"


class TestMathIntentSamples:
    """Matematik intent örnekleri testleri"""
    
    def test_code_math_samples_exist(self):
        """code_math örnekleri mevcut mu?"""
        filepath = INTENT_DIR / "code_math.json"
        assert filepath.exists(), f"code_math samples bulunamadı: {filepath}"
    
    def test_code_math_samples_count(self):
        """Yeterli örnek var mı?"""
        filepath = INTENT_DIR / "code_math.json"
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert len(data) >= 20, f"Yetersiz örnek sayısı: {len(data)}"
    
    def test_code_math_samples_format(self):
        """Örnekler doğru formatta mı?"""
        filepath = INTENT_DIR / "code_math.json"
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for item in data:
            assert "text" in item
            assert "intent" in item
            assert item["intent"] == "code_math"
    
    def test_code_math_variety(self):
        """Örneklerde çeşitlilik var mı?"""
        filepath = INTENT_DIR / "code_math.json"
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Farklı matematik konuları
        keywords = ["denklem", "alan", "çevre", "yüzde", "kesir", "oran", "üslü", "karekök"]
        found_keywords = set()
        
        for item in data:
            text_lower = item["text"].lower()
            for kw in keywords:
                if kw in text_lower:
                    found_keywords.add(kw)
        
        assert len(found_keywords) >= 4, f"Yetersiz çeşitlilik: {found_keywords}"


class TestIntentMapping:
    """Intent mapping testleri"""
    
    def test_intent_mapping_has_code_math(self):
        """Intent mapping'de code_math var mı?"""
        filepath = CONFIG_DIR / "intent_mapping.json"
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert "code_math" in data["intent_to_adapter"]
    
    def test_code_math_adapter_mapping(self):
        """code_math doğru adapter'a yönlendiriliyor mu?"""
        filepath = CONFIG_DIR / "intent_mapping.json"
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert data["intent_to_adapter"]["code_math"] == "adapter_math_expert"
    
    def test_code_math_description(self):
        """code_math açıklaması var mı?"""
        filepath = CONFIG_DIR / "intent_mapping.json"
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert "code_math" in data["intent_descriptions"]
        desc = data["intent_descriptions"]["code_math"]
        assert len(desc) > 10


class TestLoRAConfig:
    """LoRA konfigürasyon testleri"""
    
    def test_lora_math_config_exists(self):
        """Math LoRA config dosyası mevcut mu?"""
        filepath = CONFIG_DIR / "lora_math_config.yaml"
        assert filepath.exists(), f"LoRA config bulunamadı: {filepath}"
    
    def test_lora_math_config_valid(self):
        """Config geçerli YAML mı?"""
        import yaml
        filepath = CONFIG_DIR / "lora_math_config.yaml"
        
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)
        
        assert "model" in config
        assert "lora_rank" in config
        assert "batch_size" in config
        assert "iters" in config


class TestMathAdapterDirectory:
    """Adapter dizini testleri"""
    
    def test_math_expert_dir_exists(self):
        """math_expert adapter dizini mevcut mu?"""
        dirpath = BASE_DIR / "adapters" / "math_expert"
        assert dirpath.exists(), f"Adapter dizini bulunamadı: {dirpath}"


class TestIntentDataset:
    """Güncel intent dataset testleri"""
    
    def test_intent_dataset_has_code_math(self):
        """Intent dataset code_math içeriyor mu?"""
        filepath = BASE_DIR / "data" / "intents" / "intent_dataset.json"
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # code_math örneklerini say
        code_math_count = sum(1 for item in data["intents"] if item["intent"] == "code_math")
        assert code_math_count >= 20, f"Yetersiz code_math örneği: {code_math_count}"
    
    def test_intent_distribution_updated(self):
        """Intent dağılımı güncellendi mi?"""
        filepath = BASE_DIR / "data" / "intents" / "intent_dataset.json"
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert "code_math" in data["intent_distribution"]


# =========== Math Problem Parsing Tests ===========

class TestMathProblemParsing:
    """Matematik problemi ayrıştırma testleri"""
    
    def test_gsm8k_answer_format(self):
        """GSM8K cevap formatı doğru mu?"""
        # #### ile ayrılan format
        sample_answer = "Step 1: 48/2 = 24\nStep 2: 48+24 = 72\n#### 72"
        
        if "####" in sample_answer:
            parts = sample_answer.split("####")
            solution = parts[0].strip()
            final = parts[1].strip()
            
            assert len(solution) > 0
            assert final == "72"
    
    def test_turkish_math_has_sonuc(self):
        """Türkçe matematiklerde Sonuç var mı?"""
        filepath = DATA_DIR / "turkish_math.jsonl"
        
        with open(filepath, 'r') as f:
            first_line = f.readline()
            data = json.loads(first_line)
        
        assistant_msg = data["messages"][2]["content"]
        assert "Sonuç" in assistant_msg or "sonuç" in assistant_msg.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
