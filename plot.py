import matplotlib.pyplot as plt
import numpy as np

def plot_signals(y_raw, y_filtered, fft_raw, fft_filtered, fsamp, buffer_size, fft_points):
    """
    Display signals and FFT using matplotlib.

    Parameters:
    - y_raw: Raw signal data
    - y_filtered: Filtered signal data
    - fft_raw: FFT magnitude of raw signal
    - fft_filtered: FFT magnitude of filtered signal
    - fsamp: Sampling frequency
    - buffer_size: Size of time domain buffer
    - fft_points: Number of FFT points
    """
    plt.clf()

    # Create subplots: Time domain (top), FFT (bottom)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Time domain plot
    x_time = np.arange(buffer_size)
    ax1.plot(x_time, y_raw, label='Raw', color='blue', linewidth=1)
    ax1.plot(x_time, y_filtered, label='Filtered', color='red', linewidth=1)
    ax1.set_title('Signal - Real Time')
    ax1.set_xlabel('Sample Index')
    ax1.set_ylabel('Voltage (V)')
    ax1.legend()
    ax1.grid(True)

    # FFT plot
    x_freq = np.linspace(0, fsamp / 2, fft_points // 2 + 1)
    ax2.plot(x_freq, fft_raw, label='Raw FFT', color='blue', linewidth=1)
    ax2.plot(x_freq, fft_filtered, label='Filtered FFT', color='red', linewidth=1)
    ax2.set_title('FFT Spectrum (256 points)')
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Magnitude')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.pause(0.001)
