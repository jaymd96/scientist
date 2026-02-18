"""Composite publisher that forwards to multiple publishers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..protocols import Publisher

if TYPE_CHECKING:
    from ..result import Result


class CompositePublisher:
    """Forwards results to all contained publishers.

    Individual publisher errors are swallowed (best-effort).
    """

    def __init__(self, *publishers: Publisher) -> None:
        self.publishers = publishers

    def publish(self, result: Result[object]) -> None:
        for publisher in self.publishers:
            try:
                publisher.publish(result)
            except Exception:
                pass


def new_composite_publisher(*publishers: Publisher) -> Publisher:
    return CompositePublisher(*publishers)  # type: ignore
