"""Gates: factory functions for deterministic and group-based experiment gating.

Gates return ``Callable[[], bool]`` for use with ``Experiment.run_if()``.
Three flavours:

- ``entity_gate`` — deterministic per-entity (same entity always in/out)
- ``group_gate`` — membership-based (entity belongs to allowed groups)
- ``request_gate`` — random per-request (simple percentage sampling)
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Collection
from typing import Callable


def entity_gate(
    entity_id: str,
    *,
    percent: float,
    salt: str = "",
) -> Callable[[], bool]:
    """Deterministic per-entity gate.

    The same ``entity_id`` always produces the same True/False for a
    given ``salt``.  Use the experiment name as salt so the same entity
    isn't correlated across experiments.

    Args:
        entity_id: Stable identifier (customer ID, account ID, etc.).
        percent: Percentage of entities to include (0–100).
        salt: Differentiator per experiment (use experiment name).

    Returns:
        A zero-argument callable suitable for ``Experiment.run_if()``.
    """
    key = f"{salt}:{entity_id}" if salt else entity_id
    bucket = int(hashlib.sha256(key.encode()).hexdigest(), 16) % 100
    enabled = bucket < percent
    return lambda: enabled


def group_gate(
    *,
    allowed: Collection[str],
    actual: Collection[str],
) -> Callable[[], bool]:
    """Group membership gate.

    Returns True when the entity belongs to at least one allowed group.

    Args:
        allowed: Groups that should see the candidate.
        actual: Groups the current entity belongs to.

    Returns:
        A zero-argument callable suitable for ``Experiment.run_if()``.
    """
    matched = bool(set(allowed) & set(actual))
    return lambda: matched


def request_gate(*, percent: float) -> Callable[[], bool]:
    """Random per-request gate.

    Each invocation has an independent ``percent``% chance of returning
    True.  Non-deterministic — the same entity may get different results
    on consecutive requests.

    Args:
        percent: Percentage of requests to include (0–100).

    Returns:
        A zero-argument callable suitable for ``Experiment.run_if()``.
    """
    return lambda: random.random() * 100 < percent
