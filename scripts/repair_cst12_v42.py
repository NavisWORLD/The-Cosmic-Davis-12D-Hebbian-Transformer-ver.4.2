#!/usr/bin/env python3
"""Apply the minimal v4.2 CST/54D repairs proven by the RED inspection.

This script is deliberately fail-closed. Every replacement must match exactly
once so it cannot silently rewrite an unexpected source revision.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match in {path}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[repair] {label}: ok")


def main() -> None:
    web_init = ROOT / "cosmos" / "web" / "__init__.py"
    model = ROOT / "cosmos" / "web" / "cosmosynapse" / "model" / "cosmos_model.py"
    config = ROOT / "cosmos" / "web" / "cosmosynapse" / "model" / "cosmos_config.py"
    trainer = ROOT / "scripts" / "train_12d_brain.py"

    targets = [web_init, model, config, trainer]
    before = {str(p.relative_to(ROOT)): sha256(p) for p in targets}

    replace_once(
        web_init,
        '"""\ncosmos Web Interface\nToken-gated chat with glassmorphism UI\n"""\n\nfrom .server import app, main\n\n__all__ = ["app", "main"]\n',
        '"""\ncosmos Web Interface.\n\nWeb-server objects are loaded lazily so model/library imports do not require\nFastAPI or start importing the HTTP stack as a side effect.\n"""\n\n__all__ = ["app", "main"]\n\n\ndef __getattr__(name):\n    if name in {"app", "main"}:\n        from .server import app, main\n        return {"app": app, "main": main}[name]\n    raise AttributeError(name)\n',
        "decouple model import from web extras",
    )

    replace_once(
        model,
        '        # Build 12D phase vector: interleave sin/cos\n        phase_sin = torch.sin(phase_angles)\n        phase_cos = torch.cos(phase_angles)\n        phase_12d = torch.cat([phase_sin, phase_cos], dim=-1)  # [B, T, d_cst]\n',
        '        # Build 12D phase vector as six phase-conjugate sin/cos pairs.\n        phase_sin = torch.sin(phase_angles)\n        phase_cos = torch.cos(phase_angles)\n        phase_12d = torch.stack((phase_sin, phase_cos), dim=-1).flatten(-2)  # [B, T, d_cst]\n',
        "restore paired CST coordinate order",
    )

    replace_once(
        model,
        '    Seven coupled Lorenz attractors (each 3D) produce deterministic chaos\n    that is injected into the residual stream. This prevents mode collapse\n    and encourages creative, non-repetitive generation.\n\n    Total chaos dims: 7 oscillators × 3D = 21D (truncated to 18D)\n',
        '    Six coupled Lorenz attractors (each 3D) produce deterministic chaos\n    that is injected into the residual stream. This prevents mode collapse\n    and encourages creative, non-repetitive generation.\n\n    Default chaos dims: 6 oscillators × 3D = 18D. No coordinates are silently truncated.\n',
        "correct chaos documentation",
    )

    replace_once(
        model,
        '    def __init__(self, n_oscillators: int = 7, d_model: int = 512,\n',
        '    def __init__(self, n_oscillators: int = 6, d_model: int = 512,\n',
        "make standalone chaos default 18D",
    )

    replace_once(
        model,
        '        self.d_chaos = n_oscillators * 3  # 21D for 7 oscillators\n',
        '        self.d_chaos = n_oscillators * 3\n',
        "remove stale 21D comment",
    )

    replace_once(
        model,
        '        self.chaos_proj = nn.Linear(18, d_model, bias=False)  # Use 18D (6 oscillators × 3)\n',
        '        self.chaos_proj = nn.Linear(self.d_chaos, d_model, bias=False)\n',
        "project the full declared chaos state",
    )

    replace_once(
        model,
        '        # Use last state as the chaos injection\n        chaos_flat = state.reshape(B, -1)  # [B, n_osc * 3]\n        chaos_18d = chaos_flat[:, :18]  # Truncate to 18D\n\n        # Project to model dim and gate\n        chaos_signal = self.chaos_proj(chaos_18d)  # [B, D]\n',
        '        # Use the full last oscillator state as the chaos injection.\n        # CosmosConfig enforces 6 × 3 = 18 dimensions for the 54D model.\n        chaos_18d = state.reshape(B, -1)  # [B, n_osc * 3]\n\n        # Project to model dim and gate\n        chaos_signal = self.chaos_proj(chaos_18d)  # [B, D]\n',
        "remove hidden chaos truncation",
    )

    replace_once(
        model,
        '        # Expand memory for batch\n        mem = self.memory.expand(B, -1, -1)  # [B, M, D]\n',
        '        # Read from an immutable snapshot for this differentiable forward.\n        # The persistent buffer is updated later under no_grad; cloning prevents\n        # that in-place write from invalidating tensors saved by autograd.\n        memory_snapshot = self.memory.detach().clone()\n        mem = memory_snapshot.expand(B, -1, -1)  # [B, M, D]\n',
        "separate differentiable memory read from persistent write",
    )

    replace_once(
        config,
        '  18D — Chaos oscillator state (7 Lorenz + 4 Rössler attractors × 3D each)\n',
        '  18D — Chaos oscillator state (6 coupled Lorenz attractors × 3D each)\n',
        "correct config dimension provenance",
    )

    replace_once(
        config,
        '        assert self.n_chaos_oscillators * 3 <= self.d_chaos, \\\n            f"n_chaos_oscillators * 3 ({self.n_chaos_oscillators * 3}) must fit in d_chaos ({self.d_chaos})"\n',
        '        assert self.n_chaos_oscillators * 3 == self.d_chaos, \\\n            f"n_chaos_oscillators * 3 ({self.n_chaos_oscillators * 3}) must equal d_chaos ({self.d_chaos})"\n',
        "make chaos dimensionality exact",
    )

    replace_once(
        trainer,
        'from Cosmos.web.cosmosynapse.model.cosmos_config import CosmosConfig\nfrom Cosmos.web.cosmosynapse.model.cosmos_model import CosmosTransformer\n',
        'from cosmos.web.cosmosynapse.model.cosmos_config import CosmosConfig\nfrom cosmos.web.cosmosynapse.model.cosmos_model import CosmosTransformer\n',
        "fix case-sensitive package imports",
    )

    replace_once(
        trainer,
        'CHECKPOINT_DIR = os.path.join(PROJECT_ROOT, "Cosmos", "checkpoints", "cosmos")\n',
        'CHECKPOINT_DIR = os.path.join(PROJECT_ROOT, "cosmos", "checkpoints", "cosmos")\n',
        "fix case-sensitive checkpoint path",
    )

    replace_once(
        trainer,
        '    # 5. Training Loop using 12D Hebbian Plasticity (No-Grad Online Meta-Learning)\n    epochs = 1 \n    total_steps = len(dataloader) * epochs\n    print(f"\\n[12D COMPILER] Commencing Zero-Shot Hebbian & Episodic Storage ({epochs} Epoch, {total_steps} sequence strides)")\n\n    model.eval()  # We leverage the internal Hebbian logic and Memory banks instead of Autograd!\n    step = 0\n    start_time = time.time()\n    \n    try:\n        with torch.no_grad():  # Crucial! Exploits the 12D online plasticity without triggering inplace-gradient crashes!\n            for epoch in range(epochs):\n                for batch_idx, (x, y) in enumerate(dataloader):\n                    x, y = x.to(device), y.to(device)\n                    \n                    # Forward pass updates the 24D self.trace and Episodic memory slots autonomously\n                    result = model(x, targets=y)\n                    loss = result["loss"]\n                    \n                    step += 1\n                    if step % 25 == 0 or step == 1:\n                        elapsed = time.time() - start_time\n                        print(f" [HEBBIAN SYNTHESIS] Step {step}/{total_steps} | Online Coherence: {loss.item():.4f} | Time: {elapsed:.1f}s")\n                    \n',
        '    # 5. Hybrid training: gradient learning + online Hebbian/memory state updates\n    epochs = 1\n    total_steps = len(dataloader) * epochs\n    print(f"\\n[12D COMPILER] Commencing gradient + online-plasticity training ({epochs} Epoch, {total_steps} sequence strides)")\n\n    model.train()\n    step = 0\n    start_time = time.time()\n    \n    try:\n        for epoch in range(epochs):\n            for batch_idx, (x, y) in enumerate(dataloader):\n                x, y = x.to(device), y.to(device)\n\n                optimizer.zero_grad(set_to_none=True)\n                # Forward still updates the online Hebbian, memory, and chaos buffers.\n                result = model(x, targets=y)\n                loss = result["loss"]\n                loss.backward()\n                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)\n                optimizer.step()\n\n                step += 1\n                if step % 25 == 0 or step == 1:\n                    elapsed = time.time() - start_time\n                    print(f" [HEBBIAN SYNTHESIS] Step {step}/{total_steps} | Loss: {loss.item():.4f} | Time: {elapsed:.1f}s")\n\n',
        "restore optimizer-backed training",
    )

    replace_once(
        trainer,
        '        "tokens_processed": len(token_ids) * epochs\n',
        '        "tokens_processed": len(token_ids) * epochs,\n        "training_mode": "hybrid_gradient_plus_online_plasticity"\n',
        "record corrected training provenance",
    )

    after = {str(p.relative_to(ROOT)): sha256(p) for p in targets}
    for name in before:
        if before[name] == after[name]:
            raise RuntimeError(f"{name}: expected content change but hash is unchanged")
        print(f"[hash] {name}: {before[name]} -> {after[name]}")

    print("[repair] all guarded replacements applied")


if __name__ == "__main__":
    main()
