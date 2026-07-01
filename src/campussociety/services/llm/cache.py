from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, cast, runtime_checkable

from campussociety.core.entities import JsonValue, State
from campussociety.services.llm.client import LLMClient
from campussociety.services.llm.types import LLMRequest, LLMResponse, TokenUsage


@runtime_checkable
class LLMCache(Protocol):
    """Cache contract keyed by normalized LLM requests."""

    def get(self, request: LLMRequest) -> LLMResponse | None: ...

    def set(self, request: LLMRequest, response: LLMResponse) -> None: ...


class InMemoryLLMCache:
    """Deterministic in-process LLM response cache."""

    def __init__(self) -> None:
        self._responses: dict[str, LLMResponse] = {}

    def get(self, request: LLMRequest) -> LLMResponse | None:
        response = self._responses.get(request.cache_key)
        return None if response is None else response.with_cached()

    def set(self, request: LLMRequest, response: LLMResponse) -> None:
        self._responses[request.cache_key] = response.with_cached(False)

    def clear(self) -> None:
        self._responses.clear()

    @property
    def size(self) -> int:
        return len(self._responses)


class JsonlLLMCache:
    """Append-only JSONL cache for replayable LLM responses."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._memory = InMemoryLLMCache()
        self._load_existing()

    def get(self, request: LLMRequest) -> LLMResponse | None:
        return self._memory.get(request)

    def set(self, request: LLMRequest, response: LLMResponse) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._memory.set(request, response)
        record: State = {
            "cache_key": request.cache_key,
            "request": request.to_record(),
            "response": response.with_cached(False).to_record(),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")

    def _load_existing(self) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip() == "":
                continue
            raw = cast(State, json.loads(line))
            request = _request_from_record(cast(State, raw["request"]))
            response = _response_from_record(cast(State, raw["response"]))
            self._memory.set(request, response)


class CachedLLMClient:
    """LLM client wrapper that checks a cache before calling the backend."""

    def __init__(self, backend: LLMClient, cache: LLMCache) -> None:
        self._backend = backend
        self._cache = cache

    def complete(self, request: LLMRequest) -> LLMResponse:
        cached = self._cache.get(request)
        if cached is not None:
            return cached
        response = self._backend.complete(request)
        self._cache.set(request, response)
        return response


def _request_from_record(record: State) -> LLMRequest:
    from campussociety.services.llm.types import LLMMessage

    return LLMRequest(
        model=str(record["model"]),
        prompt_version=str(record["prompt_version"]),
        request_id=(
            None if record.get("request_id") is None else str(record["request_id"])
        ),
        messages=tuple(
            LLMMessage(
                role=str(message["role"]),
                content=str(message["content"]),
                name=None if message.get("name") is None else str(message["name"]),
                metadata=cast(State, message.get("metadata", {})),
            )
            for message in cast(list[State], record["messages"])
        ),
        response_schema=cast(State | None, record.get("response_schema")),
        generation_params=cast(State, record.get("generation_params", {})),
        metadata=cast(State, record.get("metadata", {})),
    )


def _response_from_record(record: State) -> LLMResponse:
    usage = cast(State, record.get("usage", {}))
    return LLMResponse(
        content=str(record["content"]),
        model=str(record["model"]),
        structured_output=cast(State, record.get("structured_output", {})),
        usage=TokenUsage(
            prompt_tokens=_int_from_json(usage.get("prompt_tokens", 0)),
            completion_tokens=_int_from_json(usage.get("completion_tokens", 0)),
            total_tokens=(
                None
                if usage.get("total_tokens") is None
                else _int_from_json(usage["total_tokens"])
            ),
        ),
        raw_response=cast(State, record.get("raw_response", {})),
        cached=bool(record.get("cached", False)),
    )


def _int_from_json(value: JsonValue) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int | float | str):
        return int(value)
    msg = f"expected numeric JSON value, got {type(value).__name__}"
    raise ValueError(msg)
