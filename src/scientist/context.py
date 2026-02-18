"""ContextVar-based defaults for publisher and enabled state."""

from __future__ import annotations

from contextvars import ContextVar

from .protocols import Publisher

_default_publisher_context: ContextVar[Publisher | None] = ContextVar(
    "scientist_default_publisher", default=None
)

_default_enabled_context: ContextVar[bool] = ContextVar(
    "scientist_default_enabled", default=True
)


def set_default_publisher(publisher: Publisher | None) -> None:
    """Set the default publisher for all experiments."""
    _default_publisher_context.set(publisher)


def get_default_publisher() -> Publisher | None:
    """Get the default publisher."""
    return _default_publisher_context.get()


def set_default_enabled(enabled: bool) -> None:
    """Set whether experiments run by default."""
    _default_enabled_context.set(enabled)


def get_default_enabled() -> bool:
    """Get default enabled state (defaults to True)."""
    return _default_enabled_context.get()
