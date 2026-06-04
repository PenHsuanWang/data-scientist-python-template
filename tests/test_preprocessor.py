import pytest
import pandas as pd
from src.ml_core.preprocessor import Preprocessor
from src.ml_core.config import ProjectConfig
from src.exceptions import PreprocessingError


@pytest.fixture
def dummy_config(mock_data_path, mock_model_path):
    return ProjectConfig(data_path=mock_data_path, model_save_path=mock_model_path)


def test_preprocessor_fit_transform(dummy_config):
    preprocessor = Preprocessor(dummy_config)
    df = pd.DataFrame({"feature1": [1, 2], "target": [0, 1]})
    X, y = preprocessor.fit_transform(df)
    assert preprocessor.is_fitted is True
    assert X is not None


def test_preprocessor_transform_without_fit(dummy_config):
    preprocessor = Preprocessor(dummy_config)
    df = pd.DataFrame({"feature1": [1, 2]})
    with pytest.raises(
        PreprocessingError, match="呼叫 transform 之前必須先執行 fit_transform"
    ):
        preprocessor.transform(df)
