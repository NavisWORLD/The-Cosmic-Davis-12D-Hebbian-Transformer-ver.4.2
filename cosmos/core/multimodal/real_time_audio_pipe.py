"""
real_time_audio_pipe.py – Capture microphone audio, convert to frequency tokens in real time.

The pipeline runs in a background thread, reads raw audio from the default input device,
computes a short‑time Fourier transform (STFT) on each chunk, extracts the most energetic
frequency bins and maps them to symbolic tokens that can be fed to the 12D/42D models.

Design goals:
* Low latency – process ~50 ms frames.
* Minimal CPU impact – use numpy FFT, optional librosa for convenience.
* Thread‑safe – expose a ``deque`` that the training loop can poll each iteration.
* Configurable – sample rate, frame size, number of bins, token vocabulary.
"""

import threading
import time
import math
import numpy as np
import sounddevice as sd
from collections import deque
from typing import List, Dict, Tuple

# ---------------------------------------------------------------------------
# Configuration – tweak as needed
# ---------------------------------------------------------------------------
SAMPLE_RATE = 22050          # Hz – matches other audio modules
FRAME_DURATION = 0.05        # seconds per chunk (≈ 50 ms)
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION)
TOP_BINS = 16                # Number of frequency bins turned into tokens
TOKEN_VOCAB = [f"<freq_{i}>" for i in range(TOP_BINS)]
VOICE_MIN_HZ = 80.0
VOICE_MAX_HZ = 3000.0
AUTO_GAIN_TRIGGER = 0.1
AUTO_GAIN_MULTIPLIER = 2.5
WEIGHT_RMS = 0.4
WEIGHT_CENTROID = 0.4
WEIGHT_FLATNESS = 0.2

def magnitudes_to_tokens(mags: np.ndarray) -> list[str]:
    if mags.size == 0:
        return []
    top_idx = np.argpartition(mags, -TOP_BINS)[-TOP_BINS:]
    top_idx = top_idx[np.argsort(-mags[top_idx])]
    tokens = [TOKEN_VOCAB[i % len(TOKEN_VOCAB)] for i in top_idx]
    return tokens

