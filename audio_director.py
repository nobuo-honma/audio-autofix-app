import io
import gc
import numpy as np
import soundfile as sf
import librosa
import pyloudnorm as pyln

from audio_modules.declipper import fix_clipping
from audio_modules.flute_fixer import fix_flute_crackble
from audio_modules.taiko_fixer import fix_taiko_clarity
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
    メモリ節約・高速化版 パイプライン
    """
    # 1. 22050Hz にダウンサンプリングしてメモリ使用量を半分以下に削減
    target_sr = 22050
    y, sr = librosa.load(io.BytesIO(file_bytes), sr=target_sr, mono=False)
    
    # 2. 音割れ補正
    if declip:
        if y.ndim > 1:
            y[0] = fix_clipping(y[0])
            y[1] = fix_clipping(y[1])
        else:
            y = fix_clipping(y)

    # 3. 笛のバリバリ音低減 ＆ 抜け強調
    if flute:
        y = fix_flute_crackble(y, sr)

    # 4. 太鼓の濁り低減
    y = fix_taiko_clarity(y, sr)

    # 5. ノイズ除去
    if denoise or demask:
        y = apply_denoise_and_eq(y, sr, demask=demask)

    # ガベージコレクションで一時メモリを即座に解放
    gc.collect()

    # 6. ラウドネス正規化 (LUFS)
    is_stereo = y.ndim > 1
    y_trans = y.T if is_stereo else y
    
    try:
        meter = pyln.Meter(sr)
        current_loudness = meter.integrated_loudness(y_trans)
        y_normalized = pyln.normalize.loudness(y_trans, current_loudness, target_lufs)
    except Exception:
        max_val = np.max(np.abs(y_trans))
        y_normalized = y_trans / max_val if max_val > 0 else y_trans

    # 7. 出力生成
    output_io = io.BytesIO()
    sf.write(output_io, y_normalized, sr, format='WAV', subtype='PCM_16')
    output_io.seek(0)
    
    result_bytes = output_io.getvalue()
    
    # 後処理のメモリ解放
    del y, y_trans, y_normalized
    gc.collect()

    return result_bytes