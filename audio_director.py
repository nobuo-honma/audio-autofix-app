import numpy as np
import librosa
import soundfile as sf
import pyloudnorm as pyln

from audio_modules.declipper import fix_clipping
from audio_modules.denoiser import remove_background_noise
from audio_modules.flute_fixer import fix_flute_crackble
from audio_modules.taiko_fixer import fix_taiko_clarity  # 新しく追加

def process_audio_pipeline(input_path: str, output_path: str):
    # 1. 音声の読み込み
    y, sr = librosa.load(input_path, sr=None, mono=False)
    
    # 2. 音割れ・クリッピング修復
    y_declipped = fix_clipping(y)
    
    # 3. 笛のバリバリ音・高域ノイズの修復
    y_flute_fixed = fix_flute_crackble(y_declipped, sr)

    # 4. 複数太鼓の濁り・低域かぶりの修正（新設）
    y_taiko_fixed = fix_taiko_clarity(y_flute_fixed, sr)
    
    # 5. サー・ヒスノイズ等の背景ノイズ除去
    y_denoised = remove_background_noise(y_taiko_fixed, sr)
    
    # 6. 音量（ラウドネス）の最適化 (-14 LUFS)
    meter = pyln.Meter(sr)
    
    # ステレオ/モノラルの処理分岐
    if y_denoised.ndim > 1:
        loudness = meter.integrated_loudness(y_denoised.T)
        y_normalized = pyln.normalize.loudness(y_denoised.T, loudness, -14.0).T
    else:
        loudness = meter.integrated_loudness(y_denoised)
        y_normalized = pyln.normalize.loudness(y_denoised, loudness, -14.0)

    # 7. ファイル保存
    sf.write(output_path, y_normalized.T if y_normalized.ndim > 1 else y_normalized, sr)