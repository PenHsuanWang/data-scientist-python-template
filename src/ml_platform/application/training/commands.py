"""
Training Context — Application Commands。

定義 Training Context 接受的所有 Command。
Command 是 Application Layer 的輸入，代表使用者的意圖。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CreateTrainingJobCommand:
    """
    建立 Training Job 的 Command。

    :param dataset_id: 要使用的 Dataset ID。
    :param experiment_name: MLflow experiment 名稱。
    :param learning_rate: 學習率 (可選)。
    :param random_state: 亂數種子 (可選)。
    :param registered_model_name: 自動註冊模型名稱 (可選)。
    :param extra_params: 額外超參數。
    :param correlation_id: 關聯 ID (用於跨 Context 追蹤)。
    """

    dataset_id: str
    experiment_name: str = "default"
    learning_rate: float = 0.01
    random_state: int = 42
    registered_model_name: str | None = None
    extra_params: dict[str, float | int | str] = field(
        default_factory=dict,
    )
    correlation_id: str = ""


@dataclass(frozen=True, slots=True)
class StartTrainingCommand:
    """
    開始執行 Training Job 的 Command。

    :param job_id: 要開始的 TrainingJob ID。
    :param correlation_id: 關聯 ID。
    """

    job_id: str
    correlation_id: str = ""


@dataclass(frozen=True, slots=True)
class CancelTrainingCommand:
    """
    取消 Training Job 的 Command。

    :param job_id: 要取消的 TrainingJob ID。
    :param reason: 取消原因 (可選)。
    :param correlation_id: 關聯 ID。
    """

    job_id: str
    reason: str = ""
    correlation_id: str = ""


@dataclass(frozen=True, slots=True)
class CompleteTrainingCommand:
    """
    標記 Training 完成的 Command (由 Worker 回報)。

    :param job_id: TrainingJob ID。
    :param run_id: TrainingRun ID。
    :param metrics: 訓練指標。
    :param artifact_uri: 模型 Artifact URI。
    :param correlation_id: 關聯 ID。
    """

    job_id: str
    run_id: str
    metrics: dict[str, float] = field(default_factory=dict)
    artifact_uri: str = ""
    correlation_id: str = ""


@dataclass(frozen=True, slots=True)
class FailTrainingCommand:
    """
    標記 Training 失敗的 Command (由 Worker 回報)。

    :param job_id: TrainingJob ID。
    :param run_id: TrainingRun ID。
    :param error_message: 失敗原因。
    :param correlation_id: 關聯 ID。
    """

    job_id: str
    run_id: str
    error_message: str = ""
    correlation_id: str = ""
