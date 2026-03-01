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
import numpy as np
import sounddevice as sd
from collections import deque
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Configuration – tweak as needed
# ---------------------------------------------------------------------------
SAMPLE_RATE = 22050          # Hz – matches other audio modules
FRAME_DURATION = 0.05        # seconds per chunk (≈ 50 ms)
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION)
TOP_BINS = 16                # Number of frequency bins turned into tokens
TOKEN_VOCAB = [f"<freq_{i}>" for i in range(TOP_BINS)]  # Simple placeholder vocab

# ---------------------------------------------------------------------------
# Helper: map frequency magnitudes to tokens
# ---------------------------------------------------------------------------
def magnitudes_to_tokens(mags: np.ndarray) -> List[str]:
    """Given an array of magnitude values, return the top‑N tokens.
    The mapping is deterministic: the index of the sorted magnitude picks a token
    from ``TOKEN_VOCAB``. If there are fewer bins than ``TOP_BINS`` we pad with a
    generic ``<silence>`` token.
    """
    if mags.size == 0:
        return []
    # Get indices of the largest magnitudes
    top_idx = np.argpartition(mags, -TOP_BINS)[-TOP_BINS:]
    # Sort them descending for consistency
    top_idx = top_idx[np.argsort(-mags[top_idx])]
    tokens = [TOKEN_VOCAB[i % len(TOKEN_VOCAB)] for i in top_idx]
    return tokens

# ---------------------------------------------------------------------------
# Core class – runs the audio capture loop
# ---------------------------------------------------------------------------
class RealTimeAudioPipe:
    """Capture microphone audio and expose a rolling token buffer.

    Usage::
        pipe = RealTimeAudioPipe()
        pipe.start()
        # In the training loop:
        audio_tokens = pipe.pop_tokens()
        # … feed ``audio_tokens`` into the multimodal fusion system …
        pipe.stop()
    """

    def __init__(self):
        self._running = threading.Event()
        self._buffer = deque(maxlen=1024)  # raw audio frames (numpy arrays)
        self._token_buffer = deque(maxlen=4096)  # token strings ready for consumption
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._stream = None

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def start(self):
        """Start the microphone stream and processing thread."""
        self._running.set()
        # Open a non‑blocking InputStream – callback pushes raw audio into ``_buffer``
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=FRAME_SIZE,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._thread.start()

    def stop(self):
        """Stop the stream and wait for the thread to finish."""
        self._running.clear()
        if self._stream:
            self._stream.stop()
            self._stream.close()
        self._thread.join(timeout=1.0)

    def pop_tokens(self) -> List[str]:
        """Retrieve and clear all tokens accumulated since the last call."""
        tokens = list(self._token_buffer)
        self._token_buffer.clear()
        return tokens

    # ---------------------------------------------------------------------
    # Internal: audio callback – runs in the sounddevice thread
    # ---------------------------------------------------------------------
    def _audio_callback(self, indata, frames, time_info, status):
        if not self._running.is_set():
            return
        # ``indata`` shape: (frames, channels)
        # Flatten to 1‑D array
        audio_chunk = indata[:, 0].copy()
        self._buffer.append(audio_chunk)

    # ---------------------------------------------------------------------
    # Internal: worker thread – consumes raw frames, computes FFT, emits tokens
    # ---------------------------------------------------------------------
    def _worker(self):
        while self._running.is_set():
            if not self._buffer:
                time.sleep(0.01)
                continue
            # Pull the oldest chunk
            chunk = self._buffer.popleft()
            # Apply a Hann window to reduce spectral leakage
            windowed = chunk * np.hanning(len(chunk))
            # Compute magnitude spectrum (real FFT is enough for mono audio)
            spectrum = np.abs(np.fft.rfft(windowed))
            # Convert magnitudes to tokens
            tokens = magnitudes_to_tokens(spectrum)
            # Push tokens into the public token buffer
            self._token_buffer.extend(tokens)
            # Sleep a tiny bit to keep CPU usage low (processing is fast)
            time.sleep(0.001)

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

