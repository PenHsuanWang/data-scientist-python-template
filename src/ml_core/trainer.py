import pandas as pd
from pathlib import Path
from typing import Any
from src.ml_core.config import ProjectConfig
from src.exceptions import ModelTrainingError, MLProjectBaseError


class Trainer:
    """
    封裝特定機器學習演算法的狀態模型，提供統一的訓練與評估介面。
    """

    def __init__(self, config: ProjectConfig):
        """
        初始化訓練器。

        :param config: 已驗證的全域設定物件 (包含超參數)。
        """
        self.config = config
        # TODO: 實例化底層演算法 (e.g. XGBClassifier)
        self.model: Any | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> dict[str, float]:
        """
        接收特徵矩陣與標籤，執行模型訓練。

        :param X: 特徵矩陣。
        :param y: 目標變數。
        :return: 包含訓練結果指標 (Metrics) 的字典。
        :raises ModelTrainingError: 若演算法不收斂或發生 OOM 錯誤。
        """
        try:
            # TODO: 執行自我驗證或 Cross Validation
            # self.model.fit(X, y)

            # 回傳假指標
            return {"accuracy": 0.95, "f1_score": 0.92}

        except MLProjectBaseError:
            raise
        except Exception as e:
            raise ModelTrainingError("模型訓練過程失敗") from e

    def save(self, save_path: Path) -> None:
        """
        將訓練好的模型狀態序列化並儲存至磁碟。

        :param save_path: 模型儲存的目標路徑。
        :raises ModelTrainingError: 若儲存失敗。
        """
        if self.model is None:
            raise ModelTrainingError("無法儲存未訓練的模型")

        # TODO: 實作 joblib 或 pickle 的儲存邏輯
        pass
