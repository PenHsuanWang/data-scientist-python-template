"""
Domain 與 Application 測試共用 Fixtures。

提供 Fake Port 實作，確保 Domain/Application 測試
完全 in-memory，不依賴任何外部基礎設施 (SDD §65-66)。
"""

from __future__ import annotations

import pytest

from src.ml_platform.domain.shared.domain_event import DomainEvent
from src.ml_platform.domain.shared.entity_id import EntityId
from src.ml_platform.domain.training.training_job import TrainingJob


class FakeTrainingJobRepository:
    """
    In-Memory TrainingJob Repository (Fake)。

    用於 Application 層 Use Case 測試。
    """

    def __init__(self) -> None:
        self._store: dict[str, TrainingJob] = {}

    async def get(self, job_id: EntityId) -> TrainingJob | None:
        """取得 TrainingJob。"""
        return self._store.get(str(job_id))

    async def save(self, job: TrainingJob) -> None:
        """儲存 TrainingJob。"""
        self._store[str(job.id)] = job

    async def list_all(self) -> list[TrainingJob]:
        """列出所有 TrainingJob。"""
        return list(self._store.values())


class FakeEventPublisher:
    """
    In-Memory Event Publisher (Fake)。

    記錄所有已發佈的事件，供測試斷言使用。
    """

    def __init__(self) -> None:
        self.published_events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        """發佈單一事件。"""
        self.published_events.append(event)

    async def publish_all(self, events: list[DomainEvent]) -> None:
        """批次發佈事件。"""
        self.published_events.extend(events)


@pytest.fixture()
def fake_repository() -> FakeTrainingJobRepository:
    """提供 Fake TrainingJob Repository。"""
    return FakeTrainingJobRepository()


@pytest.fixture()
def fake_event_publisher() -> FakeEventPublisher:
    """提供 Fake Event Publisher。"""
    return FakeEventPublisher()
