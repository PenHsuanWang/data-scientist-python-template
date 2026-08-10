"""
FastAPI Router 的整合測試。

使用 FastAPI TestClient 與 Mock 的 DI 依賴進行測試，
確保 API 端點的 request/response 行為正確。
"""

import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.ml_core.config import ProjectConfig
from src.ml_core.serving import ModelServingEngine
from src.server.app import create_app
from src.server.dependencies import get_config, get_serving_engine


@pytest.fixture
def mock_serving_engine() -> MagicMock:
    """建立一個 Mock 的 ModelServingEngine。"""
    engine = MagicMock(spec=ModelServingEngine)
    engine.get_model_info.return_value = {
        "model_uri": "models:/test@champion",
        "is_loaded": True,
    }
    engine.predict.return_value = [0, 1, 1]
    engine.list_registered_models.return_value = [
        {
            "name": "test-model",
            "latest_versions": [
                {"version": "1", "status": "READY", "run_id": "abc123"}
            ],
            "description": "Test model",
        }
    ]
    engine.get_model_versions.return_value = [
        {
            "version": "1",
            "status": "READY",
            "run_id": "abc123",
            "aliases": ["champion"],
            "creation_timestamp": 1700000000000,
        }
    ]
    return engine


@pytest.fixture
def test_client(mock_data_path, mock_serving_engine) -> TestClient:
    """建立 TestClient 並覆蓋 DI 依賴。"""
    app = create_app()

    mock_config = ProjectConfig(data_path=mock_data_path)

    app.dependency_overrides[get_config] = lambda: mock_config
    app.dependency_overrides[get_serving_engine] = lambda: mock_serving_engine

    return TestClient(app)


class TestHealthEndpoint:
    """健康檢查端點的測試。"""

    def test_health_returns_ok(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestPredictEndpoint:
    """推論端點的測試。"""

    def test_predict_success(self, test_client, mock_serving_engine):
        payload = {
            "model_name": "test-model",
            "alias": "champion",
            "features": [{"f1": 1.0, "f2": 2.0}, {"f1": 3.0, "f2": 4.0}],
        }
        response = test_client.post("/api/v1/predict", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["model_name"] == "test-model"
        assert data["predictions"] == [0, 1, 1]
        mock_serving_engine.load_model.assert_called_once_with(
            model_name="test-model",
            version=None,
            alias="champion",
        )

    def test_predict_empty_features_returns_422(self, test_client):
        payload = {
            "model_name": "test-model",
            "features": [],
        }
        response = test_client.post("/api/v1/predict", json=payload)
        assert response.status_code == 422

    def test_predict_missing_model_name_returns_422(self, test_client):
        payload = {
            "features": [{"f1": 1.0}],
        }
        response = test_client.post("/api/v1/predict", json=payload)
        assert response.status_code == 422


class TestModelsEndpoint:
    """模型管理端點的測試。"""

    def test_list_models(self, test_client, mock_serving_engine):
        response = test_client.get("/api/v1/models")

        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 1
        assert data["models"][0]["name"] == "test-model"

    def test_get_model_versions(self, test_client, mock_serving_engine):
        response = test_client.get("/api/v1/models/test-model/versions")

        assert response.status_code == 200
        data = response.json()
        assert data["model_name"] == "test-model"
        assert len(data["versions"]) == 1
        assert data["versions"][0]["aliases"] == ["champion"]

    def test_set_model_alias(self, test_client, mock_serving_engine):
        payload = {"version": "1", "alias": "champion"}
        response = test_client.put(
            "/api/v1/models/test-model/alias",
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model_name"] == "test-model"
        assert data["alias"] == "champion"
        assert data["version"] == "1"
        mock_serving_engine.set_model_alias.assert_called_once_with(
            model_name="test-model",
            version="1",
            alias="champion",
        )


class TestTrainEndpoint:
    """訓練端點的測試。"""

    @patch("src.server.routers.train.MLflowExperimentTracker")
    @patch("src.server.routers.train.TrainingPipeline")
    def test_train_success(
        self,
        mock_pipeline_cls,
        mock_tracker_cls,
        test_client,
    ):
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = MagicMock(
            run_id="test-run-123",
            metrics={"accuracy": 0.95},
            model_uri="models:/test/1",
        )
        mock_pipeline_cls.return_value = mock_pipeline

        payload = {
            "data_path": "/tmp/test.csv",
            "learning_rate": 0.05,
        }
        response = test_client.post("/api/v1/train", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "test-run-123"
        assert data["metrics"]["accuracy"] == 0.95
