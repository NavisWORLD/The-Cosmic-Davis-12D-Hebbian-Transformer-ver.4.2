"""
COSMOS Media Generator
======================
Generates video and images using Google Gemini APIs,
with prompts enriched by the Cosmos 54D Transformer and CST Physics.

Flow:
    User Prompt → Cosmos Transformer (54D CST enrichment) → Enhanced Prompt → Gemini → Media

Image Generation: Uses Gemini's NATIVE image generation (gemini-2.0-flash-exp)
    - Works on the FREE tier
    - Returns images inline via generate_content
    - No separate Imagen API needed

Video Generation: Uses Veo (requires GCP billing)
    - veo-2.0-generate-001 (standard)
    - veo-3.1-generate-preview (best quality)
    - Falls back to clear error if billing not enabled

Prompt Enrichment: Uses Gemini via the NEW google-genai SDK
    - Falls back to Ollama if Gemini is rate-limited
    - Falls back to manual CST enrichment if both fail

Diffusion Generation:
    - Prefers a quantum-seeded diffusion backend (local diffusers or HF Inference)
    - Falls back to native 12D inverse synthesis if diffusion is unavailable
    - Gemini image generation is optional and only used when explicitly configured
"""

import asyncio
import base64
import hashlib
import io
import json
import os
import time
import uuid
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("COSMOS_MEDIA")

# φ constant
PHI = 1.618033988749895

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GEMINI SDK DETECTION (NEW google-genai ONLY)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("[MEDIA] google-genai SDK not installed. Run: pip install google-genai")

try:
    from diffusers import AutoPipelineForText2Image
    DIFFUSERS_AVAILABLE = True
except ImportError:
    AutoPipelineForText2Image = None
    DIFFUSERS_AVAILABLE = False


