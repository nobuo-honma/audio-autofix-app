import torch
import demucs.separate

def separate_stems(input_path: str, output_dir: str):
    """
    AIモデル(Demucs)で ボーカル / ドラム / ベース / その他 に分離
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    demucs.separate.main(["-n", "htdemucs", "-o", output_dir, "--device", device, input_path])