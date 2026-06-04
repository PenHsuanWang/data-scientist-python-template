import pytest
import pandas as pd
from src.ml_core.trainer import Trainer
from src.ml_core.config import ProjectConfig
from src.exceptions import ModelTrainingError


@pytest.fixture
def dummy_config(mock_data_path, mock_model_path):
    return ProjectConfig(data_path=mock_data_path, model_save_path=mock_model_path)


def test_trainer_fit(dummy_config):
    trainer = Trainer(dummy_config)
    X = pd.DataFrame({"feature1": [1, 2]})
    y = pd.Series([0, 1])
    metrics = trainer.fit(X, y)
    assert "accuracy" in metrics
    assert "f1_score" in metrics


def test_trainer_save_untrained(dummy_config):
    trainer = Trainer(dummy_config)
    with pytest.raises(ModelTrainingError, match="無法儲存未訓練的模型"):
        trainer.save(dummy_config.model_save_path)
