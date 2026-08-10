"""
Aggregate Root 基底類別。

所有 DDD Aggregate Root 繼承此類別，
統一管理 Domain Event 的收集與發佈機制。
"""

from __future__ import annotations

from src.ml_platform.domain.shared.domain_event import DomainEvent
from src.ml_platform.domain.shared.entity_id import EntityId


class AggregateRoot:
    """
    Aggregate Root 基底類別。

    提供 Domain Event 收集機制：Aggregate 在執行業務邏輯時
    透過 ``_record_event()`` 記錄事件，Application Layer
    在持久化後透過 ``collect_events()`` 取出並發佈。

    :param id: Aggregate 的唯一識別符。
    """

    def __init__(self, id: EntityId) -> None:
        self.id = id
        self._pending_events: list[DomainEvent] = []

    def _record_event(self, event: DomainEvent) -> None:
        """
        記錄一筆 Domain Event 到待發佈佇列。

        :param event: 要記錄的 Domain Event。
        """
        self._pending_events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """
        取出並清空所有待發佈的 Domain Events。

        Application Layer 在完成持久化後呼叫此方法，
        取得所有事件後透過 EventPublisher 發佈。

        :return: 待發佈的 Domain Event 列表。
        """
        events = list(self._pending_events)
        self._pending_events.clear()
        return events
