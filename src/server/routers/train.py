"""
訓練 API Router。

提供 HTTP 端點觸發模型訓練流程，
訓練結果會自動記錄至 MLflow Tracking Server。
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends

from src.adapters.loader import DataLoader
from src.adapters.mlflow_tracker import MLflowExperimentTracker
from src.ml_core.config import ProjectConfig
from src.ml_core.pipeline import TrainingPipeline
from src.ml_core.preprocessor import Preprocessor
from src.ml_core.trainer import Trainer
from src.server.dependencies import get_config
from src.server.schemas import TrainRequest, TrainResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Training"])


@router.post(
    "/train",
    response_model=TrainResponse,
    summary="觸發模型訓練",
    description="啟動完整的訓練流程，包含資料讀取、預處理、訓練與 MLflow 記錄。",
)
def train_model(
    request: TrainRequest,
    config: ProjectConfig = Depends(get_config),
) -> TrainResponse:
    """
    觸發一次完整的模型訓練流程。

    接收超參數覆蓋與資料路徑，實例化 Pipeline 執行訓練，
    並將結果記錄至 MLflow。

    :param request: 訓練請求 Payload。
    :param config: 從 DI 注入的專案設定。
    :return: 包含 run_id、指標與模型 URI 的回應。
    """
    # 用 request 欄位覆蓋 config
    train_config = config.model_copy(
        update={
            k: v
            for k, v in {
                "data_path": Path(request.data_path),
                "learning_rate": request.learning_rate,
                "random_state": request.random_state,
                "mlflow_experiment_name": request.experiment_name,
                "mlflow_registered_model_name": (request.registered_model_name),
            }.items()
            if v is not None
        },
    )

    # Composition Root：在 API handler 中組裝依賴
    tracker = MLflowExperimentTracker(
        tracking_uri=train_config.mlflow_tracking_uri,
    )

    pipeline = TrainingPipeline(
        config=train_config,
        loader=DataLoader(),
        preprocessor=Preprocessor(train_config),
        trainer=Trainer(train_config),
        tracker=tracker,
    )

    logger.info("API: 啟動訓練流程，data_path=%s", train_config.data_path)
    result = pipeline.run()

    return TrainResponse(
        run_id=result.run_id,
        metrics=result.metrics,
        model_uri=result.model_uri,
    )
