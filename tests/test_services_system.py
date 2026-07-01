from __future__ import annotations

from campussociety.environment import (
    EnvironmentBuilder,
    LocationRef,
    Route,
    RouteRequest,
    SimpleNetworkRouter,
)
from campussociety.scenario import (
    FacilitiesSpec,
    FacilitySpec,
    MobilityModeSpec,
    MobilitySupplySpec,
    NetworkLinkSpec,
    NetworkNodeSpec,
    NetworkSpec,
    PreparedScenario,
    ScenarioSpec,
)
from campussociety.services import (
    LLMServiceConfig,
    RoutingServiceConfig,
    ServiceConfig,
    build_service_bundle,
)
from campussociety.services.llm import (
    CachedLLMClient,
    DeterministicLLMClient,
    InMemoryLLMCache,
    LLMMessage,
    LLMRequest,
    PromptRenderer,
    PromptTemplate,
)
from campussociety.services.routing import CachedRoutingService


def build_services_scenario() -> PreparedScenario:
    return PreparedScenario(
        spec=ScenarioSpec(
            scenario_id="services_test",
            version="2026.06",
        ),
        network=NetworkSpec(
            nodes=(
                NetworkNodeSpec(node_id="gate"),
                NetworkNodeSpec(node_id="quad"),
                NetworkNodeSpec(node_id="classroom"),
            ),
            links=(
                NetworkLinkSpec(
                    link_id="gate-quad",
                    from_node_id="gate",
                    to_node_id="quad",
                    length_meters=1.4,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
                NetworkLinkSpec(
                    link_id="quad-classroom",
                    from_node_id="quad",
                    to_node_id="classroom",
                    length_meters=1.4,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
                NetworkLinkSpec(
                    link_id="gate-classroom",
                    from_node_id="gate",
                    to_node_id="classroom",
                    length_meters=10.0,
                    allowed_modes=("walk",),
                ),
            ),
        ),
        facilities=FacilitiesSpec(
            facilities=(
                FacilitySpec(
                    facility_id="classroom-a",
                    facility_type="classroom",
                    location_id="classroom",
                ),
            ),
        ),
        mobility_supply=MobilitySupplySpec(
            modes=(MobilityModeSpec(mode_id="walk", mode_type="active"),),
        ),
    )


def test_prompt_renderer_and_deterministic_llm_client_are_provider_neutral() -> None:
    template = PromptTemplate(
        template_id="mode_choice",
        version="v1",
        text="Agent {agent_id} chooses from {modes}.",
    )
    renderer = PromptRenderer((template,))
    message = renderer.render("mode_choice", {"agent_id": "student-1"})
    request = LLMRequest(
        model="deterministic",
        prompt_version=template.prompt_version,
        messages=(message,),
    )

    response = DeterministicLLMClient(default_content='{"decision":"wait"}').complete(
        request
    )

    assert message.content == "Agent student-1 chooses from {modes}."
    assert response.model == "deterministic"
    assert response.content == '{"decision":"wait"}'
    assert response.raw_response["provider"] == "deterministic"


def test_cached_llm_client_returns_cached_response() -> None:
    request = LLMRequest(
        model="deterministic",
        prompt_version="test:v1",
        messages=(LLMMessage(role="user", content="hello"),),
    )
    cache = InMemoryLLMCache()
    client = CachedLLMClient(
        DeterministicLLMClient(default_content="first"),
        cache,
    )

    first = client.complete(request)
    second = client.complete(request)

    assert first.cached is False
    assert second.cached is True
    assert second.content == "first"
    assert cache.size == 1


def test_cached_routing_service_wraps_environment_routing_contract() -> None:
    environment = EnvironmentBuilder().build(build_services_scenario())
    cached_router = CachedRoutingService(SimpleNetworkRouter())
    request = RouteRequest(
        origin=LocationRef.node("gate"),
        destination=LocationRef.facility("classroom-a"),
        mode="walk",
        departure_time=0,
    )

    first = cached_router.route(request, environment.world)
    second = cached_router.route(request, environment.world)
    environment.world.close_link("quad-classroom")
    rerouted = cached_router.route(request, environment.world)

    assert first is second
    assert isinstance(rerouted, Route)
    assert [leg.link_id for leg in rerouted.legs] == ["gate-classroom"]
    assert cached_router.size == 2


def test_service_bundle_wires_mvp_llm_and_routing_services() -> None:
    router = SimpleNetworkRouter()
    bundle = build_service_bundle(
        ServiceConfig(
            llm=LLMServiceConfig(max_retries=2),
            routing=RoutingServiceConfig(enable_cache=True),
        ),
        routing_service=router,
    )

    assert bundle.llm_client is not None
    assert isinstance(bundle.require_routing_service(), CachedRoutingService)
