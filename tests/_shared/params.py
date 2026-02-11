# tests/_shared/params.py
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping

def iter_params(params: Any) -> Iterable[tuple[str, Any]]:
    """
    Normalize 'params' to (key, value) pairs for logging.
    Supports:
      - dict / Mapping
      - dataclass instances
      - NamedTuple (has _asdict)
      - plain objects with __dict__
    """
    if params is None:
        return []

    if isinstance(params, Mapping):
        return params.items()

    if is_dataclass(params):
        return asdict(params).items()

    if hasattr(params, "_asdict"):  # NamedTuple instances
        return params._asdict().items()  # type: ignore[attr-defined]

    if hasattr(params, "__dict__"):  # plain objects
        return vars(params).items()

    raise TypeError(f"Unsupported params type: {type(params).__name__}")


def params_dict(params: Any) -> dict[str, Any]:
    """Normalize params into a dict for requests.get(..., params=...)."""
    return dict(iter_params(params))
