"""
Preprocessing: convert to a single intensity channel and flatten illumination.

Validated behaviour: removes the warm colour cast and the central-bright /
edge-dark vignetting visible in real A549 images, leaving the granular spheroid
evenly contrasted against a uniform background.
"""
import numpy as np
import cv2

from ..config import PreprocessConfig


def to_gray(rgb: np.ndarray, channel: str = "green") -> np.ndarray:
    """Collapse a warm RGB image to one intensity channel (float32)."""
    if channel == "green":
        return rgb[:, :, 1].astype(np.float32)
    if channel == "luminance":
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    if channel == "gray":
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    raise ValueError(f"unknown channel: {channel}")


def flatten_illumination(gray: np.ndarray, bg_sigma: float = 80.0) -> np.ndarray:
    """Subtract a large-Gaussian background model; rescale to uint8 [0,255]."""
    bg = cv2.GaussianBlur(gray, (0, 0), sigmaX=bg_sigma)
    flat = gray - bg
    flat -= flat.min()
    flat = flat / (flat.max() + 1e-6) * 255.0
    return flat.astype(np.uint8)


def preprocess(rgb: np.ndarray, cfg: PreprocessConfig) -> np.ndarray:
    """Full preprocessing: returns an illumination-flattened uint8 image."""
    gray = to_gray(rgb, cfg.channel)
    return flatten_illumination(gray, cfg.bg_sigma)
