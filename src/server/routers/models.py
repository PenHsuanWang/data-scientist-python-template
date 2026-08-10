"""
模型管理 API Router。

提供 HTTP 端點查詢已註冊的模型列表、版本資訊，
以及設定/更新模型的 alias (tag)。
"""

import logging

from fastapi import APIRouter, Depends

from src.ml_core.serving import ModelServingEngine
from src.server.dependencies import get_serving_engine
from src.server.schemas import (
    AliasResponse,
    ModelListResponse,
    SetAliasRequest,
    VersionDetailInfo,
    VersionListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["Model Registry"])


@router.get(
    "",
    response_model=ModelListResponse,
    summary="列出所有已註冊模型",
    description="從 MLflow Model Registry 取得所有已註冊的模型清單。",
)
def list_models(
    engine: ModelServingEngine = Depends(get_serving_engine),
) -> ModelListResponse:
    """
    列出 MLflow Model Registry 中的所有模型。

    :param engine: 從 DI 注入的 ModelServingEngine。
    :return: 模型列表回應。
    """
    models = engine.list_registered_models()
    return ModelListResponse(models=models)


@router.get(
    "/{model_name}/versions",
    response_model=VersionListResponse,
    summary="取得模型版本列表",
    description="取得指定模型的所有版本詳細資訊，包含 alias。",
)
def get_model_versions(
    model_name: str,
    engine: ModelServingEngine = Depends(get_serving_engine),
) -> VersionListResponse:
    """
    取得指定模型的所有版本資訊。

    :param model_name: 已註冊的模型名稱。
    :param engine: 從 DI 注入的 ModelServingEngine。
    :return: 版本列表回應。
    """
    versions = engine.get_model_versions(model_name)
    return VersionListResponse(
        model_name=model_name,
        versions=[VersionDetailInfo(**v) for v in versions],
    )


@router.put(
    "/{model_name}/alias",
    response_model=AliasResponse,
    summary="設定模型別名 (Tag)",
    description=("為指定模型版本設定別名，如將 version 3 設為 'champion'。"),
)
def set_model_alias(
    model_name: str,
    request: SetAliasRequest,
    engine: ModelServingEngine = Depends(get_serving_engine),
) -> AliasResponse:
    """
    為指定模型版本設定 alias。

    :param model_name: 已註冊的模型名稱。
    :param request: 包含版本號與別名的請求。
    :param engine: 從 DI 注入的 ModelServingEngine。
    :return: 設定結果回應。
    """
    engine.set_model_alias(
        model_name=model_name,
        version=request.version,
        alias=request.alias,
    )

    logger.info(
        "API: 已設定 alias '%s' → %s (version %s)",
        request.alias,
        model_name,
        request.version,
    )

    return AliasResponse(
        model_name=model_name,
        version=request.version,
        alias=request.alias,
    )
