"""
Unit Tests for Pure NumPy Daubechies-4 (db4) Discrete Wavelet Filter.

Verifies:
1. Exact filter coefficient orthogonality and QMF properties for db4 and db2.
2. Orthogonal circular convolution matrix W construction (W @ W.T = I to machine precision).
3. Machine-precision perfect reconstruction (< 10^-14) across dyadic decomposition levels.
4. Non-power-of-two signal padding via symmetric reflection with strict [:N] slicing.
5. Flatline constant microgravity signal (10^-6 g) with zero detail energy.
6. Quiescent microgravity pass-through without spurious attenuation.
7. Frequency band isolation and suppression of 1.8 Hz astronaut treadmill jitter (PAR > 80%, SNR > 20 dB).
8. Extreme impulse spike attenuation.
9. Filtering modes ('threshold', 'pure_approx', 'band_stop').
10. Dynamic Grashof Gr(t) and Richardson Ri(t) microgravity hydrodynamics.
11. Wavelet specification metadata and frequency subband tables.
12. Strict parameter validation (N < 8, NaN/Inf rejection, invalid levels, negative thresholds).
"""

import math

import numpy as np
import pytest
from backend.app.timeseries.wavelet_filter import (
    BUOYANCY_GRASHOF_CRITICAL,
    DB2_SCALING,
    DB2_WAVELET,
    DB4_SCALING,
    DB4_WAVELET,
    build_dwt_matrix,
    calculate_grashof,
    calculate_richardson,
    dwt_decompose,
    filter_g_jitter,
    get_filter_coefficients,
    get_wavelet_specs,
    idwt_reconstruct,
)


class TestWaveletCoefficientsAndMatrix:
    """Verifies analytical properties of Daubechies wavelet filter coefficients and matrices."""

    def test_db4_scaling_and_wavelet_coefficients(self):
        """db4 coefficients must satisfy sum(h) = sqrt(2), norm(h) = 1, and vanishing moments."""
        h, g = get_filter_coefficients("db4")
        assert np.array_equal(h, DB4_SCALING)
        assert np.array_equal(g, DB4_WAVELET)

        # Sum of scaling coefficients must equal sqrt(2)
        assert np.isclose(np.sum(DB4_SCALING), math.sqrt(2.0), atol=1e-14)
        # L2 norm of scaling filter must be 1.0
        assert np.isclose(np.sum(DB4_SCALING ** 2), 1.0, atol=1e-14)
        # Sum of wavelet coefficients must equal 0.0 (zeroth moment)
        assert np.isclose(np.sum(DB4_WAVELET), 0.0, atol=1e-14)
        # L2 norm of wavelet filter must be 1.0
        assert np.isclose(np.sum(DB4_WAVELET ** 2), 1.0, atol=1e-14)
        # Orthogonality between scaling and wavelet filters
        assert np.isclose(np.dot(DB4_SCALING, DB4_WAVELET), 0.0, atol=1e-14)
        # Double shift orthogonality: sum(h_k * h_{k + 2m}) = delta_{0, m}
        for m in [1, 2, 3]:
            shifted_dot = np.sum(DB4_SCALING[:-2 * m] * DB4_SCALING[2 * m:])
            assert np.isclose(shifted_dot, 0.0, atol=1e-14)

    def test_db2_scaling_and_wavelet_coefficients(self):
        """db2 (D4) coefficients must satisfy exact closed-form algebraic relationships."""
        assert np.isclose(np.sum(DB2_SCALING), math.sqrt(2.0), atol=1e-14)
        assert np.isclose(np.sum(DB2_SCALING ** 2), 1.0, atol=1e-14)
        assert np.isclose(np.sum(DB2_WAVELET), 0.0, atol=1e-14)
        assert np.isclose(np.sum(DB2_WAVELET ** 2), 1.0, atol=1e-14)
        assert np.isclose(np.dot(DB2_SCALING, DB2_WAVELET), 0.0, atol=1e-14)

    @pytest.mark.parametrize("n", [8, 16, 32, 64, 128])
    def test_build_dwt_matrix_db4_orthogonality(self, n: int):
        """DWT matrix W must satisfy W @ W.T = I and W.T @ W = I to machine precision."""
        W = build_dwt_matrix(n, DB4_SCALING, DB4_WAVELET)
        assert W.shape == (n, n)
        eye = np.eye(n, dtype=np.float64)

        forward_ortho_err = np.max(np.abs(W @ W.T - eye))
        backward_ortho_err = np.max(np.abs(W.T @ W - eye))

        assert forward_ortho_err < 1e-14, f"W @ W.T error: {forward_ortho_err}"
        assert backward_ortho_err < 1e-14, f"W.T @ W error: {backward_ortho_err}"

    def test_build_dwt_matrix_odd_dimension_raises_error(self):
        """Constructing DWT matrix with odd dimension must raise ValueError."""
        with pytest.raises(ValueError, match="even integer"):
            build_dwt_matrix(15, DB4_SCALING, DB4_WAVELET)


