"""
ModelServingEngine 的單元測試。

使用 Mock 隔離真實的 MLflow SDK，測試模型載入、推論與快取邏輯。
"""

import pytest
from unittest.mock import MagicMock, patch

import pandas as pd

from src.exceptions import ModelNotFoundError, ModelServingError
from src.ml_core.serving import ModelServingEngine


class TestModelServingEngineURIBuilder:
    """_build_model_uri 應根據參數組合建構正確的 URI。"""

    def test_build_uri_with_alias(self):
        uri = ModelServingEngine._build_model_uri("my-model", alias="champion")
        assert uri == "models:/my-model@champion"

    def test_build_uri_with_version(self):
        uri = ModelServingEngine._build_model_uri("my-model", version="3")
        assert uri == "models:/my-model/3"

    def test_build_uri_latest_fallback(self):
        uri = ModelServingEngine._build_model_uri("my-model")
        assert uri == "models:/my-model/latest"

    def test_alias_takes_priority_over_version(self):
        uri = ModelServingEngine._build_model_uri(
            "my-model", version="3", alias="champion"
        )
        assert uri == "models:/my-model@champion"


class TestModelServingEnginePredict:
    """推論邏輯的單元測試。"""

    def _make_engine(self) -> ModelServingEngine:
        """建立一個已 mock 初始化的 Engine 實例。"""
        with patch.object(ModelServingEngine, "__init__", lambda self, *a: None):
            engine = ModelServingEngine.__new__(ModelServingEngine)
            engine._mlflow = MagicMock()
            engine._loaded_model = None
            engine._loaded_model_uri = None
            return engine

    def test_predict_without_loaded_model_raises(self):
        engine = self._make_engine()
        df = pd.DataFrame({"f1": [1, 2]})
        with pytest.raises(ModelServingError, match="尚未載入模型"):
            engine.predict(df)

    def test_predict_returns_list(self):
        engine = self._make_engine()
        mock_model = MagicMock()
        mock_model.predict.return_value = pd.Series([0, 1, 1])
        engine._loaded_model = mock_model
        engine._loaded_model_uri = "models:/test/1"

        result = engine.predict(pd.DataFrame({"f1": [1, 2, 3]}))
        assert result == [0, 1, 1]
        mock_model.predict.assert_called_once()

    def test_load_model_caches_same_uri(self):
        engine = self._make_engine()
        mock_pyfunc_model = MagicMock()
        engine._mlflow.pyfunc.load_model.return_value = mock_pyfunc_model

        engine.load_model("my-model", alias="champion")
        assert engine._loaded_model == mock_pyfunc_model

        # 再次載入相同 URI 應使用快取
        engine._mlflow.pyfunc.load_model.reset_mock()
        engine.load_model("my-model", alias="champion")
        engine._mlflow.pyfunc.load_model.assert_not_called()

    def test_load_model_not_found_raises(self):
        engine = self._make_engine()
        engine._mlflow.pyfunc.load_model.side_effect = Exception("not found")

        with pytest.raises(ModelNotFoundError, match="無法載入模型"):
            engine.load_model("nonexistent-model")


class TestModelServingEngineInfo:
    """get_model_info 的測試。"""

    def test_model_info_when_not_loaded(self):
        with patch.object(ModelServingEngine, "__init__", lambda self, *a: None):
            engine = ModelServingEngine.__new__(ModelServingEngine)
            engine._loaded_model = None
            engine._loaded_model_uri = None

            info = engine.get_model_info()
            assert info["is_loaded"] is False
            assert info["model_uri"] is None

    def test_model_info_when_loaded(self):
        with patch.object(ModelServingEngine, "__init__", lambda self, *a: None):
            engine = ModelServingEngine.__new__(ModelServingEngine)
            engine._loaded_model = MagicMock()
            engine._loaded_model_uri = "models:/test@champion"

            info = engine.get_model_info()
            assert info["is_loaded"] is True
            assert info["model_uri"] == "models:/test@champion"
