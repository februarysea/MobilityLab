from __future__ import annotations


class EnvironmentError(Exception):
    """Base class for environment runtime errors."""


class EnvironmentValidationError(EnvironmentError, ValueError):
    """Raised when environment runtime data is invalid."""


class RoutingError(EnvironmentError):
    """Raised when a route request cannot be satisfied."""


class RouteNotFoundError(RoutingError):
    """Raised when no route exists for the request."""


class MovementError(EnvironmentError):
    """Raised when a movement request cannot be executed."""