class TestDecompositionAndReconstruction:
    """Verifies forward DWT and inverse IDWT reconstruction precision across signals."""

    @pytest.mark.parametrize("length", [8, 16, 32, 64, 128, 512])
    def test_perfect_reconstruction_machine_precision(self, length: int):
        """Random signals must achieve numerical reconstruction error < 10^-14."""
        np.random.seed(42 + length)
        x = np.random.randn(length)

        max_levels = int(np.log2(length))
        levels = min(5, max_levels)

        approx, details, matrices = dwt_decompose(x, levels=levels, wavelet="db4")
        reconstructed = idwt_reconstruct(approx, details, matrices)

        max_abs_err = np.max(np.abs(x - reconstructed))
        assert max_abs_err < 1e-14, f"Error {max_abs_err} exceeded 10^-14 on length {length}"

    @pytest.mark.parametrize("length", [13, 27, 45, 100, 250, 500, 777])
    def test_arbitrary_non_power_of_two_lengths(self, length: int):
        """Signals of arbitrary length must pad via symmetric reflection and reconstruct with zero shape error."""
        np.random.seed(101 + length)
        x = np.random.randn(length)

        # Execute through full filtering pipeline
        result = filter_g_jitter(x, sample_rate_hz=50.0, levels=4, mode="threshold")
        filtered = result["filtered_accelerations"]

        assert len(filtered) == length
        assert isinstance(filtered, list)
        assert all(isinstance(v, float) for v in filtered)

    def test_db2_wavelet_roundtrip(self):
        """DWT and IDWT with db2 wavelet must also achieve machine precision reconstruction."""
        np.random.seed(2026)
        x = np.random.randn(64)
        approx, details, matrices = dwt_decompose(x, levels=3, wavelet="db2")
        reconstructed = idwt_reconstruct(approx, details, matrices)
        assert np.max(np.abs(x - reconstructed)) < 1e-14


class TestMicroGJitterFilterScenarios:
    """Verifies the four canonical physics scenarios from the Flow 1 specification."""

    def test_flatline_constant_microgravity(self):
        """Constant 10^-6 g signal must produce 0 detail energy, 0% PAR, and 0 dB SNR gain."""
        length = 512
        signal = np.full(length, 1.0e-6, dtype=np.float64)

        result = filter_g_jitter(
            signal,
            sample_rate_hz=50.0,
            levels=5,
            mode="threshold",
            threshold_g=1.0e-4,
        )

        filtered = np.array(result["filtered_accelerations"])
        # Reconstructed signal should match input to float precision
        assert np.max(np.abs(signal - filtered)) < 1e-15
        assert result["peak_acceleration_reduction_percent"] == 0.0
        assert result["snr_improvement_db"] == 0.0
        assert result["buoyant_perturbation_flag"] is False

        # Power spectrum: 100% in approximation, 0% in detail bands
        spectrum = result["wavelet_power_spectrum"]
        assert np.isclose(spectrum["A5"], 100.0, atol=1e-3)
        assert np.isclose(spectrum["approx"], 100.0, atol=1e-3)
        for j in range(1, 6):
            assert spectrum[f"D{j}"] == 0.0

        # Hydrodynamic indices
        assert result["raw_grashof_peak"] < 0.01
        assert result["filtered_grashof_peak"] < 0.01
        assert result["raw_richardson_peak"] < 0.001
        assert result["filtered_richardson_peak"] < 0.001

    def test_quiescent_microgravity_with_orbital_drift(self):
        """Quiescent microgravity with slow 0.05 Hz orbital drift must pass through unattenuated."""
        sample_rate = 50.0
        t = np.arange(0, 10.24, 1.0 / sample_rate)  # 512 samples
        drift = 1.0e-6 * (1.0 + 0.2 * np.sin(2.0 * np.pi * 0.05 * t))

        result = filter_g_jitter(drift, sample_rate_hz=sample_rate, levels=5, mode="threshold")

        # Detail coefficients remain below threshold; signal passes through
        assert result["buoyant_perturbation_flag"] is False
        assert result["raw_grashof_peak"] < 0.01
        assert result["filtered_grashof_peak"] < 0.01
        assert result["raw_richardson_peak"] < 0.001

    def test_1_8hz_astronaut_treadmill_jitter_suppression(self):
        """1.8 Hz astronaut exercise vibration (5x10^-3 g) must concentrate in D4 and be heavily attenuated."""
        sample_rate = 50.0
        t = np.arange(0, 10.24, 1.0 / sample_rate)  # 512 samples
        quiescent = 1.0e-6 * np.ones_like(t)
        jitter = 5.0e-3 * np.sin(2.0 * np.pi * 1.8 * t)  # 5 milli-g vibration
        noisy = quiescent + jitter

        result = filter_g_jitter(
            noisy,
            sample_rate_hz=sample_rate,
            levels=5,
            mode="threshold",
            threshold_g=1.0e-4,
        )

        par = result["peak_acceleration_reduction_percent"]
        snr = result["snr_improvement_db"]
        spectrum = result["wavelet_power_spectrum"]

        # 1. PAR must exceed 80%
        assert par > 80.0, f"Expected PAR > 80%, got {par}%"

        # 2. SNR improvement must exceed 20 dB
        assert snr > 20.0, f"Expected SNR improvement > 20 dB, got {snr} dB"

        # 3. Energy must concentrate heavily in Detail Level 4 (1.56 to 3.125 Hz)
        assert spectrum["D4"] > 60.0, f"Expected D4 > 60% energy, got {spectrum['D4']}%"

        # 4. Raw signal triggers buoyant perturbation; filtered signal drops below threshold
        assert result["buoyant_perturbation_flag"] is True
        assert result["raw_grashof_peak"] > BUOYANCY_GRASHOF_CRITICAL
        assert result["filtered_grashof_peak"] < BUOYANCY_GRASHOF_CRITICAL

    def test_extreme_impulse_spike_response(self):
        """Single-sample extreme spike (10^-2 g) must be strongly attenuated (> 80% PAR)."""
        length = 512
        impulse = np.full(length, 1.0e-6, dtype=np.float64)
        impulse[256] = 1.0e-2  # 10 milli-g shock spike

        result = filter_g_jitter(impulse, sample_rate_hz=50.0, levels=5, mode="threshold")

        par = result["peak_acceleration_reduction_percent"]
        assert par > 80.0, f"Expected impulse PAR > 80%, got {par}%"
        assert result["filtered_peak_g"] < result["raw_peak_g"]


