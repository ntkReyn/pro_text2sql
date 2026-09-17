"""Validation at the Wren proposal and execution boundary."""

from packages.analytics_engine.validation.sql_security import (
    WrenSQLSecurityValidator,
)

__all__ = ["WrenSQLSecurityValidator"]
