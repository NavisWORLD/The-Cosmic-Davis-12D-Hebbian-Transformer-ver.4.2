
import asyncio
import time
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set API Key early for all modules
os.environ["IBM_QUANTUM_TOKEN"] = "gQZcrqfRzKL5rzF86L-LIx3afGsz1e1ULBquzyS4BoSm"

from Cosmos.web.server import get_cosmos_swarm
from Cosmos.web.cosmosynapse.engine.cosmos_swarm_orchestrator import SwarmResponse
from Cosmos.core.quantum_bridge import get_quantum_bridge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QUANTUM_BENCHMARK")

BENCHMARK_PROMPTS = [
    "Predict the next major shift in the global financial market using quantum chaos theory.",
    "Solve the P vs NP problem using 12D Hebbian logic.",
    "Design a propulsion system for interstellar travel based on dark matter Lorenz attractors.",
    "Pick 6 lottery numbers for the next drawing and justify them with Shannon entropy.",
    "Explain the core connection between human consciousness and quantum entanglement in 12D space."
]

async def get_available_models():
    import ollama
    try:
        models_info = ollama.list()
        return [m['name'] for m in models_info['models']]
    except:
        return ["llama3.2:3b"]

async def run_benchmark():
    available_models = await get_available_models()
    print(f"[SYSTEM] Available models: {available_models}")
    
    MODELS_TO_TEST = [m for m in available_models if any(x in m.lower() for x in ["llama", "ds", "phi", "gemma", "deepseek", "qwen", "mistral"])]
    if not MODELS_TO_TEST:
        MODELS_TO_TEST = available_models[:3] # Fallback to first 3 if none match
    print("="*60)
    print("   QUANTUM MULTI-MODEL COMPETITION BENCHMARK")
    print("="*60)
    
    orchestrator = get_cosmos_swarm()
    
    # [NEW] Initialize the 12D Engine
    print("[SYSTEM] Initializing Cosmo's 12D Brain...")
    await orchestrator.initialize()
    
    if hasattr(orchestrator, 'cosmos_backend') and orchestrator.cosmos_backend and orchestrator.cosmos_backend.is_loaded:
        print(f"[SWARM] Cosmo's 12D Brain ACTIVATED.")
    else:
        print("[!] Warning: 12D Brain not loaded. Sub-optimal synthesis might occur.")

    bridge = get_quantum_bridge("gQZcrqfRzKL5rzF86L-LIx3afGsz1e1ULBquzyS4BoSm")
    bridge.connect()
    
    # Ensure bridge is connected
    if not bridge.connected:
        print("[!] Warning: Quantum Bridge not connected to hardware. Working in Simulation Mode.")
    else:
        print(f"[QUANTUM] Connected to Hardware: {bridge.backend.name if bridge.backend else 'Unknown'}")
    
    results = []
    
    # Mock user physics for the benchmark (High synchrony)
    user_physics = {
        "cst_physics": {
            "geometric_phase_rad": 0.785, # pi/4
            "entanglement_score": 0.9
        },
        "bio_signatures": {
            "emotion": "CURIOSITY",
            "intensity": 0.8
        }
    }

    for prompt_idx, prompt in enumerate(BENCHMARK_PROMPTS):
        print(f"\n[PROMPT {prompt_idx+1}] {prompt}")
        prompt_results = {
            "prompt": prompt,
            "models": {}
        }
        
        # Trigger an entropy refill with current physics before testing
        # This ensures the quantum state is fresh for this prompt
        bridge.get_entropy(user_physics)
        
        for model in MODELS_TO_TEST:
            print(f"  > Querying {model}...", end="", flush=True)
            start_time = time.time()
            
            try:
                # We use query_swarm with target_models if available, 
                # or just call _query_ollama_text directly via orchestrator for simplicity in benchmark
                
                # Check for quantum entropy
                q_entropy = bridge.get_entropy(user_physics)
                
                # We'll use the orchestrator's internal helper to get a direct response
                # This bypasses the full synthesis for individual model benchmarking
                content = await orchestrator._query_ollama_text(
                    model_name=model, 
                    prompt=prompt, 
                    quantum_entropy=q_entropy
                )
                
                duration = time.time() - start_time
                print(f" Done ({duration:.2f}s)")
                
                # Simple coherence estimate (length + keyword presence)
                coherence = min(1.0, len(content) / 1000.0) 
                
                prompt_results["models"][model] = {
                    "content": content,
                    "time_seconds": duration,
                    "quantum_entropy": q_entropy,
                    "coherence": coherence
                }
                
            except Exception as e:
                print(f" Failed: {e}")
                prompt_results["models"][model] = {"error": str(e)}
        
        results.append(prompt_results)
        
    # Final Synthesis (The Swarm Decision)
    print("\n[SYNTHESIZING SWARM CONSENSUS]...")
    last_prompt = BENCHMARK_PROMPTS[-1]
    last_responses = [
        SwarmResponse(
            model_name=m, 
            content=r.get('content', ''), 
            confidence=r.get('coherence', 0.1),
            time_seconds=r.get('time_seconds', 0.0),
            backend_type='ollama',
            informational_mass=0.5,
            phase_alignment=0.5,
            weight=1.0,
            error=None
        ) 
        for m, r in results[-1]["models"].items() if "error" not in r
    ]
    
    swarm_synthesis = await orchestrator.cosmos_synthesize(last_prompt, last_responses, user_physics)
    print(f"\n--- SWARM SYNTHESIS ---\n{swarm_synthesis[:500]}...\n")

    # Save Results
    output = {
        "timestamp": datetime.now().isoformat(),
        "bridge_connected": bridge.connected,
        "prompts": results,
        "final_synthesis": swarm_synthesis
    }
    
    report_path = project_root / "data" / f"quantum_benchmark_{int(time.time())}.json"
    os.makedirs(report_path.parent, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(output, f, indent=2)
        
    print(f"\n[REPORT SAVED] {report_path}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
