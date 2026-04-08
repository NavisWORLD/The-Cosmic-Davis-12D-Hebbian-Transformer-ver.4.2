"""
VISUAL ENGINE (12D VISUAL CORTEX)
==================================
Maps images to 12D embeddings using 2D Fourier Transform.
Images are spatial vibrations, just as audio is temporal vibrations.
"""

import numpy as np
from dataclasses import dataclass
import hashlib
import uuid
from datetime import datetime

PHI = 1.618033988749895
C = 299792458

# ============================================================================
# 2D FOURIER ANALYSIS
# ============================================================================

def compute_2d_fft(image):
    """
    Compute 2D FFT of image
    
    Args:
        image: numpy array, shape (H, W) for grayscale or (H, W, 3) for RGB
    
    Returns:
        frequencies_u, frequencies_v, magnitude, phase
    """
    # Convert to grayscale if RGB
    if len(image.shape) == 3:
        gray = 0.2989 * image[:,:,0] + 0.5870 * image[:,:,1] + 0.1140 * image[:,:,2]
    else:
        gray = image
    
    # 2D FFT
    fft_2d = np.fft.fft2(gray)
    fft_2d_shifted = np.fft.fftshift(fft_2d)
    
    # Magnitude and phase
    magnitude = np.abs(fft_2d_shifted)
    phase = np.angle(fft_2d_shifted)
    
    # Frequency grids
    H, W = gray.shape
    frequencies_u = np.fft.fftshift(np.fft.fftfreq(W))
    frequencies_v = np.fft.fftshift(np.fft.fftfreq(H))
    
    return frequencies_u, frequencies_v, magnitude, phase

def extract_dominant_spatial_frequency(magnitude):
    """Find dominant spatial frequency"""
    H, W = magnitude.shape
    center_h, center_w = H // 2, W // 2
    
    y, x = np.ogrid[:H, :W]
    distance_from_center = np.sqrt((x - center_w)**2 + (y - center_h)**2)
    
    total_power = np.sum(magnitude)
    if total_power == 0:
        return 0.0
    dominant_freq = np.sum(distance_from_center * magnitude) / total_power
    
    return dominant_freq

def visual_spectral_centroid(magnitude):
    """Center of mass of spatial frequency spectrum"""
    H, W = magnitude.shape
    y, x = np.mgrid[:H, :W]
    
    total_mag = np.sum(magnitude)
    if total_mag == 0:
        return 0.0
    
    centroid_x = np.sum(x * magnitude) / total_mag
    centroid_y = np.sum(y * magnitude) / total_mag
    
    center_x, center_y = W // 2, H // 2
    centroid_distance = np.sqrt((centroid_x - center_x)**2 + (centroid_y - center_y)**2)
    
    return centroid_distance

def visual_spectral_entropy(magnitude):
    """Shannon entropy of spatial frequency distribution"""
    power = magnitude ** 2
    total_power = np.sum(power)
    if total_power == 0:
        return 0.0
    
    prob = power / total_power
    entropy = -np.sum(prob * np.log2(prob + 1e-10))
    
    max_entropy = np.log2(prob.size)
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    
    return normalized_entropy

# ============================================================================
# COLOR AS FREQUENCY (φ-HARMONICS)
# ============================================================================

def rgb_to_frequency(rgb):
    """
    Map RGB color to frequency using visible light spectrum
    
    Red: ~430 THz (700 nm)
    Green: ~545 THz (550 nm)
    Blue: ~670 THz (450 nm)
    """
    red_freq = 430e12   # Hz
    green_freq = 545e12
    blue_freq = 670e12
    
    r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
    
    avg_freq = r * red_freq + g * green_freq + b * blue_freq
    
    return avg_freq

def frequency_to_rgb(freq):
    """Convert light frequency to RGB (approximate)"""
    freq_normalized = (freq - 430e12) / (770e12 - 430e12)
    freq_normalized = np.clip(freq_normalized, 0, 1)
    
    wavelength = 700 - freq_normalized * 250  # nm
    
    if wavelength >= 645:
        r, g, b = 1.0, 0.0, 0.0
    elif wavelength >= 590:
        r = 1.0
        g = (wavelength - 590) / 55
        b = 0.0
    elif wavelength >= 510:
        r = 1.0 - (wavelength - 510) / 80
        g = 1.0
        b = 0.0
    elif wavelength >= 490:
        r = 0.0
        g = 1.0
        b = (wavelength - 490) / 20
    elif wavelength >= 450:
        r = 0.0
        g = 1.0 - (wavelength - 450) / 40
        b = 1.0
    else:
        r, g, b = 0.0, 0.0, 1.0
    
    return np.array([int(r*255), int(g*255), int(b*255)])

