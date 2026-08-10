"""
Job Executor Port (SDD §45)。

定義訓練任務的執行合約。
Application Layer 透過此 Port 將訓練任務
提交至執行平面 (Local Worker / Kubernetes / Spark)。
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Protocol


class ExecutionStatus(str, enum.Enum):
    """執行任務的狀態。"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class ExecutionHandle:
    """
    執行任務的控制代碼，用於查詢或取消。

    :param handle_id: 執行任務的唯一 ID。
    :param job_id: 對應的 TrainingJob ID。
    """

    handle_id: str
    job_id: str


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """
    執行結果。

    :param status: 最終執行狀態。
    :param metrics: 訓練指標 (若 COMPLETED)。
    :param artifact_uri: Artifact URI (若 COMPLETED)。
    :param error_message: 錯誤訊息 (若 FAILED)。
    """

    status: ExecutionStatus
    metrics: dict[str, float]
    artifact_uri: str = ""
    error_message: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionJob:
    """
    提交至執行平面的任務描述。

    :param job_id: TrainingJob ID。
    :param run_id: TrainingRun ID。
    :param dataset_id: 要使用的 Dataset ID。
    :param hyper_parameters: 超參數。
    :param experiment_name: MLflow experiment 名稱。
    :param registered_model_name: 自動註冊的模型名稱 (可選)。
    """

    job_id: str
    run_id: str
    dataset_id: str
    hyper_parameters: dict[str, float | int | str]
    experiment_name: str = "default"
    registered_model_name: str | None = None


class JobExecutor(Protocol):
    """
    Job 執行器介面 (Port)。

    Infrastructure Layer 提供具體實作，如：
    - ``LocalJobExecutor`` (本地 Python 執行)
    - ``KubernetesJobExecutor`` (K8s Pod)
    """

    async def submit(self, job: ExecutionJob) -> ExecutionHandle:
        """
        提交任務至執行平面。

        :param job: 任務描述。
        :return: 執行控制代碼。
        """
        ...

    async def cancel(self, handle: ExecutionHandle) -> None:
        """
        取消執行中的任務。

        :param handle: 執行控制代碼。
        """
        ...

    async def status(self, handle: ExecutionHandle) -> ExecutionStatus:
        """
        查詢任務的執行狀態。

        :param handle: 執行控制代碼。
        :return: 當前執行狀態。
        """
        ...
