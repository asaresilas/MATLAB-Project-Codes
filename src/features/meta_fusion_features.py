import numpy as np


def ensure_3_classes(probs: np.ndarray) -> np.ndarray:
    """Match the training-time class handling exactly."""
    if probs.shape[1] < 3:
        return np.pad(probs, ((0, 0), (0, 3 - probs.shape[1])), mode="constant")
    return probs[:, :3]


def build_nasa_probs(ruls: np.ndarray) -> np.ndarray:
    """Convert scalar NASA RUL predictions into the 3-class training encoding."""
    nasa_prob = np.zeros((len(ruls), 3), dtype=np.float32)
    for i, rul in enumerate(ruls):
        norm_rul = np.clip(rul / 100.0, 0, 1)
        p = np.zeros(3, dtype=np.float32)
        p[0] = norm_rul
        p[2] = 1.0 - norm_rul
        p[1] = 4.0 * norm_rul * (1.0 - norm_rul)
        p = p / (np.sum(p) + 1e-9)
        nasa_prob[i] = p
    return nasa_prob


def get_rich_features(probs: np.ndarray) -> np.ndarray:
    ent = -np.sum(probs * np.log(np.clip(probs, 1e-7, 1.0)), axis=1, keepdims=True)
    sorted_p = np.sort(probs, axis=1)
    margin = (sorted_p[:, -1] - sorted_p[:, -2]).reshape(-1, 1)
    return np.hstack([probs, ent, margin])


def extract_meta_features_from_predictions(preds: dict) -> np.ndarray:
    expert_names = ["CWRU", "Induction", "NASA", "Current", "Thermal"]
    meta_blocks = [get_rich_features(preds[name]) for name in expert_names]
    x_meta = np.hstack(meta_blocks)
    mean_p = np.mean([preds[name] for name in expert_names], axis=0)
    var_p = np.var([preds[name] for name in expert_names], axis=0)
    global_ent = -np.sum(mean_p * np.log(np.clip(mean_p, 1e-7, 1.0)), axis=1, keepdims=True)
    return np.hstack([x_meta, mean_p, var_p, global_ent])
