import pytest
import pandas as pd
from src.ml_core.trainer import Trainer
from src.exceptions import ModelTrainingError


def test_trainer_fit(dummy_config):
    trainer = Trainer(dummy_config)
    X = pd.DataFrame({"feature1": [1, 2]})
    y = pd.Series([0, 1])
    metrics = trainer.fit(X, y)
    assert "accuracy" in metrics
    assert "f1_score" in metrics


def test_trainer_save_untrained(dummy_config, mock_model_path):
    trainer = Trainer(dummy_config)
    with pytest.raises(ModelTrainingError, match="無法儲存未訓練的模型"):
        trainer.save(mock_model_path)


def test_trainer_get_model_untrained(dummy_config):
    """get_model() 在未訓練時應拋出 ModelTrainingError。"""
    trainer = Trainer(dummy_config)
    with pytest.raises(ModelTrainingError, match="無法取得未訓練的模型物件"):
        trainer.get_model()