class TestFilterModes:
    """Verifies behavior across filter modes: 'threshold', 'pure_approx', and 'band_stop'."""

    @pytest.fixture
    def noisy_exercise_signal(self):
        t = np.arange(0, 10.24, 0.02)
        quiescent = 1.0e-6 * np.ones_like(t)
        jitter = 2.5e-3 * np.sin(2.0 * np.pi * 1.8 * t)
        return quiescent + jitter

    def test_pure_approx_mode(self, noisy_exercise_signal):
        """pure_approx mode reconstructs strictly from approximation A_J, zeroing all details."""
        res = filter_g_jitter(noisy_exercise_signal, levels=5, mode="pure_approx")
        assert res["peak_acceleration_reduction_percent"] > 75.0
        assert res["filter_mode"] == "pure_approx"

    def test_band_stop_mode(self, noisy_exercise_signal):
        """band_stop mode zeroes out details overlapping with 1-3 Hz exercise band."""
        res = filter_g_jitter(noisy_exercise_signal, levels=5, mode="band_stop")
        assert res["filter_mode"] == "band_stop"
        assert res["filtered_peak_g"] < res["raw_peak_g"]

    def test_threshold_mode_preserves_below_threshold_harmonics(self):
        """Detail coefficients below threshold_g are preserved unattenuated."""
        sample_rate = 50.0
        t = np.arange(0, 10.24, 1.0 / sample_rate)
        # Small vibration well below 1.0e-4 g threshold
        small_vibe = 1.0e-6 + 2.0e-5 * np.sin(2.0 * np.pi * 10.0 * t)

        res = filter_g_jitter(small_vibe, threshold_g=1.0e-4, mode="threshold")
        # PAR should be 0 or near 0 because small vibration is not clipped
        assert res["peak_acceleration_reduction_percent"] < 5.0


class TestPhysicsFormulas:
    """Verifies Grashof and Richardson combustion hydrodynamics formulations."""

    def test_calculate_grashof_scaling(self):
        """Grashof number scales linearly with effective gravity and cubically with length."""
        gr_base = calculate_grashof(1.0e-6, characteristic_length_m=0.003)
        gr_double_g = calculate_grashof(2.0e-6, characteristic_length_m=0.003)
        assert np.isclose(gr_double_g, 2.0 * gr_base, rtol=1e-5)

        gr_double_l = calculate_grashof(1.0e-6, characteristic_length_m=0.006)
        assert np.isclose(gr_double_l, 8.0 * gr_base, rtol=1e-5)

    def test_calculate_richardson_scaling(self):
        """Richardson number scales inversely with ventilation velocity squared."""
        gr = 5.0
        ri_1 = calculate_richardson(gr, characteristic_length_m=0.003, ventilation_velocity_m_s=0.10)
        ri_2 = calculate_richardson(gr, characteristic_length_m=0.003, ventilation_velocity_m_s=0.20)
        assert np.isclose(ri_2, ri_1 / 4.0, rtol=1e-5)

    def test_vector_grashof_and_richardson(self):
        """Vector inputs to calculate_grashof and calculate_richardson return numpy arrays."""
        arr = np.array([1e-6, 1e-4, 1e-3])
        gr_arr = calculate_grashof(arr)
        assert isinstance(gr_arr, np.ndarray)
        assert len(gr_arr) == 3

        ri_arr = calculate_richardson(gr_arr)
        assert isinstance(ri_arr, np.ndarray)
        assert len(ri_arr) == 3


