"""Experimental parameters, NOT vendor benchmarks, prices or capability facts."""
from .model import Behavior, Capability, ModelProfile, ReasoningDepth


PROFILES = {
    "luna": ModelProfile(id="luna", label="Luna",
        capability=Capability(reasoning=48, constraint_tracking=48, evidence_handling=45),
        behavior=Behavior(exploration=.2, dependency_expansion=.2, constraint_discovery=.2,
                          uncertainty_discovery=.2, alternative_generation=.2, compression=.2),
        relative_inference_cost=1),
    "terra": ModelProfile(id="terra", label="Terra",
        capability=Capability(reasoning=60, constraint_tracking=62, evidence_handling=58),
        behavior=Behavior(exploration=.35, dependency_expansion=.35, constraint_discovery=.35,
                          uncertainty_discovery=.35, alternative_generation=.35, compression=.25),
        relative_inference_cost=1.5),
    "sol": ModelProfile(id="sol", label="Sol",
        capability=Capability(reasoning=72, constraint_tracking=74, evidence_handling=70),
        behavior=Behavior(exploration=.5, dependency_expansion=.5, constraint_discovery=.5,
                          uncertainty_discovery=.5, alternative_generation=.5, compression=.3),
        relative_inference_cost=2),
    "astra": ModelProfile(id="astra", label="Astra",
        capability=Capability(reasoning=90, constraint_tracking=92, evidence_handling=90),
        behavior=Behavior(exploration=.8, dependency_expansion=.8, constraint_discovery=.8,
                          uncertainty_discovery=.8, alternative_generation=.8, compression=.4),
        relative_inference_cost=4),
}
DEPTHS = {
    "light": ReasoningDepth(id="light", capability_modifier=-8, exploration_modifier=.6, cost_modifier=.7),
    "standard": ReasoningDepth(id="standard", capability_modifier=0, exploration_modifier=1, cost_modifier=1),
    "high": ReasoningDepth(id="high", capability_modifier=8, exploration_modifier=1.6, cost_modifier=1.6),
}
