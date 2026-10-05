import numpy as np
from scipy.signal import butter, sosfiltfilt, medfilt

def fix_flute_crackble(y: np.ndarray, sr: int) -> np.ndarray:
    """
    重度のクリッピング・過大入力による「バリバリノイズ」を強力に除去・平滑化する処理
    """
    is_stereo = y.ndim > 1

    def process_channel(sig: np.ndarray) -> np.ndarray:
        # 1. 限界値付近の極端な歪みピークを検知してダイナミックに抑圧
        max_val = np.max(np.abs(sig))
        if max_val > 0:
            norm_sig = sig / max_val
            # 閾値（0.7以上）のバリバリしたスパイク波形を対数関数的に圧縮して歪みを丸める
            threshold = 0.65
            mask_pos = norm_sig > threshold
            mask_neg = norm_sig < -threshold
            
            norm_sig[mask_pos] = threshold + (1 - threshold) * np.tanh((norm_sig[mask_pos] - threshold) / (1 - threshold))
            norm_sig[mask_neg] = -threshold - (1 - threshold) * np.tanh((-norm_sig[mask_neg] - threshold) / (1 - threshold))
            sig = norm_sig * max_val

        # 2. 高域の鋭いバリバリノイズ（スパイク）を中央値フィルタで除去
        # (短い時間の突発ノイズを平滑化)
        sig_smoothed = medfilt(sig, kernel_size=3)
        
        # 3. 笛の倍音ノイズ帯域 (3kHz〜8kHz) の過剰な突き上げを低減
        sos_high = butter(4, 6500, fs=sr, btype='low', output='sos')
        sig_filtered = sosfiltfilt(sos_high, sig_smoothed)

        # 4. バリバリ感が強く出る 3.5kHz〜5.5kHz を帯域制限
        sos_notch = butter(2, [3500, 5500], fs=sr, btype='bandstop', output='sos')
        sig_final = sosfiltfilt(sos_notch, sig_filtered)

        return sig_final

    if is_stereo:
        y_out = np.zeros_like(y)
        for ch in range(y.shape[0]):
            y_out[ch] = process_channel(y[ch])
    else:
        y_out = process_channel(y)

    return y_out