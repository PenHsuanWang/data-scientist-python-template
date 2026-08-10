"""
MLflow Experiment Tracker Adapter。

將 MLflow SDK 封裝在 Adapter 層中，確保 ML Core 不直接依賴 ``mlflow`` 套件。
提供 ``ExperimentTrackerProtocol`` 作為 Port，以及兩個具體實作：

- ``MLflowExperimentTracker``：連接真實 MLflow Tracking Server。
- ``NoOpExperimentTracker``：不執行任何操作，用於本地除錯或單元測試。
"""

import logging
from typing import Any, Protocol

from src.exceptions import ExperimentTrackingError

logger = logging.getLogger(__name__)


class ExperimentTrackerProtocol(Protocol):
    """
    實驗追蹤器的介面合約 (Port)。

    所有需要記錄實驗參數、指標與模型的元件，
    都應依賴此 Protocol 而非具體的 MLflow 套件。
    """

    def start_run(
        self,
        experiment_name: str,
        run_name: str | None = None,
    ) -> str:
        """
        開啟一個新的實驗 Run。

        :param experiment_name: 實驗名稱。
        :param run_name: 可選的 Run 名稱。
        :return: 此次 Run 的唯一 ID。
        """
        ...

    def log_params(self, params: dict[str, Any]) -> None:
        """
        記錄超參數。

        :param params: 鍵值對形式的超參數字典。
        """
        ...

    def log_metrics(
        self,
        metrics: dict[str, float],
        step: int | None = None,
    ) -> None:
        """
        記錄訓練指標。

        :param metrics: 鍵值對形式的指標字典。
        :param step: 可選的步驟編號 (用於迭代追蹤)。
        """
        ...

    def log_model(
        self,
        model: Any,
        artifact_path: str,
        registered_model_name: str | None = None,
    ) -> str:
        """
        記錄模型 Artifact 並可選地註冊到 Model Registry。

        :param model: 已訓練的模型物件。
        :param artifact_path: Artifact 存放的子路徑。
        :param registered_model_name: 若提供則自動註冊。
        :return: 模型 Artifact 的 URI。
        """
        ...

    def end_run(self) -> None:
        """結束當前的實驗 Run。"""
        ...


