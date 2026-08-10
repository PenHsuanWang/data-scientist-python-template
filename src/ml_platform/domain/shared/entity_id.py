"""
強型別 Entity ID — Value Object。

所有 Domain Entity 的 ID 統一使用此 Value Object，
避免 primitive obsession (直接用 str/UUID)。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EntityId:
    """
    不可變的 Entity 識別符。

    使用 ``frozen=True`` 確保 Value Object 語意：
    一旦建立就不可修改，可安全用於 dict key 或 set。

    :param value: UUID 字串。
    """

    value: str

    @classmethod
    def generate(cls) -> EntityId:
        """
        產生一個新的隨機 UUID v4 識別符。

        :return: 新的 EntityId 實例。
        """
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls, raw: str) -> EntityId:
        """
        從字串建立 EntityId，驗證其 UUID 格式。

        :param raw: UUID 格式字串。
        :return: EntityId 實例。
        :raises ValueError: 若格式不合法。
        """
        uuid.UUID(raw)  # validate
        return cls(value=raw)

    def __str__(self) -> str:
        return self.value
