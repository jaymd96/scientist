"""No-op publisher that silently discards results."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..protocols import Publisher

if TYPE_CHECKING:
    from ..result import Result


class NoopPublisher:
    """Publisher that does nothing. Default when no publisher is configured."""

    def publish(self, result: Result[object]) -> None:
        pass


def new_noop_publisher() -> Publisher:
    return NoopPublisher()  # type: ignore
