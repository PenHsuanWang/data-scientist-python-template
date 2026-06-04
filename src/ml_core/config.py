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

    data_path: Path = Field(
        ..., description="原始資料來源路徑 (CSV 或 SQLite 檔案位置)"
    )
    model_save_path: Path = Field(
        ..., description="訓練完成後的模型儲存路徑 (.pkl 或 .onnx)"
    )
    learning_rate: float = Field(
        default=0.01, gt=0.0, description="模型學習率，必須大於 0"
    )
    random_state: int = Field(default=42, description="全域亂數種子，確保結果可重現")