class TestWaveletSpecsEndpointMetadata:
    """Verifies technical specifications and metadata returned by get_wavelet_specs."""

    def test_wavelet_specs_db4(self):
        specs = get_wavelet_specs(sample_rate_hz=50.0, levels=5, wavelet="db4")
        assert specs["wavelet"] == "db4"
        assert specs["taps"] == 8
        assert specs["vanishing_moments"] == 4
        assert len(specs["scaling_coefficients_h"]) == 8
        assert len(specs["wavelet_coefficients_g"]) == 8
        assert specs["sample_rate_hz"] == 50.0
        assert specs["decomposition_levels"] == 5

        bands = specs["frequency_subbands"]
        # 5 detail bands + 1 approximation band = 6 total bands
        assert len(bands) == 6

        # Check detail band 1 (12.5 - 25 Hz)
        d1 = bands[0]
        assert d1["band"] == "D1"
        assert d1["type"] == "detail"
        assert np.isclose(d1["frequency_high_hz"], 25.0)
        assert np.isclose(d1["frequency_low_hz"], 12.5)

        # Check detail band 4 (1.5625 - 3.125 Hz) -> Astronaut exercise band
        d4 = bands[3]
        assert d4["band"] == "D4"
        assert "Astronaut Exercise" in d4["description"]

        # Check approximation band A5 (0 - 0.7812 Hz) -> Quiescent microgravity
        a5 = bands[5]
        assert a5["band"] == "A5"
        assert a5["type"] == "approximation"
        assert a5["frequency_low_hz"] == 0.0

    def test_wavelet_specs_db2(self):
        specs = get_wavelet_specs(sample_rate_hz=50.0, levels=3, wavelet="db2")
        assert specs["wavelet"] == "db2"
        assert specs["taps"] == 4
        assert specs["vanishing_moments"] == 2


class TestValidationAndErrorHandling:
    """Verifies comprehensive boundary validation and error handling."""

    def test_short_signal_rejection(self):
        """Signals shorter than 8 samples must raise ValueError."""
        with pytest.raises(ValueError, match="at least 8 samples"):
            filter_g_jitter([1e-6] * 7)

    def test_nan_and_inf_rejection(self):
        """Signals containing NaN or Inf must raise ValueError adhering to Rule 4."""
        nan_signal = [1e-6] * 16
        nan_signal[5] = float("nan")
        with pytest.raises(ValueError, match="invalid non-numeric or NaN values"):
            filter_g_jitter(nan_signal)

        inf_signal = [1e-6] * 16
        inf_signal[3] = float("inf")
        with pytest.raises(ValueError, match="invalid non-numeric or NaN values"):
            filter_g_jitter(inf_signal)

    def test_invalid_decomposition_levels(self):
        """Levels < 1 must raise ValueError."""
        with pytest.raises(ValueError, match="levels must be at least 1"):
            filter_g_jitter([1e-6] * 32, levels=0)

    def test_negative_threshold_rejection(self):
        """Non-positive threshold must raise ValueError."""
        with pytest.raises(ValueError, match="Threshold must be positive"):
            filter_g_jitter([1e-6] * 32, threshold_g=-1.0e-4)

        with pytest.raises(ValueError, match="Threshold must be positive"):
            filter_g_jitter([1e-6] * 32, threshold_g=0.0)

    def test_unsupported_wavelet_family_rejection(self):
        """Unsupported wavelets like 'haar' or 'sym8' must raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported wavelet family"):
            filter_g_jitter([1e-6] * 32, wavelet="haar")

    def test_unsupported_filter_mode_rejection(self):
        """Unsupported filter mode must raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported filter mode"):
            filter_g_jitter([1e-6] * 32, mode="magic_filter")

    def test_multidimensional_input_rejection(self):
        """2D matrices must raise ValueError."""
        with pytest.raises(ValueError, match="1-dimensional"):
            filter_g_jitter(np.zeros((16, 2)))
