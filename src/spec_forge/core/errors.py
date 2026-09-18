# Purpose: every layer needs to raise structured, catchable errors instead of bare exceptions, and
# core is the one place every other layer already depends on (L0). SpecForgeError is the single
# base class every module-specific exception (toolchain, ingest, validate, ...) inherits from, so
# callers can catch "a SpecForge error" without knowing which subsystem raised it.

from __future__ import annotations


class SpecForgeError(Exception):
    """Base class for every exception raised by spec_forge code."""
