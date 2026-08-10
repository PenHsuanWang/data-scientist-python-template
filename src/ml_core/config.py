from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectConfig(BaseSettings):
    """
    專案全域設定與超參數的單一真相來源 (Single Source of Truth)。
    遵循 12-Factor App 原則 (Factor III: Config)，優先讀取環境變數。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ML_",
        extra="ignore",
    )

    # --- Data & Training ---
    data_path: Path = Field(
        ..., description="原始資料來源路徑 (CSV 或 SQLite 檔案位置)"
    )
    model_save_path: Path | None = Field(
        default=None,
        description="本地模型儲存路徑 (整合 MLflow 後為 Optional)",
    )
    learning_rate: float = Field(
        default=0.01, gt=0.0, description="模型學習率，必須大於 0"
    )
    random_state: int = Field(default=42, description="全域亂數種子，確保結果可重現")

    # --- MLflow ---
    mlflow_tracking_uri: str = Field(
        default="http://localhost:5000",
        description="MLflow Tracking Server URI",
    )
    mlflow_experiment_name: str = Field(
        default="default",
        description="MLflow experiment 名稱",
    )
    mlflow_registered_model_name: str | None = Field(
        default=None,
        description="若設定，模型會自動註冊到 Model Registry",
    )

    # --- FastAPI Server ---
    server_host: str = Field(
        default="0.0.0.0",
        description="FastAPI 服務監聽位址",
    )
    server_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="FastAPI 服務監聽埠號",
    )
