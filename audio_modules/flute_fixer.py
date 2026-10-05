import numpy as np
from scipy.signal import butter, sosfiltfilt

def fix_flute_crackble(y: np.ndarray, sr: int) -> np.ndarray:
    """
    軽量化・高速化した笛のバリバリ音低減＆存在感強調処理
    """
    is_stereo = y.ndim > 1

    # 1. フィルターの事前計算（ループ外で作成してメモリ・CPU負荷を軽減）
    sos_high = butter(4, 6500, fs=sr, btype='low', output='sos')
    sos_notch = butter(2, [4500, 5500], fs=sr, btype='bandstop', output='sos')
    sos_presence = butter(2, [2200, 3800], fs=sr, btype='bandpass', output='sos')

    def process_channel(sig: np.ndarray) -> np.ndarray:
        # 歪み・クリッピング緩和 (In-place処理風に軽く計算)
        max_val = np.max(np.abs(sig))
        if max_val > 0:
            threshold = 0.7
            over = np.abs(sig) > (max_val * threshold)
            sig[over] = np.sign(sig[over]) * (max_val * threshold + (np.abs(sig[over]) - max_val * threshold) * 0.3)

        # フィルター処理
        sig_filtered = sosfiltfilt(sos_high, sig)
        sig_clean = sosfiltfilt(sos_notch, sig_filtered)

        # 笛の音の抜け（存在感）強調
        flute_presence = sosfiltfilt(sos_presence, sig_clean)
        return sig_clean + (flute_presence * 0.3)

    if is_stereo:
        y_out = np.zeros_like(y)
        for ch in range(y.shape[0]):
            y_out[ch] = process_channel(y[ch])
        return y_out
    else:
        return process_channel(y)