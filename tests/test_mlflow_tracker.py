"""
MLflow Experiment Tracker 的單元測試。

使用 Mock 隔離真實的 MLflow SDK，確保 Adapter 層的邏輯正確。
"""

import pytest
from unittest.mock import MagicMock, patch

from src.adapters.mlflow_tracker import (
    MLflowExperimentTracker,
    NoOpExperimentTracker,
)
from src.exceptions import ExperimentTrackingError


class TestNoOpExperimentTracker:
    """NoOpExperimentTracker 應安全地不執行任何操作。"""

    def test_start_run_returns_noop_id(self):
        tracker = NoOpExperimentTracker()
        run_id = tracker.start_run("test-experiment")
        assert run_id == "no-op-run-id"

    def test_log_params_does_not_raise(self):
        tracker = NoOpExperimentTracker()
        tracker.log_params({"lr": 0.01})

    def test_log_metrics_does_not_raise(self):
        tracker = NoOpExperimentTracker()
        tracker.log_metrics({"accuracy": 0.9})

    def test_log_model_returns_noop_uri(self):
        tracker = NoOpExperimentTracker()
        uri = tracker.log_model(MagicMock(), "model")
        assert uri == "no-op-model-uri"

    def test_end_run_does_not_raise(self):
        tracker = NoOpExperimentTracker()
        tracker.end_run()


class TestMLflowExperimentTracker:
    """MLflowExperimentTracker 應正確包裝 MLflow SDK 呼叫。"""

    @patch("src.adapters.mlflow_tracker.MLflowExperimentTracker.__init__")
    def test_start_run_calls_mlflow(self, mock_init):
        mock_init.return_value = None
        tracker = MLflowExperimentTracker.__new__(
            MLflowExperimentTracker,
        )
        mock_mlflow = MagicMock()
        tracker._mlflow = mock_mlflow
        tracker._active_run_id = None

        mock_run = MagicMock()
        mock_run.info.run_id = "abc123"
        mock_mlflow.start_run.return_value = mock_run

        run_id = tracker.start_run("my-experiment", run_name="run-1")

        mock_mlflow.set_experiment.assert_called_once_with("my-experiment")
        mock_mlflow.start_run.assert_called_once_with(run_name="run-1")
        assert run_id == "abc123"

    @patch("src.adapters.mlflow_tracker.MLflowExperimentTracker.__init__")
    def test_log_params_calls_mlflow(self, mock_init):
        mock_init.return_value = None
        tracker = MLflowExperimentTracker.__new__(
            MLflowExperimentTracker,
        )
        mock_mlflow = MagicMock()
        tracker._mlflow = mock_mlflow

        params = {"lr": 0.01, "seed": 42}
        tracker.log_params(params)

        mock_mlflow.log_params.assert_called_once_with(params)

    @patch("src.adapters.mlflow_tracker.MLflowExperimentTracker.__init__")
    def test_log_metrics_calls_mlflow(self, mock_init):
        mock_init.return_value = None
        tracker = MLflowExperimentTracker.__new__(
            MLflowExperimentTracker,
        )
        mock_mlflow = MagicMock()
        tracker._mlflow = mock_mlflow

        metrics = {"accuracy": 0.95}
        tracker.log_metrics(metrics, step=1)

        mock_mlflow.log_metrics.assert_called_once_with(metrics, step=1)

    @patch("src.adapters.mlflow_tracker.MLflowExperimentTracker.__init__")
    def test_start_run_wraps_exception(self, mock_init):
        mock_init.return_value = None
        tracker = MLflowExperimentTracker.__new__(
            MLflowExperimentTracker,
        )
        mock_mlflow = MagicMock()
        tracker._mlflow = mock_mlflow
        tracker._active_run_id = None
        mock_mlflow.set_experiment.side_effect = RuntimeError("conn error")

        with pytest.raises(ExperimentTrackingError, match="啟動 MLflow Run 失敗"):
            tracker.start_run("my-experiment")
