import numpy as np
from scipy.signal import butter, sosfiltfilt

def apply_denoise_and_eq(y: np.ndarray, sr: int, demask: bool = True) -> np.ndarray:
    """
    メモリ消費量を最小限に抑えた高速ノイズ低減 ＆ マスキング調整処理
    """
    is_stereo = y.ndim > 1

    # 1. 100Hz以下の不要な低域ブースノイズ・風切り音をカット
    sos_hp = butter(2, 100, fs=sr, btype='highpass', output='sos')
    
    # 2. 周波数被り（マスキング）調整: 中低域のこもり（200Hz〜400Hz）を軽くリダクション
    sos_demask = butter(2, [200, 400], fs=sr, btype='bandstop', output='sos') if demask else None

    def process_channel(sig: np.ndarray) -> np.ndarray:
        # ハイパス処理
        sig_clean = sosfiltfilt(sos_hp, sig)
        
        # マスキング軽減
        if sos_demask is not None:
            sig_clean = sosfiltfilt(sos_demask, sig_clean)
            
        # 簡易ソフトノイズゲート（サー音などの微小雑音を抑止）
        gate_threshold = 0.015
        abs_sig = np.abs(sig_clean)
        mask = abs_sig < gate_threshold
        sig_clean[mask] *= 0.3  # ノイズフロアを減衰

        return sig_clean

    if is_stereo:
        y_out = np.zeros_like(y)
        for ch in range(y.shape[0]):
            y_out[ch] = process_channel(y[ch])
        return y_out
    else:
        return process_channel(y)