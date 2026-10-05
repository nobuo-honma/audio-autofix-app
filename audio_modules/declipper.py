import numpy as np

def fix_clipping(y: np.ndarray, threshold: float = 0.85) -> np.ndarray:
    """
    低めの閾値で歪んだ音割れ波形の上限を圧縮・スムージング
    """
    y_fixed = y.copy()
    max_val = np.max(np.abs(y_fixed))
    
    if max_val == 0:
        return y_fixed
        
    y_norm = y_fixed / max_val
    
    # 歪みが発生している波形の天井部分を滑らかなアーク状に収縮
    over_idx = np.abs(y_norm) > threshold
    y_norm[over_idx] = np.sign(y_norm[over_idx]) * (
        threshold + (1 - threshold) * np.sin((np.abs(y_norm[over_idx]) - threshold) / (1 - threshold) * (np.pi / 2))
    )
    
    return y_norm * max_val