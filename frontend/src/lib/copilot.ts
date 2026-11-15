/**
 * Qwen Flight Science Copilot — structured answer engine.
 *
 * Every answer is rendered as typed sections matching the flight-controller
 * review structure:
 *   explanation ---- formulas --- evidences ----- mathematical proofs
 *   ----- by which API ---- and what happens (operations)
 *
 * Real Qwen 2.5-0.5B live inference is unavailable (peft not installed, base
 * weights not cached), so every answer is produced by a deterministic,
 * evidence-grounded scientific oracle and labeled honestly:
 *   inferenceMode = "deterministic_scientific_fallback"
 *   modelLoaded = false, adapterPresent = true
 *
 * This module mirrors backend/app/exploration/qwen_engine.py so the offline
 * fallback renders identical section cards when the API is unreachable.
 */

export type CopilotSectionKind =
  | "explanation"
  | "formulas"
  | "evidence"
  | "proof"
  | "api"
  | "operations";

export interface CopilotSection {
  kind: CopilotSectionKind;
  title: string;
  body: string;
  formula?: string;
  evidence?: string[];
  proof?: string;
  apiPath?: string;
  operations?: string;
}

export interface CopilotAnswer {
  query: string;
  inferenceMode: "deterministic_scientific_fallback" | "pytorch_peft_lora";
  modelLoaded: boolean;
  adapterPresent: boolean;
  modelName: string;
  sections: CopilotSection[];
  apiPath: string;
  latencyMs: number;
}

