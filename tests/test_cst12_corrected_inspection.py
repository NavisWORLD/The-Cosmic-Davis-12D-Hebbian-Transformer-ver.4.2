from __future__ import annotations

import ast
from pathlib import Path

import torch

from cosmos.web.cosmosynapse.model.cosmos_config import CosmosConfig
from cosmos.web.cosmosynapse.model.cosmos_model import (
    CSTPhaseEncoding,
    ChaosOscillatorBank,
    CosmosTransformer,
)

ROOT = Path(__file__).resolve().parents[1]
TRAIN_SCRIPT = ROOT / "scripts" / "train_12d_brain.py"


def _called_methods(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            names.add(node.func.attr)
    return names


def test_cst_phase_coordinates_are_interleaved_sin_cos_pairs() -> None:
    enc = CSTPhaseEncoding(d_model=8, d_cst=12)
    with torch.no_grad():
        enc.phase_proj.weight.zero_()

    x = torch.zeros(1, 1, 8)
    positions = torch.tensor([[1]])
    _, state = enc(x, positions=positions)

    pairs = []
    for frequency in enc.freqs:
        angle = frequency
        pairs.extend((torch.sin(angle), torch.cos(angle)))
    expected = 0.5 * torch.stack(pairs).reshape(1, 1, 12)

    assert state.shape == (1, 1, 12)
    assert torch.allclose(state, expected, atol=1e-7), (
        "CST 12D coordinate order must preserve six sin/cos phase pairs"
    )


def test_chaos_bank_default_has_no_hidden_truncation() -> None:
    bank = ChaosOscillatorBank(d_model=8)
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


def test_executable_state_is_exactly_12_plus_24_plus_18() -> None:
    cfg = CosmosConfig(
        vocab_size=64,
        d_model=24,
        n_layers=1,
        n_heads=4,
        d_ff=48,
        max_seq_len=8,
        dropout=0.0,
    )
    cfg.validate()
    model = CosmosTransformer(cfg).eval()
    tokens = torch.tensor([[1, 2, 3, 4]], dtype=torch.long)
    result = model(tokens)
    state = result["state_54d"]

    assert state.shape == (1, 54)
    assert state[:, :12].shape[-1] == 12
    assert state[:, 12:36].shape[-1] == 24
    assert state[:, 36:54].shape[-1] == 18
    assert cfg.n_chaos_oscillators * 3 == cfg.d_chaos