def generate_phi_color_harmonics(base_color_rgb, num_harmonics=7):
    """Generate φ-harmonic color series"""
    base_freq = rgb_to_frequency(base_color_rgb)
    
    harmonics_freq = []
    for n in range(-num_harmonics//2, num_harmonics//2 + 1):
        harmonic_freq = base_freq * (PHI ** n)
        
        # Fold into visible spectrum
        while harmonic_freq > 770e12:
            harmonic_freq /= PHI
        while harmonic_freq < 430e12:
            harmonic_freq *= PHI
        
        harmonics_freq.append(harmonic_freq)
    
    harmonic_colors = [frequency_to_rgb(f) for f in harmonics_freq]
    
    return harmonic_colors

# ============================================================================
# 12D VISUAL EMBEDDING
# ============================================================================

@dataclass
class Visual12DEmbedding:
    """12-dimensional visual embedding"""
    D1_energy: float
    D2_mass: float
    D3_phi_coupling: float
    D4_chaos: float
    D5_vx: float
    D6_vy: float
    D7_vz: float
    D8_connectivity: float
    D9_cosmic_energy: float
    D10_entropy: float
    D11_frequency: float
    D12_x12: float
    
    # Additional features
    magnitude_spectrum: np.ndarray
    phase_spectrum: np.ndarray
    color_frequency: float
    phi_color_harmonics: list
    
    def to_vector(self):
        return np.array([
            self.D1_energy, self.D2_mass, self.D3_phi_coupling, self.D4_chaos,
            self.D5_vx, self.D6_vy, self.D7_vz, self.D8_connectivity,
            self.D9_cosmic_energy, self.D10_entropy, self.D11_frequency, self.D12_x12
        ])

def create_visual_12d_embedding(image):
    """Create 12D embedding from image"""
    # Compute 2D FFT
    freqs_u, freqs_v, magnitude, phase = compute_2d_fft(image)
    
    # D1: Energy (total pixel intensity)
    D1 = np.mean(image) / 255.0
    
    # D2: Mass-energy
    D2 = (PHI * D1) / (C ** 2) * 1e17
    
    # D3: Phi coupling
    D3 = PHI * D1
    
    # D4: Chaos (spectral entropy)
    D4 = visual_spectral_entropy(magnitude)
    
    # D5-D7: Spatial gradients (rate of change)
    gray = np.mean(image, axis=2) if len(image.shape) == 3 else image
    grad_x = np.gradient(gray, axis=1)
    grad_y = np.gradient(gray, axis=0)
    
    D5 = np.mean(np.abs(grad_x)) / 255.0
    D6 = np.mean(np.abs(grad_y)) / 255.0
    D7 = np.mean(np.sqrt(grad_x**2 + grad_y**2)) / 255.0
    
    # D8: Connectivity (computed later)
    D8 = 0.5
    
    # D9: Cosmic energy (spatial frequency centroid)
    centroid = visual_spectral_centroid(magnitude)
    max_distance = np.sqrt((magnitude.shape[0]/2)**2 + (magnitude.shape[1]/2)**2)
    D9 = centroid / max_distance if max_distance > 0 else 0.0
    
    # D10: Entropy
    D10 = D4
    
    # D11: Frequency (dominant spatial frequency)
    dom_freq = extract_dominant_spatial_frequency(magnitude)
    D11 = dom_freq / max_distance if max_distance > 0 else 0.0
    
    # D12: Adaptive state
    D12 = 0.0
    
    # Color frequency
    mean_color = np.mean(image.reshape(-1, 3), axis=0) if len(image.shape) == 3 else np.array([128, 128, 128])
    color_freq = rgb_to_frequency(mean_color)
    phi_harmonics = generate_phi_color_harmonics(mean_color)
    
    return Visual12DEmbedding(
        D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12,
        magnitude, phase, color_freq, phi_harmonics
    )

# ============================================================================
# VISUAL LIGHT TOKEN
# ============================================================================

class VisualLightToken:
    """Light token for images"""
    
    def __init__(self, image, metadata=None):
        self.token_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        
        # Image data
        self.image = image
        self.height, self.width = image.shape[:2]
        
        # 12D embedding
        self.embedding = create_visual_12d_embedding(image)
        
        # Metadata
        self.metadata = metadata or {}
        
        # Hash
        self.hash = hashlib.sha256(image.tobytes()).hexdigest()
    
    def spectral_similarity(self, other):
        """Compare images in frequency domain"""
        mag1 = self.embedding.magnitude_spectrum
        mag2 = other.embedding.magnitude_spectrum
        
        # Resize to same shape
        min_h = min(mag1.shape[0], mag2.shape[0])
        min_w = min(mag1.shape[1], mag2.shape[1])
        mag1 = mag1[:min_h, :min_w]
        mag2 = mag2[:min_h, :min_w]
        
        # Flatten and compute cosine similarity
        mag1_flat = mag1.flatten()
        mag2_flat = mag2.flatten()
        
        dot = np.dot(mag1_flat, mag2_flat)
        norm = np.linalg.norm(mag1_flat) * np.linalg.norm(mag2_flat)
        
        return dot / (norm + 1e-10)

# ============================================================================
# INVERSE 12D SENSORY MANIFESTATION (SYNTHESIS)
# ============================================================================

def _normalize_field(field):
    """Normalize a field to [0, 1]."""
    field_min = field.min()
    field_max = field.max()
    if field_max > field_min:
        return (field - field_min) / (field_max - field_min)
    return np.zeros_like(field)


def _project_visual_geometry(x_grid, y_grid, phi_coupling, vx, vy, vz):
    """
    Apply lightweight geometric transformations and pseudo-projection.

    This gives the 12D synthesizer explicit geometric control instead of relying
    solely on radial rings in the frequency domain.
    """
    rotation = phi_coupling * PHI * 0.35
    shear_x = np.tanh(vx * 4.0) * 0.7
    shear_y = np.tanh(vy * 4.0) * 0.7
    zoom = 1.0 + np.tanh(vz * 3.0) * 0.4
    perspective = 1.0 + 0.25 * np.tanh(vz * 2.0) * y_grid

    cos_t = np.cos(rotation)
    sin_t = np.sin(rotation)
    x_rot = (cos_t * x_grid) - (sin_t * y_grid)
    y_rot = (sin_t * x_grid) + (cos_t * y_grid)

    x_proj = zoom * (x_rot + shear_x * y_rot) / np.maximum(0.35, perspective)
    y_proj = zoom * (y_rot + shear_y * x_rot) * perspective
    return x_proj, y_proj


def _synthesize_harmonic_field(x_proj, y_proj, base_frequency, phi_coupling, entropy):
    """
    Build a phi-spaced harmonic field.

    This acts like a compact harmonic analysis/synthesis stage for native image generation.
    """
    harmonic_count = 3 + int(np.clip(abs(entropy) * 4.0, 0, 4))
    harmonic_field = np.zeros_like(x_proj)
    orientation = phi_coupling * 0.5

    for idx in range(1, harmonic_count + 1):
        harmonic_frequency = base_frequency * (PHI ** (idx - 1))
        theta = orientation + idx * (np.pi / (harmonic_count + 1))
        longitudinal = (np.cos(theta) * x_proj) + (np.sin(theta) * y_proj)
        transverse = (-np.sin(theta) * x_proj) + (np.cos(theta) * y_proj)
        wave = np.sin((longitudinal * harmonic_frequency * np.pi) + (phi_coupling * idx))
        interference = np.cos((transverse * harmonic_frequency * np.pi / PHI) - (entropy * idx))
        harmonic_field += ((wave * interference) + 1.0) / (PHI ** idx)

    return _normalize_field(harmonic_field)


def _synthesize_fractal_field(x_proj, y_proj, chaos, entropy, iteration_signal):
    """
    Build a lightweight iterative fractal field using a complex quadratic map.

    Kept intentionally compact so the native image path remains fast enough for
    repeated frame synthesis in video generation.
    """
    iterations = 4 + int(np.clip(abs(iteration_signal) * 6.0, 0, 6))
    c_real = (chaos * 0.32) + ((entropy - 0.5) * 0.85)
    c_imag = np.sin(iteration_signal * PHI) * 0.45

    z_real = x_proj * (1.0 + entropy * 0.35)
    z_imag = y_proj * (1.0 + abs(chaos) * 0.25)
    fractal_field = np.zeros_like(x_proj)
    escape_limit = 6.0 + abs(c_real) + abs(c_imag)

    for idx in range(iterations):
        z_real = np.clip(z_real, -escape_limit, escape_limit)
        z_imag = np.clip(z_imag, -escape_limit, escape_limit)
        next_real = (z_real * z_real) - (z_imag * z_imag) + c_real
        next_imag = (2.0 * z_real * z_imag) + c_imag
        z_real = np.nan_to_num(next_real, nan=0.0, posinf=escape_limit, neginf=-escape_limit)
        z_imag = np.nan_to_num(next_imag, nan=0.0, posinf=escape_limit, neginf=-escape_limit)

        radius_sq = np.clip((z_real * z_real) + (z_imag * z_imag), 0.0, escape_limit * escape_limit)
        layer = np.exp(-radius_sq / (1.2 + idx * 0.35))
        fractal_field += layer / (idx + 1)

    return _normalize_field(fractal_field)

def generate_image_from_12d(embedding_12d_vector, width=512, height=512):
    """
    Inverse synthesis: Generate a spatial image from a 12D Phase embedding vector.
    Uses geometric projection, harmonic synthesis, iterative fractal modulation,
    and inverse 2D FFT to collapse abstract 12D thought frequencies into pixels.
    """
    import numpy as np
    
    # Extract params (safely handle tensor or list)
    if hasattr(embedding_12d_vector, 'tolist'):
        e = embedding_12d_vector.tolist()
    else:
        e = embedding_12d_vector
        
    D1_energy = float(e[0])
    D2_mass = float(e[1])
    D3_phi = float(e[2])
    D4_chaos = float(e[3])
    D5_vx = float(e[4]) if len(e) > 4 else 0.0
    D6_vy = float(e[5]) if len(e) > 5 else 0.0
    D7_vz = float(e[6]) if len(e) > 6 else 0.0
    D9_cosmic = float(e[8])
    D10_entropy = float(e[9]) if len(e) > 9 else abs(D4_chaos)
    D11_freq = float(e[10])
    D12_x12 = float(e[11]) if len(e) > 11 else 0.0

    # Deterministic seed so identical 12D states generate identical manifestations
    seed_material = "|".join(f"{float(val):.6f}" for val in e[:12])
    seed = int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest()[:16], 16) & 0xFFFFFFFF
    rng = np.random.default_rng(seed)
    
    # 1. Construct normalized coordinate system and apply geometric projection
    y_grid, x_grid = np.mgrid[-1.0:1.0:complex(height), -1.0:1.0:complex(width)]
    x_proj, y_proj = _project_visual_geometry(x_grid, y_grid, D3_phi, D5_vx, D6_vy, D7_vz)
    distance = np.sqrt((x_proj * x_proj) + (y_proj * y_proj)) + 1e-6
    angle = np.arctan2(y_proj, x_proj)

    # 2. Harmonic and fractal fields
    spatial_frequency = 3.0 + max(abs(D11_freq), 0.05) * 18.0
    harmonic_field = _synthesize_harmonic_field(x_proj, y_proj, spatial_frequency, D3_phi, D10_entropy)
    fractal_field = _synthesize_fractal_field(x_proj, y_proj, D4_chaos, D10_entropy, D12_x12)
    
    # 3. Base dominant frequency ring (from D11), now in projected coordinates
    target_radius = 0.18 + np.clip(abs(D11_freq), 0.0, 1.5) * 0.55
    ring_width = 0.08 + abs(D4_chaos) * 0.18 + D10_entropy * 0.06
    ring = np.exp(-((distance - target_radius) ** 2) / (2 * (ring_width ** 2)))
    
    # 4. Cosmic energy centroid bias and directional symmetry
    symmetry = max(1, int(2 + abs(D12_x12) * 6 + abs(D3_phi) * 2))
    bias = 1.0 + abs(D9_cosmic) * np.cos(angle * (symmetry + 1))
    
    # 5. Magnitude: ring + harmonic synthesis + iterative fractal modulation + seeded chaos
    seeded_noise = rng.random((height, width))
    magnitude = (
        (ring * bias * (abs(D1_energy) * 3200 + 140))
        + (harmonic_field * (320 + abs(D3_phi) * 260 + D10_entropy * 180))
        + (fractal_field * (240 + abs(D4_chaos) * 960))
        + (seeded_noise * (18 + abs(D4_chaos) * 160))
    )
    
    # 6. Phase: phi-coupled spirals enhanced by harmonic and fractal fields
    phase = (
        (angle * symmetry)
        + (distance * ((D2_mass * PHI * 0.35) + spatial_frequency))
        + (harmonic_field * np.pi * (1.5 + D10_entropy))
        + (fractal_field * np.pi * (0.75 + abs(D4_chaos)))
    )
    
    # 7. Reconstruct Complex Frequency Domain
    complex_domain = magnitude * np.exp(1j * phase)
    complex_shifted = np.fft.ifftshift(complex_domain)
    
    # 8. Inverse 2D FFT to spatial domain
    image_spatial = np.fft.ifft2(complex_shifted).real
    
    # 9. Normalize spatial to 0-1
    image_norm = _normalize_field(image_spatial)
        
    # 10. Colorize using phi-harmonic palette synthesis
    base_freq = 430e12 + (abs(D1_energy + (D9_cosmic * 0.5)) % 1.0 * (770e12 - 430e12))
    base_rgb = frequency_to_rgb(base_freq)
    harmonic_palette = [color / 255.0 for color in generate_phi_color_harmonics(base_rgb, num_harmonics=5)]
    primary_color = harmonic_palette[len(harmonic_palette) // 2]
    secondary_color = harmonic_palette[-1]
    tertiary_color = harmonic_palette[0]
    
    interference = (
        np.sin((x_proj * spatial_frequency * PHI) + D4_chaos)
        * np.cos((y_proj * spatial_frequency) + D3_phi)
        + 1.0
    ) / 2.0
    blend = (
        image_norm[:, :, np.newaxis] * primary_color
        + harmonic_field[:, :, np.newaxis] * secondary_color * 0.55
        + fractal_field[:, :, np.newaxis] * tertiary_color * 0.45
    )
    
    img_rgb = (
        blend * (0.72 + ring[:, :, np.newaxis] * 0.28)
        + (image_norm[:, :, np.newaxis] * secondary_color) * interference[:, :, np.newaxis] * 0.4
        + (harmonic_field[:, :, np.newaxis] * primary_color) * (1.0 - interference[:, :, np.newaxis]) * 0.18
    )
    
    # 11. Convert to 8-bit uint8 image
    img_rgb = np.clip(img_rgb * 255, 0, 255).astype(np.uint8)
    
    return img_rgb

def generate_video_from_54d(state_54d, frames=30, width=512, height=512):
    """
    Evolve the 54D state temporally using Lorenz chaos and render sequence of IFFT images.
    Returns list of numpy rgb images.
    """
    import numpy as np
    
    if hasattr(state_54d, 'tolist'):
        state = state_54d.tolist()
    else:
        state = list(state_54d)
        
    # Need at least 54 dims, pad if missing
    if len(state) < 54:
        state = state + [0.0] * (54 - len(state))
    
    cst_12d = np.nan_to_num(np.array(state[:12], dtype=float), nan=0.0, posinf=PHI * 2.0, neginf=-PHI * 2.0)
    chaos_18d = np.nan_to_num(np.array(state[36:54], dtype=float), nan=0.0, posinf=1.0, neginf=-1.0)
    
    video_frames = []
    
    # Evolve the 12D Phase vector using the 18D Chaos oscillators over time
    for f in range(frames):
        # Generate image for current 12D state
        img = generate_image_from_12d(cst_12d.tolist(), width, height)
        video_frames.append(img)
        
        # Non-linear Chaos evolution for next frame
        for i in range(12):
            chaos_driver = chaos_18d[i % 18]
            # Lorenz-like derivative
            delta = chaos_driver * np.sin(cst_12d[i] * PHI + f * 0.1) * 0.05
            cst_12d[i] = cst_12d[i] + delta
        cst_12d = np.nan_to_num(np.clip(cst_12d, -PHI * 4.0, PHI * 4.0), nan=0.0, posinf=PHI * 4.0, neginf=-PHI * 4.0)
            
        # Slightly evolve chaos itself
        for i in range(18):
            chaos_18d[i] += (np.random.rand() - 0.5) * 0.1
        chaos_18d = np.nan_to_num(np.clip(chaos_18d, -4.0, 4.0), nan=0.0, posinf=4.0, neginf=-4.0)

    return video_frames

