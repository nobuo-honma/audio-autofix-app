import numpy as np
import noisereduce as nr
import librosa

def apply_denoise_and_eq(y: np.ndarray, sr: int, demask: bool = True) -> np.ndarray:
    """
    AIノイズ除去およびマスキング（中低域のこもり感）低減フィルター
    """
    # 1. ノイズ除去
    y_denoised = nr.reduce_noise(y=y, sr=sr, stationary=True, prop_decrease=0.75)

    # 2. マスキング軽減（太鼓や会場の残響でこもりやすい 200Hz〜400Hz 帯のピークを軽減）
    if demask:
        # スペクトル解析で中低域のエネルギー過多を判定・調整
        S = np.abs(librosa.stft(y_denoised[0] if y_denoised.ndim > 1 else y_denoised))
        freqs = librosa.fft_frequencies(sr=sr)
        mask = (freqs >= 200) & (freqs <= 400)
        
        if np.mean(S[mask, :]) > np.mean(S) * 1.5:
            # 250Hz付近にQ値低めのノッチフィルターを適用
            from scipy.signal import butter, sosfiltfilt
            sos_demask = butter(2, [200, 400], fs=sr, btype='bandstop', output='sos')
            if y_denoised.ndim > 1:
                for ch in range(y_denoised.shape[0]):
                    y_denoised[ch] = sosfiltfilt(sos_demask, y_denoised[ch])
            else:
                y_denoised = sosfiltfilt(sos_demask, y_denoised)

    return y_denoised