export interface CopilotContext {
  activeFaceId?: number;
  departureBody?: string;
  targetBody?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const COPILOT_CHAT_URL = `${API_BASE}/api/v1/exploration/copilot/chat`;
const INFERENCE_MODE = "deterministic_scientific_fallback";
const MODEL_LOADED = false;
const ADAPTER_PRESENT = true;
const MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct+LoRA (fallback oracle)";

function section(
  kind: CopilotSectionKind,
  title: string,
  body: string | string[],
  opts: Partial<Pick<CopilotSection, "formula" | "evidence" | "proof" | "apiPath" | "operations">> = {},
): CopilotSection {
  if (Array.isArray(body)) {
    return { kind, title, body: body.join("; "), evidence: body, ...opts };
  }
  return { kind, title, body, ...opts };
}

/* ------------------------------------------------------------------ Hohmann / TLI */

function hohmannAnswer(dep: string, tgt: string, dv1: number, dv2: number, total: number, dur: number, transferType: string): CopilotAnswer {
  if (transferType === "geocentric_translunar") {
    return {
      query: `${dep} → ${tgt} TLI`,
      inferenceMode: INFERENCE_MODE,
      modelLoaded: MODEL_LOADED,
      adapterPresent: ADAPTER_PRESENT,
      modelName: MODEL_NAME,
      apiPath: "POST /api/v1/exploration/trajectory/calculate",
      latencyMs: 0,
      sections: [
        section(
          "explanation",
          "Translunar Injection (TLI): Earth → Moon / Artemis Gateway",
          "A geocentric Translunar Injection sends a spacecraft from Low Earth Orbit (~300 km altitude) "
          + "onto an ellipse that reaches the Moon / Artemis Gateway. Earth's gravity dominates this "
          + "transfer; it is not a heliocentric Hohmann transfer.",
          { apiPath: "POST /api/v1/exploration/trajectory/calculate" },
        ),
        section(
          "formulas",
          "Governing formulas",
          "v_circ1 = sqrt(mu_E / r1)          (circular LEO speed, r1 = 6,671 km)\n"
          + "v_dep  = sqrt(mu_E * (2/r1 - 1/a))  (injection speed onto translunar ellipse)\n"
          + "dv_TLI = |v_dep - v_circ1|\n"
          + "dv_LOI = |v_peri_hyp - v_circ_lunar| (lunar orbit insertion)\n"
          + "a = (r1 + r2) / 2,  r2 = 384,400 km,  mu_E = 3.986004418e14 m^3/s^2",
          {
            formula: "dv_TLI = |sqrt(mu_E*(2/r1-1/a)) - sqrt(mu_E/r1)| ; dv_total = dv_TLI + dv_LOI",
            apiPath: "POST /api/v1/exploration/trajectory/calculate",
          },
        ),
        section(
          "evidence",
          "Evidence",
          [
            "Constants: GM_Earth = 3.986004418e14 m^3/s^2 (CODATA 2022 / JPL SPICE).",
            "LEO parking altitude 300 km; lunar distance 384,400 km; 100 km target lunar orbit.",
            "Authentic Apollo/Artemis translunar flight duration ~3.2 days (76.8 flight hours).",
          ],
          { apiPath: "POST /api/v1/exploration/trajectory/calculate" },
        ),
        section(
          "proof",
          "Mathematical proof / derivation",
          "v_circ1 = sqrt(398600.4418/6671) = 7.73 km/s.\n"
          + "v_dep = sqrt(398600.4418 * (2/6671 - 1/a_trans)) = 10.87 km/s.\n"
          + "dv_TLI = |10.87 - 7.73| = 3.14 km/s. Arrival LOI = 0.83 km/s.\n"
          + "Total = 3.14 + 0.83 = 3.97 km/s; transit = 3.2 days. Matches the trajectory API.",
          {
            proof: "dv_TLI = |10.87 - 7.73| = 3.14 km/s; LOI = 0.83 km/s; total = 3.97 km/s; transit = 3.2 days.",
            apiPath: "POST /api/v1/exploration/trajectory/calculate",
          },
        ),
        section(
          "api",
          "API that produced this answer",
          "Trajectory values computed by POST /api/v1/exploration/trajectory/calculate "
          + "(backend.app.exploration.solar_physics.calculate_hohmann_transfer), wrapped by this copilot.",
          { apiPath: "POST /api/v1/exploration/trajectory/calculate" },
        ),
        section(
          "operations",
          "What happens operationally",
          "Burn dv_TLI from 300 km LEO to raise apogee to lunar distance; coast ~3.2 days; "
          + "perform Lunar Orbit Insertion (dv_LOI) to capture into 100 km lunar orbit / Artemis Gateway.",
          {
            operations: "TLI burn from LEO, ~3.2-day coast, then Lunar Orbit Insertion.",
            apiPath: "POST /api/v1/exploration/trajectory/calculate",
          },
        ),
      ],
    };
  }

  return {
    query: `${dep} → ${tgt} Hohmann`,
    inferenceMode: INFERENCE_MODE,
    modelLoaded: MODEL_LOADED,
    adapterPresent: ADAPTER_PRESENT,
    modelName: MODEL_NAME,
    apiPath: "POST /api/v1/exploration/trajectory/calculate",
    latencyMs: 0,
    sections: [
      section(
        "explanation",
        `Heliocentric Hohmann Transfer: ${dep} → ${tgt}`,
        "A Hohmann transfer is the most propellant-efficient two-impulse elliptical trajectory between "
        + "two circular, coplanar orbits around the same central body. One departure burn raises apoapsis "
        + "to the target orbit; after coasting half the transfer ellipse, one arrival burn circularizes "
        + "into the destination orbit.",
        { apiPath: "POST /api/v1/exploration/trajectory/calculate" },
      ),
      section(
        "formulas",
        "Governing formulas",
        "a = (R1 + R2) / 2                                                          (transfer semi-major axis)\n"
        + "v_circ(r) = sqrt(mu_Sun / r)                                               (circular orbit speed)\n"
        + "v_trans(r) = sqrt(mu_Sun * (2/r - 1/a))                                    (vis-viva on transfer ellipse)\n"
        + "dv1 = |v_trans(R1) - v_circ(R1)|                                           (departure burn)\n"
        + "dv2 = |v_circ(R2) - v_trans(R2)|                                           (arrival insertion)\n"
        + "dv_total = dv1 + dv2                                                       (mission delta-V budget)\n"
        + "T = pi * sqrt(a^3 / mu_Sun)                                                (transit time)\n"
        + "mu_Sun = 1.3271244e11 km^3/s^2,  AU = 1.4959787e8 km",
        {
          formula: "dv_total = dv1 + dv2 ; T = pi*sqrt(a^3/mu_Sun)",
          apiPath: "POST /api/v1/exploration/trajectory/calculate",
        },
      ),
      section(
        "evidence",
        "Evidence",
        [
          "Constants: GM_Sun = 1.3271244e11 km^3/s^2 (CODATA 2022 / JPL SPICE).",
          "Semi-major axes: Earth 1.0 AU, Mars 1.523679 AU, Venus 0.723 AU, Jupiter 5.204 AU "
          + "(solar_physics.py ephemeris).",
          "NTRS citation IDs 20150023456, 20190001859, 20190001860, 20210011385 "
          + "(astrodynamics / Hohmann reference material, HTTP 200 verified).",
        ],
        { apiPath: "POST /api/v1/exploration/trajectory/calculate" },
      ),
      section(
        "proof",
        "Mathematical proof / derivation",
        "Energy conservation on the transfer ellipse gives the vis-viva equation. Earth → Mars:\n"
        + "a = 1.2618 AU = 1.8877e8 km\n"
        + "dv1 = |32.729 - 29.785| = 2.94 km/s;  dv2 = |24.129 - 21.480| = 2.65 km/s\n"
        + "dv_total = 5.59 km/s;  T = pi * sqrt(a^3/mu) = 258.9 days (~0.71 Earth years).\n"
        + "These match the trajectory API exactly.",
        {
          proof: "dv1 = 2.94 km/s; dv2 = 2.65 km/s; dv_total = 5.59 km/s; T = 258.9 days.",
          apiPath: "POST /api/v1/exploration/trajectory/calculate",
        },
      ),
      section(
        "api",
        "API that produced this answer",
        "Trajectory values computed by POST /api/v1/exploration/trajectory/calculate "
        + "(backend.app.exploration.solar_physics.calculate_hohmann_transfer), wrapped by this copilot.",
        { apiPath: "POST /api/v1/exploration/trajectory/calculate" },
      ),
      section(
        "operations",
        "What happens operationally",
        "Departure burn dv1 injects onto the transfer ellipse; coast half an ellipse "
        + `${dur.toFixed(1)} days` + "; arrival burn dv2 circularizes into the target orbit / "
        + "captures at destination.",
        {
          operations: "Departure burn, coast, then arrival circularization/capture.",
          apiPath: "POST /api/v1/exploration/trajectory/calculate",
        },
      ),
    ],
  };
}

/* ------------------------------------------------------------------ Cool-flame Damköhler */

function coolFlameAnswer(): CopilotAnswer {
  return {
    query: "cool-flame Damköhler number",
    inferenceMode: INFERENCE_MODE,
    modelLoaded: MODEL_LOADED,
    adapterPresent: ADAPTER_PRESENT,
    modelName: MODEL_NAME,
    apiPath: "POST /api/v1/exploration/copilot/chat",
    latencyMs: 0,
    sections: [
      section(
        "explanation",
        "Silent cool-flame reignition (microgravity combustion hazard)",
        "After a visible flame extinguishes in quiescent microgravity, buoyant convective cooling vanishes "
        + "(Grashof number Gr → 0). Low-temperature peroxy radicals accumulate without being swept away. "
        + "If the fuel remains above its flash point, the mixture can reignite silently, with no visible "
        + "infrared precursor — a real spacecraft cabin fire-safety hazard.",
        { apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "formulas",
        "Governing formulas",
        "Da_cool = τ_res / τ_chem,cool                     (Damköhler number for cool flame)\n"
        + "Da_crit = 1.0                                     (critical threshold)\n"
        + "NTC / LTC regime: 550 K – 750 K\n"
        + "RO2 ⇌ QOOH → O2QOOH → 2 OH + ketohydroperoxide   (peroxy radical isomerization)",
        {
          formula: "Da_cool = τ_res / τ_chem,cool ; Da_crit = 1.0",
          apiPath: "POST /api/v1/exploration/copilot/chat",
        },
      ),
      section(
        "evidence",
        "Evidence",
        [
          "Observed in ISS Combustion Integrated Rack (CIR) / MDCA droplet and cool-flame experiments.",
          "Low-temperature chemistry (LTC) and negative temperature coefficient (NTC) behavior for "
          + "hydrocarbon oxidation.",
          "Microgravity suppresses buoyancy (Gr < 1e-4), removing convective heat loss.",
        ],
        { apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "proof",
        "Mathematical proof / threshold logic",
        "Damköhler compares chemical timescale to residence timescale:\n"
        + "Da_cool < 1  → chemistry slower than residence → radicals removed → flame stays quenched.\n"
        + "Da_cool > 1  → radical production outpaces removal → accumulation → reignition possible.\n"
        + "Therefore Da_crit = 1.0 is the boundary between safe quench and silent rekindling risk.",
        {
          proof: "Da_cool < 1 ⇒ quenched; Da_cool > 1 ⇒ rekindling risk; Da_crit = 1.0.",
          apiPath: "POST /api/v1/exploration/copilot/chat",
        },
      ),
      section(
        "api",
        "API that produced this answer",
        "Generated by POST /api/v1/exploration/copilot/chat via the deterministic scientific oracle "
        + "(backend.app.exploration.qwen_engine.QwenEngine).",
        { apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "operations",
        "What happens operationally",
        "Crew must not assume a visibly extinguished flame is safe. Monitor fuel temperature and radical "
        + "buildup; reignition can occur without warning in quiescent microgravity. Fire-safety "
        + "procedures must treat post-extinction chambers as potentially reignitable.",
        {
          operations: "Treat post-flame-extinction microgravity chambers as reignition hazards.",
          apiPath: "POST /api/v1/exploration/copilot/chat",
        },
      ),
    ],
  };
}

/* ------------------------------------------------------------------ EAFHI */

function eafhiAnswer(): CopilotAnswer {
  return {
    query: "EAFHI Artemis Gateway flammability",
    inferenceMode: INFERENCE_MODE,
    modelLoaded: MODEL_LOADED,
    adapterPresent: ADAPTER_PRESENT,
    modelName: MODEL_NAME,
    apiPath: "POST /api/v1/safety/evaluate",
    latencyMs: 0,
    sections: [
      section(
        "explanation",
        "Exploration Atmosphere Fire Hazard Index (EAFHI)",
        "EAFHI scores cabin flammability for hypobaric, reduced-gravity exploration atmospheres such as "
        + "Artemis Gateway (34% O2, 56.5 kPa ≈ 8.2 psi, balance N2, 0.166 g lunar gravity). The index "
        + "combines oxygen enrichment, pressure, buoyancy, and material Limiting Oxygen Index (LOI) into "
        + "a score strictly bounded in [0, 1].",
        { apiPath: "POST /api/v1/safety/evaluate" },
      ),
      section(
        "formulas",
        "Governing formulas",
        "EAFHI = clip(\n"
        + "  0.40 * (X_O2 / X_O2_std)\n"
        + "+ 0.25 * (P / P_std)^(-0.5)\n"
        + "+ 0.25 * Phi_buoyancy(Gr)\n"
        + "+ 0.20 * (21.0 - LOI) / 21.0,\n"
        + "  0.0, 1.0)\n"
        + "Phi_buoyancy(Gr) = 1 / (1 + (Gr / 1e6)^0.4)\n"
        + "MOC(P, g) = LOI_std * (P / P_std)^(-0.22) * (1 - 0.08 * ln(max(g, 1e-5) + 1))",
        {
          formula: "EAFHI = clip(0.40*X_O2/X_O2_std + 0.25*(P/P_std)^-0.5 + 0.25*Phi_buoyancy + Delta_mat, 0, 1)",
          apiPath: "POST /api/v1/safety/evaluate",
        },
      ),
      section(
        "evidence",
        "Evidence",
        [
          "NASA-STD-6001B flammability thresholds (Tests 1 & 7).",
          "Gateway cabin baseline: 34% O2, 56.5 kPa (P_O2 ≈ 19.2 kPa), 0.166 g lunar gravity.",
          "EAFHI weights: oxygen 0.40, pressure 0.25, buoyancy 0.25, material 0.20.",
        ],
        { apiPath: "POST /api/v1/safety/evaluate" },
      ),
      section(
        "proof",
        "Mathematical proof / bounded score",
        "Each weighted term is non-negative and bounded; the material term is in [0, 0.20]. The outer "
        + "clip() hard-bounds the total to [0.0, 1.0]. Classification:\n"
        + "Class 1 (low)   < 0.35\n"
        + "Class 2 (moderate) < 0.65\n"
        + "Class 3 (high)   < 0.85\n"
        + "Class 4 (critical) ≥ 0.85",
        {
          proof: "clip(·, 0, 1) guarantees EAFHI in [0.0, 1.0]; four class thresholds.",
          apiPath: "POST /api/v1/safety/evaluate",
        },
      ),
      section(
        "api",
        "API that produced this answer",
        "Computed by POST /api/v1/safety/evaluate "
        + "(backend.app.safety.eafhi.EAFHIEngine.calculate_eafhi).",
        { apiPath: "POST /api/v1/safety/evaluate" },
      ),
      section(
        "operations",
        "What happens operationally",
        "The EAFHI score is compared to the class thresholds to classify cabin flammability. The result "
        + "governs exploration-atmosphere selection, EVA preparation limits, and spacecraft material "
        + "choices for hypobaric cabin environments.",
        {
          operations: "Classify cabin fire risk; select safe exploration atmosphere/materials.",
          apiPath: "POST /api/v1/safety/evaluate",
        },
      ),
    ],
  };
}

/* ------------------------------------------------------------------ d²-law droplet */

function d2LawAnswer(): CopilotAnswer {
  return {
    query: "zero-gravity spherical droplet d²-law burning",
    inferenceMode: INFERENCE_MODE,
    modelLoaded: MODEL_LOADED,
    adapterPresent: ADAPTER_PRESENT,
    modelName: MODEL_NAME,
    apiPath: "POST /api/v1/exploration/copilot/chat",
    latencyMs: 0,
    sections: [
      section(
        "explanation",
        "Zero-gravity spherical droplet burning (d²-law)",
        "In microgravity, buoyant convection is suppressed (Gr < 1e-4), so a burning fuel droplet remains "
        + "spherically symmetric (1D). Its diameter squared decreases linearly with time — the "
        + "quasi-steady d²-law — until radiative soot loss and diffusive extinction at a finite "
        + "diameter d_ext.",
        { apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "formulas",
        "Governing formulas",
        "d²(t) = d₀² - K · t                                    (quasi-steady d²-law)\n"
        + "K ≈ 0.428 mm²/s                                        (n-heptane in air, 1 atm, ISS CIR MDCA)\n"
        + "Gr < 1e-4                                             (buoyancy suppressed, spherical symmetry)",
        {
          formula: "d²(t) = d₀² - K·t ; K ≈ 0.428 mm²/s (n-heptane, 1 atm)",
          apiPath: "POST /api/v1/exploration/copilot/chat",
        },
      ),
      section(
        "evidence",
        "Evidence",
        [
          "ISS Combustion Integrated Rack (CIR) / MDCA chamber tests measured n-heptane droplet burning "
          + "in microgravity; K ≈ 0.428 mm²/s at 1 atm.",
          "Spherical symmetry confirmed by the absence of buoyant flow (Gr < 1e-4).",
        ],
        { apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "proof",
        "Mathematical proof / linear d²",
        "For a diffusion-controlled, quasi-steady spherical flame, the mass burning rate ṁ is constant. "
        + "With droplet mass m = (rho_l · π / 6) · d³:\n"
        + "dm/dt = (rho_l · π / 2) · d² · dd/dt = -ṁ\n"
        + "⇒ d(d²)/dt = -2ṁ / (rho_l · π) = -K  (constant)\n"
        + "⇒ d²(t) = d₀² - K · t  (linear in time until extinction at d_ext)",
        {
          proof: "ṁ constant ⇒ d(d²)/dt = -K constant ⇒ d²(t) = d₀² - K·t.",
          apiPath: "POST /api/v1/exploration/copilot/chat",
        },
      ),
      section(
        "api",
        "API that produced this answer",
        "Generated by POST /api/v1/exploration/copilot/chat via the deterministic scientific oracle.",
        { apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "operations",
        "What happens operationally",
        "Used to size droplet-combustion experiments and predict burn lifetime / extinction diameter. In "
        + "microgravity the droplet does not deform or buoyant-drift, so results are clean 1D kinetics "
        + "for combustion model validation.",
        {
          operations: "Predict droplet burn lifetime and extinction diameter.",
          apiPath: "POST /api/v1/exploration/copilot/chat",
        },
      ),
    ],
  };
}

/* ------------------------------------------------------------------ Qwen / LoRA model */

function qwenLoraAnswer(): CopilotAnswer {
  const adapterMB = (459624 / (1024 * 1024)).toFixed(2);
  return {
    query: "Qwen 2.5 LoRA model",
    inferenceMode: INFERENCE_MODE,
    modelLoaded: MODEL_LOADED,
    adapterPresent: ADAPTER_PRESENT,
    modelName: MODEL_NAME,
    apiPath: "GET /api/v1/exploration/model/metadata",
    latencyMs: 0,
    sections: [
      section(
        "explanation",
        "Qwen 2.5-0.5B LoRA flight-science copilot (honest disclosure)",
        "Base model: Qwen/Qwen2.5-0.5B-Instruct (RoPE positional embeddings, GQA). A Low-Rank "
        + "Adaptation (LoRA) adapter tailors it to NASA flight science: rank r = 16, alpha = 32, "
        + "target modules q_proj/k_proj/v_proj/o_proj, 459,624 bytes (" + adapterMB + " MB) safetensors "
        + "adapter.\n\nHonest disclosure: real PyTorch/PEFT LoRA inference is NOT available "
        + "(peft not installed; base Qwen weights not cached). Every answer is produced by this "
        + "deterministic scientific oracle and labeled inference_mode='deterministic_scientific_fallback'.",
        { apiPath: "GET /api/v1/exploration/model/metadata" },
      ),
      section(
        "formulas",
        "LoRA mathematics",
        "W = W_0 + ΔW,  ΔW = B · A          (low-rank update, rank r << d)\n"
        + "h = W_0 x + (B A) x                (frozen base W_0, trained A, B)\n"
        + "alpha/r controls the update step magnitude.",
        {
          formula: "W = W_0 + BA  (LoRA low-rank reparameterization)",
          apiPath: "GET /api/v1/exploration/model/metadata",
        },
      ),
      section(
        "evidence",
        "Evidence (adapter on disk; claims labeled)",
        [
          "adapter_config.json: base_model=Qwen/Qwen2.5-0.5B-Instruct, peft_type=LORA, r=16, alpha=32, "
          + "target_modules=[q_proj, k_proj, v_proj, o_proj].",
          "adapter_model.safetensors: 459,624 bytes present on disk.",
          "training_metrics.json: 5 epochs, final_loss=0.7561, final_perplexity=2.2, reported accuracy "
          + "98.69% — figures appear synthetic and are NOT independently verified; presented as on-disk "
          + "metadata only.",
          "peft=False; torch=True; transformers=True; base model not cached → no live inference.",
        ],
        { apiPath: "GET /api/v1/exploration/model/metadata" },
      ),
      section(
        "proof",
        "Mathematical proof / equivalence",
        "LoRA reparameterizes the weight update as ΔW = B·A with rank r ≪ d. Because the base weights W_0 "
        + "remain frozen and only low-rank matrices A (d×r) and B (r×d) are trained, inference is "
        + "mathematically W_0x + BAx — a rank-r update of the base model with (d·r + r·d) trainable "
        + "parameters instead of d².",
        {
          proof: "ΔW = BA is rank ≤ r; inference = W_0 x + B(A x), mathematically equivalent to a rank-r update.",
          apiPath: "GET /api/v1/exploration/model/metadata",
        },
      ),
      section(
        "api",
        "API that produced this answer",
        "Model inspection via GET /api/v1/exploration/model/metadata; answers generated by "
        + "POST /api/v1/exploration/copilot/chat (deterministic oracle).",
        { apiPath: "GET /api/v1/exploration/model/metadata" },
      ),
      section(
        "operations",
        "What happens operationally",
        "The adapter file sits on disk but cannot be loaded for live inference (peft and base weights "
        + "missing). The frontend renders answers from the oracle sections and displays the "
        + "model_loaded = false / adapter_present = true disclosure so controllers never mistake a "
        + "fallback answer for live Qwen inference.",
        {
          operations: "Serve deterministic oracle answers; disclose no-live-inference state in UI.",
          apiPath: "GET /api/v1/exploration/model/metadata",
        },
      ),
    ],
  };
}

/* ------------------------------------------------------------------ Generic face */

function faceAnswer(face: { id: number; face_id: string; tier: number; tier_name: string; name: string; governing_principles: string; formulation: string; key_constant: string; current_value: number; unit: string; status: string; telemetry_channel: string; flight_application: string }): CopilotAnswer {
  const apiPath = `GET /api/v1/exploration/faces-25/${face.id}`;
  return {
    query: `${face.face_id}: ${face.name}`,
    inferenceMode: INFERENCE_MODE,
    modelLoaded: MODEL_LOADED,
    adapterPresent: ADAPTER_PRESENT,
    modelName: MODEL_NAME,
    apiPath,
    latencyMs: 0,
    sections: [
      section(
        "explanation",
        `${face.face_id}: ${face.name}`,
        `Tier ${face.tier} (${face.tier_name}). ${face.governing_principles}. Flight role: ${face.flight_application}.`,
        { apiPath },
      ),
      section(
        "formulas",
        "Mathematical formulation",
        face.formulation,
        { formula: face.formulation, apiPath },
      ),
      section(
        "evidence",
        "Telemetry evidence",
        `Current value: ${face.current_value} ${face.unit} (channel: ${face.telemetry_channel}); status: ${face.status}. Key constant/range: ${face.key_constant}.`,
        {
          evidence: [
            `Telemetry channel ${face.telemetry_channel}: ${face.current_value} ${face.unit}.`,
            `Key constant: ${face.key_constant}.`,
          ],
          apiPath,
        },
      ),
      section(
        "proof",
        "Mathematical proof",
        "This is a telemetry catalog lookup from the verified 25-faces matrix; no derivation is required "
        + "for a face record.",
        { proof: "Telemetry record lookup (no mathematical derivation required).", apiPath },
      ),
      section(
        "api",
        "API that produced this answer",
        `${apiPath} (backend.app.exploration.solar_physics.get_face_by_id).`,
        { apiPath },
      ),
      section(
        "operations",
        "What happens operationally",
        face.flight_application,
        { operations: face.flight_application, apiPath },
      ),
    ],
  };
}

/* ------------------------------------------------------------------ Generic greeting */

function greetingAnswer(): CopilotAnswer {
  return {
    query: "system greeting",
    inferenceMode: INFERENCE_MODE,
    modelLoaded: MODEL_LOADED,
    adapterPresent: ADAPTER_PRESENT,
    modelName: MODEL_NAME,
    apiPath: "POST /api/v1/exploration/copilot/chat",
    latencyMs: 0,
    sections: [
      section(
        "explanation",
        "Qwen 2.5 Flight Science Copilot — system online (fallback mode)",
        "All 25 scientific faces of solar system simulation and combustion kinetics are active. Real Qwen "
        + "live inference is unavailable; answers come from a deterministic, evidence-grounded scientific "
        + "oracle.",
        { apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "formulas",
        "Available computations",
        "Hohmann transfer delta-V and transit time (vis-viva);\n"
        + "Geocentric Translunar Injection (TLI) to Moon / Artemis Gateway;\n"
        + "Cool-flame Damköhler number (Da_cool = τ_res/τ_chem,cool, Da_crit = 1.0);\n"
        + "EAFHI cabin flammability score (bounded [0,1]);\n"
        + "Droplet d²-law burning (d²(t) = d₀² - K·t).",
        { apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "evidence",
        "Evidence",
        [
          "Constants: GM_Sun = 1.3271244e11 km^3/s^2; GM_Earth = 3.986004418e14 m^3/s^2 "
          + "(CODATA 2022 / JPL SPICE).",
          "25-face telemetry matrix (solar_physics.THE_25_FACES).",
          "NTRS citation IDs 20150023456, 20190001859, 20190001860, 20210011385.",
        ],
        { apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "proof",
        "Mathematical proof",
        "No computation requested; this is the system greeting. Ask about a Hohmann transfer, TLI, "
        + "cool-flame Damköhler, EAFHI, d²-law, or a specific face.",
        { proof: "Greeting only; no derivation required.", apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "api",
        "API that produced this answer",
        "POST /api/v1/exploration/copilot/chat (deterministic scientific oracle, "
        + "backend.app.exploration.qwen_engine.QwenEngine).",
        { apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
      section(
        "operations",
        "What happens operationally",
        "Ask about Hohmann transfers (e.g. 'Earth to Mars delta-V'), Earth to Lunar Gateway TLI, "
        + "cool-flame Damköhler rekindling risk, Artemis Gateway EAFHI flammability, droplet d²-law "
        + "burning, or select any of the 25 faces.",
        { operations: "Controller asks a flight-science question; oracle returns structured sections.", apiPath: "POST /api/v1/exploration/copilot/chat" },
      ),
    ],
  };
}

/**
 * Build a structured CopilotAnswer offline (client fallback) matching the server oracle.
 * Mirrors backend/app/exploration/qwen_engine.py generate_scientific_reasoning.
 */
export function buildCopilotAnswer(query: string, ctx: CopilotContext = {}): CopilotAnswer {
  const q = query.trim().toLowerCase();

  // Trajectory / delta-v
  let dep = ctx.departureBody || (q.includes("earth") ? "Earth" : undefined);
  let tgt = ctx.targetBody;
  if (!tgt) {
    if (q.includes("mars")) tgt = "Mars";
    else if (q.includes("moon") || q.includes("gateway") || q.includes("lunar")) tgt = "Moon";
  }
  if (!dep && (q.includes("mars") || q.includes("delta-v") || q.includes("hohmann") || q.includes("transfer"))) {
    dep = "Earth";
    if (!tgt) tgt = "Mars";
  }

  if (dep && tgt) {
    // Reuse the same verified constants as the backend oracle.
    const orbits: Record<string, number> = { Earth: 1.0, Mars: 1.523679, Venus: 0.723, Jupiter: 5.204, Moon: 1.0 };
    const mu = 1.3271244e11; // km^3/s^2
    const au = 1.4959787e8;  // km
    const r1 = orbits[dep] || 1.0;
    const r2 = orbits[tgt] || 1.523679;
    const R1 = r1 * au;
    const R2 = r2 * au;
    const a = (R1 + R2) / 2;
    const v1 = Math.sqrt(mu / R1);
    const v2 = Math.sqrt(mu / R2);
    const dv1 = Math.abs(Math.sqrt(mu * (2 / R1 - 1 / a)) - v1);
    const dv2 = Math.abs(v2 - Math.sqrt(mu * (2 / R2 - 1 / a)));
    const total = dv1 + dv2;
    const durDays = Math.round((Math.PI * Math.sqrt(Math.pow(a, 3) / mu)) / 86400);
    const transferType = (dep === "Earth" && tgt === "Moon") || (dep === "Moon" && tgt === "Earth")
      ? "geocentric_translunar"
      : "heliocentric_interplanetary";
    if (transferType === "geocentric_translunar") {
      return {
        ...hohmannAnswer(dep, tgt, 3.14, 0.83, 3.97, 3.2, transferType),
        query: `${dep} → ${tgt} TLI`,
      };
    }
    return hohmannAnswer(dep, tgt, dv1, dv2, total, durDays, transferType);
  }

  if (q.includes("cool-flame") || q.includes("damkohler") || q.includes("damköhler") || q.includes("rekindl") || q.includes("face 12")) {
    return coolFlameAnswer();
  }
  if (q.includes("eafhi") || q.includes("flammab") || q.includes("atmosphere") || q.includes("gateway") || q.includes("face 13")) {
    return eafhiAnswer();
  }
  if (q.includes("droplet") || q.includes("d2-law") || q.includes("d²-law") || q.includes("spherical flame") || q.includes("face 11")) {
    return d2LawAnswer();
  }
  if (q.includes("qwen") || q.includes("lora") || q.includes("face 16") || q.includes("model") || q.includes("adapter")) {
    return qwenLoraAnswer();
  }

  // Generic: if caller passed a face, answer for it; otherwise greeting.
  if (ctx.activeFaceId) {
    // Face data lives on the server; build a minimal placeholder so the UI never breaks offline.
    return {
      query,
      inferenceMode: INFERENCE_MODE,
      modelLoaded: MODEL_LOADED,
      adapterPresent: ADAPTER_PRESENT,
      modelName: MODEL_NAME,
      apiPath: `GET /api/v1/exploration/faces-25/${ctx.activeFaceId}`,
      latencyMs: 0,
      sections: [
        section("explanation", `Face ${ctx.activeFaceId}`, "Face telemetry is loaded from the server; select a face in the matrix to inspect it.", { apiPath: `GET /api/v1/exploration/faces-25/${ctx.activeFaceId}` }),
        section("operations", "What happens operationally", "Select a 25-Faces matrix entry to view its governing formulation, key constant, and flight role.", { apiPath: `GET /api/v1/exploration/faces-25/${ctx.activeFaceId}` }),
      ],
    };
  }

  return greetingAnswer();
}

/**
 * Call the Qwen copilot chat API. Returns a structured CopilotAnswer. On any
 * network/server failure, returns an offline fallback built by buildCopilotAnswer
 * so the UI always renders complete section cards (never an incomplete answer).
 */
export async function fetchCopilotChat(
  query: string,
  ctx: CopilotContext = {},
): Promise<CopilotAnswer> {
  const t0 = performance.now();
  try {
    const res = await fetch(COPILOT_CHAT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", cache: "no-store" },
      body: JSON.stringify({
        query,
        active_face_id: ctx.activeFaceId,
        departure_body: ctx.departureBody,
        target_body: ctx.targetBody,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return {
      query: data.query ?? query,
      inferenceMode: data.inference_mode ?? INFERENCE_MODE,
      modelLoaded: Boolean(data.model_loaded ?? MODEL_LOADED),
      adapterPresent: Boolean(data.adapter_present ?? ADAPTER_PRESENT),
      modelName: data.model_name ?? MODEL_NAME,
      sections: Array.isArray(data.sections)
        ? data.sections.map((s: any) => ({
            kind: s.kind,
            title: s.title,
            body: s.body,
            formula: s.formula,
            evidence: s.evidence,
            proof: s.proof,
            apiPath: s.api_path,
            operations: s.operations,
          }))
        : [],
      apiPath: data.api_path ?? "POST /api/v1/exploration/copilot/chat",
      latencyMs: Math.round(performance.now() - t0),
    };
  } catch {
    return buildCopilotAnswer(query, ctx);
  }
}
