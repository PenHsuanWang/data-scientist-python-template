"""
推論 API Router。

提供 HTTP 端點使用已註冊的模型進行推論，
支援按 model name + version 或 alias 載入模型。
"""

import logging

import pandas as pd
from fastapi import APIRouter, Depends

from src.ml_core.serving import ModelServingEngine
from src.server.dependencies import get_serving_engine
from src.server.schemas import PredictRequest, PredictResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Prediction"])


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="模型推論",
    description="使用指定的模型對輸入特徵進行推論，支援 version 或 alias 選擇。",
)
def predict(
    request: PredictRequest,
    engine: ModelServingEngine = Depends(get_serving_engine),
) -> PredictResponse:
    """
    使用已註冊的模型進行批次推論。

    :param request: 推論請求 Payload (含模型名稱、版本/別名、特徵)。
    :param engine: 從 DI 注入的 ModelServingEngine。
    :return: 預測結果回應。
    """
    engine.load_model(
        model_name=request.model_name,
        version=request.version,
        alias=request.alias,
    )

    input_df = pd.DataFrame(request.features)

    logger.info(
        "API: 推論請求 — model=%s, alias=%s, version=%s, rows=%d",
        request.model_name,
        request.alias,
        request.version,
        len(input_df),
    )

    predictions = engine.predict(input_df)
    model_info = engine.get_model_info()

    return PredictResponse(
        model_name=request.model_name,
        model_uri=model_info["model_uri"],
        predictions=predictions,
    )
