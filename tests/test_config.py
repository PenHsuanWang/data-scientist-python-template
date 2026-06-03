import pytest
from pydantic import ValidationError
from pathlib import Path
from src.ml_core.config import ProjectConfig


def test_project_config_valid_input(
    mock_data_path: Path, mock_model_path: Path
) -> None:
    """測試提供正確參數時，Config 是否能成功實例化"""
    config = ProjectConfig(
        data_path=mock_data_path, model_save_path=mock_model_path, learning_rate=0.05
    )

    assert config.learning_rate == 0.05
    assert config.random_state == 42  # 預設值
    assert isinstance(config.data_path, Path)


def test_project_config_invalid_learning_rate(
    mock_data_path: Path, mock_model_path: Path
) -> None:
    """測試提供非法的學習率時，是否會觸發 ValidationError"""
    with pytest.raises(ValidationError) as exc_info:
        ProjectConfig(
            data_path=mock_data_path,
            model_save_path=mock_model_path,
            learning_rate=-0.1,  # 不可小於 0
        )

    assert "Input should be greater than 0" in str(exc_info.value)
