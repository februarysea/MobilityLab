from __future__ import annotations

from typing import Protocol, runtime_checkable

from mobilitylab.services.llm.types import LLMRequest, LLMResponse


@runtime_checkable
class LLMClient(Protocol):
    """Synchronous provider-neutral LLM client contract."""

    def complete(self, request: LLMRequest) -> LLMResponse: ...