class RealTimeAudioPipe:
    """Capture microphone audio and expose a rolling token buffer."""
    def __init__(self):
        self._running = threading.Event()
        self._buffer = deque(maxlen=1024)
        self._token_buffer = deque(maxlen=4096)
        self._latest_lock = threading.Lock()
        self._token_lock = threading.Lock()
        self._stream_lock = threading.Lock()
        self._latest_event = None
        self._latest_event_at = 0.0
        self._last_chunk_at = 0.0
        self._last_error = None
        self._thread = None
        self._stream = None

    def start(self):
        with self._stream_lock:
            if self._running.is_set() and self._thread and self._thread.is_alive():
                return

            self._last_error = None
            self._running.set()

            try:
                self._stream = sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype="float32",
                    blocksize=FRAME_SIZE,
                    callback=self._audio_callback,
                )
                self._stream.start()
                self._thread = threading.Thread(target=self._worker, daemon=True)
                self._thread.start()
            except Exception as exc:
                self._last_error = str(exc)
                self._running.clear()
                if self._stream:
                    try:
                        self._stream.close()
                    except Exception:
                        pass
                self._stream = None
                self._thread = None
                raise

    def stop(self):
        with self._stream_lock:
            self._running.clear()
            stream = self._stream
            self._stream = None
            thread = self._thread
            self._thread = None

        if stream:
            try:
                stream.stop()
            except Exception:
                pass
            try:
                stream.close()
            except Exception:
                pass

        if thread and thread.is_alive():
            thread.join(timeout=1.0)

    def pop_tokens(self) -> list[str]:
        with self._token_lock:
            tokens = list(self._token_buffer)
            self._token_buffer.clear()
        return [dict(token) if isinstance(token, dict) else token for token in tokens]

    def snapshot_tokens(self, limit: int | None = None) -> list[Dict]:
        """Return a copy of recent tokens without consuming the buffer."""
        with self._token_lock:
            tokens = list(self._token_buffer)

        if limit and limit > 0:
            tokens = tokens[-limit:]

        return [dict(token) if isinstance(token, dict) else token for token in tokens]

    def get_latest_event(self) -> Dict | None:
        """Return the latest structured audio event without consuming the queue."""
        with self._latest_lock:
            if not isinstance(self._latest_event, dict):
                return None
            return dict(self._latest_event)

    def get_status(self, max_idle_seconds: float = 2.0) -> Dict:
        """Return a lightweight health snapshot for the microphone stream."""
        now = time.time()
        latest_activity = max(self._latest_event_at, self._last_chunk_at)
        latest_age = (now - latest_activity) if latest_activity else None
        thread_alive = bool(self._thread and self._thread.is_alive())
        stream_active = self._stream is not None
        healthy = bool(
            self._running.is_set()
            and thread_alive
            and stream_active
            and (latest_age is None or latest_age <= max_idle_seconds)
        )
        return {
            "running": self._running.is_set(),
            "thread_alive": thread_alive,
            "stream_active": stream_active,
            "latest_activity_age": latest_age,
            "last_error": self._last_error,
            "healthy": healthy,
        }

    def _audio_callback(self, indata, frames, time_info, status):
        if not self._running.is_set():
            return
        if status:
            self._last_error = str(status)
        audio_chunk = indata[:, 0].copy()
        self._buffer.append(audio_chunk)
        self._last_chunk_at = time.time()

    def _worker(self):
        phi = 1.618033988749895
        
        while self._running.is_set():
            try:
                if not self._buffer:
                    time.sleep(0.01)
                    continue
                chunk = self._buffer.popleft()
                
                # --- 1. TIME DOMAIN METRICS ---
                rms_raw = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
                # Scale RMS by 10 to match the 12D HTML frontend visualization
                rms_energy = rms_raw * 10.0
                rms_normalized = rms_raw
                if rms_normalized < AUTO_GAIN_TRIGGER:
                    rms_normalized *= AUTO_GAIN_MULTIPLIER
                rms_normalized = min(1.0, rms_normalized * 3.0)
                
                # --- 2. FREQUENCY DOMAIN (FFT) ---
                windowed = chunk * np.hanning(len(chunk))
                # Normalize spectrum to true amplitude [0, 1] range rather than scaling with N
                spectrum = np.abs(np.fft.rfft(windowed)) / (len(chunk) / 2.0)
                freqs = np.fft.rfftfreq(len(chunk), d=1/SAMPLE_RATE)
                
                # --- 3. SPECTRAL CENTROID ---
                weighted_sum = np.sum(freqs * spectrum)
                magnitude_sum = np.sum(spectrum)
                centroid = float(weighted_sum / magnitude_sum) if magnitude_sum > 0 else 0.0

                voice_mask = (freqs >= VOICE_MIN_HZ) & (freqs <= VOICE_MAX_HZ)
                voice_spectrum = spectrum[voice_mask]
                voice_freqs = freqs[voice_mask]
                if voice_spectrum.size > 0 and float(np.sum(voice_spectrum)) > 1e-10:
                    voice_weighted_sum = np.sum(voice_freqs * voice_spectrum)
                    voice_magnitude_sum = np.sum(voice_spectrum)
                    voice_centroid = float(voice_weighted_sum / voice_magnitude_sum)
                    centroid_normalized = min(
                        1.0,
                        max(0.0, (voice_centroid - VOICE_MIN_HZ) / (VOICE_MAX_HZ - VOICE_MIN_HZ)),
                    )
                    geometric_mean = float(np.exp(np.mean(np.log(voice_spectrum + 1e-10))))
                    arithmetic_mean = float(np.mean(voice_spectrum))
                    spectral_flatness = min(1.0, geometric_mean / (arithmetic_mean + 1e-10))
                else:
                    centroid_normalized = 0.5
                    spectral_flatness = 0.3

                audio_mass = (
                    WEIGHT_RMS * rms_normalized
                    + WEIGHT_CENTROID * centroid_normalized
                    + WEIGHT_FLATNESS * spectral_flatness
                )
                
                # --- 4. TOP 10 FREQUENCIES ---
                num_bins = min(10, len(spectrum))
                if num_bins > 0:
                    top_idx = np.argpartition(spectrum, -num_bins)[-num_bins:]
                    top_idx = top_idx[np.argsort(-spectrum[top_idx])]
                    
                    top_freqs = []
                    for idx in top_idx:
                        mag = float(spectrum[idx])
                        if mag > 0.001: # Lower noise floor filter, scaled for amplitude
                            top_freqs.append({
                                "frequency": float(freqs[idx]),
                                "magnitude": mag
                            })
                    
                    # --- 5. PHI-HARMONICS (Golden Ratio Resonance) ---
                    harmonics = []
                    if len(top_freqs) > 0:
                        fundamental = top_freqs[0]["frequency"]
                        if fundamental > 0:
                            for n in range(1, 9):
                                h_freq = fundamental * math.pow(phi, n / 2.0)
                                harmonics.append(float(h_freq))
                    
                    # --- 6. TOKEN GENERATION ---
                    # Bundle the full acoustic state into a structured payload
                    token_payload = {
                        "timestamp": time.time(),
                        "sample_rate": SAMPLE_RATE,
                        "frame_size": FRAME_SIZE,
                        "rms_raw": rms_raw,
                        "rms_energy": rms_energy,
                        "rms_normalized": rms_normalized,
                        "spectral_centroid": centroid,
                        "spectral_centroid_normalized": centroid_normalized,
                        "spectral_flatness": spectral_flatness,
                        "audio_mass": audio_mass,
                        "top_frequencies": top_freqs,
                        "phi_harmonics": harmonics
                    }

                    # Push the structured token state instead of raw strings
                    with self._token_lock:
                        self._token_buffer.append(token_payload)
                    with self._latest_lock:
                        self._latest_event = dict(token_payload)
                        self._latest_event_at = token_payload["timestamp"]

                # Sleep a tiny bit to keep CPU usage low
                time.sleep(0.001)
            except Exception as exc:
                self._last_error = str(exc)
                time.sleep(0.05)

# ---------------------------------------------------------------------------
# Simple sanity‑check when run as a script
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    pipe = RealTimeAudioPipe()
    print("Starting real‑time audio capture – press Ctrl+C to stop")
    pipe.start()
    try:
        while True:
            toks = pipe.pop_tokens()
            if toks:
                print("Tokens:", toks)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("Stopping…")
        pipe.stop()

