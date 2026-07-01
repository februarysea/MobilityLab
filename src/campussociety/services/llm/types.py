from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field

from campussociety.core.entities import JsonValue, State, copy_state


def _copy_mapping(values: Mapping[str, JsonValue]) -> State:
    return copy_state(values)


def _require_non_empty(value: str, field_name: str) -> None:
    if value == "":
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)


def _require_non_negative(value: int, field_name: str) -> None:
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class LLMMessage:
    """One provider-agnostic chat message."""

    role: str
    content: str
    name: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.role, "role")
        object.__setattr__(self, "metadata", _copy_mapping(self.metadata))

    def to_record(self) -> State:
        return {
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "metadata": _copy_mapping(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class TokenUsage:
    """Provider-neutral token usage summary."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int | None = None

    def __post_init__(self) -> None:
        _require_non_negative(self.prompt_tokens, "prompt_tokens")
        _require_non_negative(self.completion_tokens, "completion_tokens")
        total = self.total_tokens
        if total is None:
            total = self.prompt_tokens + self.completion_tokens
        _require_non_negative(total, "total_tokens")
        object.__setattr__(self, "total_tokens", total)

    def to_record(self) -> State:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """Provider-agnostic LLM request used by cognition services."""

    model: str
    messages: tuple[LLMMessage, ...]
    prompt_version: str
    request_id: str | None = None
    response_schema: Mapping[str, JsonValue] | None = None
    generation_params: Mapping[str, JsonValue] = field(default_factory=dict)
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.model, "model")
        _require_non_empty(self.prompt_version, "prompt_version")
        object.__setattr__(self, "messages", tuple(self.messages))
        object.__setattr__(
            self,
            "response_schema",
            (
                None
                if self.response_schema is None
                else _copy_mapping(self.response_schema)
            ),
        )
        object.__setattr__(
            self,
            "generation_params",
            _copy_mapping(self.generation_params),
        )
        object.__setattr__(self, "metadata", _copy_mapping(self.metadata))

    @property
    def cache_key(self) -> str:
        encoded = json.dumps(
            self.to_cache_record(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def to_cache_record(self) -> State:
        return {
            "model": self.model,
            "prompt_version": self.prompt_version,
            "messages": [message.to_record() for message in self.messages],
            "response_schema": self._response_schema_record(),
            "generation_params": _copy_mapping(self.generation_params),
        }

    def to_record(self) -> State:
        record = self.to_cache_record()
        record["request_id"] = self.request_id
        record["metadata"] = _copy_mapping(self.metadata)
        return record

    def _response_schema_record(self) -> State | None:
        if self.response_schema is None:
            return None
        return _copy_mapping(self.response_schema)


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Provider-agnostic LLM response."""

    content: str
    model: str
    structured_output: Mapping[str, JsonValue] = field(default_factory=dict)
    usage: TokenUsage = field(default_factory=TokenUsage)
    raw_response: Mapping[str, JsonValue] = field(default_factory=dict)
    cached: bool = False

    def __post_init__(self) -> None:
        _require_non_empty(self.model, "model")
        object.__setattr__(
            self,
            "structured_output",
            _copy_mapping(self.structured_output),
        )
        object.__setattr__(self, "raw_response", _copy_mapping(self.raw_response))

    def with_cached(self, cached: bool = True) -> LLMResponse:
        return LLMResponse(
            content=self.content,
            model=self.model,
            structured_output=self.structured_output,
            usage=self.usage,
            raw_response=self.raw_response,
            cached=cached,
        )

    def to_record(self) -> State:
        return {
            "content": self.content,
            "model": self.model,
            "structured_output": _copy_mapping(self.structured_output),
            "usage": self.usage.to_record(),
            "raw_response": _copy_mapping(self.raw_response),
            "cached": self.cached,
        }


@dataclass(frozen=True, slots=True)
class LLMCallRecord:
    """Structured audit record for one service-layer LLM call."""

    request: LLMRequest
    response: LLMResponse | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.response is not None and self.error is None

    def to_record(self) -> State:
        return {
            "request": self.request.to_record(),
            "response": None if self.response is None else self.response.to_record(),
            "error": self.error,
            "succeeded": self.succeeded,
        }
