"""
cosmos Evolution Module

Genetic optimization for self-improvement with:
- NSGA-II multi-objective optimization
- Behavioral genome encoding for swarm evolution
- LoRA adapter breeding and merging
- Hash-chain evolution logging for integrity
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
]