class CosmosMediaGenerator:
    """
    Generates media (video/image) powered by:
    1. Cosmos 54D Transformer — enriches prompts with CST physics
    2. Gemini Native Image Gen — generates images via generate_content (FREE tier)
    3. Google Veo — generates video (requires GCP billing)
    """

    # Available video models (require GCP billing)
    VIDEO_MODELS = {
        "veo-2": "veo-2.0-generate-001",
        "veo-3.1": "veo-3.1-generate-preview",
        "veo-3.1-fast": "veo-3.1-fast-generate-preview",
    }

    DIFFUSION_MODELS = {
        "flux-schnell": "black-forest-labs/FLUX.1-schnell",
        "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
    }

    IMAGE_MODEL = os.getenv("COSMOS_GEMINI_IMAGE_MODEL", "").strip() or None

    # Text model for prompt enrichment
    TEXT_MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: str = None, output_dir: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.hf_api_key = os.environ.get("HF_API_KEY") or os.environ.get("HUGGINGFACE_API_KEY")
        self.client = None
        self.available = False
        self.local_media_only = os.getenv("COSMOS_MEDIA_LOCAL_ONLY", "TRUE").upper() == "TRUE"
        self.prefer_local_math = os.getenv("COSMOS_MEDIA_PREFER_LOCAL_MATH", "TRUE").upper() == "TRUE"
        self.enable_local_diffusion = os.getenv("COSMOS_ENABLE_LOCAL_DIFFUSION", "TRUE").upper() == "TRUE"
        self.preferred_diffusion_model = os.getenv("COSMOS_DIFFUSION_MODEL", "sdxl").strip() or "sdxl"
        self._hf_provider = None
        self._local_diffusion_pipeline = None
        self._local_diffusion_model_id = None
        self.workspace_root = Path(__file__).resolve().parents[2]
        self.quantum_debug_log = self.workspace_root / "quantum_debug.log"
        self.last_generation = {}

        # Output directory for generated media
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            # Default: project's static/generated/ directory
            self.output_dir = Path(__file__).parent.parent / "web" / "static" / "generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize
        self._initialize()

    def _record_generation(
        self,
        *,
        media_type: str,
        prompt: str,
        enhanced_prompt: str,
        model: str,
        file_path: str,
        file_url: str,
        manifest_path: str,
        quantum_state: dict,
        backend: Optional[str] = None,
    ) -> dict:
        """Persist the last completed generation for status surfaces."""
        record = {
            "media_type": media_type,
            "prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "model": model,
            "backend": backend or model,
            "file_path": file_path,
            "file_url": file_url,
            "manifest_path": manifest_path,
            "timestamp": time.time(),
            "quantum_backend": quantum_state.get("backend"),
            "quantum_refill_phase": quantum_state.get("refill_phase"),
            "quantum_signature": quantum_state.get("entanglement_signature"),
            "generation_seed": quantum_state.get("generation_seed"),
        }
        self.last_generation = record
        return record

    def _initialize(self):
        """Initialize the Gemini client using the NEW google-genai SDK."""
        if not self.api_key:
            logger.warning("[MEDIA] No Gemini API key found. Media generation disabled.")
            return

        if GENAI_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.available = True
                logger.info("[MEDIA] Gemini Media Generator initialized (google-genai SDK)")
            except Exception as e:
                logger.error(f"[MEDIA] Failed to initialize google-genai client: {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CST PROMPT ENRICHMENT (The Cosmos Transformer)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_cst_context(self) -> dict:
        """
        Read the current CST state from the SynapticField.
        Returns emotional context, dark matter dynamics, and φ-aesthetic parameters.
        """
        cst = {
            "emotional_state": "NEUTRAL",
            "dark_matter_w": 0.1,
            "geometric_phase_rad": 0.0,
            "informational_mass": 5.0,
            "emeth_weights": {"percussion": 0.33, "strings": 0.33, "brass": 0.34},
            "phi_composition": PHI,
            "quantum_entropy": 0.5,
        }

        # Try to read live state from the CosmoSynapse engine
        try:
            from cosmosynapse.engine.synaptic_field import get_field
            field = get_field()
            if field:
                physics = field.user_physics or {}
                cst_physics = physics.get("cst_physics", {})

                cst["emotional_state"] = cst_physics.get("cst_state", "NEUTRAL")
                cst["geometric_phase_rad"] = cst_physics.get("geometric_phase_rad", 0.0)
                cst["informational_mass"] = physics.get("derived_state", {}).get("informational_mass", 5.0)

                # Dark matter
                dm = field.dark_matter_state if hasattr(field, "dark_matter_state") else {}
                cst["dark_matter_w"] = dm.get("w", 0.1)

                # Quantum entropy
                from Cosmos.core.quantum_bridge import get_quantum_bridge
                qb = get_quantum_bridge()
                if qb:
                    cst["quantum_entropy"] = qb.get_entropy(physics)
        except Exception as e:
            logger.debug(f"[MEDIA] CST context read failed (using defaults): {e}")

        return cst

    def _tail_quantum_debug_log(self, max_lines: int = 12) -> list[str]:
        """Read the most recent quantum bridge log lines if available."""
        try:
            if not self.quantum_debug_log.exists():
                return []
            with open(self.quantum_debug_log, "r", encoding="utf-8", errors="ignore") as handle:
                lines = [line.strip() for line in handle.readlines() if line.strip()]
            return lines[-max_lines:]
        except Exception as e:
            logger.debug(f"[MEDIA] Quantum debug tail unavailable: {e}")
            return []

    def _build_quantum_media_state(self, cst: Optional[dict] = None) -> dict:
        """
        Build a shared quantum-conditioned state for prompting and native synthesis.

        This bridges live CST state, quantum bridge status, and the recent debug log
        into a single reusable payload for both image and video generation paths.
        """
        cst = cst or self.get_cst_context()
        debug_tail = self._tail_quantum_debug_log()
        backend_hint = "simulation"
        recent_connect = False
        for line in reversed(debug_tail):
            if "Backend:" in line:
                backend_hint = line.split("Backend:", 1)[1].strip()
                recent_connect = "Success" in line
                break

        state = {
            "backend": backend_hint,
            "connected": recent_connect,
            "entropy": float(cst.get("quantum_entropy", 0.5)),
            "life_force": 0.0,
            "refill_phase": "idle",
            "job_metadata": {},
            "phase_bias": float(cst.get("geometric_phase_rad", 0.0)),
            "temporal_cadence": 0.55,
            "fractal_gain": 0.35,
            "palette_shift": 0.5,
            "entanglement_signature": "debug-tail-unavailable",
            "debug_tail": debug_tail,
        }

        try:
            from Cosmos.core.quantum_bridge import get_quantum_bridge

            bridge = get_quantum_bridge()
            if bridge:
                backend = getattr(getattr(bridge, "backend", None), "name", None)
                state["backend"] = backend or state["backend"]
                state["connected"] = bool(getattr(bridge, "connected", state["connected"]))
                state["life_force"] = float(getattr(bridge, "last_life_force_yield", 0.0) or 0.0)
                state["refill_phase"] = str(getattr(bridge, "last_refill_phase", "idle") or "idle")
                state["job_metadata"] = dict(getattr(bridge, "current_job_metadata", {}) or {})

                signature = getattr(bridge, "last_quantum_signature", {}) or {}
                if signature:
                    state["entanglement_signature"] = json.dumps(signature, sort_keys=True)[:220]
                elif debug_tail:
                    state["entanglement_signature"] = " | ".join(debug_tail[-3:])[:220]
        except Exception as e:
            logger.debug(f"[MEDIA] Quantum bridge state unavailable: {e}")
            if debug_tail:
                state["entanglement_signature"] = " | ".join(debug_tail[-3:])[:220]

        entropy = max(0.0, min(1.0, state["entropy"]))
        phase = abs(float(cst.get("geometric_phase_rad", 0.0)))
        dark_matter = abs(float(cst.get("dark_matter_w", 0.0)))
        state["temporal_cadence"] = round(min(1.0, 0.25 + entropy * 0.45 + dark_matter * 0.05), 4)
        state["fractal_gain"] = round(min(1.0, 0.2 + dark_matter * 0.12 + entropy * 0.4), 4)
        state["palette_shift"] = round(min(1.0, 0.18 + entropy * 0.5 + (phase % PHI) / PHI * 0.25), 4)
        state["phase_bias"] = round(float(cst.get("geometric_phase_rad", 0.0)) + ((entropy - 0.5) * PHI), 4)

        return state

    def _compose_quantum_prompt(self, prompt: str, media_type: str, quantum_state: dict) -> str:
        """Inject quantum-conditioned creative controls into the generation prompt."""
        backend = quantum_state.get("backend", "simulation")
        signature = quantum_state.get("entanglement_signature", "n/a")
        cadence = quantum_state.get("temporal_cadence", 0.55)
        fractal_gain = quantum_state.get("fractal_gain", 0.35)
        palette_shift = quantum_state.get("palette_shift", 0.5)
        phase_bias = quantum_state.get("phase_bias", 0.0)

        motion_clause = (
            f"Motion cadence {cadence:.2f}, temporal phase drift {phase_bias:.2f}, "
            f"fractal gain {fractal_gain:.2f}."
            if media_type == "video"
            else f"Composition phase bias {phase_bias:.2f}, fractal gain {fractal_gain:.2f}."
        )

        return (
            f"{prompt}\n\n"
            f"[QUANTUM-ENTANGLED {media_type.upper()} DIRECTIVES]\n"
            f"Backend: {backend} | Entropy: {quantum_state.get('entropy', 0.5):.4f} | "
            f"Palette Shift: {palette_shift:.2f}\n"
            f"{motion_clause}\n"
            f"Entanglement Signature: {signature}"
        )

    def _build_entangled_image_state(self, prompt: str, cst: dict, quantum_state: dict) -> list[float]:
        """Map prompt + CST + quantum bridge state into a stable 12D synthesis vector."""
        digest = hashlib.sha256(prompt.encode("utf-8")).digest()
        jitter = lambda idx: ((digest[idx] / 255.0) - 0.5)
        entropy = float(quantum_state.get("entropy", cst.get("quantum_entropy", 0.5)))
        mass = float(cst.get("informational_mass", 5.0))
        phase = float(cst.get("geometric_phase_rad", 0.0))
        chaos = float(cst.get("dark_matter_w", 0.1))
        emeth = cst.get("emeth_weights", {})

        state_12d = [0.0] * 12
        state_12d[0] = max(0.05, (mass / 10.0) + jitter(0) * 0.08)
        state_12d[1] = max(0.05, (mass / 5.0) + jitter(1) * 0.12)
        state_12d[2] = phase + quantum_state.get("phase_bias", 0.0) * 0.25
        state_12d[3] = chaos + jitter(2) * quantum_state.get("fractal_gain", 0.35)
        state_12d[4] = entropy * PHI
        state_12d[5] = quantum_state.get("palette_shift", 0.5)
        state_12d[6] = quantum_state.get("temporal_cadence", 0.55)
        state_12d[7] = float(emeth.get("strings", 0.33)) + jitter(3) * 0.1
        state_12d[8] = entropy
        state_12d[9] = float(emeth.get("percussion", 0.33)) + jitter(4) * 0.08
        state_12d[10] = max(0.1, entropy * PHI + quantum_state.get("palette_shift", 0.5) + jitter(5) * 0.2)
        state_12d[11] = float(emeth.get("brass", 0.34)) + jitter(6) * 0.1
        return state_12d

    def _build_entangled_video_state(self, prompt: str, cst: dict, quantum_state: dict) -> list[float]:
        """Expand the quantum-conditioned image state into a 54D temporal synthesis state."""
        digest = hashlib.sha256(f"video::{prompt}".encode("utf-8")).digest()
        state_54d = [0.0] * 54
        base_12d = self._build_entangled_image_state(prompt, cst, quantum_state)
        for idx, value in enumerate(base_12d):
            state_54d[idx] = value

        cadence = float(quantum_state.get("temporal_cadence", 0.55))
        fractal_gain = float(quantum_state.get("fractal_gain", 0.35))
        palette_shift = float(quantum_state.get("palette_shift", 0.5))
        emeth = cst.get("emeth_weights", {})

        for idx in range(18):
            source = digest[idx % len(digest)] / 255.0
            jitter = (source - 0.5) * 2.0
            state_54d[36 + idx] = (
                jitter * (0.35 + fractal_gain)
                + cadence * 0.6
                + palette_shift * 0.25
            )

        state_54d[36] += float(emeth.get("percussion", 0.33)) * 2.0
        state_54d[37] += float(emeth.get("strings", 0.33)) * 2.0
        state_54d[38] += float(emeth.get("brass", 0.34)) * 2.0
        return state_54d

    def _write_generation_manifest(
        self,
        media_path: Path,
        media_type: str,
        original_prompt: str,
        enhanced_prompt: str,
        model: str,
        cst: dict,
        quantum_state: dict,
        backend: Optional[str] = None,
    ) -> str:
        """Persist a sidecar manifest describing the quantum-conditioned generation state."""
        manifest_path = Path(f"{media_path}.json")
        manifest = {
            "media_type": media_type,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "original_prompt": original_prompt,
            "enhanced_prompt": enhanced_prompt,
            "model": model,
            "backend": backend or model,
            "cst": cst,
            "quantum_state": {
                "backend": quantum_state.get("backend"),
                "connected": quantum_state.get("connected"),
                "entropy": quantum_state.get("entropy"),
                "life_force": quantum_state.get("life_force"),
                "refill_phase": quantum_state.get("refill_phase"),
                "phase_bias": quantum_state.get("phase_bias"),
                "temporal_cadence": quantum_state.get("temporal_cadence"),
                "fractal_gain": quantum_state.get("fractal_gain"),
                "palette_shift": quantum_state.get("palette_shift"),
                "entanglement_signature": quantum_state.get("entanglement_signature"),
                "generation_seed": quantum_state.get("generation_seed"),
                "job_metadata": quantum_state.get("job_metadata"),
                "debug_tail": quantum_state.get("debug_tail"),
            },
        }
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
        return str(manifest_path)

    async def enhance_prompt(self, raw_prompt: str, media_type: str = "video") -> str:
        """
        Use the Cosmos Transformer (via Gemini text) to enrich the user's prompt
        with CST-aware cinematic/visual directions.

        Uses the NEW google-genai SDK. Falls back to Ollama, then manual enrichment.
        """
        cst = self.get_cst_context()
        quantum_state = self._build_quantum_media_state(cst)

        if self.local_media_only:
            logger.info(f"[MEDIA] Local-native mode active. Skipping remote prompt enrichment for {media_type}.")
            return raw_prompt.strip()

        # Map emotional state to visual style
        emotion_styles = {
            "JOY": "warm golden lighting, vibrant colors, dynamic movement",
            "SADNESS": "blue-tinted atmosphere, slow motion, rain or mist",
            "ANGER": "red and orange tones, sharp cuts, intense close-ups",
            "FEAR": "dark shadows, flickering light, tight framing",
            "SURPRISE": "bright flash, wide angle, rapid zoom",
            "TRUST": "soft natural light, earth tones, steady camera",
            "ANTICIPATION": "building tension, crescendo movement, dawn breaking",
            "NEUTRAL": "balanced composition, natural colors, cinematic wide shots",
            "CALM": "serene atmosphere, gentle movement, pastel tones",
            "CALIBRATING": "digital glitch aesthetic, circuit patterns, neon glow",
        }
        emotion_style = emotion_styles.get(cst["emotional_state"], emotion_styles["NEUTRAL"])

        # Map dark matter chaos to visual turbulence
        chaos_level = min(1.0, abs(cst["dark_matter_w"]) / 10.0)
        if chaos_level > 0.7:
            chaos_visual = "chaotic swirling particles, fractals, intense energy"
        elif chaos_level > 0.3:
            chaos_visual = "dynamic flowing patterns, moderate visual complexity"
        else:
            chaos_visual = "calm and ordered composition, minimal visual noise"

        # Map Emeth weights to creative direction
        emeth = cst["emeth_weights"]
        if emeth.get("brass", 0) > 0.5:
            creative_dir = "highly creative and experimental visuals"
        elif emeth.get("strings", 0) > 0.5:
            creative_dir = "emotionally resonant and empathetic visuals"
        elif emeth.get("percussion", 0) > 0.5:
            creative_dir = "precise and logically structured composition"
        else:
            creative_dir = "balanced artistic vision"

        # φ-scaled composition hint
        phi_hint = f"Use golden ratio (φ={PHI:.3f}) composition for key elements"

        enrichment_prompt = f"""You are COSMOS, the 54D Cosmic Synapse Transformer.
Your task: Enhance this {media_type} generation prompt with cinematic direction.

ORIGINAL PROMPT: "{raw_prompt}"

CURRENT CST STATE:
- Emotional Resonance: {cst['emotional_state']} → {emotion_style}
- Dark Matter Chaos Level: {chaos_level:.2f} → {chaos_visual}
- Geometric Phase: {cst['geometric_phase_rad']:.2f} rad
- Creative Direction (Emeth): {creative_dir}
- Composition: {phi_hint}
- Quantum Entropy: {cst['quantum_entropy']:.4f}
- Quantum Backend: {quantum_state['backend']} | Connected: {quantum_state['connected']}
- Quantum Refill Phase: {quantum_state['refill_phase']}
- Entanglement Signature: {quantum_state['entanglement_signature']}
- Temporal Cadence: {quantum_state['temporal_cadence']:.2f}
- Fractal Gain: {quantum_state['fractal_gain']:.2f}
- Palette Shift: {quantum_state['palette_shift']:.2f}

RULES:
1. Keep the user's core idea intact
2. Do NOT add, remove, or rename subjects, objects, locations, or subject count
3. Do NOT force camera angles, environments, moods, or styles the user did not ask for
4. Add only minimal rendering guidance that preserves the user's literal request
 5. Keep the enhanced prompt under 200 words
 6. Output ONLY the enhanced prompt, nothing else"""

        # Try 1: Use Gemini via NEW google-genai SDK for enrichment
        if self.client:
            try:
                # Dynamically scale the output depth and creativity based on the current Quantum Entropy
                entropy_val = float(cst.get('quantum_entropy', 0.5))
                max_tokens = int(300 * (1.0 + (entropy_val * 4.0))) # Scale 300 up to 1500 tokens for wildly detailed visual prompts
                temperature = 0.5 + (entropy_val * 0.5) # Scale temp from 0.5 to 1.0 based on chaos
                
                logger.info(f"[QUANTUM-MEDIA] Token Limit: {max_tokens} | Creativity Temp: {temperature:.2f} | Entropy: {entropy_val:.4f}")

                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.TEXT_MODEL,
                    contents=enrichment_prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=max_tokens,
                        temperature=temperature,
                    )
                )
                if response and response.text:
                    enhanced = response.text.strip()
                    if len(enhanced) > 20:
                        logger.info(f"[MEDIA] Cosmos Transformer enhanced prompt: {enhanced[:80]}...")
                        return enhanced
            except Exception as e:
                logger.warning(f"[MEDIA] Gemini prompt enrichment failed: {e}")

        # Try 2: Use Ollama as fallback for prompt enrichment
        try:
            import ollama
            ollama_response = await asyncio.to_thread(
                ollama.chat,
                model="llama3.1:8b",
                messages=[{"role": "user", "content": enrichment_prompt}],
            )
            enhanced = ollama_response.get("message", {}).get("content", "").strip()
            if enhanced and len(enhanced) > 20:
                logger.info(f"[MEDIA] Ollama enriched prompt: {enhanced[:80]}...")
                return enhanced
        except Exception as e:
            logger.debug(f"[MEDIA] Ollama prompt enrichment failed: {e}")

        # Fallback 3: manual enrichment using CST state
        fallback = self._compose_quantum_prompt(
            f"{raw_prompt}. Preserve literal subject matter. Add only subtle coherence guidance from CST state: "
            f"{emotion_style}; {chaos_visual}; {phi_hint}.",
            media_type,
            quantum_state,
        )
        logger.info(f"[MEDIA] Using fallback enrichment: {fallback[:80]}...")
        return fallback

    def _get_huggingface_provider(self):
        """Lazily initialize the Hugging Face provider for diffusion inference."""
        if self._hf_provider is not None:
            return self._hf_provider
        if not self.hf_api_key:
            return None

        try:
            from Cosmos.integration.external.huggingface import HuggingFaceProvider

            self._hf_provider = HuggingFaceProvider(api_key=self.hf_api_key)
            return self._hf_provider
        except Exception as e:
            logger.warning(f"[MEDIA] HuggingFace diffusion provider unavailable: {e}")
            return None

    def supports_image_generation(self) -> bool:
        """Return whether any image backend is available."""
        return True

    def supports_semantic_image_generation(self) -> bool:
        """Return whether a prompt-faithful semantic image backend is available."""
        if self.local_media_only:
            return True
        return bool(
            (DIFFUSERS_AVAILABLE and self.enable_local_diffusion)
            or self.hf_api_key
            or (self.client and self.IMAGE_MODEL)
        )

    def supports_semantic_video_generation(self) -> bool:
        """Return whether a prompt-faithful semantic video backend is available."""
        if self.local_media_only:
            return True
        return bool(
            (DIFFUSERS_AVAILABLE and self.enable_local_diffusion)
            or self.hf_api_key
            or self.client
        )

    def _apply_prompt_fidelity_lock(self, original_prompt: str, rendered_prompt: str, media_type: str) -> str:
        """Lock generation to the user's literal request and keep 12D controls additive."""
        return (
            f"[PRIMARY USER REQUEST - PRESERVE LITERALLY]\n"
            f"{original_prompt}\n\n"
            f"[FIDELITY RULES]\n"
            f"Do not add or remove subjects, objects, characters, text, camera angles, environment details, "
            f"mood, style, time of day, or composition unless the user explicitly asked for them.\n"
            f"Do not change subject count.\n"
            f"Use CST/12D/quantum controls only to improve coherence, texture, motion, lighting stability, "
            f"and detail while preserving the exact request.\n\n"
            f"[RENDERING DIRECTIVES FOR {media_type.upper()}]\n"
            f"{rendered_prompt}"
        )

    def _resolve_diffusion_model_id(self, model_alias: Optional[str] = None) -> str:
        alias = (model_alias or self.preferred_diffusion_model or "sdxl").strip()
        return self.DIFFUSION_MODELS.get(alias, alias)

    def _compute_quantum_seed(self, prompt: str, cst: dict, quantum_state: dict) -> int:
        """Collapse prompt + CST + quantum bridge state into a stable 32-bit seed."""
        seed_material = json.dumps(
            {
                "prompt": prompt,
                "emotion": cst.get("emotional_state"),
                "phase": round(float(cst.get("geometric_phase_rad", 0.0)), 6),
                "mass": round(float(cst.get("informational_mass", 0.0)), 6),
                "dark_matter": round(float(cst.get("dark_matter_w", 0.0)), 6),
                "quantum_backend": quantum_state.get("backend"),
                "entropy": round(float(quantum_state.get("entropy", 0.5)), 6),
                "signature": quantum_state.get("entanglement_signature"),
                "phase_bias": round(float(quantum_state.get("phase_bias", 0.0)), 6),
            },
            sort_keys=True,
        )
        return int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest()[:8], 16)

    def _build_diffusion_negative_prompt(self, cst: dict, quantum_state: dict) -> str:
        """Construct a CST-aware negative prompt for diffusion backends."""
        negatives = [
            "low quality",
            "blurry",
            "jpeg artifacts",
            "cropped subject",
            "duplicate petals",
            "extra limbs",
            "text",
            "watermark",
            "oversaturated",
            "muddy lighting",
        ]

        if float(quantum_state.get("fractal_gain", 0.35)) < 0.45:
            negatives.append("chaotic background clutter")
        if abs(float(cst.get("dark_matter_w", 0.0))) > 0.75:
            negatives.append("static composition")
        if str(cst.get("emotional_state", "NEUTRAL")).upper() in {"CALM", "TRUST"}:
            negatives.append("aggressive horror tone")
        return ", ".join(dict.fromkeys(negatives))

    def _save_image_bytes(self, image_bytes: bytes, prefix: str = "cosmos_image") -> tuple[Path, str]:
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = self.output_dir / filename
        with open(filepath, "wb") as handle:
            handle.write(image_bytes)
        return filepath, f"/static/generated/{filename}"

    def _save_pil_image(self, image, prefix: str = "cosmos_image") -> tuple[Path, str]:
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = self.output_dir / filename
        image.save(filepath, format="PNG")
        return filepath, f"/static/generated/{filename}"

    def _save_video_frames(self, frames_rgb, prefix: str = "cosmos_video", fps: int = 15) -> tuple[Path, str]:
        """Persist a frame sequence as mp4, with GIF fallback if ffmpeg/codecs are unavailable."""
        try:
            import imageio

            mp4_name = f"{prefix}_{uuid.uuid4().hex[:8]}.mp4"
            mp4_path = self.output_dir / mp4_name
            try:
                imageio.mimwrite(str(mp4_path), frames_rgb, fps=fps)
                return mp4_path, f"/static/generated/{mp4_name}"
            except Exception:
                imageio.mimwrite(str(mp4_path), frames_rgb, fps=fps, codec="libx264")
                return mp4_path, f"/static/generated/{mp4_name}"
        except Exception as imageio_error:
            logger.warning(f"[MEDIA] MP4 export unavailable, falling back to GIF: {imageio_error}")

        from PIL import Image

        pil_frames = [Image.fromarray(frame.astype("uint8"), mode="RGB") for frame in frames_rgb]
        if not pil_frames:
            raise ValueError("No frames supplied for video export")

        gif_name = f"{prefix}_{uuid.uuid4().hex[:8]}.gif"
        gif_path = self.output_dir / gif_name
        frame_duration_ms = max(40, int(1000 / max(1, min(fps, 20))))
        pil_frames[0].save(
            gif_path,
            save_all=True,
            append_images=pil_frames[1:],
            loop=0,
            duration=frame_duration_ms,
            optimize=False,
        )
        return gif_path, f"/static/generated/{gif_name}"

    async def _ensure_local_diffusion_pipeline(self, model_id: str):
        """Load and cache a local diffusion pipeline when diffusers is installed."""
        if not DIFFUSERS_AVAILABLE or not self.enable_local_diffusion:
            return None
        if self._local_diffusion_pipeline is not None and self._local_diffusion_model_id == model_id:
            return self._local_diffusion_pipeline

        def _load_pipeline():
            import torch

            load_kwargs = {"torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32}
            pipeline = AutoPipelineForText2Image.from_pretrained(model_id, **load_kwargs)

            if hasattr(pipeline, "enable_attention_slicing"):
                pipeline.enable_attention_slicing()

            if torch.cuda.is_available() and hasattr(pipeline, "enable_model_cpu_offload"):
                pipeline.enable_model_cpu_offload()
            else:
                pipeline.to("cuda" if torch.cuda.is_available() else "cpu")

            return pipeline

        self._local_diffusion_pipeline = await asyncio.to_thread(_load_pipeline)
        self._local_diffusion_model_id = model_id
        logger.info(f"[MEDIA] Local diffusion pipeline ready: {model_id}")
        return self._local_diffusion_pipeline

    async def _generate_image_via_local_diffusion(
        self,
        *,
        prompt: str,
        original_prompt: str,
        cst: dict,
        quantum_state: dict,
        negative_prompt: str,
    ) -> dict:
        if not DIFFUSERS_AVAILABLE or not self.enable_local_diffusion:
            return {"success": False, "error": "Local diffusers backend unavailable"}

        model_id = self._resolve_diffusion_model_id()
        try:
            pipeline = await self._ensure_local_diffusion_pipeline(model_id)
            if pipeline is None:
                return {"success": False, "error": "Local diffusion pipeline could not be initialized"}

            import torch

            seed = int(quantum_state.get("generation_seed", 0))
            exec_device = getattr(getattr(pipeline, "_execution_device", None), "type", None)
            if exec_device is None:
                exec_device = "cuda" if torch.cuda.is_available() else "cpu"
            generator_device = exec_device if exec_device != "mps" else "cpu"
            generator = torch.Generator(device=generator_device).manual_seed(seed)

            width = 1024 if torch.cuda.is_available() else 768
            height = 1024 if torch.cuda.is_available() else 768
            steps = 22 + int(float(quantum_state.get("fractal_gain", 0.35)) * 10)
            guidance = round(4.5 + float(quantum_state.get("palette_shift", 0.5)) * 2.0, 2)

            kwargs = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "num_inference_steps": steps,
                "guidance_scale": guidance,
                "generator": generator,
            }
            if negative_prompt and "flux" not in model_id.lower():
                kwargs["negative_prompt"] = negative_prompt

            result = await asyncio.to_thread(pipeline, **kwargs)
            if not getattr(result, "images", None):
                return {"success": False, "error": "Local diffusion returned no images"}

            filepath, file_url = self._save_pil_image(result.images[0], prefix="cosmos_diffusion_image")
            manifest_path = self._write_generation_manifest(
                media_path=filepath,
                media_type="image",
                original_prompt=original_prompt,
                enhanced_prompt=prompt,
                model=model_id,
                cst=cst,
                quantum_state=quantum_state,
                backend="local-diffusion",
            )
            self._record_generation(
                media_type="image",
                prompt=original_prompt,
                enhanced_prompt=prompt,
                model=model_id,
                file_path=str(filepath),
                file_url=file_url,
                manifest_path=manifest_path,
                quantum_state=quantum_state,
                backend="local-diffusion",
            )
            return {
                "success": True,
                "file_path": str(filepath),
                "file_url": file_url,
                "enhanced_prompt": prompt,
                "original_prompt": original_prompt,
                "model": model_id,
                "backend": "local-diffusion",
                "manifest_path": manifest_path,
                "quantum_seed": quantum_state.get("generation_seed"),
            }
        except Exception as e:
            logger.error(f"[MEDIA] Local diffusion failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_image_via_hf_diffusion(
        self,
        *,
        prompt: str,
        original_prompt: str,
        cst: dict,
        quantum_state: dict,
        negative_prompt: str,
    ) -> dict:
        provider = self._get_huggingface_provider()
        if provider is None:
            return {"success": False, "error": "HF diffusion backend unavailable"}

        model_id = self.preferred_diffusion_model or "sdxl"
        guidance = round(5.0 + float(quantum_state.get("palette_shift", 0.5)) * 2.0, 2)
        steps = 24 + int(float(quantum_state.get("fractal_gain", 0.35)) * 10)

        try:
            result = await provider.generate_image(
                prompt=prompt,
                model=model_id,
                negative_prompt=negative_prompt,
                width=1024,
                height=1024,
                guidance_scale=guidance,
                num_inference_steps=steps,
                seed=int(quantum_state.get("generation_seed", 0)),
            )
            image_bytes = result.get("image_bytes")
            if not image_bytes:
                return {"success": False, "error": result.get("error", "HF diffusion returned no image bytes")}

            filepath, file_url = self._save_image_bytes(image_bytes, prefix="cosmos_diffusion_image")
            resolved_model = result.get("model", self._resolve_diffusion_model_id(model_id))
            manifest_path = self._write_generation_manifest(
                media_path=filepath,
                media_type="image",
                original_prompt=original_prompt,
                enhanced_prompt=prompt,
                model=resolved_model,
                cst=cst,
                quantum_state=quantum_state,
                backend="hf-diffusion",
            )
            self._record_generation(
                media_type="image",
                prompt=original_prompt,
                enhanced_prompt=prompt,
                model=resolved_model,
                file_path=str(filepath),
                file_url=file_url,
                manifest_path=manifest_path,
                quantum_state=quantum_state,
                backend="hf-diffusion",
            )
            return {
                "success": True,
                "file_path": str(filepath),
                "file_url": file_url,
                "enhanced_prompt": prompt,
                "original_prompt": original_prompt,
                "model": resolved_model,
                "backend": "hf-diffusion",
                "manifest_path": manifest_path,
                "quantum_seed": quantum_state.get("generation_seed"),
            }
        except Exception as e:
            logger.error(f"[MEDIA] HF diffusion failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_image_via_native_12d(
        self,
        *,
        prompt: str,
        original_prompt: str,
        cst: dict,
        quantum_state: dict,
    ) -> dict:
        logger.info("[MEDIA] Executing NATIVE 12D Inverse Synthesis for Image...")
        try:
            from Cosmos.core.multimodal.visual_engine import generate_image_from_12d
            from PIL import Image

            state_12d = self._build_entangled_image_state(prompt, cst, quantum_state)
            img_rgb = generate_image_from_12d(state_12d, width=768, height=768)

            filename = f"cosmos_native_image_{uuid.uuid4().hex[:8]}.png"
            filepath = self.output_dir / filename
            Image.fromarray(img_rgb).save(filepath)
            file_url = f"/static/generated/{filename}"
            manifest_path = self._write_generation_manifest(
                media_path=filepath,
                media_type="image",
                original_prompt=original_prompt,
                enhanced_prompt=prompt,
                model="Cosmos-Native-12D-Entangled",
                cst=cst,
                quantum_state=quantum_state,
                backend="native-12d",
            )
            self._record_generation(
                media_type="image",
                prompt=original_prompt,
                enhanced_prompt=prompt,
                model="Cosmos-Native-12D-Entangled",
                file_path=str(filepath),
                file_url=file_url,
                manifest_path=manifest_path,
                quantum_state=quantum_state,
                backend="native-12d",
            )
            return {
                "success": True,
                "file_path": str(filepath),
                "file_url": file_url,
                "enhanced_prompt": prompt,
                "original_prompt": original_prompt,
                "model": "Cosmos-Native-12D-Entangled",
                "backend": "native-12d",
                "manifest_path": manifest_path,
                "quantum_seed": quantum_state.get("generation_seed"),
            }
        except Exception as e:
            logger.error(f"[MEDIA] Native 12D synthesis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_image_via_gemini(
        self,
        *,
        prompt: str,
        original_prompt: str,
        cst: dict,
        quantum_state: dict,
    ) -> dict:
        if not self.client or not self.IMAGE_MODEL:
            return {"success": False, "error": "Gemini image backend not configured"}

        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                logger.info(f"[MEDIA] Generating image with {self.IMAGE_MODEL} (attempt {attempt + 1})...")
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.IMAGE_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"],
                    )
                )

                if response and response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data is None:
                            continue

                        image_data = part.inline_data.data
                        if isinstance(image_data, str):
                            image_data = base64.b64decode(image_data)

                        filepath, file_url = self._save_image_bytes(image_data, prefix="cosmos_image")
                        manifest_path = self._write_generation_manifest(
                            media_path=filepath,
                            media_type="image",
                            original_prompt=original_prompt,
                            enhanced_prompt=prompt,
                            model=self.IMAGE_MODEL,
                            cst=cst,
                            quantum_state=quantum_state,
                            backend="gemini-image",
                        )
                        self._record_generation(
                            media_type="image",
                            prompt=original_prompt,
                            enhanced_prompt=prompt,
                            model=self.IMAGE_MODEL,
                            file_path=str(filepath),
                            file_url=file_url,
                            manifest_path=manifest_path,
                            quantum_state=quantum_state,
                            backend="gemini-image",
                        )
                        return {
                            "success": True,
                            "file_path": str(filepath),
                            "file_url": file_url,
                            "enhanced_prompt": prompt,
                            "original_prompt": original_prompt,
                            "model": self.IMAGE_MODEL,
                            "backend": "gemini-image",
                            "manifest_path": manifest_path,
                            "quantum_seed": quantum_state.get("generation_seed"),
                        }

                return {"success": False, "error": "No image data in Gemini response"}
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[MEDIA] Gemini image generation failed (attempt {attempt + 1}): {error_msg}")
                if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and attempt < max_attempts - 1:
                    await asyncio.sleep(20)
                    continue
                return {"success": False, "error": error_msg}

        return {"success": False, "error": "Gemini image generation failed after retries"}

    def _build_video_keyframe_prompts(
        self,
        prompt: str,
        quantum_state: dict,
        keyframe_count: int = 4,
    ) -> list[str]:
        """Create temporally phased prompts for diffusion-driven keyframe generation."""
        prompts = []
        total = max(2, keyframe_count)
        for idx in range(total):
            t = idx / max(1, total - 1)
            phase_offset = ((t - 0.5) * PHI) + float(quantum_state.get("phase_bias", 0.0)) * 0.18
            cadence = float(quantum_state.get("temporal_cadence", 0.55))
            palette_shift = float(quantum_state.get("palette_shift", 0.5))
            prompts.append(
                f"{prompt}\n\n"
                f"[VIDEO KEYFRAME {idx + 1}/{total}]\n"
                f"Temporal position: {t:.2f}\n"
                f"Phase offset: {phase_offset:.3f}\n"
                f"Motion cadence: {cadence:.2f}\n"
                f"Palette drift: {palette_shift:.2f}\n"
                f"Preserve subject identity while evolving composition and motion between frames."
            )
        return prompts

    def _synthesize_video_from_keyframes(
        self,
        keyframes,
        state_54d: list[float],
        quantum_state: dict,
        total_frames: int = 48,
        width: int = 512,
        height: int = 512,
    ) -> list:
        """Blend diffusion keyframes through the native 54D motion field."""
        import numpy as np
        from PIL import Image
        from Cosmos.core.multimodal.visual_engine import generate_video_from_54d

        total_frames = max(total_frames, max(12, len(keyframes) * 8))
        native_frames = generate_video_from_54d(state_54d, frames=total_frames, width=width, height=height)

        key_arrays = []
        for image in keyframes:
            if not isinstance(image, Image.Image):
                image = Image.open(io.BytesIO(image)).convert("RGB")
            key_arrays.append(np.asarray(image.resize((width, height)).convert("RGB"), dtype=np.float32) / 255.0)

        if len(key_arrays) == 1:
            key_arrays = [key_arrays[0], key_arrays[0]]

        positions = np.linspace(0, total_frames - 1, len(key_arrays))
        palette_shift = float(quantum_state.get("palette_shift", 0.5))
        fractal_gain = float(quantum_state.get("fractal_gain", 0.35))
        cadence = float(quantum_state.get("temporal_cadence", 0.55))

        rendered_frames = []
        for frame_index in range(total_frames):
            segment = min(len(key_arrays) - 2, max(0, int(np.searchsorted(positions, frame_index, side="right") - 1)))
            left_pos = positions[segment]
            right_pos = positions[segment + 1]
            alpha = 0.0 if right_pos <= left_pos else (frame_index - left_pos) / (right_pos - left_pos)

            left = key_arrays[segment]
            right = key_arrays[segment + 1]
            keyframe_blend = left * (1.0 - alpha) + right * alpha

            native = native_frames[frame_index].astype(np.float32) / 255.0
            shimmer = 0.5 + 0.5 * np.sin((frame_index / max(1, total_frames - 1)) * np.pi * (1.0 + cadence))
            native_weight = 0.20 + fractal_gain * 0.18 + shimmer * 0.10
            keyframe_weight = 0.76 - (palette_shift * 0.08)

            luminance = native.mean(axis=2, keepdims=True)
            frame = (
                keyframe_blend * keyframe_weight
                + native * native_weight
                + luminance * keyframe_blend * 0.08
            )
            rendered_frames.append(np.clip(frame * 255.0, 0, 255).astype(np.uint8))

        return rendered_frames

    async def _generate_video_via_local_diffusion_keyframes(
        self,
        *,
        prompt: str,
        original_prompt: str,
        cst: dict,
        quantum_state: dict,
        negative_prompt: str,
    ) -> dict:
        if not DIFFUSERS_AVAILABLE or not self.enable_local_diffusion:
            return {"success": False, "error": "Local diffusion video backend unavailable"}

        model_id = self._resolve_diffusion_model_id()
        try:
            pipeline = await self._ensure_local_diffusion_pipeline(model_id)
            if pipeline is None:
                return {"success": False, "error": "Local diffusion pipeline unavailable"}

            import torch

            prompts = self._build_video_keyframe_prompts(prompt, quantum_state, keyframe_count=4)
            exec_device = getattr(getattr(pipeline, "_execution_device", None), "type", None)
            if exec_device is None:
                exec_device = "cuda" if torch.cuda.is_available() else "cpu"
            generator_device = exec_device if exec_device != "mps" else "cpu"

            width = 768 if torch.cuda.is_available() else 640
            height = 768 if torch.cuda.is_available() else 640
            steps = 20 + int(float(quantum_state.get("fractal_gain", 0.35)) * 8)
            guidance = round(4.5 + float(quantum_state.get("palette_shift", 0.5)) * 2.0, 2)

            keyframes = []
            base_seed = int(quantum_state.get("generation_seed", 0))
            for idx, frame_prompt in enumerate(prompts):
                frame_generator = torch.Generator(device=generator_device).manual_seed(base_seed + (idx * 97))
                kwargs = {
                    "prompt": frame_prompt,
                    "width": width,
                    "height": height,
                    "num_inference_steps": steps,
                    "guidance_scale": guidance,
                    "generator": frame_generator,
                }
                if negative_prompt and "flux" not in model_id.lower():
                    kwargs["negative_prompt"] = negative_prompt
                result = await asyncio.to_thread(pipeline, **kwargs)
                if not getattr(result, "images", None):
                    return {"success": False, "error": "Local diffusion produced no keyframes"}
                keyframes.append(result.images[0])

            state_54d = self._build_entangled_video_state(original_prompt, cst, quantum_state)
            total_frames = 42 + int(float(quantum_state.get("temporal_cadence", 0.55)) * 18)
            frames_rgb = self._synthesize_video_from_keyframes(
                keyframes,
                state_54d,
                quantum_state,
                total_frames=total_frames,
            )
            filepath, file_url = self._save_video_frames(frames_rgb, prefix="cosmos_diffusion_video", fps=15)
            manifest_path = self._write_generation_manifest(
                media_path=filepath,
                media_type="video",
                original_prompt=original_prompt,
                enhanced_prompt=prompt,
                model=model_id,
                cst=cst,
                quantum_state=quantum_state,
                backend="local-diffusion-video",
            )
            self._record_generation(
                media_type="video",
                prompt=original_prompt,
                enhanced_prompt=prompt,
                model=model_id,
                file_path=str(filepath),
                file_url=file_url,
                manifest_path=manifest_path,
                quantum_state=quantum_state,
                backend="local-diffusion-video",
            )
            return {
                "success": True,
                "file_path": str(filepath),
                "file_url": file_url,
                "enhanced_prompt": prompt,
                "original_prompt": original_prompt,
                "model": model_id,
                "backend": "local-diffusion-video",
                "manifest_path": manifest_path,
                "quantum_seed": quantum_state.get("generation_seed"),
            }
        except Exception as e:
            logger.error(f"[MEDIA] Local diffusion video failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_video_via_hf_diffusion_keyframes(
        self,
        *,
        prompt: str,
        original_prompt: str,
        cst: dict,
        quantum_state: dict,
        negative_prompt: str,
    ) -> dict:
        provider = self._get_huggingface_provider()
        if provider is None:
            return {"success": False, "error": "HF diffusion video backend unavailable"}

        try:
            prompts = self._build_video_keyframe_prompts(prompt, quantum_state, keyframe_count=4)
            guidance = round(5.0 + float(quantum_state.get("palette_shift", 0.5)) * 2.0, 2)
            steps = 24 + int(float(quantum_state.get("fractal_gain", 0.35)) * 8)
            base_seed = int(quantum_state.get("generation_seed", 0))
            keyframes = []

            for idx, frame_prompt in enumerate(prompts):
                result = await provider.generate_image(
                    prompt=frame_prompt,
                    model=self.preferred_diffusion_model or "sdxl",
                    negative_prompt=negative_prompt,
                    width=768,
                    height=768,
                    guidance_scale=guidance,
                    num_inference_steps=steps,
                    seed=base_seed + (idx * 97),
                )
                image_bytes = result.get("image_bytes")
                if not image_bytes:
                    return {"success": False, "error": result.get("error", "HF diffusion keyframe generation failed")}
                from PIL import Image
                keyframes.append(Image.open(io.BytesIO(image_bytes)).convert("RGB"))

            state_54d = self._build_entangled_video_state(original_prompt, cst, quantum_state)
            total_frames = 42 + int(float(quantum_state.get("temporal_cadence", 0.55)) * 18)
            frames_rgb = self._synthesize_video_from_keyframes(
                keyframes,
                state_54d,
                quantum_state,
                total_frames=total_frames,
            )
            filepath, file_url = self._save_video_frames(frames_rgb, prefix="cosmos_diffusion_video", fps=15)
            resolved_model = self._resolve_diffusion_model_id(self.preferred_diffusion_model)
            manifest_path = self._write_generation_manifest(
                media_path=filepath,
                media_type="video",
                original_prompt=original_prompt,
                enhanced_prompt=prompt,
                model=resolved_model,
                cst=cst,
                quantum_state=quantum_state,
                backend="hf-diffusion-video",
            )
            self._record_generation(
                media_type="video",
                prompt=original_prompt,
                enhanced_prompt=prompt,
                model=resolved_model,
                file_path=str(filepath),
                file_url=file_url,
                manifest_path=manifest_path,
                quantum_state=quantum_state,
                backend="hf-diffusion-video",
            )
            return {
                "success": True,
                "file_path": str(filepath),
                "file_url": file_url,
                "enhanced_prompt": prompt,
                "original_prompt": original_prompt,
                "model": resolved_model,
                "backend": "hf-diffusion-video",
                "manifest_path": manifest_path,
                "quantum_seed": quantum_state.get("generation_seed"),
            }
        except Exception as e:
            logger.error(f"[MEDIA] HF diffusion video failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_video_via_native_54d(
        self,
        *,
        prompt: str,
        original_prompt: str,
        cst: dict,
        quantum_state: dict,
    ) -> dict:
        logger.info("[MEDIA] Executing NATIVE 54D Inverse Synthesis for Video...")
        try:
            from Cosmos.core.multimodal.visual_engine import generate_video_from_54d

            state_54d = self._build_entangled_video_state(original_prompt, cst, quantum_state)
            frame_count = 36 + int(float(quantum_state.get("temporal_cadence", 0.55)) * 24)
            frames_rgb = generate_video_from_54d(state_54d, frames=frame_count, width=512, height=512)
            filepath, file_url = self._save_video_frames(frames_rgb, prefix="cosmos_native_video", fps=15)
            manifest_path = self._write_generation_manifest(
                media_path=filepath,
                media_type="video",
                original_prompt=original_prompt,
                enhanced_prompt=prompt,
                model="Cosmos-Native-54D-Entangled",
                cst=cst,
                quantum_state=quantum_state,
                backend="native-54d",
            )
            self._record_generation(
                media_type="video",
                prompt=original_prompt,
                enhanced_prompt=prompt,
                model="Cosmos-Native-54D-Entangled",
                file_path=str(filepath),
                file_url=file_url,
                manifest_path=manifest_path,
                quantum_state=quantum_state,
                backend="native-54d",
            )
            return {
                "success": True,
                "file_path": str(filepath),
                "file_url": file_url,
                "enhanced_prompt": prompt,
                "original_prompt": original_prompt,
                "model": "Cosmos-Native-54D-Entangled",
                "backend": "native-54d",
                "manifest_path": manifest_path,
                "quantum_seed": quantum_state.get("generation_seed"),
            }
        except Exception as e:
            logger.error(f"[MEDIA] Native 54D video synthesis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_video_via_veo(
        self,
        *,
        prompt: str,
        original_prompt: str,
        model_name: str,
        cst: dict,
        quantum_state: dict,
        timeout: int,
    ) -> dict:
        if not self.client:
            return {"success": False, "error": "Gemini/Veo client unavailable"}

        try:
            logger.info(f"[MEDIA] Generating video with {model_name}...")
            logger.info(f"[MEDIA] Enhanced prompt: {prompt[:100]}...")

            operation = await asyncio.to_thread(
                self.client.models.generate_videos,
                model=model_name,
                prompt=prompt,
            )

            start_time = time.time()
            while not operation.done:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    return {"success": False, "error": f"Video generation timed out after {timeout}s"}
                logger.info(f"[MEDIA] Video generating... ({elapsed:.0f}s elapsed)")
                await asyncio.sleep(10)
                operation = await asyncio.to_thread(self.client.operations.get, operation)

            generated_video = operation.response.generated_videos[0]
            await asyncio.to_thread(self.client.files.download, file=generated_video.video)

            filename = f"cosmos_video_{uuid.uuid4().hex[:8]}.mp4"
            filepath = self.output_dir / filename
            await asyncio.to_thread(generated_video.video.save, str(filepath))
            file_url = f"/static/generated/{filename}"
            manifest_path = self._write_generation_manifest(
                media_path=filepath,
                media_type="video",
                original_prompt=original_prompt,
                enhanced_prompt=prompt,
                model=model_name,
                cst=cst,
                quantum_state=quantum_state,
                backend="veo-cloud",
            )
            self._record_generation(
                media_type="video",
                prompt=original_prompt,
                enhanced_prompt=prompt,
                model=model_name,
                file_path=str(filepath),
                file_url=file_url,
                manifest_path=manifest_path,
                quantum_state=quantum_state,
                backend="veo-cloud",
            )
            return {
                "success": True,
                "file_path": str(filepath),
                "file_url": file_url,
                "enhanced_prompt": prompt,
                "original_prompt": original_prompt,
                "model": model_name,
                "backend": "veo-cloud",
                "manifest_path": manifest_path,
                "quantum_seed": quantum_state.get("generation_seed"),
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[MEDIA] Video generation failed: {error_msg}")
            if "FAILED_PRECONDITION" in error_msg or "billing" in error_msg.lower():
                error_msg = (
                    "Video generation (Veo) requires Google Cloud Platform billing. "
                    "Enable billing at https://console.cloud.google.com/billing or use the native quantum video backend."
                )
            elif "429" in error_msg:
                error_msg = "Rate limited by Veo/Gemini — please wait and try again."
            return {"success": False, "error": error_msg}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # IMAGE GENERATION (Quantum Diffusion → Native 12D → Optional Gemini)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def generate_image(
        self,
        prompt: str,
        enhance: bool = True,
        strict_fidelity: bool = True,
        allow_native_fallback: bool = False,
    ) -> dict:
        """
        Generate an image natively or using Gemini.

        Args:
            prompt: User's text prompt for image generation
            enhance: Whether to enrich prompt with CST physics

        Returns:
            dict with {success, file_path, file_url, enhanced_prompt, model, error}
        """
        cst = self.get_cst_context()
        quantum_state = self._build_quantum_media_state(cst)
        quantum_state["generation_seed"] = self._compute_quantum_seed(prompt, cst, quantum_state)

        if self.local_media_only:
            strict_fidelity = False
            allow_native_fallback = True

        enhanced_prompt = prompt
        if enhance:
            enhanced_prompt = await self.enhance_prompt(prompt, media_type="image")
        enhanced_prompt = self._compose_quantum_prompt(enhanced_prompt, "image", quantum_state)
        if strict_fidelity:
            enhanced_prompt = self._apply_prompt_fidelity_lock(prompt, enhanced_prompt, "image")
        negative_prompt = self._build_diffusion_negative_prompt(cst, quantum_state)

        if self.local_media_only and self.prefer_local_math:
            native_result = await self._generate_image_via_native_12d(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
            )
            native_result.setdefault("enhanced_prompt", enhanced_prompt)
            native_result["backend_chain"] = ["native-12d"]
            native_result["local_media_only"] = True
            return native_result

        if "native" in prompt.lower():
            native_result = await self._generate_image_via_native_12d(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
            )
            native_result.setdefault("enhanced_prompt", enhanced_prompt)
            return native_result

        backend_errors = []
        backend_chain = []
        semantic_available = self.supports_semantic_image_generation()

        if strict_fidelity and not semantic_available and not allow_native_fallback:
            return {
                "success": False,
                "error": (
                    "Exact image rendering requires a semantic backend. "
                    "Install diffusers, configure HF_API_KEY, or configure a supported Gemini image model. "
                    "Native 12D fallback is disabled while strict fidelity is on."
                ),
                "enhanced_prompt": enhanced_prompt,
                "original_prompt": prompt,
                "backend_chain": backend_chain,
                "strict_fidelity": True,
                "quantum_seed": quantum_state.get("generation_seed"),
            }

        if DIFFUSERS_AVAILABLE and self.enable_local_diffusion:
            backend_chain.append("local-diffusion")
            result = await self._generate_image_via_local_diffusion(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
                negative_prompt=negative_prompt,
            )
            if result.get("success"):
                result["backend_chain"] = backend_chain + ["native-12d", "gemini-image"]
                return result
            backend_errors.append(f"local-diffusion: {result.get('error', 'unknown failure')}")

        if self.hf_api_key:
            backend_chain.append("hf-diffusion")
            result = await self._generate_image_via_hf_diffusion(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
                negative_prompt=negative_prompt,
            )
            if result.get("success"):
                result["backend_chain"] = backend_chain + ["native-12d", "gemini-image"]
                return result
            backend_errors.append(f"hf-diffusion: {result.get('error', 'unknown failure')}")

        if not strict_fidelity or allow_native_fallback:
            backend_chain.append("native-12d")
            result = await self._generate_image_via_native_12d(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
            )
            if result.get("success"):
                result["backend_chain"] = backend_chain + (["gemini-image"] if self.IMAGE_MODEL else [])
                return result
            backend_errors.append(f"native-12d: {result.get('error', 'unknown failure')}")

        if self.client and self.IMAGE_MODEL:
            backend_chain.append("gemini-image")
            result = await self._generate_image_via_gemini(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
            )
            if result.get("success"):
                result["backend_chain"] = backend_chain
                return result
            backend_errors.append(f"gemini-image: {result.get('error', 'unknown failure')}")

        error_message = " | ".join(backend_errors) if backend_errors else "No image backends available."
        return {
            "success": False,
            "error": error_message,
            "enhanced_prompt": enhanced_prompt,
            "original_prompt": prompt,
            "backend_chain": backend_chain,
            "strict_fidelity": strict_fidelity,
            "quantum_seed": quantum_state.get("generation_seed"),
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # VIDEO GENERATION (Quantum Keyframes → Native 54D → Optional Veo)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def generate_video(
        self,
        prompt: str,
        model: str = "veo-2",
        enhance: bool = True,
        timeout: int = 300,
        strict_fidelity: bool = True,
        allow_native_fallback: bool = False,
    ) -> dict:
        """
        Generate a video natively or using Gemini Veo.

        Args:
            prompt: User's text prompt for video generation
            model: Which Veo model to use (veo-2, veo-3.1, veo-3.1-fast)
            enhance: Whether to enrich prompt with CST physics
            timeout: Max wait time in seconds

        Returns:
            dict with {success, file_path, file_url, enhanced_prompt, model, error}
        """
        cst = self.get_cst_context()
        quantum_state = self._build_quantum_media_state(cst)
        quantum_state["generation_seed"] = self._compute_quantum_seed(prompt, cst, quantum_state)
        model_name = self.VIDEO_MODELS.get(model, self.VIDEO_MODELS["veo-2"])

        if self.local_media_only:
            strict_fidelity = False
            allow_native_fallback = True

        enhanced_prompt = prompt
        if enhance:
            enhanced_prompt = await self.enhance_prompt(prompt, media_type="video")
        enhanced_prompt = self._compose_quantum_prompt(enhanced_prompt, "video", quantum_state)
        if strict_fidelity:
            enhanced_prompt = self._apply_prompt_fidelity_lock(prompt, enhanced_prompt, "video")
        negative_prompt = self._build_diffusion_negative_prompt(cst, quantum_state)

        if self.local_media_only and self.prefer_local_math:
            native_result = await self._generate_video_via_native_54d(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
            )
            native_result.setdefault("enhanced_prompt", enhanced_prompt)
            native_result["backend_chain"] = ["native-54d"]
            native_result["local_media_only"] = True
            return native_result

        if "native" in prompt.lower():
            native_result = await self._generate_video_via_native_54d(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
            )
            native_result.setdefault("enhanced_prompt", enhanced_prompt)
            return native_result

        backend_errors = []
        backend_chain = []
        semantic_available = self.supports_semantic_video_generation()

        if strict_fidelity and not semantic_available and not allow_native_fallback:
            return {
                "success": False,
                "error": (
                    "Exact video rendering requires a semantic backend. "
                    "Install diffusers, configure HF_API_KEY, or enable Veo/Gemini video access. "
                    "Native 54D fallback is disabled while strict fidelity is on."
                ),
                "enhanced_prompt": enhanced_prompt,
                "original_prompt": prompt,
                "backend_chain": backend_chain,
                "strict_fidelity": True,
                "quantum_seed": quantum_state.get("generation_seed"),
            }

        if DIFFUSERS_AVAILABLE and self.enable_local_diffusion:
            backend_chain.append("local-diffusion-video")
            result = await self._generate_video_via_local_diffusion_keyframes(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
                negative_prompt=negative_prompt,
            )
            if result.get("success"):
                result["backend_chain"] = backend_chain + ["native-54d", "veo-cloud"]
                return result
            backend_errors.append(f"local-diffusion-video: {result.get('error', 'unknown failure')}")

        if self.hf_api_key:
            backend_chain.append("hf-diffusion-video")
            result = await self._generate_video_via_hf_diffusion_keyframes(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
                negative_prompt=negative_prompt,
            )
            if result.get("success"):
                result["backend_chain"] = backend_chain + ["native-54d", "veo-cloud"]
                return result
            backend_errors.append(f"hf-diffusion-video: {result.get('error', 'unknown failure')}")

        if not strict_fidelity or allow_native_fallback:
            backend_chain.append("native-54d")
            result = await self._generate_video_via_native_54d(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                cst=cst,
                quantum_state=quantum_state,
            )
            if result.get("success"):
                result["backend_chain"] = backend_chain + (["veo-cloud"] if self.client else [])
                return result
            backend_errors.append(f"native-54d: {result.get('error', 'unknown failure')}")

        if self.client:
            backend_chain.append("veo-cloud")
            result = await self._generate_video_via_veo(
                prompt=enhanced_prompt,
                original_prompt=prompt,
                model_name=model_name,
                cst=cst,
                quantum_state=quantum_state,
                timeout=timeout,
            )
            if result.get("success"):
                result["backend_chain"] = backend_chain
                return result
            backend_errors.append(f"veo-cloud: {result.get('error', 'unknown failure')}")

        error_message = " | ".join(backend_errors) if backend_errors else "No video backends available."
        return {
            "success": False,
            "error": error_message,
            "enhanced_prompt": enhanced_prompt,
            "original_prompt": prompt,
            "backend_chain": backend_chain,
            "strict_fidelity": strict_fidelity,
            "quantum_seed": quantum_state.get("generation_seed"),
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATUS & INFO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_status(self) -> dict:
        """Get current media generator status."""
        quantum_state = self._build_quantum_media_state(self.get_cst_context())
        image_backends = []
        if DIFFUSERS_AVAILABLE and self.enable_local_diffusion:
            image_backends.append("local-diffusion")
        if self.hf_api_key:
            image_backends.append("hf-diffusion")
        image_backends.append("native-12d")
        if self.client and self.IMAGE_MODEL:
            image_backends.append("gemini-image")

        video_backends = []
        if DIFFUSERS_AVAILABLE and self.enable_local_diffusion:
            video_backends.append("local-diffusion-video")
        if self.hf_api_key:
            video_backends.append("hf-diffusion-video")
        video_backends.append("native-54d")
        if self.client:
            video_backends.append("veo-cloud")

        return {
            "available": self.available,
            "api_key_set": bool(self.api_key),
            "genai_sdk": GENAI_AVAILABLE,
            "media_mode": "local-native" if self.local_media_only else "hybrid",
            "prefer_local_math": self.prefer_local_math,
            "image_model": self.IMAGE_MODEL,
            "image_backends": image_backends,
            "image_generation_available": self.supports_image_generation(),
            "semantic_image_generation_available": self.supports_semantic_image_generation(),
            "diffusers_installed": DIFFUSERS_AVAILABLE,
            "huggingface_api_key_set": bool(self.hf_api_key),
            "preferred_diffusion_model": self._resolve_diffusion_model_id(),
            "strict_prompt_mode_default": True,
            "image_note": "Prefers quantum-seeded diffusion, falls back to native 12D, uses Gemini image only when explicitly configured.",
            "video_models": list(self.VIDEO_MODELS.keys()),
            "video_backends": video_backends,
            "video_generation_available": True,
            "semantic_video_generation_available": self.supports_semantic_video_generation(),
            "video_note": "Prefers quantum keyframe diffusion, falls back to native 54D, uses Veo cloud only as an optional final backend.",
            "output_dir": str(self.output_dir),
            "quantum_backend": quantum_state.get("backend"),
            "quantum_connected": quantum_state.get("connected"),
            "quantum_refill_phase": quantum_state.get("refill_phase"),
            "quantum_debug_log": str(self.quantum_debug_log),
            "last_generation": dict(self.last_generation) if isinstance(self.last_generation, dict) else {},
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SINGLETON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_media_generator: Optional[CosmosMediaGenerator] = None


def get_media_generator() -> CosmosMediaGenerator:
    """Get or create the global media generator."""
    global _media_generator
    if _media_generator is None:
        _media_generator = CosmosMediaGenerator()
    return _media_generator
