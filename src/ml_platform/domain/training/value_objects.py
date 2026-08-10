"""
Training Context — Value Objects。

定義 Training 領域中不可變的值型別，
確保業務資料的語意明確且自我驗證。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TrainingConfig:
    """
    訓練任務的完整設定，作為 CreateTrainingJob 的輸入。

    :param dataset_id: 要使用的 Dataset ID。
    :param pipeline_id: Pipeline 定義 ID (可選，預設為 None)。
    :param hyper_parameters: 模型超參數。
    :param experiment_name: MLflow experiment 名稱。
    :param registered_model_name: 若設定，訓練完成後自動註冊到 Model Registry。
    """

    dataset_id: str
    pipeline_id: str | None = None
    hyper_parameters: HyperParameters = field(
        default_factory=lambda: HyperParameters(),
    )
    experiment_name: str = "default"
    registered_model_name: str | None = None


@dataclass(frozen=True, slots=True)
class HyperParameters:
    """
    模型超參數的 Value Object。

    :param learning_rate: 學習率。
    :param random_state: 亂數種子。
    :param extra: 額外超參數字典。
    """

    learning_rate: float = 0.01
    random_state: int = 42
    extra: dict[str, float | int | str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, float | int | str]:
        """
        將超參數轉為扁平字典，供 MLflow log_params 使用。

        :return: 扁平化的超參數字典。
        """
        result: dict[str, float | int | str] = {
            "learning_rate": self.learning_rate,
            "random_state": self.random_state,
        }
        result.update(self.extra)
        return result


@dataclass(frozen=True, slots=True)
class TrainingMetrics:
    """
    訓練結果指標的 Value Object。

    :param values: 指標名稱與數值的映射。
    """

    values: dict[str, float] = field(default_factory=dict)

    def get(self, key: str) -> float | None:
        """
        取得指定指標的值。

        :param key: 指標名稱。
        :return: 指標值，若不存在則回傳 None。
        """
        return self.values.get(key)
