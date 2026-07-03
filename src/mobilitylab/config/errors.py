"""Configuration-layer exceptions."""


class ConfigError(Exception):
    """Base class for configuration errors."""


class ConfigLoadError(RuntimeError, ConfigError):
    """Raised when a user configuration file cannot be loaded."""


class ConfigValidationError(ValueError, ConfigError):
    """Raised when a user configuration document is invalid."""
