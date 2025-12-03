import numpy as np

def compute_fft(data, n_points=256):
    """
    Compute FFT magnitude spectrum of the signal.

    Parameters:
    - data: Input signal array
    - n_points: Number of FFT points (default: 256)

    Returns:
    - freqs: Frequency bins
    - magnitude: FFT magnitude spectrum
    """
    # Take last n_points for FFT
    signal = data[-n_points:] if len(data) >= n_points else data

    # Compute FFT
    fft_vals = np.fft.rfft(signal, n=n_points)
    magnitude = np.abs(fft_vals)

    return magnitude
