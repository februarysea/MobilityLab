"""Agent-layer errors."""


class AgentError(Exception):
    """Base class for agent-layer failures."""


class AgentValidationError(ValueError, AgentError):
    """Raised when agent declarations or runtime state are invalid."""


class AgentDecisionError(RuntimeError, AgentError):
    """Raised when an agent decision cannot be executed."""
