"""REST API endpoints for Active Learning Bayesian Optimal Experiment Design (Upgrade E-08)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, status

from backend.app.ml.active_learning import (
    FACILITY_CATALOG,
    HISTORICAL_MICROGRAVITY_PRIORS,
    PARAM_BOUNDS,
    PARAM_KEYS,
    GaussianProcessRegressorARD,
    UCBOptimizer,
)
from backend.app.schemas.active_learning import (
    FacilityOperationalEnvelope,
    GPPredictRequest,
    GPPredictResponse,
    GPPredictResult,
    OEDOptimizeRequest,
    OEDOptimizeResponse,
    ParameterBoundsResponse,
)

router = APIRouter(prefix="/active-learning", tags=["active-learning"])


@router.post("/optimize", response_model=OEDOptimizeResponse)
async def optimize_experiment_design(payload: OEDOptimizeRequest):
    """Proposes optimal flight experiment parameters using Gaussian Process UCB acquisition."""
    priors_raw = None
    if payload.priors:
        priors_raw = [
            {
                "parameters": {
                    "pressure_kpa": p.parameters.pressure_kpa,
                    "oxygen_pct": p.parameters.oxygen_pct,
                    "ventilation_cm_s": p.parameters.ventilation_cm_s,
                    "initial_diameter_mm": p.parameters.initial_diameter_mm,
                },
                "observed_value": p.observed_value,
                "facility": p.facility,
            }
            for p in payload.priors
        ]

    try:
        result = UCBOptimizer.optimize(
            target_metric=payload.target_metric,
            kappa=payload.kappa,
            num_proposals=payload.num_proposals,
            facility=payload.facility or "iss_cir",
            fixed_parameters=payload.fixed_parameters,
            custom_priors=priors_raw,
        )
        return OEDOptimizeResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Active learning optimization failed: {exc}",
        )


@router.post("/surrogate/predict", response_model=GPPredictResponse)
async def predict_surrogate(payload: GPPredictRequest):
    """Evaluates Gaussian Process surrogate posterior mean and uncertainty over specific test points."""
    # 1. Gather prior trials
    priors_raw = HISTORICAL_MICROGRAVITY_PRIORS
    if payload.priors and len(payload.priors) >= 2:
        priors_raw = [
            {
                "pressure_kpa": p.parameters.pressure_kpa,
                "oxygen_pct": p.parameters.oxygen_pct,
                "ventilation_cm_s": p.parameters.ventilation_cm_s,
                "initial_diameter_mm": p.parameters.initial_diameter_mm,
                "observed_value": p.observed_value,
            }
            for p in payload.priors
        ]

    X_train_list = []
    y_train_list = []
    for item in priors_raw:
        params = item.get("parameters", item)
        X_train_list.append([
            float(params["pressure_kpa"]),
            float(params["oxygen_pct"]),
            float(params["ventilation_cm_s"]),
            float(params["initial_diameter_mm"]),
        ])
        y_train_list.append(float(item.get("observed_value", 0.70)))

    gp = GaussianProcessRegressorARD()
    gp.fit(np.array(X_train_list, dtype=float), np.array(y_train_list, dtype=float))

    # 2. Evaluate candidate points
    test_coords = []
    for pt in payload.points:
        test_coords.append([
            pt.pressure_kpa,
            pt.oxygen_pct,
            pt.ventilation_cm_s,
            pt.initial_diameter_mm,
        ])
    X_test = np.array(test_coords, dtype=float)

    means, stds = gp.predict(X_test)

    results: list[GPPredictResult] = []
    for i, pt in enumerate(payload.points):
        m = float(means[i])
        s = float(stds[i])
        ucb = m + payload.kappa * s
        ent = 0.5 * math.log(2.0 * math.pi * math.e * (s ** 2) + 1e-12)

        results.append(
            GPPredictResult(
                parameters=pt,
                mean=round(m, 4),
                std=round(s, 4),
                ucb=round(ucb, 4),
                entropy=round(ent, 4),
            )
        )

    return GPPredictResponse(
        target_metric="burning_rate_mm2_s",
        predictions=results,
    )


@router.get("/parameter-bounds", response_model=ParameterBoundsResponse)
async def get_parameter_bounds():
    """Returns parameter bounds, physical units, and NASA flight facility constraints."""
    bounds = {k: [v[0], v[1]] for k, v in PARAM_BOUNDS.items()}
    units = {
        "pressure_kpa": "kPa",
        "oxygen_pct": "vol %",
        "ventilation_cm_s": "cm/s",
        "initial_diameter_mm": "mm",
    }
    facilities = [FacilityOperationalEnvelope(**f) for f in FACILITY_CATALOG.values()]

    return ParameterBoundsResponse(
        bounds=bounds,
        units=units,
        facilities=facilities,
    )


@router.get("/facilities", response_model=list[FacilityOperationalEnvelope])
async def list_facilities():
    """Lists NASA microgravity research facilities and their operational flight envelopes."""
    return [FacilityOperationalEnvelope(**f) for f in FACILITY_CATALOG.values()]
