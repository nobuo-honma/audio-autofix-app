import numpy as np
from scipy.signal import butter, sosfiltfilt

def fix_taiko_clarity(y: np.ndarray, sr: int) -> np.ndarray:
    """
    軽量化・高速化した太鼓の濁り低減処理
    """
    is_stereo = y.ndim > 1

    # フィルター事前計算
    sos_hp = butter(2, 45, fs=sr, btype='highpass', output='sos')
    sos_notch1 = butter(2, [150, 280], fs=sr, btype='bandstop', output='sos')
    sos_notch2 = butter(2, [1600, 2400], fs=sr, btype='bandstop', output='sos')

    def process_channel(sig: np.ndarray) -> np.ndarray:
        sig_hp = sosfiltfilt(sos_hp, sig)
        sig_c1 = sosfiltfilt(sos_notch1, sig_hp)
        return sosfiltfilt(sos_notch2, sig_c1)

    if is_stereo:
        y_out = np.zeros_like(y)
        for ch in range(y.shape[0]):
            y_out[ch] = process_channel(y[ch])
        return y_out
    else:
        return process_channel(y)