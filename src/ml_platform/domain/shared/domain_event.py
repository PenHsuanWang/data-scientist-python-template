"""
Domain Event 基底類別。

遵循 SDD §27 Event Contract，所有 Domain Event 繼承此類別，
確保攜帶 event_id, event_type, occurred_at, aggregate_id 等標準欄位。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """
    Domain Event 的不可變基底類別。

    所有 Bounded Context 產生的事件都繼承此類別，
    確保符合 SDD §27 Event Contract 的標準欄位。

    :param event_id: 事件的唯一 ID。
    :param event_type: 事件類型 (如 ``ml.training.job.created.v1``)。
    :param occurred_at: 事件發生時間 (UTC)。
    :param aggregate_id: 觸發事件的 Aggregate ID。
    :param aggregate_type: Aggregate 的類型名稱。
    :param correlation_id: 關聯 ID (用於追蹤同一業務流程)。
    :param causation_id: 因果 ID (觸發此事件的上一個事件/命令 ID)。
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    aggregate_id: str = ""
    aggregate_type: str = ""
    correlation_id: str = ""
    causation_id: str = ""
