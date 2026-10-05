import io
import soundfile as sf
import numpy as np
import librosa
import pyloudnorm as pyln

from audio_modules.declipper import fix_clipping
from audio_modules.flute_fixer import fix_flute_crackble
from audio_modules.denoiser import apply_denoise_and_eq

def process_audio_director(
    file_bytes: bytes,
    declip: bool = True,
    denoise: bool = True,
    demask: bool = True,
    flute: bool = True,
    target_lufs: float = -14.0
) -> bytes:
    """
    オーディオディレクターメイン処理パイプライン
    """
    # 1. 音声データの読み込み
    y, sr = librosa.load(io.BytesIO(file_bytes), sr=None, mono=False)
    is_stereo = y.ndim > 1

    # 2. 音割れ補正 (De-clip)
    if declip:
        if is_stereo:
            y[0] = fix_clipping(y[0])
            y[1] = fix_clipping(y[1])
        else:
            y = fix_clipping(y)

    # 3. 笛のバリバリ音低減
    if flute:
        y = fix_flute_crackble(y, sr)

    # 4. ノイズ除去 & マスキング軽減
    if denoise or demask:
        y = apply_denoise_and_eq(y, sr, demask=demask)

    # 5. ターゲットラウドネス正規化 (LUFS調整)
    meter = pyln.Meter(sr)
    y_trans = y.T if is_stereo else y
    
    try:
        current_loudness = meter.integrated_loudness(y_trans)
        y_normalized = pyln.normalize.loudness(y_trans, current_loudness, target_lufs)
    except Exception:
        # 短すぎる音声などでラウドネス計算に失敗した場合は通常のピークノーマライズ
        max_val = np.max(np.abs(y_trans))
        y_normalized = y_trans / max_val if max_val > 0 else y_trans

    # 6. WAVバイナリデータへの出力
    output_io = io.BytesIO()
    sf.write(output_io, y_normalized, sr, format='WAV', subtype='PCM_16')
    output_io.seek(0)

    return output_io.getvalue()