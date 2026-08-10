"""
Training Run Entity。

代表一次實際的訓練執行 (SDD §34: "What actually happened?")。
一個 TrainingJob 可以有多個 TrainingRun (retry 時建立新 Run)。
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.ml_platform.domain.shared.entity_id import EntityId
from src.ml_platform.domain.training.value_objects import TrainingMetrics


class RunStatus(str, enum.Enum):
    """TrainingRun 的狀態。"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class TrainingRun:
    """
    一次實際的模型訓練執行。

    TrainingRun 記錄 Worker 的真實執行結果，
    包含開始/結束時間、指標、Artifact 位置與失敗原因。

    :param id: Run 唯一識別符。
    :param job_id: 所屬 TrainingJob ID。
    :param status: 當前執行狀態。
    :param metrics: 訓練指標 (完成後填入)。
    :param artifact_uri: 模型 Artifact URI (完成後填入)。
    :param error_message: 失敗原因 (失敗後填入)。
    :param started_at: 開始時間。
    :param completed_at: 結束時間。
    :param created_at: 建立時間。
    """

    id: EntityId
    job_id: EntityId
    status: RunStatus = RunStatus.PENDING
    metrics: TrainingMetrics = field(
        default_factory=TrainingMetrics,
    )
    artifact_uri: str = ""
    error_message: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @classmethod
    def create(cls, job_id: EntityId) -> TrainingRun:
        """
        工廠方法：為指定的 Job 建立新的 Run。

        :param job_id: 所屬 TrainingJob ID。
        :return: 新建的 TrainingRun 實例。
        """
        return cls(
            id=EntityId.generate(),
            job_id=job_id,
        )

    def mark_running(self) -> None:
        """
        標記 Run 為執行中。

        :raises ValueError: 若 Run 不在 PENDING 狀態。
        """
        if self.status != RunStatus.PENDING:
            raise ValueError(f"Cannot start run in {self.status} state")
        self.status = RunStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(
        self,
        metrics: TrainingMetrics,
        artifact_uri: str = "",
    ) -> None:
        """
        標記 Run 為完成。

        :param metrics: 訓練指標。
        :param artifact_uri: 模型 Artifact URI。
        :raises ValueError: 若 Run 不在 RUNNING 狀態。
        """
        if self.status != RunStatus.RUNNING:
            raise ValueError(f"Cannot complete run in {self.status} state")
        self.status = RunStatus.COMPLETED
        self.metrics = metrics
        self.artifact_uri = artifact_uri
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error_message: str) -> None:
        """
        標記 Run 為失敗。

        :param error_message: 失敗原因。
        :raises ValueError: 若 Run 不在 RUNNING 狀態。
        """
        if self.status != RunStatus.RUNNING:
            raise ValueError(f"Cannot fail run in {self.status} state")
        self.status = RunStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc)

    def mark_cancelled(self) -> None:
        """
        標記 Run 為取消。

        :raises ValueError: 若 Run 已結束。
        """
        terminal = {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}
        if self.status in terminal:
            raise ValueError(f"Cannot cancel run in {self.status} state")
        self.status = RunStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)
