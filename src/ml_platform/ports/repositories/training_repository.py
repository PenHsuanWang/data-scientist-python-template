"""
Training Job Repository Port (SDD §58)。

Domain 不依賴 SQLAlchemy 或任何具體 ORM。
此 Protocol 定義了 Training Context 對持久化的需求。
"""

from __future__ import annotations

from typing import Protocol

from src.ml_platform.domain.shared.entity_id import EntityId
from src.ml_platform.domain.training.training_job import TrainingJob


class TrainingJobRepository(Protocol):
    """
    TrainingJob 的持久化介面 (Port)。

    Infrastructure Layer 提供具體實作，如：
    - ``PostgresTrainingJobRepository``
    - ``InMemoryTrainingJobRepository`` (測試用)
    """

    async def get(self, job_id: EntityId) -> TrainingJob | None:
        """
        根據 ID 取得 TrainingJob。

        :param job_id: TrainingJob 的唯一識別符。
        :return: TrainingJob 實例，若不存在則回傳 None。
        """
        ...

    async def save(self, job: TrainingJob) -> None:
        """
        持久化 TrainingJob (含 TrainingRun)。

        實作必須以 Transactional 方式同時寫入 Job 與
        其所有 TrainingRun 的狀態。

        :param job: 要持久化的 TrainingJob 實例。
        """
        ...

    async def list_all(self) -> list[TrainingJob]:
        """
        取得所有 TrainingJob。

        :return: TrainingJob 列表。
        """
        ...
