from __future__ import annotations

from dataclasses import dataclass

from mobilitylab.services.llm.client import LLMClient
from mobilitylab.services.llm.types import LLMRequest, LLMResponse


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Retry policy for provider calls."""

    max_attempts: int = 1

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            msg = "max_attempts must be at least 1"
            raise ValueError(msg)


class RetryingLLMClient:
    """Synchronous retry wrapper for transient provider failures."""

    def __init__(self, backend: LLMClient, config: RetryConfig | None = None) -> None:
        self._backend = backend
        self._config = config or RetryConfig()

    def complete(self, request: LLMRequest) -> LLMResponse:
        last_error: Exception | None = None
        for _attempt in range(self._config.max_attempts):
            try:
                return self._backend.complete(request)
            except Exception as exc:  # noqa: BLE001 - provider adapters normalize later
                last_error = exc
        assert last_error is not None
        raise last_error
