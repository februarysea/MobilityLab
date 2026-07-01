from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LLMServiceConfig:
    """Configuration for provider-neutral LLM service wiring."""

    provider: str = "deterministic"
    model: str = "deterministic"
    prompt_version: str = "default"
    cache_path: Path | None = None
    max_retries: int = 1
    timeout_seconds: float = 30.0
    concurrency: int = 1

    def __post_init__(self) -> None:
        _require_non_empty(self.provider, "provider")
        _require_non_empty(self.model, "model")
        _require_non_empty(self.prompt_version, "prompt_version")
        if self.max_retries < 1:
            msg = "max_retries must be at least 1"
            raise ValueError(msg)
        if self.timeout_seconds <= 0:
            msg = "timeout_seconds must be positive"
            raise ValueError(msg)
        if self.concurrency < 1:
            msg = "concurrency must be at least 1"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class RoutingServiceConfig:
    """Configuration for optional routing service wrappers."""

    enable_cache: bool = False
    include_world_state_in_cache_key: bool = True


@dataclass(frozen=True, slots=True)
class ServiceConfig:
    """Top-level MVP service wiring configuration."""

    llm: LLMServiceConfig | None = None
    routing: RoutingServiceConfig = field(default_factory=RoutingServiceConfig)


def _require_non_empty(value: str, field_name: str) -> None:
    if value == "":
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)
