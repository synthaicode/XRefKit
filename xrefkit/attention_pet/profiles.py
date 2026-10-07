"""Experimental parameters, NOT vendor benchmarks, prices or capability facts."""
from .model import Behavior, CANONICAL_REASONING_LEVELS, Capability, ModelProfile, ReasoningDepth


PROFILES = {
    "luna": ModelProfile(id="luna", label="Luna",
        capability=Capability(reasoning=48, constraint_tracking=48, evidence_handling=45),
        behavior=Behavior(exploration=.2, dependency_expansion=.2, constraint_discovery=.2,
                          uncertainty_discovery=.2, alternative_generation=.2, compression=.2),
        relative_inference_cost=1, supported_reasoning=("low", "medium", "high", "xhigh")),
    "terra": ModelProfile(id="terra", label="Terra",
        capability=Capability(reasoning=60, constraint_tracking=62, evidence_handling=58),
        behavior=Behavior(exploration=.35, dependency_expansion=.35, constraint_discovery=.35,
                          uncertainty_discovery=.35, alternative_generation=.35, compression=.25),
        relative_inference_cost=1.5, supported_reasoning=("low", "medium", "high")),
    "sol": ModelProfile(id="sol", label="Sol",
        capability=Capability(reasoning=72, constraint_tracking=74, evidence_handling=70),
        behavior=Behavior(exploration=.5, dependency_expansion=.5, constraint_discovery=.5,
                          uncertainty_discovery=.5, alternative_generation=.5, compression=.3),
        relative_inference_cost=2, supported_reasoning=("low", "medium", "high", "xhigh", "max")),
    "astra": ModelProfile(id="astra", label="Astra",
        capability=Capability(reasoning=90, constraint_tracking=92, evidence_handling=90),
        behavior=Behavior(exploration=.8, dependency_expansion=.8, constraint_discovery=.8,
                          uncertainty_discovery=.8, alternative_generation=.8, compression=.4),
        relative_inference_cost=4, supported_reasoning=("low", "medium", "high", "xhigh", "max")),
}
DEPTHS = {
    "light": ReasoningDepth(id="light", capability_modifier=-8, exploration_modifier=.6, cost_modifier=.7),
    "standard": ReasoningDepth(id="standard", capability_modifier=0, exploration_modifier=1, cost_modifier=1),
    "low": ReasoningDepth(id="low", capability_modifier=-8, exploration_modifier=.6, cost_modifier=.7),
    "medium": ReasoningDepth(id="medium", capability_modifier=0, exploration_modifier=1, cost_modifier=1),
    "high": ReasoningDepth(id="high", capability_modifier=8, exploration_modifier=1.6, cost_modifier=1.6),
    "xhigh": ReasoningDepth(id="xhigh", capability_modifier=15, exploration_modifier=2, cost_modifier=2.1),
    "max": ReasoningDepth(id="max", capability_modifier=20, exploration_modifier=2.4, cost_modifier=2.7),
}

# Input aliases preserve the old API while candidate enumeration uses canonical levels.
REASONING_ALIASES = {"light": "low", "standard": "medium"}
if set(DEPTHS) - set(REASONING_ALIASES) != CANONICAL_REASONING_LEVELS:
    raise ValueError("canonical reasoning levels and depth definitions differ")


def canonical_reasoning(reasoning: str) -> str:
    return REASONING_ALIASES.get(reasoning, reasoning)


def execution_profiles(profiles=None):
    """Enumerate only combinations declared by each model capability profile."""
    for profile in (PROFILES if profiles is None else profiles).values():
        for reasoning in profile.supported_reasoning:
            yield profile, DEPTHS[reasoning]
