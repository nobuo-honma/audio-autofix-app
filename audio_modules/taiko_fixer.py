import numpy as np
from scipy.signal import butter, sosfiltfilt

def fix_taiko_clarity(y: np.ndarray, sr: int) -> np.ndarray:
    """
    太鼓の濁りを抑え、笛の音がしっかり聞こえるように音域の隙間をつくる処理
    """
    is_stereo = y.ndim > 1

    def process_channel(sig: np.ndarray) -> np.ndarray:
        # 1. 不要な超低域（40Hz以下）をカット
        sos_hp = butter(4, 40, fs=sr, btype='highpass', output='sos')
        sig_clean = sosfiltfilt(sos_hp, sig)

        # 2. 太鼓同士の重なりによる濁り帯域（150Hz〜300Hz）のカット
        sos_notch1 = butter(2, [150, 300], fs=sr, btype='bandstop', output='sos')
        sig_clarified = sosfiltfilt(sos_notch1, sig_clean)

        # 3. ★【追加】笛の音（2kHz付近）と衝突する「太鼓の張り・鳴り成分（1.5kHz〜2.5kHz）」を少し抑える
        # これにより太鼓の音に小さな「ポケット」ができ、笛の音が前に出てきます
        sos_notch2 = butter(2, [1500, 2500], fs=sr, btype='bandstop', output='sos')
        sig_space_made = sosfiltfilt(sos_notch2, sig_clarified)

        # 4. 太鼓本来の「ドッ」というアタックの芯（800Hz〜1.2kHz）は活かす
        sos_bp = butter(2, [800, 1200], fs=sr, btype='bandpass', output='sos')
        attack_comp = sosfiltfilt(sos_bp, sig)
        
        sig_out = sig_space_made + (attack_comp * 0.2)

        return sig_out

    if is_stereo:
        y_out = np.zeros_like(y)
        for ch in range(y.shape[0]):
            y_out[ch] = process_channel(y[ch])
    else:
        y_out = process_channel(y)

    return y_out