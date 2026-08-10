"""
FastAPI Request/Response 資料模型。

使用 Pydantic v2 定義所有 API 端點的輸入與輸出結構，
確保序列化與驗證的一致性。
"""

from typing import Any

from pydantic import BaseModel, Field


# ─── Train ────────────────────────────────────────────────────────


class TrainRequest(BaseModel):
    """訓練請求的 Payload。"""

    data_path: str = Field(
        ...,
        description="訓練資料的檔案路徑",
    )
    learning_rate: float | None = Field(
        default=None,
        gt=0.0,
        description="覆蓋預設學習率",
    )
    random_state: int | None = Field(
        default=None,
        description="覆蓋預設亂數種子",
    )
    experiment_name: str | None = Field(
        default=None,
        description="覆蓋預設 MLflow experiment 名稱",
    )
    registered_model_name: str | None = Field(
        default=None,
        description="若提供，模型會自動註冊到 Model Registry",
    )


class TrainResponse(BaseModel):
    """訓練回應的 Payload。"""

    run_id: str = Field(description="MLflow Run ID")
    metrics: dict[str, float] = Field(
        description="訓練指標",
    )
    model_uri: str | None = Field(
        default=None,
        description="模型 Artifact 的 URI",
    )


# ─── Predict ──────────────────────────────────────────────────────


class PredictRequest(BaseModel):
    """推論請求的 Payload。"""

    model_name: str = Field(
        ...,
        description="已註冊的模型名稱",
    )
    version: str | None = Field(
        default=None,
        description="指定模型版本號",
    )
    alias: str | None = Field(
        default=None,
        description="指定模型別名 (如 champion)",
    )
    features: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="輸入特徵，每個 dict 代表一筆資料",
    )


class PredictResponse(BaseModel):
    """推論回應的 Payload。"""

    model_name: str = Field(description="使用的模型名稱")
    model_uri: str | None = Field(
        default=None,
        description="載入的模型 URI",
    )
    predictions: list[Any] = Field(description="預測結果列表")


# ─── Models ───────────────────────────────────────────────────────


class ModelVersionInfo(BaseModel):
    """單一模型版本的資訊。"""

    version: str
    status: str
    run_id: str


class ModelInfo(BaseModel):
    """已註冊模型的基本資訊。"""

    name: str
    latest_versions: list[ModelVersionInfo] = Field(default_factory=list)
    description: str | None = None


class ModelListResponse(BaseModel):
    """模型列表回應。"""

    models: list[ModelInfo]


class VersionDetailInfo(BaseModel):
    """模型版本的詳細資訊。"""

    version: str
    status: str
    run_id: str
    aliases: list[str] = Field(default_factory=list)
    creation_timestamp: int | None = None


class VersionListResponse(BaseModel):
    """模型版本列表回應。"""

    model_name: str
    versions: list[VersionDetailInfo]


class SetAliasRequest(BaseModel):
    """設定模型別名的請求。"""

    version: str = Field(
        ...,
        description="目標模型版本號",
    )
    alias: str = Field(
        ...,
        description="要設定的別名 (如 champion)",
    )


class AliasResponse(BaseModel):
    """設定別名的回應。"""

    model_name: str
    version: str
    alias: str
    status: str = "ok"


# ─── Common ──────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """統一錯誤回應格式。"""

    error: str = Field(description="錯誤類型")
    detail: str = Field(description="錯誤訊息")
