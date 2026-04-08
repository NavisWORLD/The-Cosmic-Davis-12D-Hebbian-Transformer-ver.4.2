"""
Compatibility helpers for live sensory payloads.

The option-2 runner talks to multiple versions of the emotional API:
- Full CST packets returned directly from `EmotionalStateAPI.get_state()`
- Wrapped `{"cosmos_packet": ...}` payloads returned by virtual embodiment

This adapter normalizes both shapes into one additive schema so existing
consumers can safely read the live packet without losing any original fields.
"""

from __future__ import annotations

from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp01(value: Any, default: float = 0.0) -> float:
    numeric = _as_float(value, default)
    if numeric < 0.0:
        return 0.0
    if numeric > 1.0:
        return 1.0
    return numeric


def normalize_live_bio_state(payload: dict[str, Any] | None) -> dict[str, Any]:
    """
    Normalize live sensory payloads into a stable additive schema.

    The returned dict preserves the original packet data while adding:
    - top-level `cst_physics`, `spectral_physics`, `derived_state`, `meta_instruction`
    - flattened legacy aliases like `frequency_mass`, `geometric_phase`, `emotion_state`
    - `bio_signatures` for older swarm components
    """
    if not isinstance(payload, dict):
        return {}

    normalized = dict(payload)

    packet = _as_dict(payload.get("cosmos_packet"))
    if not packet:
        packet = payload

    header = _as_dict(packet.get("header")) or _as_dict(payload.get("header"))
    cst_physics = _as_dict(packet.get("cst_physics")) or _as_dict(payload.get("cst_physics"))
    spectral_physics = _as_dict(packet.get("spectral_physics")) or _as_dict(payload.get("spectral_physics"))
    cross_modal = _as_dict(packet.get("cross_modal")) or _as_dict(payload.get("cross_modal"))
    derived_state = _as_dict(packet.get("derived_state")) or _as_dict(payload.get("derived_state"))
    meta_instruction = _as_dict(packet.get("meta_instruction")) or _as_dict(payload.get("meta_instruction"))

    pad_vector = derived_state.get("pad_vector")
    if isinstance(pad_vector, dict):
        valence = _as_float(pad_vector.get("pleasure"), 0.0)
        arousal = _as_float(pad_vector.get("arousal"), 0.0)
        dominance = _as_float(pad_vector.get("dominance"), 0.0)
    elif isinstance(pad_vector, (list, tuple)):
        values = list(pad_vector) + [0.0, 0.0, 0.0]
        valence = _as_float(values[0], 0.0)
        arousal = _as_float(values[1], 0.0)
        dominance = _as_float(values[2], 0.0)
    else:
        virtual_body = _as_dict(cst_physics.get("virtual_body"))
        valence = _as_float(derived_state.get("pleasure"), 0.0)
        arousal = _as_float(derived_state.get("arousal"), _as_float(virtual_body.get("arousal"), 0.0))
        dominance = _as_float(derived_state.get("dominance"), 0.0)

    emotion = (
        derived_state.get("primary_affect_label")
        or derived_state.get("emotion")
        or payload.get("emotion")
        or payload.get("emotion_state")
        or "UNKNOWN"
    )

    informational_mass = _as_float(
        derived_state.get("informational_mass"),
        _as_float(payload.get("informational_mass"), 0.0),
    )
    if informational_mass <= 0.0:
        informational_mass = _as_float(spectral_physics.get("audio_psi"), 0.0)

    intensity = max(_clamp01(abs(arousal), 0.0), _clamp01(informational_mass / 100.0, 0.0))

    normalized.update(
        {
            "header": header,
            "timestamp_utc": payload.get("timestamp_utc") or header.get("timestamp_utc"),
            "sequence_id": payload.get("sequence_id") or header.get("sequence_id"),
            "session_id": payload.get("session_id") or header.get("session_id"),
            "source": payload.get("source") or packet.get("source"),
            "cst_physics": cst_physics,
            "spectral_physics": spectral_physics,
            "cross_modal": cross_modal,
            "derived_state": derived_state,
            "meta_instruction": meta_instruction,
            "virtual_body": _as_dict(cst_physics.get("virtual_body")) or _as_dict(payload.get("virtual_body")),
            "frequency_mass": _as_float(
                payload.get("frequency_mass"),
                _as_float(
                    payload.get("freq_mass"),
                    _as_float(
                        spectral_physics.get("audio_psi"),
                        informational_mass,
                    ),
                ),
            ),
            "freq_mass": _as_float(
                payload.get("freq_mass"),
                _as_float(
                    payload.get("frequency_mass"),
                    _as_float(
                        spectral_physics.get("audio_psi"),
                        informational_mass,
                    ),
                ),
            ),
            "geometric_phase": _as_float(
                payload.get("geometric_phase"),
                _as_float(
                    payload.get("geo_phase"),
                    _as_float(cst_physics.get("geometric_phase_rad"), 0.0),
                ),
            ),
            "geo_phase": _as_float(
                payload.get("geo_phase"),
                _as_float(
                    payload.get("geometric_phase"),
                    _as_float(cst_physics.get("geometric_phase_rad"), 0.0),
                ),
            ),
            "spectral_flatness": _as_float(
                payload.get("spectral_flatness"),
                _as_float(spectral_physics.get("spectral_flatness"), 0.0),
            ),
            "entanglement": _as_float(
                payload.get("entanglement"),
                _as_float(cst_physics.get("entanglement_score"), 0.0),
            ),
            "emotion": emotion,
            "emotion_state": emotion,
            "valence": valence,
            "arousal": arousal,
            "dominance": dominance,
            "bio_signatures": {
                "emotion": emotion,
                "intensity": intensity,
                "valence": valence,
                "arousal": arousal,
                "dominance": dominance,
            },
        }
    )

    return normalized
