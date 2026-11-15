"""Pydantic data schemas for microgravity combustion anomaly and contradiction detection (E-09).

Defines request and response models for evaluating combustion behaviors that fundamentally
contradict classical 1g terrestrial combustion intuition, backed by authentic NASA flight archives.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, model_validator


class NASAArchiveCitation(BaseModel):
    """Authentic NASA technical report or flight investigation citation."""

    investigation_slug: str = Field(..., description="Normalized investigation slug in repository")
    project_acronym: str = Field(..., description="Flight mission or investigation acronym (e.g. 'FLEX', 'BASS-II', 'ACME')")
    mission: str = Field(default="", description="Mission name alias")
    title: str = Field(..., description="Official report or paper title")
    nasa_ntrs_id: str = Field(..., description="NASA Technical Reports Server (NTRS) accession ID")
    ntrs_id: str = Field(default="", description="Alias for nasa_ntrs_id")
    nasa_source_url: str = Field(..., description="Direct NTRS / STI landing page URL")
    doi: str | None = Field(default=None, description="Digital Object Identifier if published in journal")
    citation_text: str = Field(..., description="Standard academic citation string")
    flight_facility: str = Field(..., description="Microgravity research facility (e.g. 'CIR / MDCA', 'MSG')")
    primary_investigators: list[str] = Field(default_factory=list, description="Principal investigators")
    verification_status: str = Field(default="AUTHENTIC_NASA_ARCHIVE", description="Provenance verification status")

    @model_validator(mode="after")
    def populate_citation_aliases(self) -> NASAArchiveCitation:
        if not self.mission:
            self.mission = self.project_acronym
        if not self.ntrs_id:
            self.ntrs_id = self.nasa_ntrs_id
        return self


class MicrogravityAnomaly(BaseModel):
    """Individual combustion contradiction defying classical 1g intuition."""

    anomaly_id: str = Field(..., description="Unique anomaly identifier (e.g. 'ANOMALY_MICRO_DRAFT_PARADOX')")
    title: str = Field(..., description="Human-readable contradiction title")
    name: str = Field(default="", description="Alias for title")
    regime: str = Field(..., description="Combustion regime ('solid_flame_spread', 'isolated_droplet_combustion', 'low_temperature_chemistry')")
    divergence_score: float = Field(..., ge=0.0, le=1.0, description="Divergence from classical 1g theory [0.0, 1.0]")
    contradiction_level: str = Field(..., description="Severity level: 'CRITICAL', 'STRONG_CONTRADICTION', 'MODERATE_CONTRADICTION', 'MILD_CONTRADICTION', 'CONSISTENT_WITH_1G'")
    mechanism: str = Field(..., description="Microgravity physical mechanism explaining the counter-intuitive behavior")
    physical_mechanism: str = Field(default="", description="Alias for mechanism")
    classical_1g_behavior: str = Field(..., description="Terrestrial 1g intuition or classical combustion prediction")
    classical_1g_prediction: str = Field(default="", description="Alias for classical_1g_behavior")
    microgravity_behavior: str = Field(..., description="Actual microgravity observation and physics")
    microgravity_observation: str = Field(default="", description="Alias for microgravity_behavior")
    quantitative_metrics: dict[str, Any] = Field(default_factory=dict, description="Calculated physical and dimensionless metrics")
    governing_parameters: dict[str, Any] = Field(default_factory=dict, description="Alias for quantitative_metrics")
    evidence_measurements: dict[str, Any] = Field(default_factory=dict, description="Alias for quantitative_metrics")
    citations: list[NASAArchiveCitation] = Field(default_factory=list, description="Authentic NASA flight citations")
    verifiable_citations: list[NASAArchiveCitation] = Field(default_factory=list, description="Alias for citations")

    @model_validator(mode="after")
    def populate_anomaly_aliases(self) -> MicrogravityAnomaly:
        if not self.name:
            self.name = self.title
        if not self.physical_mechanism:
            self.physical_mechanism = self.mechanism
        if not self.classical_1g_prediction:
            self.classical_1g_prediction = self.classical_1g_behavior
        if not self.microgravity_observation:
            self.microgravity_observation = self.microgravity_behavior
        if not self.governing_parameters:
            self.governing_parameters = dict(self.quantitative_metrics)
        if not self.evidence_measurements:
            self.evidence_measurements = dict(self.quantitative_metrics)
        if not self.verifiable_citations:
            self.verifiable_citations = list(self.citations)
        return self


class AnomalyDetectionRequest(BaseModel):
    """Payload for detecting microgravity combustion anomalies and contradictions."""

    fuel: str = Field(default="n-heptane", description="Fuel or material name (e.g. 'n-heptane', 'pmma', 'methanol')")
    regime: str | None = Field(default=None, description="Optional target combustion regime filter")
    gravity_level: str | None = Field(default="microgravity (~10^-6 g)", description="Gravity condition string")
    gravity_level_g: float | None = Field(default=None, ge=0.0, le=10.0, description="Gravity level in Earth g (0.0 to 10.0)")
    ventilation_velocity_cm_s: float = Field(default=3.0, ge=0.0, le=200.0, description="Concurrent/forced air speed in cm/s")
    initial_diameter_mm: float | None = Field(default=None, ge=0.1, le=50.0, description="Droplet diameter or sample thickness in mm")
    droplet_diameter_mm: float | None = Field(default=None, ge=0.1, le=50.0, description="Droplet diameter in mm")
    ambient_o2_percentage: float | None = Field(default=None, ge=1.0, le=100.0, description="Ambient oxygen volume %")
    o2_percentage: float | None = Field(default=None, ge=1.0, le=100.0, description="Ambient oxygen volume %")
    chamber_pressure_kpa: float = Field(default=101.325, ge=10.0, le=500.0, description="Ambient chamber pressure in kPa")
    fuel_temperature_k: float | None = Field(default=None, ge=100.0, le=3000.0, description="Core / flame zone temperature in K")
    temperature_k: float | None = Field(default=None, ge=100.0, le=3000.0, description="Core / flame zone temperature in K")
    investigation_slug: str | None = Field(default=None, description="Optional authentic NASA investigation slug")

    @model_validator(mode="after")
    def synchronize_aliases(self) -> AnomalyDetectionRequest:
        # Synchronize diameter
        if self.initial_diameter_mm is not None and self.droplet_diameter_mm is None:
            self.droplet_diameter_mm = self.initial_diameter_mm
        elif self.droplet_diameter_mm is not None and self.initial_diameter_mm is None:
            self.initial_diameter_mm = self.droplet_diameter_mm
        elif self.initial_diameter_mm is None and self.droplet_diameter_mm is None:
            self.initial_diameter_mm = 3.0
            self.droplet_diameter_mm = 3.0

        # Synchronize O2 percentage
        if self.ambient_o2_percentage is not None and self.o2_percentage is None:
            self.o2_percentage = self.ambient_o2_percentage
        elif self.o2_percentage is not None and self.ambient_o2_percentage is None:
            self.ambient_o2_percentage = self.o2_percentage
        elif self.ambient_o2_percentage is None and self.o2_percentage is None:
            self.ambient_o2_percentage = 21.0
            self.o2_percentage = 21.0

        # Synchronize temperature
        if self.fuel_temperature_k is not None and self.temperature_k is None:
            self.temperature_k = self.fuel_temperature_k
        elif self.temperature_k is not None and self.fuel_temperature_k is None:
            self.fuel_temperature_k = self.temperature_k
        elif self.fuel_temperature_k is None and self.temperature_k is None:
            self.fuel_temperature_k = 720.0
            self.temperature_k = 720.0

        # Synchronize gravity
        if self.gravity_level_g is not None:
            if self.gravity_level_g < 0.1:
                self.gravity_level = (
                    "microgravity (~10^-6 g)"
                    if self.gravity_level_g <= 1e-4
                    else f"partial_gravity ({self.gravity_level_g:.2f} g)"
                )
            else:
                self.gravity_level = f"normal_gravity ({self.gravity_level_g:.2f} g)"
        else:
            g_str = (self.gravity_level or "").lower()
            if "micro" in g_str or "zero" in g_str or "10^" in g_str or "0g" in g_str:
                self.gravity_level_g = 1e-6
            elif "normal" in g_str or "1g" in g_str or "terrestrial" in g_str:
                self.gravity_level_g = 1.0
            elif "partial" in g_str:
                match = re.search(r"([0-9]*\.?[0-9]+)", g_str)
                if match:
                    try:
                        self.gravity_level_g = float(match.group(1))
                    except ValueError:
                        self.gravity_level_g = 0.05
                else:
                    self.gravity_level_g = 0.05
            else:
                self.gravity_level_g = 1e-6

        return self


class AnomalyDetectionResponse(BaseModel):
    """Result of microgravity combustion anomaly and contradiction evaluation."""

    anomalies_detected: list[MicrogravityAnomaly] = Field(default_factory=list, description="Contradictions meeting detection threshold")
    anomalies: list[MicrogravityAnomaly] = Field(default_factory=list, description="All evaluated contradiction records")
    detected_anomalies_count: int = Field(..., description="Number of active microgravity contradictions detected")
    overall_divergence_score: float = Field(..., ge=0.0, le=1.0, description="Overall divergence score from 1g intuition [0.0, 1.0]")
    max_divergence_score: float = Field(..., ge=0.0, le=1.0, description="Maximum individual contradiction divergence score [0.0, 1.0]")
    gravity_level: str = Field(..., description="Evaluated gravitational condition")
    primary_contradiction: str | None = Field(default=None, description="Dominant contradiction ID if detected")
    summary: str = Field(..., description="Executive scientific summary")
    scientific_summary: str = Field(default="", description="Detailed scientific summary alias")
    citations: list[NASAArchiveCitation] = Field(default_factory=list, description="Authentic NASA flight archive citations")
    verifiable_citations: list[NASAArchiveCitation] = Field(default_factory=list, description="Verifiable citations alias")

    @model_validator(mode="after")
    def populate_response_aliases(self) -> AnomalyDetectionResponse:
        if not self.scientific_summary:
            self.scientific_summary = self.summary
        if not self.verifiable_citations:
            self.verifiable_citations = list(self.citations)
        return self
