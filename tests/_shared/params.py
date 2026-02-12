# tests/_shared/params.py
from __future__ import annotations # Keep type hints as strings (lazy evaluation) to avoid forward-ref/circular-import issues.

from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping

def iter_params(params: Any) -> Iterable[tuple[str, Any]]:
    """
    Normalize 'params' to (key, value) pairs for logging.
    Return an *iterable* of (key, value) pairs for the given `params`.
    Example: for k, v in iter_params(test_case.params): ...

    Why this exists:
    - Different suites define different TestParams shapes (dataclass, dict, NamedTuple, etc.).
    - Logging + requests should stay generic and not care about the concrete type.
    - So we normalize everything to a single common format: (key, value) pairs.

    Supported inputs:
    - dict / Mapping: use .items()
    - dataclass instance: convert via dataclasses.asdict(...)
    - NamedTuple: use ._asdict() if available
    - plain objects: use vars(obj) / obj.__dict__
    """    
    # No params => no pairs (keeps callers simple)
    if params is None:
        return []

    # Mapping (dict-like): already in key/value form
    if isinstance(params, Mapping):
        return params.items()

    # Dataclass: turn into a dict first, then expose .items()
    if is_dataclass(params):
        return asdict(params).items()

    # NamedTuple: _asdict() provides an OrderedDict-like mapping
    if hasattr(params, "_asdict"):  # NamedTuple instances
        return params._asdict().items()  # type: ignore[attr-defined]

    # Plain object: fall back to its attribute dict
    if hasattr(params, "__dict__"):  # plain objects
        return vars(params).items()

    # Anything else is ambiguous => fail loudly
    raise TypeError(f"Unsupported params type: {type(params).__name__}")


def params_dict(params: Any) -> dict[str, Any]:
    """
    Convert suite-specific params into a plain dict for requests.get(..., params=...).

    Why:
    - requests expects a mapping for query params.
    - iter_params() gives us a uniform (key, value) stream.
    - dict(...) turns that stream into the mapping requests needs.
    """
    return dict(iter_params(params))
