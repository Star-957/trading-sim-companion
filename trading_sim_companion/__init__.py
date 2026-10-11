"""Offline synthetic event replay; no trading or account functionality."""

from .engine import InputError, replay

__all__ = ["InputError", "replay"]
__version__ = "0.1.0"