class MLflowExperimentTracker:
    """
    MLflow Tracking Server 的具體 Adapter 實作。

    負責與 MLflow SDK 互動，包括 Run 管理、參數/指標/模型記錄，
    以及 Model Registry 的自動註冊。
    """

    def __init__(self, tracking_uri: str) -> None:
        """
        初始化 MLflow Tracker。

        :param tracking_uri: MLflow Tracking Server 的位址。
        :raises ExperimentTrackingError: 若 MLflow 套件不可用。
        """
        try:
            import mlflow

            self._mlflow = mlflow
        except ImportError as e:
            raise ExperimentTrackingError(
                "mlflow 套件未安裝，請執行 `pip install mlflow`"
            ) from e

        self._mlflow.set_tracking_uri(tracking_uri)
        self._active_run_id: str | None = None
        logger.info("MLflow Tracker 初始化完成，URI: %s", tracking_uri)

    def start_run(
        self,
        experiment_name: str,
        run_name: str | None = None,
    ) -> str:
        """
        開啟一個新的 MLflow Run。

        :param experiment_name: MLflow experiment 名稱。
        :param run_name: 可選的 Run 顯示名稱。
        :return: 新建 Run 的 ID。
        :raises ExperimentTrackingError: 若 MLflow 操作失敗。
        """
        try:
            self._mlflow.set_experiment(experiment_name)
            run = self._mlflow.start_run(run_name=run_name)
            self._active_run_id = run.info.run_id
            logger.info(
                "MLflow Run 已啟動: %s (experiment: %s)",
                self._active_run_id,
                experiment_name,
            )
            return self._active_run_id
        except Exception as e:
            raise ExperimentTrackingError(f"啟動 MLflow Run 失敗: {e}") from e

    def log_params(self, params: dict[str, Any]) -> None:
        """
        記錄超參數到當前 MLflow Run。

        :param params: 超參數字典。
        :raises ExperimentTrackingError: 若記錄失敗。
        """
        try:
            self._mlflow.log_params(params)
        except Exception as e:
            raise ExperimentTrackingError(f"記錄超參數失敗: {e}") from e

    def log_metrics(
        self,
        metrics: dict[str, float],
        step: int | None = None,
    ) -> None:
        """
        記錄訓練指標到當前 MLflow Run。

        :param metrics: 指標字典。
        :param step: 可選的步驟編號。
        :raises ExperimentTrackingError: 若記錄失敗。
        """
        try:
            self._mlflow.log_metrics(metrics, step=step)
        except Exception as e:
            raise ExperimentTrackingError(f"記錄訓練指標失敗: {e}") from e

    def log_model(
        self,
        model: Any,
        artifact_path: str,
        registered_model_name: str | None = None,
    ) -> str:
        """
        記錄模型 Artifact 並可選地註冊到 Model Registry。

        :param model: 已訓練的 sklearn-compatible 模型物件。
        :param artifact_path: Artifact 存放子路徑。
        :param registered_model_name: 若提供則自動註冊。
        :return: 模型 Artifact 的 URI。
        :raises ExperimentTrackingError: 若記錄失敗。
        """
        try:
            model_info = self._mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path=artifact_path,
                registered_model_name=registered_model_name,
            )
            model_uri = model_info.model_uri
            logger.info("模型已記錄至 MLflow: %s", model_uri)
            return model_uri
        except Exception as e:
            raise ExperimentTrackingError(f"記錄模型至 MLflow 失敗: {e}") from e

    def end_run(self) -> None:
        """
        結束當前的 MLflow Run。

        :raises ExperimentTrackingError: 若結束操作失敗。
        """
        try:
            self._mlflow.end_run()
            logger.info("MLflow Run 已結束: %s", self._active_run_id)
            self._active_run_id = None
        except Exception as e:
            raise ExperimentTrackingError(f"結束 MLflow Run 失敗: {e}") from e


class NoOpExperimentTracker:
    """
    無操作的實驗追蹤器 (Null Object Pattern)。

    用於本地除錯或單元測試場景，不依賴任何外部服務。
    所有方法皆為空操作。
    """

    def start_run(
        self,
        experiment_name: str,
        run_name: str | None = None,
    ) -> str:
        """
        模擬開啟 Run，回傳固定的假 ID。

        :param experiment_name: 實驗名稱 (忽略)。
        :param run_name: Run 名稱 (忽略)。
        :return: 固定的 no-op Run ID。
        """
        logger.debug("NoOp Tracker: start_run (no-op)")
        return "no-op-run-id"

    def log_params(self, params: dict[str, Any]) -> None:
        """
        模擬記錄超參數 (不執行任何操作)。

        :param params: 超參數字典 (忽略)。
        """
        logger.debug("NoOp Tracker: log_params (no-op)")

    def log_metrics(
        self,
        metrics: dict[str, float],
        step: int | None = None,
    ) -> None:
        """
        模擬記錄指標 (不執行任何操作)。

        :param metrics: 指標字典 (忽略)。
        :param step: 步驟編號 (忽略)。
        """
        logger.debug("NoOp Tracker: log_metrics (no-op)")

    def log_model(
        self,
        model: Any,
        artifact_path: str,
        registered_model_name: str | None = None,
    ) -> str:
        """
        模擬記錄模型，回傳假的 URI。

        :param model: 模型物件 (忽略)。
        :param artifact_path: Artifact 路徑 (忽略)。
        :param registered_model_name: 註冊名稱 (忽略)。
        :return: 固定的 no-op URI。
        """
        logger.debug("NoOp Tracker: log_model (no-op)")
        return "no-op-model-uri"

    def end_run(self) -> None:
        """模擬結束 Run (不執行任何操作)。"""
        logger.debug("NoOp Tracker: end_run (no-op)")
