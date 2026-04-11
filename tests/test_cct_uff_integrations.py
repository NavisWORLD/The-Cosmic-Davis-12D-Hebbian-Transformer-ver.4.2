"""
Smoke test for the CCT-UFF Critical Integrations module + planetary memory
+ Cosmos 12D/54D model.

Run from the worktree root:
    python tests/test_cct_uff_integrations.py
"""

from __future__ import annotations

import importlib.util
import math
import sys
import traceback
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_file(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {rel_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # required for dataclass type resolution
    spec.loader.exec_module(module)
    return module


PASS = "[PASS]"
FAIL = "[FAIL]"
results: list[tuple[str, bool, str]] = []


def check(name: str, fn):
    try:
        fn()
        results.append((name, True, ""))
        print(f"{PASS} {name}")
    except Exception as e:  # pragma: no cover
        results.append((name, False, f"{type(e).__name__}: {e}"))
        print(f"{FAIL} {name} -> {type(e).__name__}: {e}")
        traceback.print_exc()


# ---------------------------------------------------------------------------
# 1. Load the new module directly to avoid heavy package __init__ side-effects
# ---------------------------------------------------------------------------
cct = _load_file(
    "cct_uff_integrations",
    "cosmos/web/cosmosynapse/engine/cct_uff_integrations.py",
)


# ---------------------------------------------------------------------------
# Integration 1 — Coherence conservation
# ---------------------------------------------------------------------------
def t_conservation():
    b, c = 1.0, 0.0
    total_initial = b + c
    for _ in range(1000):
        b, c = cct.coherence_conservation_step(b, c, dt=0.001)
    assert abs((b + c) - total_initial) < 1e-6, f"Total drifted: {b+c}"
    assert b < 1.0 and c > 0.0, "No transfer occurred"


check("Integration 1 — Coherence conservation law", t_conservation)


# ---------------------------------------------------------------------------
# Integration 2 — Hysteresis gate
# ---------------------------------------------------------------------------
def t_hysteresis():
    gate = cct.HysteresisGate()
    assert gate.update(0.030) is False
    assert gate.update(0.050) is True   # collapses past 0.048
    assert gate.update(0.040) is True   # still collapsed (above 0.037)
    assert gate.update(0.036) is False  # recovered below 0.037
    assert gate.update(0.045) is False  # below collapse threshold


check("Integration 2 — Phase transition hysteresis gap", t_hysteresis)


# ---------------------------------------------------------------------------
# Integration 3 — Fold-Onset Triplet
# ---------------------------------------------------------------------------
def t_fot():
    fot = cct.FoldOnsetTriplet()
    fot.push(0.10, 0.90, 0.20)
    fot.push(0.15, 0.85, 0.25)  # Δλ2 +, ΔID -, Δζ +  → fire
    assert fot.fot_active() is True
    fot.push(0.10, 0.90, 0.20)  # reverse
    assert fot.fot_active() is False


check("Integration 3 — Fold-Onset Triplet predictor", t_fot)


# ---------------------------------------------------------------------------
# Integration 4 — Spectral radius
# ---------------------------------------------------------------------------
def t_spectral():
    stable = np.array([[0.5, 0.1], [0.1, 0.4]])
    unstable = np.array([[1.5, 0.0], [0.0, 0.9]])
    assert cct.spectral_radius(stable) < 1.0
    assert cct.spectral_radius(unstable) > 1.0


check("Integration 4 — Spectral radius companion metric", t_spectral)


# ---------------------------------------------------------------------------
# Integration 5 — Enhanced Lorenz
# ---------------------------------------------------------------------------
def t_lorenz():
    state = np.array([0.1, 0.0, 0.0])
    for _ in range(50):
        state = cct.enhanced_lorenz_step(
            state,
            omega_net=0.5,
            x12=0.3,
            x12_baseline=0.1,
            laplacian_epsilon=0.05,
            ci_b=0.7,
        )
    assert np.all(np.isfinite(state)), f"Lorenz blew up: {state}"


check("Integration 5 — Enhanced Lorenz with network coupling", t_lorenz)


# ---------------------------------------------------------------------------
# Integration 6 — Global mean-field coherence
# ---------------------------------------------------------------------------
def t_meanfield():
    cohs = [0.4, 0.5, 0.6, 0.7]
    nudged = cct.global_mean_field_nudge(cohs, nudge_strength=0.01)
    assert all(n >= c for n, c in zip(nudged, cohs)), "Nudge should be non-negative"
    assert all(n <= 1.0 for n in nudged)


check("Integration 6 — Global mean-field coherence coupling", t_meanfield)


# ---------------------------------------------------------------------------
# Integration 7 — Mahalanobis collapse distance
# ---------------------------------------------------------------------------
def t_mahalanobis():
    rng = np.random.default_rng(42)
    collapse_states = rng.normal(loc=0.0, scale=1.0, size=(50, 4))
    model = cct.MahalanobisCollapseModel()
    model.fit(collapse_states)
    near = model.distance(np.zeros(4))
    far = model.distance(np.ones(4) * 5.0)
    assert far > near, f"Far ({far}) should exceed near ({near})"


check("Integration 7 — Mahalanobis collapse distance", t_mahalanobis)


# ---------------------------------------------------------------------------
# Integration 8 — Dynamic temperature
# ---------------------------------------------------------------------------
def t_temperature():
    sophia = cct.SOPHIA_POINT
    assert math.isclose(cct.dynamic_temperature(sophia), sophia, rel_tol=1e-9)
    assert cct.dynamic_temperature(0.2) > sophia
    assert cct.dynamic_temperature(0.95) <= cct.TEMPERATURE_MAX + 1e-9


check("Integration 8 — Dynamic temperature adaptation", t_temperature)


# ---------------------------------------------------------------------------
# Integration 9 — Triple-gate phase transition
# ---------------------------------------------------------------------------
def t_triple_gate():
    assert cct.triple_gate_phase_transition(
        coherence=0.618,
        paradox_intensity=2.0,
        dx12_dt=0.0005,
        omega_net=1.5,
    ) is True
    assert cct.triple_gate_phase_transition(
        coherence=0.618,
        paradox_intensity=0.5,  # fails paradox gate
        dx12_dt=0.0005,
        omega_net=1.5,
    ) is False


check("Integration 9 — Triple-gate phase transition", t_triple_gate)


# ---------------------------------------------------------------------------
# Integration 10 — Omega Point convergence ratio
# ---------------------------------------------------------------------------
def t_omega_point():
    target = cct.OMEGA_POINT_TARGET
    ratio = cct.omega_point_convergence(
        epsilon=target / 5.0,
        omega_net=target / 5.0,
        x12_avg=target / 5.0,
        ci_b=target / 5.0,
        ci_c=target / 5.0,
    )
    assert math.isclose(ratio, 1.0, rel_tol=1e-9)


check("Integration 10 — Omega Point convergence ratio", t_omega_point)


# ---------------------------------------------------------------------------
# Dashboard wiring (all 10 in one step)
# ---------------------------------------------------------------------------
def t_dashboard():
    dash = cct.CCTUFFDashboard()
    rng = np.random.default_rng(0)
    dash.mahalanobis.fit(rng.normal(size=(20, 3)))
    out = dash.step(
        sigma=0.05,
        coherence=0.618,
        lambda2=0.10,
        ideational_density=0.90,
        zeta=0.20,
        w_effective=np.array([[0.5, 0.1], [0.1, 0.4]]),
        agent_coherences=[0.4, 0.5, 0.6],
        paradox_intensity=2.0,
        dx12_dt=0.0005,
        omega_net=1.5,
        x12_avg=0.3,
        epsilon=0.2,
        state_vector=np.zeros(3),
    )
    for key in (
        "ci_b", "ci_c", "collapsed", "fot_active", "spectral_radius",
        "agent_coherences_nudged", "mahalanobis_distance",
        "dynamic_temperature", "true_phase_transition",
        "omega_convergence_ratio",
    ):
        assert key in out, f"Missing dashboard key: {key}"


check("CCTUFFDashboard — full integration step", t_dashboard)


# ---------------------------------------------------------------------------
# Planetary Memory smoke test
# ---------------------------------------------------------------------------
def t_planetary():
    akashic = _load_file(
        "akashic_test", "cosmos/core/memory/planetary/akashic.py"
    )
    audio_shard = _load_file(
        "audio_shard_test", "cosmos/core/memory/planetary/audio_shard.py"
    )
    assert hasattr(akashic, "MemoryScope")
    assert hasattr(akashic, "SkillVector")
    # Construct a minimal SkillVector to confirm dataclass is intact
    sv = akashic.SkillVector(
        id="test",
        problem_hash="abc",
        vector=[0.1, 0.2, 0.3],
        abstract_solution="restart the daemon",
    )
    assert sv.id == "test"
    pm = akashic.PlanetaryMemory()
    assert hasattr(pm, "local_skills")


check("Planetary Memory — akashic & audio_shard import", t_planetary)


# ---------------------------------------------------------------------------
# Cosmos 12D / 54D Model smoke test
# ---------------------------------------------------------------------------
def t_cosmos_model():
    cfg_mod = _load_file(
        "cosmos_config_test",
        "cosmos/web/cosmosynapse/model/cosmos_config.py",
    )
    cfg = cfg_mod.CosmosConfig()
    cfg.validate()
    assert cfg.d_state == 54
    assert cfg.d_cst == 12
    assert cfg.d_hebbian == 24
    assert cfg.d_chaos == 18
    # 12 + 24 + 18 = 54
    assert cfg.d_cst + cfg.d_hebbian + cfg.d_chaos == cfg.d_state

    # Try to load the heavy model module — degrade gracefully if torch is missing
    try:
        import torch  # noqa: F401
    except ImportError:
        print("    [info] torch unavailable — skipping heavy 54D forward test")
        return

    # cosmos_model.py uses `from .cosmos_config import CosmosConfig`, so we
    # must simulate a package. We do that by loading cosmos_config under a
    # synthetic parent package name and registering both in sys.modules.
    import types as _types
    pkg_name = "cosmos_model_pkg"
    pkg = _types.ModuleType(pkg_name)
    pkg.__path__ = [str(ROOT / "cosmos" / "web" / "cosmosynapse" / "model")]
    sys.modules[pkg_name] = pkg

    cfg_sub = _load_file(
        f"{pkg_name}.cosmos_config",
        "cosmos/web/cosmosynapse/model/cosmos_config.py",
    )
    pkg.cosmos_config = cfg_sub

    cm = _load_file(
        f"{pkg_name}.cosmos_model",
        "cosmos/web/cosmosynapse/model/cosmos_model.py",
    )

    assert hasattr(cm, "CSTPhaseEncoding")
    assert hasattr(cm, "HebbianPlasticityLayer")
    assert hasattr(cm, "CosmosTransformer")

    # CSTPhaseEncoding returns (modulated_x, phase_12d)
    cst_layer = cm.CSTPhaseEncoding(d_model=64, d_cst=12)
    x = torch.zeros(1, 4, 64)
    mod_x, phase_12d = cst_layer(x)
    assert mod_x.shape == x.shape
    assert phase_12d.shape == (1, 4, 12)
    print("    [info] CSTPhaseEncoding forward OK:", tuple(mod_x.shape), tuple(phase_12d.shape))

    # Hebbian effective_W accessor (new)
    heb = cm.HebbianPlasticityLayer(d_model=64, d_hebbian=24)
    W = heb.effective_W
    assert W.shape == (24, 24), f"effective_W shape wrong: {W.shape}"
    print("    [info] HebbianPlasticityLayer.effective_W shape:", tuple(W.shape))

    # Tiny end-to-end CosmosTransformer forward pass
    cfg = cfg_sub.CosmosConfig(
        vocab_size=64,
        d_model=64,
        n_layers=2,
        n_heads=4,
        d_ff=128,
        max_seq_len=32,
        memory_size=16,
        n_chaos_oscillators=6,
    )
    model = cm.CosmosTransformer(cfg)
    ids = torch.randint(0, 64, (1, 8))
    out = model(ids)
    assert "logits" in out and "state_54d" in out
    assert out["logits"].shape == (1, 8, 64)
    assert out["state_54d"].shape == (1, 54)
    print("    [info] CosmosTransformer forward OK; state_54d shape:", tuple(out["state_54d"].shape))
    # Stash for the CCT wiring test
    t_cosmos_model.model = model
    t_cosmos_model.cm = cm
    t_cosmos_model.cfg_sub = cfg_sub


check("Cosmos 12D/54D model config + (optional) forward", t_cosmos_model)


# ---------------------------------------------------------------------------
# CCT-UFF-wired generation: exercises all 4 integrations inside generate_cct()
# ---------------------------------------------------------------------------
def t_generate_cct():
    if not hasattr(t_cosmos_model, "model"):
        print("    [info] torch/model unavailable — skipping generate_cct test")
        return
    import torch
    model = t_cosmos_model.model
    cm = t_cosmos_model.cm

    # Fit Mahalanobis on some synthetic 54D "collapse states"
    fit_states = torch.randn(32, 54)

    prompt = torch.randint(0, 64, (1, 4))

    result = model.generate_cct(
        prompt_ids=prompt,
        max_new_tokens=6,
        base_temperature=None,  # force dynamic_temperature
        top_k=20,
        top_p=0.9,
        fit_collapse_states=fit_states,
        intervention_on_fot=True,
        verbose=False,
    )

    assert "ids" in result and "trace" in result
    assert result["ids"].shape[1] == prompt.shape[1] + 6, \
        f"Expected {prompt.shape[1] + 6} tokens, got {result['ids'].shape[1]}"
    assert len(result["trace"]) == 6

    # Every step must report all 4 integration outputs
    for rec in result["trace"]:
        for key in (
            "temperature", "coherence", "spectral_radius", "lambda_2",
            "collapsed", "fot_active", "mahalanobis_distance",
            "omega_convergence_ratio", "true_phase_transition",
        ):
            assert key in rec, f"Missing trace key: {key}"
        # Dynamic temperature must live in a sane range
        assert 0.0 < rec["temperature"] <= 1.0, \
            f"Temperature out of range: {rec['temperature']}"
        # Mahalanobis should produce a finite float (model was fit)
        assert rec["mahalanobis_distance"] is not None
        import math as _m
        assert _m.isfinite(rec["mahalanobis_distance"])

    print(
        f"    [info] generate_cct final dashboard: {result['final_dashboard']}"
    )
    print(
        f"    [info] temperature trajectory: "
        f"{[round(r['temperature'], 3) for r in result['trace']]}"
    )


check("generate_cct() — all 4 integrations wired into generation", t_generate_cct)


# ---------------------------------------------------------------------------
# Existing CST engine sanity (phi_constants, dark_matter_lorenz)
# ---------------------------------------------------------------------------
def t_existing_cst():
    phi = _load_file(
        "phi_constants_test",
        "cosmos/web/cosmosynapse/engine/phi_constants.py",
    )
    assert math.isclose(phi.PHI_INV, 0.6180339887, rel_tol=1e-6)
    # dark_matter_lorenz uses a relative import (.phi_constants); load it
    # as part of an artificial package so the relative import resolves.
    engine_dir = ROOT / "cosmos" / "web" / "cosmosynapse" / "engine"
    sys.path.insert(0, str(engine_dir))
    try:
        # Pre-register phi_constants under the bare name for the absolute fallback
        sys.modules.setdefault("phi_constants", phi)
        dm = _load_file(
            "dark_matter_lorenz_test",
            "cosmos/web/cosmosynapse/engine/dark_matter_lorenz.py",
        )
        lorenz = dm.DarkMatterLorenz()
        out = lorenz.update({"bio_signatures": {"intensity": 0.5}})
        assert all(k in out for k in ("x", "y", "z", "w", "q"))
    finally:
        sys.path.pop(0)


check("Existing CST engine (phi_constants + dark_matter_lorenz)", t_existing_cst)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
print()
print("=" * 60)
print(f" CCT-UFF Integration Test Summary: {passed}/{total} passed")
print("=" * 60)
for name, ok, err in results:
    flag = PASS if ok else FAIL
    line = f" {flag} {name}"
    if err:
        line += f"  ({err})"
    print(line)

sys.exit(0 if passed == total else 1)
