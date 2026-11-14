"""
Pure NumPy Daubechies-4 (db4) Multi-Level Discrete Wavelet Transform and Micro-G Jitter Filter.

Zero native C library dependencies (no PyWavelets / pywt, no SciPy).
Designed for NASA Space Apps Challenge 2026 - ISS CIR Flame in Freefall.

This module decomposes orbital acceleration timeseries into dyadic wavelet subbands,
isolating high-frequency astronaut exercise vibrations (1-3 Hz, ~10^-3 g) and attitude
thruster firings, and reconstructing the authentic quiescent microgravity baseline (~10^-6 g).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

# Exact analytical Daubechies-4 (db4, length 8, 4 vanishing moments) scaling coefficients
DB4_SCALING = np.array([
    -0.010597401785069032,
     0.0328830116668852,
     0.030841381835560764,
    -0.18703481171909309,
    -0.027983769416859854,
     0.6308807679298589,
     0.7148465705529157,
     0.2303778133088965,
], dtype=np.float64)

# Quadrature Mirror Filter (QMF) wavelet coefficients: g_k = (-1)^k * h_{L - 1 - k}
DB4_WAVELET = np.array([
    (-1.0) ** k * DB4_SCALING[7 - k] for k in range(8)
], dtype=np.float64)

# Daubechies-2 / D4 (4-tap, 2 vanishing moments) closed-form algebraic coefficients
_SQRT3 = math.sqrt(3.0)
_DENOM = 4.0 * math.sqrt(2.0)
DB2_SCALING = np.array([
    (1.0 + _SQRT3) / _DENOM,
    (3.0 + _SQRT3) / _DENOM,
    (3.0 - _SQRT3) / _DENOM,
    (1.0 - _SQRT3) / _DENOM,
], dtype=np.float64)

DB2_WAVELET = np.array([
    (-1.0) ** k * DB2_SCALING[3 - k] for k in range(4)
], dtype=np.float64)

# Physical constants for microgravity combustion hydrodynamics
GRAVITY_G0_MS2 = 9.80665  # Standard Earth gravity (m/s^2)
T_FLAME_DEFAULT_K = 1800.0  # Flame zone temperature (K)
T_INF_DEFAULT_K = 298.15  # Quiescent ambient chamber temperature (K)
KINEMATIC_VISCOSITY_DEFAULT_M2_S = 2.76e-5  # Air mixture viscosity (m^2/s)
VENTILATION_VELOCITY_DEFAULT_M_S = 0.10  # Slow chamber ventilation velocity (m/s)
BUOYANCY_GRASHOF_CRITICAL = 1.0  # Grashof number threshold above which buoyancy perturbs spherical flame


def get_filter_coefficients(wavelet: str = "db4") -> tuple[np.ndarray, np.ndarray]:
    """Returns scaling (h) and wavelet (g) filter coefficients for the requested wavelet."""
    w_lower = wavelet.lower().strip()
    if w_lower in ("db4", "daubechies4", "d8"):
        return DB4_SCALING, DB4_WAVELET
    elif w_lower in ("db2", "daubechies2", "d4"):
        return DB2_SCALING, DB2_WAVELET
    else:
        raise ValueError(
            f"Unsupported wavelet family '{wavelet}'. Supported wavelets: ['db4', 'db2']"
        )


def build_dwt_matrix(n: int, h: np.ndarray, g: np.ndarray) -> np.ndarray:
    """Constructs an n x n circular orthogonal discrete wavelet transform matrix W.

    The upper half (rows 0 to n//2 - 1) computes low-pass approximation coefficients.
    The lower half (rows n//2 to n - 1) computes high-pass detail coefficients.

    Satisfies W @ W.T = I and W.T @ W = I to machine precision (< 10^-15).
    """
    if n % 2 != 0:
        raise ValueError(f"Matrix dimension n must be an even integer, got {n}")
    if n < len(h):
        # Even for n < len(h), circular wrapping with += h[k] maintains orthogonality
        pass

    half = n // 2
    len_h = len(h)
    len_g = len(g)
    W = np.zeros((n, n), dtype=np.float64)

    for i in range(half):
        row_approx = i
        row_detail = half + i
        shift = 2 * i
        for k in range(len_h):
            col = (shift + k) % n
            W[row_approx, col] += h[k]
        for k in range(len_g):
            col = (shift + k) % n
            W[row_detail, col] += g[k]

    return W


def dwt_decompose(
    signal: np.ndarray | list[float],
    levels: int = 5,
    wavelet: str = "db4",
) -> tuple[np.ndarray, list[np.ndarray], list[np.ndarray]]:
    """Performs multi-level dyadic discrete wavelet decomposition (Mallat pyramid algorithm).

    Args:
        signal: 1D array of real-valued signal samples (must have length >= 8).
        levels: Number of decomposition levels (>= 1).
        wavelet: Wavelet family ('db4' or 'db2').

    Returns:
        (approx, details, matrices)
        approx: 1D array of final approximation coefficients A_J.
        details: List of detail coefficient arrays [D_1, D_2, ..., D_J].
        matrices: List of orthogonal transform matrices [W_1, W_2, ..., W_J].
    """
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1:
        raise ValueError("Signal must be a 1-dimensional array")
    if len(x) < 8:
        raise ValueError(
            f"Signal length must be at least 8 samples for {wavelet} wavelet decomposition, got {len(x)}"
        )
    if levels < 1:
        raise ValueError(f"Decomposition levels must be at least 1, got {levels}")

    # Maximum levels permitted based on length
    max_levels = int(np.log2(len(x)))
    if levels > max_levels:
        raise ValueError(
            f"Requested decomposition levels {levels} exceeds maximum possible levels ({max_levels}) for length {len(x)}"
        )

    h, g = get_filter_coefficients(wavelet)
    approx = x.copy()
    details: list[np.ndarray] = []
    matrices: list[np.ndarray] = []

    for _ in range(levels):
        m = len(approx)
        if m % 2 != 0:
            raise ValueError(f"Approximation vector length {m} is odd and cannot be dyadically split")
        W = build_dwt_matrix(m, h, g)
        transformed = W @ approx
        half = m // 2
        details.append(transformed[half:])
        approx = transformed[:half]
        matrices.append(W)

    return approx, details, matrices


def idwt_reconstruct(
    approx: np.ndarray,
    details: list[np.ndarray],
    matrices: list[np.ndarray],
) -> np.ndarray:
    """Performs exact inverse discrete wavelet transform reconstruction using matrix transposes W^T.

    Args:
        approx: 1D array of approximation coefficients A_J.
        details: List of detail coefficient arrays [D_1, D_2, ..., D_J].
        matrices: List of orthogonal transform matrices [W_1, W_2, ..., W_J].

    Returns:
        Reconstructed 1D signal achieving numerical reconstruction error < 10^-14.
    """
    levels = len(details)
    if levels != len(matrices):
        raise ValueError(
            f"Mismatched levels between details ({levels}) and matrices ({len(matrices)})"
        )

    current = approx.copy()
    for j in reversed(range(levels)):
        D = details[j]
        W = matrices[j]
        combined = np.concatenate([current, D])
        current = W.T @ combined

    return current


def calculate_grashof(
    acceleration_g: float | np.ndarray,
    characteristic_length_m: float = 0.003,
    flame_temp_k: float = T_FLAME_DEFAULT_K,
    ambient_temp_k: float = T_INF_DEFAULT_K,
    kinematic_viscosity_m2_s: float = KINEMATIC_VISCOSITY_DEFAULT_M2_S,
) -> float | np.ndarray:
    """Calculates dimensionless Grashof number: Gr = g_eff * beta * (T_f - T_inf) * L^3 / nu^2.

    Quantifies natural convection buoyancy relative to viscous forces.
    """
    beta = 1.0 / max(ambient_temp_k, 1e-6)
    delta_t = max(0.0, flame_temp_k - ambient_temp_k)
    l_cubed = characteristic_length_m ** 3
    nu_sq = max(kinematic_viscosity_m2_s ** 2, 1e-18)

    acc = np.abs(acceleration_g)
    g_eff = acc * GRAVITY_G0_MS2
    gr = (g_eff * beta * delta_t * l_cubed) / nu_sq
    if isinstance(acceleration_g, (float, int)):
        return float(gr)
    return gr


def calculate_richardson(
    grashof: float | np.ndarray,
    characteristic_length_m: float = 0.003,
    ventilation_velocity_m_s: float = VENTILATION_VELOCITY_DEFAULT_M_S,
    kinematic_viscosity_m2_s: float = KINEMATIC_VISCOSITY_DEFAULT_M2_S,
) -> float | np.ndarray:
    """Calculates dimensionless Richardson number: Ri = Gr / Re^2 = Gr * nu^2 / (U_vent^2 * L^2).

    Ri << 0.01 indicates pure microgravity diffusion; Ri > 0.1 indicates buoyant disruption.
    """
    u_vent = max(ventilation_velocity_m_s, 1e-6)
    l_m = max(characteristic_length_m, 1e-6)
    factor = (kinematic_viscosity_m2_s ** 2) / ((u_vent ** 2) * (l_m ** 2))
    ri = grashof * factor
    if isinstance(grashof, (float, int)):
        return float(ri)
    return ri


def get_wavelet_specs(
    sample_rate_hz: float = 50.0,
    levels: int = 5,
    wavelet: str = "db4",
) -> dict[str, Any]:
    """Returns technical specifications, coefficients, vanishing moments, frequency bands,
    and mathematical formulas for the wavelet decomposition filter.
    """
    h, g = get_filter_coefficients(wavelet)
    vanishing_moments = 4 if wavelet.lower() == "db4" else 2

    bands: list[dict[str, Any]] = []
    # Detail bands D_1 to D_J
    for j in range(1, levels + 1):
        f_high = sample_rate_hz / (2.0 ** j)
        f_low = sample_rate_hz / (2.0 ** (j + 1))
        desc = "High-frequency electronics noise & pump ripple"
        if 1.0 <= f_high <= 3.5 or (f_low < 3.0 and f_high > 1.0):
            desc = "Primary Astronaut Exercise (Treadmill T2, ARED) & Structural Resonance"
        elif f_high < 1.0:
            desc = "Attitude Control Thruster Pulse Decay"

        bands.append({
            "level": j,
            "band": f"D{j}",
            "type": "detail",
            "frequency_low_hz": round(f_low, 4),
            "frequency_high_hz": round(f_high, 4),
            "description": desc,
        })

    # Final approximation band A_J
    f_approx_high = sample_rate_hz / (2.0 ** (levels + 1))
    bands.append({
        "level": levels,
        "band": f"A{levels}",
        "type": "approximation",
        "frequency_low_hz": 0.0,
        "frequency_high_hz": round(f_approx_high, 4),
        "description": "Quiescent Microgravity Steady Baseline (10^-6 g)",
    })

    return {
        "wavelet": wavelet,
        "taps": len(h),
        "vanishing_moments": vanishing_moments,
        "scaling_coefficients_h": [float(val) for val in h],
        "wavelet_coefficients_g": [float(val) for val in g],
        "sample_rate_hz": sample_rate_hz,
        "decomposition_levels": levels,
        "frequency_subbands": bands,
        "physical_formulas": {
            "grashof_number": "Gr = g_eff * beta * (T_flame - T_inf) * L^3 / nu^2",
            "richardson_number": "Ri = Gr / Re^2 = Gr * nu^2 / (U_vent^2 * L^2)",
            "snr_improvement_db": "SNR_gain = 10 * log10(Power_noise_raw / Power_noise_filtered)",
            "peak_acceleration_reduction_percent": "PAR = ((Peak_raw - Peak_filtered) / Peak_raw) * 100",
            "orthogonal_condition": "W @ W.T = I, W.T @ W = I",
        },
    }


def filter_g_jitter(
    accelerations: list[float] | np.ndarray,
    sample_rate_hz: float = 50.0,
    levels: int = 5,
    mode: str = "threshold",
    threshold_g: float = 1.0e-4,
    wavelet: str = "db4",
    flame_length_scale_m: float = 0.003,
) -> dict[str, Any]:
    """Filters acceleration timeseries using Daubechies multi-level discrete wavelet transform.

    Suppresses astronaut exercise vibrations and mechanical jitter, extracting the authentic
    quiescent microgravity baseline.

    Args:
        accelerations: 1D sequence of raw acceleration samples in units of g (length >= 8).
        sample_rate_hz: Sampling frequency in Hertz (default: 50.0 Hz).
        levels: Dyadic decomposition depth (default: 5).
        mode: Filter operation mode ('threshold', 'pure_approx', 'band_stop').
        threshold_g: Detail coefficient suppression threshold in g (default: 1.0e-4 g).
        wavelet: Wavelet family ('db4' or 'db2').
        flame_length_scale_m: Droplet or flame characteristic length scale in meters (default: 0.003 m).

    Returns:
        dict containing:
        - filtered_accelerations: list[float]
        - snr_improvement_db: float
        - peak_acceleration_reduction_percent: float
        - raw_grashof_peak: float
        - filtered_grashof_peak: float
        - buoyant_perturbation_flag: bool
        - wavelet_power_spectrum: dict[str, float]
        - raw_peak_g: float
        - filtered_peak_g: float
        - raw_richardson_peak: float
        - filtered_richardson_peak: float
        - decomposition_levels: int
        - wavelet: str
        - filter_mode: str
    """
    raw_arr = np.asarray(accelerations, dtype=np.float64)
    if raw_arr.ndim != 1:
        raise ValueError("Acceleration signal must be a 1-dimensional array")

    n_samples = len(raw_arr)
    if n_samples < 8:
        raise ValueError(
            f"Signal length must be at least 8 samples for {wavelet} wavelet decomposition, got {n_samples}"
        )

    if np.any(np.isnan(raw_arr)) or np.any(np.isinf(raw_arr)):
        raise ValueError(
            "Acceleration signal contains invalid non-numeric or NaN values. "
            "For missing telemetry, preserve NULL at channel level before filtering."
        )

    if levels < 1:
        raise ValueError(f"Decomposition levels must be at least 1, got {levels}")

    if threshold_g <= 0.0:
        raise ValueError(f"Threshold must be positive, got {threshold_g}")

    mode_lower = mode.lower().strip()
    valid_modes = ("threshold", "pure_approx", "band_stop")
    if mode_lower not in valid_modes:
        raise ValueError(
            f"Unsupported filter mode '{mode}'. Supported modes: {list(valid_modes)}"
        )

    # Calculate padding to next power of 2 for circular dyadic transform
    n_pad = 1 << (n_samples - 1).bit_length()
    max_levels = int(np.log2(n_pad))
    actual_levels = min(levels, max_levels)

    if n_pad == n_samples:
        padded = raw_arr.copy()
    else:
        pad_len = n_pad - n_samples
        padded = np.pad(raw_arr, (0, pad_len), mode="reflect")

    # Forward DWT decomposition
    approx, details, matrices = dwt_decompose(padded, levels=actual_levels, wavelet=wavelet)

    # Compute raw wavelet power spectrum across subbands (Parseval energy percentage)
    total_raw_energy = float(np.sum(padded ** 2))
    spectrum: dict[str, float] = {}

    if total_raw_energy > 1e-28:
        approx_energy = float(np.sum(approx ** 2))
        spectrum[f"A{actual_levels}"] = round((approx_energy / total_raw_energy) * 100.0, 4)
        spectrum["approx"] = spectrum[f"A{actual_levels}"]
        for j, d in enumerate(details):
            d_energy = float(np.sum(d ** 2))
            spectrum[f"D{j + 1}"] = round((d_energy / total_raw_energy) * 100.0, 4)
    else:
        spectrum[f"A{actual_levels}"] = 100.0
        spectrum["approx"] = 100.0
        for j in range(actual_levels):
            spectrum[f"D{j + 1}"] = 0.0

    # Apply filtering according to selected mode
    filtered_details: list[np.ndarray] = []
    filtered_approx = approx.copy()

    if mode_lower == "pure_approx":
        # Zero out all detail bands, preserving strictly the quiescent microgravity approximation
        for d in details:
            filtered_details.append(np.zeros_like(d))

    elif mode_lower == "band_stop":
        # Identify detail levels overlapping with astronaut exercise frequency range (1.0 to 3.0 Hz)
        for j, d in enumerate(details):
            level_idx = j + 1
            f_high = sample_rate_hz / (2.0 ** level_idx)
            f_low = sample_rate_hz / (2.0 ** (level_idx + 1))
            # If subband overlaps with 1-3 Hz exercise jitter band, suppress it
            if f_low < 3.0 and f_high > 1.0:
                filtered_details.append(np.zeros_like(d))
            else:
                filtered_details.append(d.copy())

    else:
        # Default 'threshold' mode:
        # Detail coefficients with absolute magnitude exceeding threshold_g are suppressed (zeroed)
        # Any residual leakage into approximation A_J above threshold_g is clamped
        for d in details:
            suppressed = np.where(np.abs(d) > threshold_g, 0.0, d)
            filtered_details.append(suppressed)

        scale = (np.sqrt(2.0)) ** actual_levels
        mean_approx = float(np.mean(approx))
        allowed_delta = threshold_g * scale
        filtered_approx = mean_approx + np.clip(
            approx - mean_approx, -allowed_delta, allowed_delta
        )

    # Inverse DWT reconstruction
    reconstructed_padded = idwt_reconstruct(filtered_approx, filtered_details, matrices)
    filtered = reconstructed_padded[:n_samples]

    # Peak metrics & acceleration reduction
    raw_peak = float(np.max(np.abs(raw_arr)))
    filt_peak = float(np.max(np.abs(filtered)))

    if raw_peak > 1e-15:
        par_percent = max(0.0, ((raw_peak - filt_peak) / raw_peak) * 100.0)
    else:
        par_percent = 0.0

    # SNR Improvement (dB) calculation
    s_est = float(np.mean(filtered))
    raw_noise_power = float(np.mean((raw_arr - s_est) ** 2))
    filt_noise_power = float(np.mean((filtered - s_est) ** 2))

    if raw_noise_power > 1e-22 and filt_noise_power > 1e-22:
        snr_gain = 10.0 * math.log10(raw_noise_power / max(filt_noise_power, 1e-18))
        snr_improvement_db = max(0.0, round(snr_gain, 2))
    else:
        snr_improvement_db = 0.0

    # Physical combustion indices: Grashof and Richardson numbers
    raw_grashof = calculate_grashof(
        raw_arr,
        characteristic_length_m=flame_length_scale_m,
    )
    filt_grashof = calculate_grashof(
        filtered,
        characteristic_length_m=flame_length_scale_m,
    )

    raw_gr_peak = float(np.max(raw_grashof))
    filt_gr_peak = float(np.max(filt_grashof))

    raw_ri = calculate_richardson(
        raw_grashof,
        characteristic_length_m=flame_length_scale_m,
    )
    filt_ri = calculate_richardson(
        filt_grashof,
        characteristic_length_m=flame_length_scale_m,
    )

    raw_ri_peak = float(np.max(raw_ri))
    filt_ri_peak = float(np.max(filt_ri))

    buoyant_perturbation = bool(raw_gr_peak > BUOYANCY_GRASHOF_CRITICAL)

    return {
        "filtered_accelerations": [float(val) for val in filtered],
        "snr_improvement_db": float(snr_improvement_db),
        "peak_acceleration_reduction_percent": round(float(par_percent), 2),
        "raw_grashof_peak": round(raw_gr_peak, 4),
        "filtered_grashof_peak": round(filt_gr_peak, 4),
        "buoyant_perturbation_flag": buoyant_perturbation,
        "wavelet_power_spectrum": spectrum,
        "raw_peak_g": round(raw_peak, 6),
        "filtered_peak_g": round(filt_peak, 6),
        "raw_richardson_peak": round(raw_ri_peak, 6),
        "filtered_richardson_peak": round(filt_ri_peak, 6),
        "decomposition_levels": actual_levels,
        "wavelet": wavelet,
        "filter_mode": mode_lower,
    }
