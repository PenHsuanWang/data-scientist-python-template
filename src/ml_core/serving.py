"""
Model Serving Engine。

負責從 MLflow Model Registry 載入已註冊的模型並執行推論。
支援按 model name + version 或 model name + alias 載入，
並提供模型快取機制避免重複載入。
"""

import logging
from typing import Any

import pandas as pd

from src.exceptions import ModelNotFoundError, ModelServingError

logger = logging.getLogger(__name__)


class ModelServingEngine:
    """
    從 MLflow Model Registry 載入模型並執行推論的引擎。

    提供模型快取機制，同一個模型 URI 不會重複載入。
    使用 ``mlflow.pyfunc.load_model()`` 進行 flavor-agnostic 載入。
    """

    def __init__(self, tracking_uri: str) -> None:
        """
        初始化 Serving Engine。

        :param tracking_uri: MLflow Tracking Server URI。
        :raises ModelServingError: 若 mlflow 套件不可用。
        """
        try:
            import mlflow

            self._mlflow = mlflow
        except ImportError as e:
            raise ModelServingError(
                "mlflow 套件未安裝，請執行 `pip install mlflow`"
            ) from e

        self._mlflow.set_tracking_uri(tracking_uri)
        self._loaded_model: Any | None = None
        self._loaded_model_uri: str | None = None
        logger.info(
            "ModelServingEngine 初始化完成，URI: %s",
            tracking_uri,
        )

    def load_model(
        self,
        model_name: str,
        version: str | None = None,
        alias: str | None = None,
    ) -> None:
        """
        從 MLflow Model Registry 載入指定模型。

        優先使用 ``alias``，若未指定則使用 ``version``。
        兩者皆未指定時，使用最新版本 (latest)。

        :param model_name: 已註冊的模型名稱。
        :param version: 模型版本號。
        :param alias: 模型別名 (如 ``champion``, ``challenger``)。
        :raises ModelNotFoundError: 若模型不存在或版本/別名無效。
        """
        model_uri = self._build_model_uri(model_name, version, alias)

        if self._loaded_model_uri == model_uri:
            logger.debug("模型已在快取中: %s", model_uri)
            return

        try:
            self._loaded_model = self._mlflow.pyfunc.load_model(model_uri)
            self._loaded_model_uri = model_uri
            logger.info("模型載入成功: %s", model_uri)
        except Exception as e:
            self._loaded_model = None
            self._loaded_model_uri = None
            raise ModelNotFoundError(f"無法載入模型 '{model_uri}': {e}") from e

    def predict(self, input_data: pd.DataFrame) -> list[Any]:
        """
        使用已載入的模型對輸入資料進行推論。

        :param input_data: 輸入特徵的 DataFrame。
        :return: 預測結果列表。
        :raises ModelServingError: 若模型尚未載入。
        """
        if self._loaded_model is None:
            raise ModelServingError("尚未載入模型，請先呼叫 load_model()")

        try:
            predictions = self._loaded_model.predict(input_data)
            return predictions.tolist()
        except Exception as e:
            raise ModelServingError(f"推論過程失敗: {e}") from e

    def get_model_info(self) -> dict[str, Any]:
        """
        取得目前已載入模型的基本資訊。

        :return: 包含模型 URI 與載入狀態的字典。
        """
        return {
            "model_uri": self._loaded_model_uri,
            "is_loaded": self._loaded_model is not None,
        }

    def list_registered_models(self) -> list[dict[str, Any]]:
        """
        列出 MLflow Model Registry 中所有已註冊的模型。

        :return: 模型資訊列表。
        :raises ModelServingError: 若查詢失敗。
        """
        try:
            client = self._mlflow.tracking.MlflowClient()
            registered_models = client.search_registered_models()
            return [
                {
                    "name": rm.name,
                    "latest_versions": [
                        {
                            "version": mv.version,
                            "status": mv.status,
                            "run_id": mv.run_id,
                        }
                        for mv in (rm.latest_versions or [])
                    ],
                    "description": rm.description,
                }
                for rm in registered_models
            ]
        except Exception as e:
            raise ModelServingError(f"查詢已註冊模型失敗: {e}") from e

    def get_model_versions(
        self,
        model_name: str,
    ) -> list[dict[str, Any]]:
        """
        取得指定模型的所有版本資訊。

        :param model_name: 已註冊的模型名稱。
        :return: 版本資訊列表。
        :raises ModelServingError: 若查詢失敗。
        """
        try:
            client = self._mlflow.tracking.MlflowClient()
            versions = client.search_model_versions(f"name='{model_name}'")
            return [
                {
                    "version": v.version,
                    "status": v.status,
                    "run_id": v.run_id,
                    "aliases": list(v.aliases) if v.aliases else [],
                    "creation_timestamp": v.creation_timestamp,
                }
                for v in versions
            ]
        except Exception as e:
            raise ModelServingError(f"查詢模型版本失敗: {e}") from e

    def set_model_alias(
        self,
        model_name: str,
        version: str,
        alias: str,
    ) -> None:
        """
        為指定模型版本設定別名 (Tag)。

        :param model_name: 已註冊的模型名稱。
        :param version: 目標版本號。
        :param alias: 要設定的別名 (如 ``champion``)。
        :raises ModelServingError: 若設定失敗。
        """
        try:
            client = self._mlflow.tracking.MlflowClient()
            client.set_registered_model_alias(
                name=model_name,
                alias=alias,
                version=version,
            )
            logger.info(
                "已設定 alias '%s' → %s (version %s)",
                alias,
                model_name,
                version,
            )
        except Exception as e:
            raise ModelServingError(f"設定模型 alias 失敗: {e}") from e

    @staticmethod
    def _build_model_uri(
        model_name: str,
        version: str | None = None,
        alias: str | None = None,
    ) -> str:
        """
        組建 MLflow 模型 URI。

        :param model_name: 模型名稱。
        :param version: 版本號。
        :param alias: 別名。
        :return: 格式化的 MLflow 模型 URI。
        """
        if alias:
            return f"models:/{model_name}@{alias}"
        if version:
            return f"models:/{model_name}/{version}"
        return f"models:/{model_name}/latest"
