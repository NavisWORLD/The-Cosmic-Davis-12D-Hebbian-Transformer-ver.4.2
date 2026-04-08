# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Chang'e-4 / LND empirical validation harness**: Added a source-backed lunar radiation reference fixture, deterministic alignment tests, and a reproducible diagnostic runner that reports per-record sub-comparisons, aggregate alignment scores, and exact reproduction commands.
- **Validation documentation bundle**: Added `docs/validation/` output paths for the Chang'e-4 empirical summary and a Zenodo-ready publication update note tied to record `10.5281/zenodo.17574447`.
- **Held-out baseline validation**: Added a separate reproducible report that compares the 12D phase proxy against midpoint and leave-one-out mean baselines so predictive performance can be judged independently from the harmonic alignment score.
- **External Artemis I generalization check**: Added an unseen lunar-mission validation basket from the Artemis I radiation paper to test whether the locked Chang'e-4 calibration generalizes outside the original six-record family.

## [2.9.4] - 2026-03-01

### Added
- **Swarm Vision API (`/vision`)**: The cosmos Full System now natively hosts a zero-latency Base64 Webcam endpoint mapped explicitly for Gemini Multimodal. The Swarm Orchestrator actively intercepts visual cues prompts ("look", "what do you see") and feeds the live webcam context directly to the LLM backend. 
- **Raw Acoustic Ingestion (Audio-Driven 12D Token System)**: Rebuilt the STFT microphone loop `real_time_audio_pipe.py`. The Microphone pipeline now actively calculates RMS Energy, Spectral Centroids, Top 10 Fundamental Frequencies, and Generates a Golden Ratio (Phi) Mathematical Resonance Series from background environmental noise. This live audio state is instantly passed to the Swarm Brain for all future reasoning loops, letting the AI implicitly "feel" the stress or energy of the User's environment.

### Changed
- Refactored `cosmos_swarm_orchestrator.py` to auto-fetch from local Vision and Audio endpoints.
- Expanded `full_system.py` to securely pipe MediaPipe frames directly to LLM Vision safely.
- **Hebbian Plasticity V2**: Real-time Synaptic Pruning, Homeostasis, Temporal Memory, and Meta-Learning implemented in the Orchestrator.
- **Dynamic Quantum Scaling**: Swarm max-tokens calculation now dynamically scales to 4000+ during high chaos/entropy states using the 12D Phase/Geometric physics pipeline.

### Fixed
- **Ollama Node Stability**: Fallback models updated to `llama3.2:3b` to prevent immediate failure on environments missing historical 3.1 models.
- **Ghost Port Connections**: Added defensive handling for `[winerror 10048]` Uvicorn zombie socket conflicts during live system rebuilds.
- **Gemini Engine Consistency**: Upgraded deprecated image generation tools spanning to the unified `gemini-2.5-flash` endpoint.
- **Quantum Bridge Initialization**: Rebuilt the IBM Quantum configuration logic to catch missing auth tokens gracefully on application start.
- **Entity Resolution**: Enhanced Knowledge Graph P2P linker logic to safely create entities on-the-fly rather than crashing if requested keys were unlinked.
