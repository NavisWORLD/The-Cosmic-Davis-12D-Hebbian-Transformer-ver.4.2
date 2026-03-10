
import logging
import time
from typing import List, Dict, Any, Optional

# Internal Imports
try:
    from .lyapunov_lock import LyapunovGatekeeper
    from .cosmos_swarm_orchestrator import CosmosSwarmOrchestrator
except ImportError:
    # Fallback for direct execution
    from lyapunov_lock import LyapunovGatekeeper
    from cosmos_swarm_orchestrator import CosmosSwarmOrchestrator

logger = logging.getLogger("COSMOS_EGO")

class CosmosEgo:
    """
    The Unity of Apperception.
    Synthesizes the final output from the Emeth Filtered thoughts.
    Integrates the Lyapunov stability check.
    """
    def __init__(self, field, orchestrator=None):
        self.field = field
        # We reuse the existing Swarm Orchestrator logic for the heavy lifting (LLM calls)
        self.orchestrator = orchestrator or CosmosSwarmOrchestrator()
        self.lock = LyapunovGatekeeper()

    async def synthesize(self, user_input: str, thoughts: List[Dict], physics: Dict, temporal_context: str) -> str:
        """
        Generate the final spoken response.
        """
        try:
            # 1. Prepare Context (The Gathering)
            subconscious_context = "\n".join([
                f"[{t.source}] (Intent: {t.intent}): {t.content}" 
                for t in thoughts
            ])
            
            # 2. Inject Temporal Anchor (Brain Surgeon's work)
            system_prompt_addition = f"\nTEMPORAL ANCHOR: {temporal_context}\n"
            
            # 3. Call the Orchestrator (The Synthesis)
            # We bypass the full orchestrator loop since we have done the pre-work
            # But relying on its existing prompt construction is safer for now
            # We inject our pre-computed thoughts into it?
            # Actually, let's just use the orchestrator as the generator
            
            # For now, simplistic integration:
            # We let the orchestrator do its thing, but we MIGHT inject our subconscious buffer
            # The original Orchestrator generates its own thoughts via 'fan_out', 
            # In Class 5, the 'fan_out' is replaced by reaading the 'subconscious_buffer'
            
            # Since modifying the Orchestrator is risky, we will conceptually link them here
            # Ideally, we refactor the Orchestrator to accept 'external_thoughts'
            
            # For this step, we will call a method on the orchestrator that takes this context
            # If that method doesn't exist, we fallback to standard generation but log the mismatch
            
            # PROVISIONAL: We just call generate_peer_response. 
            # FUTURE: Update Orchestrator to read self.field.subconscious_buffer
            
            # The signature is: generate_peer_response(prompt, system_prompt=None, history=None)
            # We map user_input -> prompt
            response = await self.orchestrator.generate_peer_response(
                prompt=user_input,
                system_prompt=system_prompt_addition, # Use our temporal anchor as system prompt
                history=[] # We might need history from Field
            )
            
            # 4. The Censor (Lyapunov)
            # The Orchestrator has an internal lock, but we apply a FINAL check here
            start_check = time.time()
            report = self.lock.validate_response(response, physics)
            
            if report.is_stable:
                 return response
            else:
                 logger.warning(f"⛔ Lyapunov Reject in Ego: {report.rejection_reason}")
                 return "... (Silence) ..."

        except Exception as e:
            logger.error(f"Ego Synthesis Error: {e}")
            return "..."
