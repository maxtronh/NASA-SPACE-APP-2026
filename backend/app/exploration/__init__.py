"""
Exploration & 25-Faces Solar System Module — Milestone M9
"""

from backend.app.exploration.solar_physics import (
    PLANETARY_ORBITS,
    THE_25_FACES,
    KeplerianOrbit,
    CartesianCoordinates,
    PlanetaryState,
    HohmannTransferResult,
    FaceTelemetry,
    calculate_planet_position,
    calculate_hohmann_transfer,
    get_all_faces,
    get_face_by_id,
    GM_SUN,
    GM_EARTH,
    GM_MOON,
    GM_MARS,
    AU_M,
)
from backend.app.exploration.qwen_engine import (
    QwenEngine,
    QwenChatRequest,
    QwenChatResponse,
    QwenModelMetadata,
    qwen_copilot_engine,
)
from backend.app.exploration.solar_dataset import (
    generate_solar_25_dataset,
    generate_face_instruction_pairs,
    export_solar_dataset_json,
)

__all__ = [
    "PLANETARY_ORBITS",
    "THE_25_FACES",
    "KeplerianOrbit",
    "CartesianCoordinates",
    "PlanetaryState",
    "HohmannTransferResult",
    "FaceTelemetry",
    "calculate_planet_position",
    "calculate_hohmann_transfer",
    "get_all_faces",
    "get_face_by_id",
    "GM_SUN",
    "GM_EARTH",
    "GM_MOON",
    "GM_MARS",
    "AU_M",
    "QwenEngine",
    "QwenChatRequest",
    "QwenChatResponse",
    "QwenModelMetadata",
    "qwen_copilot_engine",
    "generate_solar_25_dataset",
    "generate_face_instruction_pairs",
    "export_solar_dataset_json",
]
