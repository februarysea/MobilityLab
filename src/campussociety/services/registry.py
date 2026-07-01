from __future__ import annotations

from dataclasses import dataclass

from campussociety.environment.routing import RoutingService
from campussociety.services.config import ServiceConfig
from campussociety.services.llm import (
    CachedLLMClient,
    DeterministicLLMClient,
    InMemoryLLMCache,
    JsonlLLMCache,
    LLMClient,
    RetryConfig,
    RetryingLLMClient,
)
from campussociety.services.routing import CachedRoutingService


@dataclass(frozen=True, slots=True)
class ServiceBundle:
    """Thin container for optional replaceable backend services."""

    llm_client: LLMClient | None = None
    routing_service: RoutingService | None = None

    def require_llm_client(self) -> LLMClient:
        if self.llm_client is None:
            msg = "LLM client is not configured"
            raise RuntimeError(msg)
        return self.llm_client

    def require_routing_service(self) -> RoutingService:
        if self.routing_service is None:
            msg = "routing service is not configured"
            raise RuntimeError(msg)
        return self.routing_service


class ServiceRegistry:
    """Explicit service registry scoped to one assembled run or application."""

    def __init__(self, bundle: ServiceBundle | None = None) -> None:
        self._bundle = bundle or ServiceBundle()

    @property
    def bundle(self) -> ServiceBundle:
        return self._bundle

    @property
    def llm_client(self) -> LLMClient | None:
        return self._bundle.llm_client

    @property
    def routing_service(self) -> RoutingService | None:
        return self._bundle.routing_service


def build_service_bundle(
    config: ServiceConfig | None = None,
    *,
    llm_client: LLMClient | None = None,
    routing_service: RoutingService | None = None,
) -> ServiceBundle:
    """Build a thin service bundle from config and explicit overrides."""

    resolved = config or ServiceConfig()
    resolved_llm = llm_client
    if resolved.llm is not None:
        if resolved_llm is None:
            if resolved.llm.provider != "deterministic":
                msg = (
                    "only the deterministic LLM provider is available in the "
                    "services MVP"
                )
                raise ValueError(msg)
            resolved_llm = DeterministicLLMClient()
        resolved_llm = RetryingLLMClient(
            resolved_llm,
            RetryConfig(max_attempts=resolved.llm.max_retries),
        )
        cache = (
            JsonlLLMCache(resolved.llm.cache_path)
            if resolved.llm.cache_path is not None
            else InMemoryLLMCache()
        )
        resolved_llm = CachedLLMClient(resolved_llm, cache)

    resolved_routing = routing_service
    if resolved_routing is not None and resolved.routing.enable_cache:
        resolved_routing = CachedRoutingService(
            resolved_routing,
            include_world_state=resolved.routing.include_world_state_in_cache_key,
        )

    return ServiceBundle(
        llm_client=resolved_llm,
        routing_service=resolved_routing,
    )
