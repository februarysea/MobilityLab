from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from campussociety.services.llm.client import LLMClient
from campussociety.services.llm.types import LLMRequest, LLMResponse, TokenUsage


@dataclass(frozen=True, slots=True)
class DeterministicLLMClient(LLMClient):
    """Deterministic test client for cognition workflows."""

    default_content: str = "{}"
    responses: Mapping[str, str | LLMResponse] = field(default_factory=dict)

    def complete(self, request: LLMRequest) -> LLMResponse:
        configured = self.responses.get(request.cache_key, self.default_content)
        if isinstance(configured, LLMResponse):
            return configured.with_cached(False)
        return LLMResponse(
            content=configured,
            model=request.model,
            usage=TokenUsage(
                prompt_tokens=sum(
                    len(message.content.split()) for message in request.messages
                ),
                completion_tokens=len(configured.split()),
            ),
            raw_response={
                "provider": "deterministic",
                "prompt_version": request.prompt_version,
            },
        )
