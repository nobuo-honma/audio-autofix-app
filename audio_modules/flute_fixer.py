import numpy as np
from scipy.signal import butter, sosfiltfilt, medfilt

def fix_flute_crackble(y: np.ndarray, sr: int) -> np.ndarray:
    """
    笛の音割れ・バリバリノイズを除去しつつ、
    太鼓の音に埋もれないよう「通る音（存在感・輪郭）」を強調する処理
    """
    is_stereo = y.ndim > 1

    def process_channel(sig: np.ndarray) -> np.ndarray:
        # 1. 歪み・上限波形の緩和（クリッピング補正）
        max_val = np.max(np.abs(sig))
        if max_val > 0:
            norm_sig = sig / max_val
            threshold = 0.65
            mask_pos = norm_sig > threshold
            mask_neg = norm_sig < -threshold
            
            norm_sig[mask_pos] = threshold + (1 - threshold) * np.tanh((norm_sig[mask_pos] - threshold) / (1 - threshold))
            norm_sig[mask_neg] = -threshold - (1 - threshold) * np.tanh((-norm_sig[mask_neg] - threshold) / (1 - threshold))
            sig = norm_sig * max_val

        # 2. 突発的なバリバリノイズ（スパイク）の低減
        sig_smoothed = medfilt(sig, kernel_size=3)
        
        # 3. 不快なバリバリ感が出る超高域（6.5kHz以上）は抑える
        sos_high = butter(4, 6500, fs=sr, btype='low', output='sos')
        sig_filtered = sosfiltfilt(sos_high, sig_smoothed)

        # 4. バリバリ感が強い領域のピンポイントカット
        sos_notch = butter(2, [4500, 5500], fs=sr, btype='bandstop', output='sos')
        sig_clean = sosfiltfilt(sos_notch, sig_filtered)

        # 5. ★【追加】笛が太鼓に埋もれないための「抜け感（2.2kHz〜3.8kHz）」の強調
        # 笛の音が最も通る周波数帯だけを抽出してミックス
        sos_presence = butter(2, [2200, 3800], fs=sr, btype='bandpass', output='sos')
        flute_presence = sosfiltfilt(sos_presence, sig_clean)
        
        # 笛の輪郭成分を20%ほど持ち上げてミックス（太鼓から浮き出させる）
        sig_final = sig_clean + (flute_presence * 0.35)

        return sig_final

    if is_stereo:
        y_out = np.zeros_like(y)
        for ch in range(y.shape[0]):
            y_out[ch] = process_channel(y[ch])
    else:
        y_out = process_channel(y)

    return y_out