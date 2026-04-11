"""
cosmos Evolution Module

Genetic optimization for self-improvement with:
- NSGA-II multi-objective optimization
- Behavioral genome encoding for swarm evolution
- LoRA adapter breeding and merging
- Hash-chain evolution logging for integrity
- Federated population evolution across P2P (AGI Cohesion)
- Quantum-enhanced evolution via IBM Quantum (AGI v1.8)
"""

from cosmos.evolution.genetic_optimizer import GeneticOptimizer
from cosmos.evolution.lora_evolver import LoRAEvolver
from cosmos.evolution.behavior_mutation import BehaviorMutator
from cosmos.evolution.fitness_tracker import FitnessTracker

__all__ = [
    "GeneticOptimizer",
    "LoRAEvolver",
    "BehaviorMutator",
    "FitnessTracker",
    "FederatedPopulationManager",
    "FederatedEvolutionConfig",
    "setup_federated_evolution",
    "QuantumEvolutionEngine",
    "get_quantum_evolution_engine",
    "quantum_evolve_agent_params",
]
