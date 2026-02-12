"""Custom exception types for GIMP MCP Pro."""

from __future__ import annotations


class GimpMCPError(Exception):
    """Base exception for all GIMP MCP Pro errors."""


class GimpConnectionError(GimpMCPError):
    """Failed to connect or communicate with the GIMP plugin."""


class GimpCommandError(GimpMCPError):
    """A command sent to GIMP returned an error."""

    def __init__(self, message: str, command: str | None = None, traceback: str | None = None):
        super().__init__(message)
        self.command = command
        self.gimp_traceback = traceback


class GimpTimeoutError(GimpMCPError):
    """A command to GIMP timed out."""

    def __init__(self, message: str, timeout_seconds: float | None = None):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class GimpValidationError(GimpMCPError):
    """Input validation failed before sending to GIMP."""
