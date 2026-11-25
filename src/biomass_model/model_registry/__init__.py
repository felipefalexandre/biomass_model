"""Registro de modelos e promoção champion/challenger (ADR-0033)."""

from .registry import (
    compare_models,
    list_models,
    load_registry,
    promote_model,
    register_model,
)

__all__ = [
    "compare_models",
    "list_models",
    "load_registry",
    "promote_model",
    "register_model",
]
