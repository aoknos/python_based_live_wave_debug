import numpy as np
from scipy import signal

def lowpass_filter(data, cutoff_freq, sampling_freq):
    """Apply a low-pass Butterworth filter to the data."""
    nyquist = sampling_freq / 2
    normalized_cutoff = cutoff_freq / nyquist
    b, a = signal.butter(4, normalized_cutoff, btype='low', analog=False)
    return signal.filtfilt(b, a, data)
