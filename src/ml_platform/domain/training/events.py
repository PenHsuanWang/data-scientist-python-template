"""
Training Context — Domain Events。

遵循 SDD §25-27 Event Contract 與 §26 命名規範。
每個事件對應 Training 領域的一次狀態變化。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ml_platform.domain.shared.domain_event import DomainEvent


@dataclass(frozen=True, slots=True)
class TrainingJobCreated(DomainEvent):
    """
    Training Job 已建立事件。

    :param dataset_id: 使用的 Dataset ID。
    :param config: 序列化的訓練設定。
    """

    event_type: str = field(
        default="ml.training.job.created.v1",
        init=False,
    )
    aggregate_type: str = field(default="TrainingJob", init=False)
    dataset_id: str = ""
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrainingStarted(DomainEvent):
    """
    Training 已開始執行事件。

    :param run_id: 本次執行的 TrainingRun ID。
    """

    event_type: str = field(
        default="ml.training.job.started.v1",
        init=False,
    )
    aggregate_type: str = field(default="TrainingJob", init=False)
    run_id: str = ""


@dataclass(frozen=True, slots=True)
class TrainingCompleted(DomainEvent):
    """
    Training 已完成事件。

    :param run_id: 完成的 TrainingRun ID。
    :param metrics: 訓練結果指標。
    :param artifact_uri: 模型 Artifact URI (若有)。
    """

    event_type: str = field(
        default="ml.training.job.completed.v1",
        init=False,
    )
    aggregate_type: str = field(default="TrainingJob", init=False)
    run_id: str = ""
    metrics: dict[str, float] = field(default_factory=dict)
    artifact_uri: str = ""


@dataclass(frozen=True, slots=True)
class TrainingFailed(DomainEvent):
    """
    Training 執行失敗事件。

    :param run_id: 失敗的 TrainingRun ID。
    :param error_message: 失敗原因。
    """

    event_type: str = field(
        default="ml.training.job.failed.v1",
        init=False,
    )
    aggregate_type: str = field(default="TrainingJob", init=False)
    run_id: str = ""
    error_message: str = ""


@dataclass(frozen=True, slots=True)
class TrainingCancelled(DomainEvent):
    """
    Training 已取消事件。
    """

    event_type: str = field(
        default="ml.training.job.cancelled.v1",
        init=False,
    )
    aggregate_type: str = field(default="TrainingJob", init=False)
