"""
Training Job — Aggregate Root。

TrainingJob 是 Training Context 的核心 Aggregate Root。
代表一次邏輯訓練請求 (SDD §34: "What should be executed?")。
包含完整的 State Machine (SDD §32) 與 Domain Event 收集。
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from src.ml_platform.domain.shared.aggregate_root import AggregateRoot
from src.ml_platform.domain.shared.entity_id import EntityId
from src.ml_platform.domain.training.events import (
    TrainingCancelled,
    TrainingCompleted,
    TrainingFailed,
    TrainingJobCreated,
    TrainingStarted,
)
from src.ml_platform.domain.training.exceptions import (
    InvalidStateTransitionError,
)
from src.ml_platform.domain.training.training_run import (
    TrainingRun,
)
from src.ml_platform.domain.training.value_objects import (
    TrainingConfig,
    TrainingMetrics,
)


class JobStatus(str, enum.Enum):
    """
    Training Job 狀態機 (SDD §32)。

    狀態轉換圖::

        CREATED → QUEUED → RUNNING → COMPLETED → VALIDATION_PENDING → APPROVED
                                   ↘ FAILED                         ↘ REJECTED
        CREATED/QUEUED → CANCELLED
        RUNNING → CANCELLING → CANCELLED
    """

    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    CANCELLING = "CANCELLING"


# 合法的狀態轉換表
_VALID_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.CREATED: {JobStatus.QUEUED, JobStatus.CANCELLED},
    JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.CANCELLED},
    JobStatus.RUNNING: {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCELLING,
    },
    JobStatus.CANCELLING: {JobStatus.CANCELLED},
    JobStatus.COMPLETED: set(),
    JobStatus.FAILED: set(),
    JobStatus.CANCELLED: set(),
}


class TrainingJob(AggregateRoot):
    """
    Training Job Aggregate Root。

    管理訓練的完整生命週期，包含：

    - 狀態機轉換 (SDD §32)
    - TrainingRun 集合 (SDD §34: Job has many Runs)
    - Domain Event 產生

    :param id: Job 唯一識別符。
    :param config: 訓練設定。
    :param status: 當前狀態。
    :param runs: 所有 TrainingRun 的列表。
    :param created_at: 建立時間。
    :param updated_at: 最後更新時間。
    """

    def __init__(
        self,
        id: EntityId,
        config: TrainingConfig,
        status: JobStatus = JobStatus.CREATED,
        runs: list[TrainingRun] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__(id)
        self.config = config
        self.status = status
        self.runs: list[TrainingRun] = runs or []
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    # ── Factory ──────────────────────────────────────────────

    @classmethod
    def create(cls, config: TrainingConfig) -> TrainingJob:
        """
        工廠方法：建立新的 TrainingJob 並產生 TrainingJobCreated 事件。

        :param config: 訓練設定。
        :return: 狀態為 CREATED 的新 TrainingJob。
        """
        job_id = EntityId.generate()
        job = cls(id=job_id, config=config)

        job._record_event(
            TrainingJobCreated(
                aggregate_id=str(job_id),
                dataset_id=config.dataset_id,
                config=config.hyper_parameters.to_dict(),
            )
        )
        return job

    # ── State Transitions ────────────────────────────────────

    def enqueue(self) -> None:
        """
        將 Job 排入執行佇列。

        :raises InvalidStateTransitionError: 若狀態轉換不合法。
        """
        self._transition_to(JobStatus.QUEUED)

    def start(self) -> TrainingRun:
        """
        開始執行訓練，建立新的 TrainingRun。

        :return: 新建的 TrainingRun。
        :raises InvalidStateTransitionError: 若狀態轉換不合法。
        """
        self._transition_to(JobStatus.RUNNING)

        run = TrainingRun.create(job_id=self.id)
        run.mark_running()
        self.runs.append(run)

        self._record_event(
            TrainingStarted(
                aggregate_id=str(self.id),
                run_id=str(run.id),
            )
        )
        return run

    def complete(
        self,
        run: TrainingRun,
        metrics: TrainingMetrics,
        artifact_uri: str = "",
    ) -> None:
        """
        標記訓練完成。

        :param run: 完成的 TrainingRun。
        :param metrics: 訓練指標。
        :param artifact_uri: 模型 Artifact URI。
        :raises InvalidStateTransitionError: 若狀態轉換不合法。
        """
        self._transition_to(JobStatus.COMPLETED)
        run.mark_completed(metrics=metrics, artifact_uri=artifact_uri)

        self._record_event(
            TrainingCompleted(
                aggregate_id=str(self.id),
                run_id=str(run.id),
                metrics=metrics.values,
                artifact_uri=artifact_uri,
            )
        )

    def fail(self, run: TrainingRun, error_message: str) -> None:
        """
        標記訓練失敗。

        :param run: 失敗的 TrainingRun。
        :param error_message: 失敗原因。
        :raises InvalidStateTransitionError: 若狀態轉換不合法。
        """
        self._transition_to(JobStatus.FAILED)
        run.mark_failed(error_message)

        self._record_event(
            TrainingFailed(
                aggregate_id=str(self.id),
                run_id=str(run.id),
                error_message=error_message,
            )
        )

    def cancel(self) -> None:
        """
        取消訓練。

        若 Job 處於 RUNNING 狀態，會先進入 CANCELLING，
        否則直接進入 CANCELLED。

        :raises InvalidStateTransitionError: 若已在終端狀態。
        """
        if self.status == JobStatus.RUNNING:
            self._transition_to(JobStatus.CANCELLING)
            self._transition_to(JobStatus.CANCELLED)
        else:
            self._transition_to(JobStatus.CANCELLED)

        # 取消所有進行中的 Run
        for run in self.runs:
            if run.status.value in ("PENDING", "RUNNING"):
                run.mark_cancelled()

        self._record_event(TrainingCancelled(aggregate_id=str(self.id)))

    # ── Query ────────────────────────────────────────────────

    @property
    def current_run(self) -> TrainingRun | None:
        """
        取得最新的 TrainingRun。

        :return: 最新的 Run，若無則回傳 None。
        """
        if not self.runs:
            return None
        return self.runs[-1]

    @property
    def is_terminal(self) -> bool:
        """
        判斷 Job 是否已進入終端狀態。

        :return: True 若狀態為 COMPLETED/FAILED/CANCELLED。
        """
        return self.status in {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }

    # ── Internal ─────────────────────────────────────────────

    def _transition_to(self, target: JobStatus) -> None:
        """
        執行狀態轉換，並更新 updated_at。

        :param target: 目標狀態。
        :raises InvalidStateTransitionError: 若轉換不合法。
        """
        valid_targets = _VALID_TRANSITIONS.get(self.status, set())
        if target not in valid_targets:
            raise InvalidStateTransitionError(
                current_state=self.status.value,
                target_state=target.value,
            )
        self.status = target
        self.updated_at = datetime.now(timezone.utc)
