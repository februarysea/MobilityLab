"""Provider-neutral LLM service contracts and local test implementations."""

from mobilitylab.services.llm.cache import (
    CachedLLMClient,
    InMemoryLLMCache,
    JsonlLLMCache,
    LLMCache,
)
from mobilitylab.services.llm.client import LLMClient
from mobilitylab.services.llm.fake import DeterministicLLMClient
from mobilitylab.services.llm.prompt import PromptRenderer, PromptTemplate
from mobilitylab.services.llm.retry import RetryConfig, RetryingLLMClient
from mobilitylab.services.llm.types import (
    LLMCallRecord,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    TokenUsage,
)

__all__ = [
    "CachedLLMClient",
    "DeterministicLLMClient",
    "InMemoryLLMCache",
    "JsonlLLMCache",
    "LLMCache",
    "LLMCallRecord",
    "LLMClient",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "PromptRenderer",
    "PromptTemplate",
    "RetryConfig",
    "RetryingLLMClient",
    "TokenUsage",
]
