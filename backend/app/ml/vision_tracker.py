"""Computer Vision Flame Front & Sphericity Tracking Module.

Extracts geometric flame features from high-speed combustion video frames:
1. Equivalent flame diameter (d_f = 2 * sqrt(Area / pi)).
2. Sphericity index (Psi = 4 * pi * Area / Perimeter^2).
3. Buoyancy vs microgravity regime classification.
4. Soot shell stand-off ratio (SSOR).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class FlameFrameMetrics:
    frame_index: int
    time_s: float
    flame_area_px2: float
    perimeter_px: float
    equivalent_diameter_px: float
    sphericity_index: float
    centroid_x: float
    centroid_y: float
    soot_standoff_ratio: Optional[float]


@dataclass
class FlameTrackingResult:
    total_frames_analyzed: int
    mean_sphericity: float
    peak_diameter_px: float
    regime_classification: str
    is_microgravity_symmetric: bool
    frames: List[FlameFrameMetrics] = field(default_factory=list)


class FlameVisionTracker:
    """Scientific vision tracker analyzing flame contours in microgravity vs buoyant environments."""

    @classmethod
    def analyze_frame(
        cls,
        image_2d: np.ndarray,
        frame_index: int = 0,
        time_s: float = 0.0,
        intensity_threshold: float = 0.35,
        droplet_radius_px: Optional[float] = None,
    ) -> FlameFrameMetrics:
        """Analyzes a 2D grayscale/intensity array for flame front geometry."""
        # Normalize to [0.0, 1.0]
        img = np.array(image_2d, dtype=float)
        img_min, img_max = img.min(), img.max()
        if img_max > img_min:
            img = (img - img_min) / (img_max - img_min)
        else:
            img = np.zeros_like(img)

        # Threshold to binary flame mask
        mask = img >= intensity_threshold
        area = float(np.sum(mask))

        if area <= 4.0:
            return FlameFrameMetrics(
                frame_index=frame_index,
                time_s=round(time_s, 4),
                flame_area_px2=0.0,
                perimeter_px=0.0,
                equivalent_diameter_px=0.0,
                sphericity_index=0.0,
                centroid_x=img.shape[1] / 2.0,
                centroid_y=img.shape[0] / 2.0,
                soot_standoff_ratio=None,
            )

        # Centroid calculation
        y_indices, x_indices = np.where(mask)
        cx = float(np.mean(x_indices))
        cy = float(np.mean(y_indices))

        # Boundary perimeter estimation using morphological gradient
        # Pixel boundary count
        padded = np.pad(mask, 1, mode="constant", constant_values=0)
        # Shift in 4 directions
        up = padded[:-2, 1:-1]
        down = padded[2:, 1:-1]
        left = padded[1:-1, :-2]
        right = padded[1:-1, 2:]
        boundary = mask & ~(up & down & left & right)
        perimeter = max(1.0, float(np.sum(boundary)))

        # Equivalent circular diameter
        eq_diam = 2.0 * math.sqrt(area / math.pi)

        # Sphericity / isoperimetric quotient: Psi = 4 * pi * Area / Perimeter^2
        # For a discrete pixel grid, circular shapes produce Psi ~ 0.85 - 1.0
        psi = min(1.0, (4.0 * math.pi * area) / (perimeter ** 2))

        # Soot Stand-Off Ratio (SSOR)
        ssor = None
        if droplet_radius_px and droplet_radius_px > 0:
            flame_radius = eq_diam / 2.0
            ssor = round(flame_radius / droplet_radius_px, 3)

        return FlameFrameMetrics(
            frame_index=frame_index,
            time_s=round(time_s, 4),
            flame_area_px2=round(area, 2),
            perimeter_px=round(perimeter, 2),
            equivalent_diameter_px=round(eq_diam, 2),
            sphericity_index=round(psi, 4),
            centroid_x=round(cx, 2),
            centroid_y=round(cy, 2),
            soot_standoff_ratio=ssor,
        )

    @classmethod
    def track_sequence(
        cls,
        frames: List[np.ndarray],
        fps: float = 30.0,
        intensity_threshold: float = 0.35,
        droplet_radius_px: Optional[float] = None,
    ) -> FlameTrackingResult:
        """Processes sequential combustion video frames into geometric timeseries."""
        frame_metrics: List[FlameFrameMetrics] = []

        for idx, frame in enumerate(frames):
            t = idx / fps
            metrics = cls.analyze_frame(
                image_2d=frame,
                frame_index=idx,
                time_s=t,
                intensity_threshold=intensity_threshold,
                droplet_radius_px=droplet_radius_px,
            )
            frame_metrics.append(metrics)

        valid_sphericity = [f.sphericity_index for f in frame_metrics if f.flame_area_px2 > 0]
        mean_psi = float(np.mean(valid_sphericity)) if valid_sphericity else 0.0
        peak_d = max([f.equivalent_diameter_px for f in frame_metrics]) if frame_metrics else 0.0

        # Microgravity criterion: sphericity index >= 0.88 for discrete pixel grid
        is_microgravity = mean_psi >= 0.88
        regime = "microgravity_spherical" if is_microgravity else "buoyant_convective_plume"

        return FlameTrackingResult(
            total_frames_analyzed=len(frames),
            mean_sphericity=round(mean_psi, 4),
            peak_diameter_px=round(peak_d, 2),
            regime_classification=regime,
            is_microgravity_symmetric=is_microgravity,
            frames=frame_metrics,
        )

    @staticmethod
    def generate_synthetic_flame_frames(
        regime: str = "microgravity",
        num_frames: int = 10,
        grid_size: int = 64,
    ) -> List[np.ndarray]:
        """Generates authentic synthetic flame intensity arrays for testing."""
        frames = []
        cy, cx = grid_size // 2, grid_size // 2
        y, x = np.ogrid[:grid_size, :grid_size]

        for i in range(num_frames):
            if regime == "microgravity":
                # Perfectly spherical / radial profile
                radius = 12.0 + 2.0 * math.sin(i / 2.0)
                dist_sq = (x - cx) ** 2 + (y - cy) ** 2
                intensity = np.exp(-dist_sq / (2.0 * (radius ** 2)))
            else:
                # 1g buoyant teardrop plume: elongated vertical ellipse within image bounds
                rx = 6.0 + 0.5 * math.sin(i / 2.0)
                ry = 22.0 + 1.0 * math.cos(i / 2.0)
                # Offset center downward so flame extends upwards without edge truncation
                flame_cy = cy + 4.0
                dist_norm = ((x - cx) / rx) ** 2 + ((y - flame_cy) / ry) ** 2
                intensity = np.exp(-dist_norm / 2.0)

            frames.append(intensity)

        return frames
