from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import subprocess
import sys
import types

import torch

ROOT = Path(__file__).resolve().parents[1]
TRAIN_SCRIPT = ROOT / "scripts" / "train_12d_brain.py"
MODEL_DIR = ROOT / "cosmos" / "web" / "cosmosynapse" / "model"


def _called_methods(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            names.add(node.func.attr)
    return names


def _load_12d_model_isolated():
    """Load the model files without executing cosmos.web.__init__."""
    package_paths = {
        "cosmos": ROOT / "cosmos",
        "cosmos.web": ROOT / "cosmos" / "web",
        "cosmos.web.cosmosynapse": ROOT / "cosmos" / "web" / "cosmosynapse",
        "cosmos.web.cosmosynapse.model": MODEL_DIR,
    }
    for name, path in package_paths.items():
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module

    config_name = "cosmos.web.cosmosynapse.model.cosmos_config"
    config_spec = importlib.util.spec_from_file_location(config_name, MODEL_DIR / "cosmos_config.py")
    assert config_spec and config_spec.loader
    config_mod = importlib.util.module_from_spec(config_spec)
    sys.modules[config_name] = config_mod
    config_spec.loader.exec_module(config_mod)

    model_name = "cosmos.web.cosmosynapse.model.cosmos_model"
    model_spec = importlib.util.spec_from_file_location(model_name, MODEL_DIR / "cosmos_model.py")
    assert model_spec and model_spec.loader
    model_mod = importlib.util.module_from_spec(model_spec)
    sys.modules[model_name] = model_mod
    model_spec.loader.exec_module(model_mod)
    return config_mod, model_mod


def _small_model():
    config_mod, model_mod = _load_12d_model_isolated()
    cfg = config_mod.CosmosConfig(
        vocab_size=64,
        d_model=24,
        n_layers=1,
        n_heads=4,
        d_ff=48,
        max_seq_len=8,
        dropout=0.0,
    )
    cfg.validate()
    return cfg, model_mod.CosmosTransformer(cfg)


def test_model_import_does_not_require_web_server_extras() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cosmos.web.cosmosynapse.model.cosmos_model import CosmosTransformer; print(CosmosTransformer.__name__)",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


def test_cst_phase_coordinates_are_interleaved_sin_cos_pairs() -> None:
    _, model_mod = _load_12d_model_isolated()
    enc = model_mod.CSTPhaseEncoding(d_model=8, d_cst=12)
    with torch.no_grad():
        enc.phase_proj.weight.zero_()

    x = torch.zeros(1, 1, 8)
    positions = torch.tensor([[1]])
    _, state = enc(x, positions=positions)

    pairs = []
    for frequency in enc.freqs:
        pairs.extend((torch.sin(frequency), torch.cos(frequency)))
    expected = 0.5 * torch.stack(pairs).reshape(1, 1, 12)

    assert state.shape == (1, 1, 12)
    assert torch.allclose(state, expected, atol=1e-7), (
        "CST 12D coordinate order must preserve six sin/cos phase pairs"
    )


def test_chaos_bank_default_has_no_hidden_truncation() -> None:
    _, model_mod = _load_12d_model_isolated()
    bank = model_mod.ChaosOscillatorBank(d_model=8)
    assert bank.n_osc * 3 == bank.chaos_proj.in_features, (
        "chaos source dimensionality must equal the projected dimensionality; "
        "do not silently create 21D and truncate to 18D"
    )


def test_training_script_uses_real_lowercase_package_path() -> None:
    source = TRAIN_SCRIPT.read_text(encoding="utf-8")
    assert "from Cosmos." not in source
    assert '"Cosmos", "checkpoints"' not in source


def test_training_script_performs_optimizer_training() -> None:
    source = TRAIN_SCRIPT.read_text(encoding="utf-8")
    methods = _called_methods(source)
    assert "backward" in methods, "training loop never backpropagates the language-model loss"
    assert "step" in methods, "optimizer is constructed but never stepped"


def test_one_gradient_step_reaches_and_updates_cst_parameters() -> None:
    _, model = _small_model()
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    x = torch.tensor([[1, 2, 3, 4]], dtype=torch.long)
    y = torch.tensor([[2, 3, 4, 5]], dtype=torch.long)

    before = model.blocks[0].cst_phase.phase_proj.weight.detach().clone()
    optimizer.zero_grad(set_to_none=True)
    loss = model(x, targets=y)["loss"]
    loss.backward()
    grad = model.blocks[0].cst_phase.phase_proj.weight.grad

    assert grad is not None
    assert torch.isfinite(grad).all()
    assert grad.abs().sum().item() > 0.0
    optimizer.step()
    after = model.blocks[0].cst_phase.phase_proj.weight.detach()
    assert not torch.equal(before, after)


def test_executable_state_is_exactly_12_plus_24_plus_18() -> None:
    cfg, model = _small_model()
    model.eval()
    tokens = torch.tensor([[1, 2, 3, 4]], dtype=torch.long)
    result = model(tokens)
    state = result["state_54d"]

    assert state.shape == (1, 54)
    assert state[:, :12].shape[-1] == 12
    assert state[:, 12:36].shape[-1] == 24
    assert state[:, 36:54].shape[-1] == 18
    assert cfg.n_chaos_oscillators * 3 == cfg.d_chaos
