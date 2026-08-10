"""
Event Publisher Port (SDD §6, §7)。

定義 Domain Event 發佈的介面合約。
Application Layer 透過此 Port 將 Domain Event
發佈至事件基礎設施 (Kafka / In-Memory / etc.)。

實作必須支援 Transactional Outbox 模式 (SDD §30)。
"""

from __future__ import annotations

from typing import Protocol

from src.ml_platform.domain.shared.domain_event import DomainEvent


class EventPublisher(Protocol):
    """
    Domain Event 發佈器介面 (Port)。

    Infrastructure Layer 提供具體實作，如：
    - ``KafkaEventPublisher`` (Outbox → Kafka relay)
    - ``InMemoryEventPublisher`` (測試/本地開發用)
    """

    async def publish(self, event: DomainEvent) -> None:
        """
        發佈單一 Domain Event。

        :param event: 要發佈的 Domain Event。
        """
        ...

    async def publish_all(self, events: list[DomainEvent]) -> None:
        """
        批次發佈多個 Domain Events。

        :param events: Domain Event 列表。
        """
        ...
