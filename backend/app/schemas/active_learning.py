"""Pydantic schemas for Active Learning Bayesian Optimal Experiment Design (Upgrade E-08)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ExperimentPointInput(BaseModel):
    """Coordinates within the 4D microgravity combustion parameter space."""

    pressure_kpa: float = Field(
        ...,
        ge=20.0,
        le=300.0,
        description="Chamber total pressure in kPa [20.0, 300.0]"
    )
    oxygen_pct: float = Field(
        ...,
        ge=12.0,
        le=50.0,
        description="Oxygen volume percentage [12.0, 50.0] %"
    )
    ventilation_cm_s: float = Field(
        ...,
        ge=0.0,
        le=30.0,
        description="Forced ventilation flow velocity in cm/s [0.0, 30.0]"
    )
    initial_diameter_mm: float = Field(
        ...,
        ge=0.5,
        le=6.0,
        description="Initial droplet/sample diameter in mm [0.5, 6.0]"
    )


class HistoricalTrial(BaseModel):
    """A previously recorded physical flight or drop tower trial."""

    parameters: ExperimentPointInput
    observed_value: float = Field(
        ...,
        description="Measured physical response (e.g. burning rate K in mm²/s)"
    )
    facility: Optional[str] = Field(default=None, description="Flight facility (e.g. 'iss_cir', 'glenn_drop_tower_2_2s')")
    trial_id: Optional[str] = Field(default=None, description="Experiment run identifier")


class OEDOptimizeRequest(BaseModel):
    """Request payload for proposing optimal flight test parameters via Gaussian Process UCB."""

    target_metric: str = Field(
        default="burning_rate_mm2_s",
        description="Target combustion response to maximize information gain (e.g. 'burning_rate_mm2_s', 'extinction_diameter_mm')"
    )
    kappa: float = Field(
        default=2.0,
        ge=0.0,
        le=10.0,
        description="Upper Confidence Bound (UCB) exploration weight kappa: alpha(x) = mu(x) + kappa * sigma(x)"
    )
    num_proposals: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of ranked experiment proposals to generate"
    )
    facility: Optional[str] = Field(
        default="iss_cir",
        description="Target NASA flight facility constraint ('iss_cir', 'glenn_drop_tower_2_2s', 'glenn_zero_g_5_18s', 'parabolic_aircraft', 'all')"
    )
    fixed_parameters: Optional[dict[str, float]] = Field(
        default=None,
        description="Optional dictionary to freeze specific dimensions (e.g. {'pressure_kpa': 101.325})"
    )
    priors: Optional[list[HistoricalTrial]] = Field(
        default=None,
        description="Optional custom prior trials. If None, authentic historical NASA baseline dataset is utilized."
    )


class ProposedExperimentPoint(BaseModel):
    """An optimized flight test proposal."""

    rank: int = Field(..., description="Rank in proposal list (1 = top information gain)")
    parameters: ExperimentPointInput
    predicted_mean: float = Field(..., description="Gaussian Process posterior mean mu(x)")
    predicted_std: float = Field(..., description="Gaussian Process epistemic uncertainty sigma(x)")
    acquisition_score_ucb: float = Field(..., description="Upper Confidence Bound score alpha_UCB(x) = mu + kappa * sigma")
    expected_information_gain: float = Field(..., description="Differential entropy reduction Delta H(x) = 0.5 * ln(2 * pi * e * sigma^2)")
    facility_compatibility: str = Field(..., description="Compatibility statement with target flight facility")
    estimated_burn_duration_s: float = Field(..., description="Estimated droplet burning lifetime d0^2 / K in seconds")
    rationale: str = Field(..., description="Scientific explanation of why this point yields high physical discovery value")


class OEDOptimizeResponse(BaseModel):
    """Response containing ranked optimal experiment design candidates."""

    target_metric: str
    kappa: float
    facility: str
    total_proposals: int
    prior_trials_count: int
    model_fit_rmse: float = Field(..., description="Leave-one-out or fit Root Mean Square Error on prior trials")
    ard_lengthscales: dict[str, float] = Field(..., description="Automatic Relevance Detection kernel lengthscales per parameter")
    proposals: list[ProposedExperimentPoint]


class GPPredictRequest(BaseModel):
    """Request payload to query GP surrogate prediction over specific points."""

    points: list[ExperimentPointInput] = Field(..., min_length=1, max_length=100)
    kappa: float = Field(default=2.0, ge=0.0, le=10.0)
    priors: Optional[list[HistoricalTrial]] = None


class GPPredictResult(BaseModel):
    """GP surrogate prediction for a single coordinate."""

    parameters: ExperimentPointInput
    mean: float
    std: float
    ucb: float
    entropy: float


class GPPredictResponse(BaseModel):
    """Response with surrogate predictions."""

    target_metric: str
    predictions: list[GPPredictResult]


class FacilityOperationalEnvelope(BaseModel):
    """Operational envelope and constraints of a NASA microgravity facility."""

    facility_id: str
    name: str
    gravity_level: str
    test_duration_s: float
    max_droplet_diameter_mm: float
    pressure_range_kpa: list[float]
    oxygen_range_pct: list[float]
    ventilation_range_cm_s: list[float]
    description: str


class ParameterBoundsResponse(BaseModel):
    """Operational parameter bounds, units, and facility constraints."""

    bounds: dict[str, list[float]]
    units: dict[str, str]
    facilities: list[FacilityOperationalEnvelope]
