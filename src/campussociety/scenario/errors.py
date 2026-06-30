"""Scenario-layer exceptions."""


class ScenarioError(Exception):
    """Base class for scenario errors."""


class ScenarioValidationError(ValueError, ScenarioError):
    """Raised when a scenario declaration is structurally invalid."""


class ScenarioLoadError(RuntimeError, ScenarioError):
    """Raised when a loader cannot prepare a scenario."""
