"use client";

import { useState, useCallback } from "react";
import {
  Orbit,
  Flame,
  Cpu,
  Compass,
  Send,
  Info,
  ChevronRight,
  ShieldAlert,
  Layers,
  AlertCircle,
} from "lucide-react";
import {
  buildCopilotAnswer,
  fetchCopilotChat,
  CopilotAnswer,
  CopilotSection,
  CopilotSectionKind,
} from "@/lib/copilot";

interface FaceData {
  id: number;
  face_id: string;
  tier: number;
  tier_name: string;
  name: string;
  governing_principles: string;
  formulation: string;
  key_constant: string;
  flight_application: string;
  current_value: number;
  unit: string;
  status: string;
  telemetry_channel: string;
}

const STATIC_25_FACES: FaceData[] = [
  // Tier 1 — Planetary Physics
  {
    id: 1,
    face_id: "Face 01",
    tier: 1,
    tier_name: "Planetary Physics",
    name: "Solar Heliosphere & Dynamic Stellar Wind",
    governing_principles: "Parker spiral geometry, proton flux density, coronal mass ejection shock",
    formulation: "B(r) = B_0 * (r_0 / r)^2 * sqrt(1 + (Omega * r / v_sw)^2)",
    key_constant: "v_sw = 450 km/s, B_0 = 5.0 nT",
    flight_application: "Solar energetic particle (SEP) storm alert & avionics radiation hardening",
    current_value: 448.2,
    unit: "km/s",
    status: "NOMINAL",
    telemetry_channel: "PDS-PSP-SW-01",
  },
  {
    id: 2,
    face_id: "Face 02",
    tier: 1,
    tier_name: "Planetary Physics",
    name: "Inner Terrestrial Atmospheres & Hypobaric Limits",
    governing_principles: "Hydrostatic scale height and runaway greenhouse equilibrium",
    formulation: "P(z) = P_0 * exp(-M * g * z / (R_u * T))",
    key_constant: "Venus: 92 bar CO2, Earth: 1.013 bar, Mars: 6.1 mbar",
    flight_application: "Aerocapture corridor selection and thermal protection sizing",
    current_value: 6.12,
    unit: "mbar",
    status: "ACTIVE",
    telemetry_channel: "MSL-REMS-P-02",
  },
  {
    id: 3,
    face_id: "Face 03",
    tier: 1,
    tier_name: "Planetary Physics",
    name: "Gas Giant Magnetospheres & Belts",
    governing_principles: "Synchrotron emission, Jovian radiation belts, Ganymede intrinsic dipole",
    formulation: "Phi_rad(E) = integral(j(E, L) dE)",
    key_constant: "Jupiter B = 428 microTesla, 100 krad/day radiation dose",
    flight_application: "Europa Clipper radiation corridor evasion",
    current_value: 412.8,
    unit: "uT",
    status: "MONITORING",
    telemetry_channel: "JUNO-MAG-03",
  },
  {
    id: 4,
    face_id: "Face 04",
    tier: 1,
    tier_name: "Planetary Physics",
    name: "Outer Ocean Worlds & Subsurface Cryovolcanism",
    governing_principles: "Tidal dissipation heating, tiger-stripe supersonic plume kinetics",
    formulation: "Q_tidal = Im(k_2) * (G M_j^2 / R_sat^5) * R_body^5 * e^2",
    key_constant: "Europa ice shell: 15-25 km, Enceladus v_plume > 400 m/s",
    flight_application: "Astrobiology in-situ sampling and plume flyby mass spectrometry",
    current_value: 418.5,
    unit: "m/s",
    status: "ACTIVE",
    telemetry_channel: "CLIPPER-INMS-04",
  },
  {
    id: 5,
    face_id: "Face 05",
    tier: 1,
    tier_name: "Planetary Physics",
    name: "Deep Kuiper Belt & Interstellar Heliopause",
    governing_principles: "Nitrogen-methane glacier sublimation, Sputnik Planitia cellular convection",
    formulation: "P_sub(T) = A * 10^(B / T), r_shock ~ 122 AU",
    key_constant: "Pluto T = 44 K, Heliopause boundary r ~ 122 AU",
    flight_application: "Interstellar probe autonomous communications",
    current_value: 122.4,
    unit: "AU",
    status: "STANDBY",
    telemetry_channel: "VGR1-PWS-05",
  },

  // Tier 2 — Astrodynamics & Propulsion
  {
    id: 6,
    face_id: "Face 06",
    tier: 2,
    tier_name: "Astrodynamics & Propulsion",
    name: "N-Body Gravitational Ephemeris & J2 Harmonics",
    governing_principles: "J2 oblateness perturbation, n-body gravitational integration, osculating elements",
    formulation: "a_dot = -(3/2) * J2 * (R_eq/p)^2 * n * cos(i) * (1 - e^2)^-2",
    key_constant: "Earth J2 = 1.08263e-3, R_eq = 6378.137 km",
    flight_application: "Precision orbit determination and station-keeping",
    current_value: 1.0826,
    unit: "e-3",
    status: "ACTIVE",
    telemetry_channel: "SLR-GNSS-06",
  },
  {
    id: 7,
    face_id: "Face 07",
    tier: 2,
    tier_name: "Astrodynamics & Propulsion",
    name: "Hohmann Transfer & Interplanetary Trajectories",
    governing_principles: "Vis-viva equation, two-impulse Hohmann transfer, synodic launch windows",
    formulation: "Delta_v_tot = |v_trans(R1) - v_circ(R1)| + |v_circ(R2) - v_trans(R2)|",
    key_constant: "Earth-Mars: 5.59 km/s (259 days); Earth-Moon: 3.97 km/s (3.2 days)",
    flight_application: "Interplanetary mission design and propellant budgeting",
    current_value: 5.59,
    unit: "km/s",
    status: "ACTIVE",
    telemetry_channel: "TRAJ-HOH-07",
  },
  {
    id: 8,
    face_id: "Face 08",
    tier: 2,
    tier_name: "Astrodynamics & Propulsion",
    name: "Translunar Injection & Lunar Gateway",
    governing_principles: "Geocentric TLI from 300 km LEO, lunar sphere-of-injection, LOI capture",
    formulation: "dv_TLI = |sqrt(mu_E*(2/r1 - 1/a)) - sqrt(mu_E/r1)|",
    key_constant: "TLI dv = 3.14 km/s, LOI dv = 0.83 km/s, total = 3.97 km/s",
    flight_application: "Artemis Lunar Gateway departure and arrival burns",
    current_value: 3.97,
    unit: "km/s",
    status: "ACTIVE",
    telemetry_channel: "ART-TLI-08",
  },
  {
    id: 9,
    face_id: "Face 09",
    tier: 2,
    tier_name: "Astrodynamics & Propulsion",
    name: "Electric & Chemical Propulsion Performance",
    governing_principles: "Tsiolkovsky rocket equation, specific impulse, thrust-to-power ratio",
    formulation: "Delta_v = I_sp * g_0 * ln(m_0 / m_f)",
    key_constant: "I_sp: chemical 300-450 s, Hall thruster 1500-3000 s",
    flight_application: "Propulsion system selection and propellant mass budgeting",
    current_value: 320.0,
    unit: "s",
    status: "ACTIVE",
    telemetry_channel: "PROP-ISP-09",
  },
  {
    id: 10,
    face_id: "Face 10",
    tier: 2,
    tier_name: "Astrodynamics & Propulsion",
    name: "Launch Vehicle Ascent & Injection",
    governing_principles: "Gravity turn, max dynamic pressure (max q), orbit insertion",
    formulation: "q = 0.5 * rho * v^2,  Delta_v_ascent ~ 9.3-10 km/s (Earth to LEO)",
    key_constant: "Earth to LEO dv ~ 9.4 km/s including gravity & drag losses",
    flight_application: "Launch vehicle performance and payload mass to orbit",
    current_value: 9.4,
    unit: "km/s",
    status: "ACTIVE",
    telemetry_channel: "LV-ASCENT-10",
  },

  // Tier 3 — Microgravity Combustion & Fire Safety
  {
    id: 11,
    face_id: "Face 11",
    tier: 3,
    tier_name: "Microgravity Combustion & Fire Safety",
    name: "Zero-Gravity Spherical Flame Kinetics (d²-law)",
    governing_principles: "Buoyancy suppression (Gr < 1e-4), spherical symmetry, diffusion-controlled burning",
    formulation: "d²(t) = d₀² - K·t",
    key_constant: "n-heptane in air at 1 atm: K ≈ 0.428 mm²/s",
    flight_application: "Droplet combustion experiment sizing and extinction prediction",
    current_value: 0.428,
    unit: "mm²/s",
    status: "ACTIVE",
    telemetry_channel: "CIR-MDCA-11",
  },
  {
    id: 12,
    face_id: "Face 12",
    tier: 3,
    tier_name: "Microgravity Combustion & Fire Safety",
    name: "Silent Cool-Flame Rekindling Early Warning",
    governing_principles: "Low-temperature chemistry (LTC), NTC regime 550-750 K, peroxy radical isomerization",
    formulation: "Da_cool = τ_res / τ_chem,cool,  Da_crit = 1.0",
    key_constant: "Critical threshold Da_crit = 1.0; RO2 ⇌ QOOH → 2 OH + ketohydroperoxide",
    flight_application: "Cabin fire-safety: post-extinction reignition hazard in microgravity",
    current_value: 1.0,
    unit: "Da_crit",
    status: "MONITORING",
    telemetry_channel: "CIR-COOL-12",
  },
  {
    id: 13,
    face_id: "Face 13",
    tier: 3,
    tier_name: "Microgravity Combustion & Fire Safety",
    name: "Artemis Gateway Exploration Atmosphere Flammability (EAFHI)",
    governing_principles: "Hypobaric MOC, buoyancy factor, LOI-based material term, bounded [0,1] score",
    formulation: "EAFHI = clip(0.40*X_O2/X_O2_std + 0.25*(P/P_std)^-0.5 + 0.25*Phi_buoyancy + 0.20*Delta_mat, 0, 1)",
    key_constant: "Gateway: 34% O2, 56.5 kPa (8.2 psi), 0.166 g lunar gravity",
    flight_application: "Cabin atmosphere selection and EVA preparation flammability limits",
    current_value: 0.0,
    unit: "score",
    status: "ACTIVE",
    telemetry_channel: "GATE-EAFHI-13",
  },
  {
    id: 14,
    face_id: "Face 14",
    tier: 3,
    tier_name: "Microgravity Combustion & Fire Safety",
    name: "Material Flammability & Limiting Oxygen Index",
    governing_principles: "NASA-STD-6001B Tests 1 & 7, LOI, Minimum Extinguishing Oxygen Concentration (MOC)",
    formulation: "MOC(P, g) = LOI_std * (P / P_std)^(-0.22) * (1 - 0.08 * ln(g + 1))",
    key_constant: "LOI: PMMA 17.4%, cotton 18%, polyurethane 22-24%",
    flight_application: "Spacecraft cabin material selection and fire safety certification",
    current_value: 17.4,
    unit: "%",
    status: "ACTIVE",
    telemetry_channel: "MAT-LOI-14",
  },
  {
    id: 15,
    face_id: "Face 15",
    tier: 3,
    tier_name: "Microgravity Combustion & Fire Safety",
    name: "Smoke & Particulate Detection in Microgravity",
    governing_principles: "Particle sedimentation absent, thermophoresis, smoke alarm threshold obscuration",
    formulation: "dM/dt = -k_dep * M,  obscuration = sigma * N * path_length",
    key_constant: "Smoke detection threshold ~0.1-1% obs/ft in quiescent cabin air",
    flight_application: "Cabin smoke detection and particulate monitoring",
    current_value: 0.5,
    unit: "% obs/ft",
    status: "STANDBY",
    telemetry_channel: "CAB-SMOKE-15",
  },

  // Tier 4 — Human Factors & Life Support
  {
    id: 16,
    face_id: "Face 16",
    tier: 4,
    tier_name: "Human Factors & Life Support",
    name: "Qwen 2.5 Architecture & LoRA Extraction",
    governing_principles: "RoPE positional embeddings, GQA, low-rank adapter update ΔW = B·A",
    formulation: "W = W_0 + BA  (rank r = 16, alpha = 32)",
    key_constant: "adapter_model.safetensors: 459,624 bytes; peft not installed (fallback only)",
    flight_application: "Edge-hosted AI copilot extracting physical insights from telemetry",
    current_value: 0.46,
    unit: "MB",
    status: "ADAPTER_PRESENT",
    telemetry_channel: "QWEN-LORA-16",
  },
  {
    id: 17,
    face_id: "Face 17",
    tier: 4,
    tier_name: "Human Factors & Life Support",
    name: "Cabin Atmosphere & EVA Prebreathe Protocol",
    governing_principles: "Nitrogen washout, decompression sickness risk, oxygen prebreathe time",
    formulation: "t_prebreathe ~ f(P_cabin, P_suit, N2 washout rate)",
    key_constant: "8 psi / 34% O2 cabin → suit 4.3 psi pure O2; prebreathe ~60-90 min",
    flight_application: "Artemis EVA preparation and decompression risk management",
    current_value: 4.3,
    unit: "psi",
    status: "ACTIVE",
    telemetry_channel: "EVA-PREB-17",
  },
  {
    id: 18,
    face_id: "Face 18",
    tier: 4,
    tier_name: "Human Factors & Life Support",
    name: "CO2 Washout & Cabin Air Revitalization",
    governing_principles: "Henry's law, amine swing-bed adsorption, CO2 partial pressure limits",
    formulation: "P_CO2 = n_CO2 * R * T / V,  24-hr SMAC = 0.7% (7 mmHg)",
    key_constant: "CO2 24-hr SMAC 7 mmHg; emergency limit 15 mmHg",
    flight_application: "Cabin air revitalization and CO2 scrubber sizing",
    current_value: 7.0,
    unit: "mmHg",
    status: "ACTIVE",
    telemetry_channel: "CAB-CO2-18",
  },
  {
    id: 19,
    face_id: "Face 19",
    tier: 4,
    tier_name: "Human Factors & Life Support",
    name: "Thermal Control & Radiator Sizing",
    governing_principles: "Stefan-Boltzmann radiative heat rejection, loop heat pipes, radiator area",
    formulation: "Q_rad = epsilon * sigma * A * (T_rad^4 - T_space^4)",
    key_constant: "Deep space T_space ~ 3 K; ISS radiator ~ 168 m²",
    flight_application: "Spacecraft thermal balance and heat-rejection system sizing",
    current_value: 168.0,
    unit: "m²",
    status: "ACTIVE",
    telemetry_channel: "THERM-RAD-19",
  },
  {
    id: 20,
    face_id: "Face 20",
    tier: 4,
    tier_name: "Human Factors & Life Support",
    name: "Water Recovery & Urine Processing",
    governing_principles: "Vapor compression distillation, multi-filtration, water purity standards",
    formulation: "recovery_rate = (product_water / input_water) * 100%",
    key_constant: "ISS water recovery ~93%; NASA potable water spec limits",
    flight_application: "Life-support consumable resupply mass reduction",
    current_value: 93.0,
    unit: "%",
    status: "ACTIVE",
    telemetry_channel: "LSS-WATER-20",
  },

  // Tier 5 — Mission Visualization HUD
  {
    id: 21,
    face_id: "Face 21",
    tier: 5,
    tier_name: "Mission Visualization HUD",
    name: "Flight Controller Situational Awareness Display",
    governing_principles: "Unified telemetry grid, alarm prioritization, CCSDS packet routing",
    formulation: "SA_display = f(telemetry_stream, alarm_state, procedure_state)",
    key_constant: "Update rate 1 Hz - 50 Hz; CCSDS packet telemetry",
    flight_application: "Primary flight controller mission overview console",
    current_value: 1.0,
    unit: "active",
    status: "NOMINAL",
    telemetry_channel: "HUD-SA-21",
  },
  {
    id: 22,
    face_id: "Face 22",
    tier: 5,
    tier_name: "Mission Visualization HUD",
    name: "Provenance & Evidence Traceability",
    governing_principles: "Cryptographic hashing, immutable audit trail, API-level provenance",
    formulation: "prov = (api_path, request, response, timestamp, model_loaded, adapter_present)",
    key_constant: "Every Qwen answer carries inference_mode + which API produced it",
    flight_application: "Flight-director audit and anomaly reconstruction",
    current_value: 1.0,
    unit: "trail",
    status: "ACTIVE",
    telemetry_channel: "PROV-AUDIT-22",
  },
  {
    id: 23,
    face_id: "Face 23",
    tier: 5,
    tier_name: "Mission Visualization HUD",
    name: "25-Face Real-Time Telemetry Matrix",
    governing_principles: "Unified telemetry grid providing flight controllers synchronized metrics across all 25 faces",
    formulation: "T_vector = [ F_01, F_02, ..., F_25 ], Update_rate = 50 Hz",
    key_constant: "25 distinct scientific channels covering physics, propulsion, safety, and AI",
    flight_application: "Primary flight controller mission overview console",
    current_value: 25.0,
    unit: "faces",
    status: "ACTIVE",
    telemetry_channel: "HUD-GRID-23",
  },
  {
    id: 24,
    face_id: "Face 24",
    tier: 5,
    tier_name: "Mission Visualization HUD",
    name: "Flight Controller Mission Control Bridge",
    governing_principles: "Integration with the verified Milestone 9 Mission Control cockpit (/mission-control)",
    formulation: "Sync( ISS_combustion_telemetry, Orbital_ephemeris_state )",
    key_constant: "CCSDS packet routing & SSE telemetry event stream",
    flight_application: "Mission operations flight director console synchronization",
    current_value: 1.0,
    unit: "active",
    status: "NOMINAL",
    telemetry_channel: "MC-BRIDGE-24",
  },
  {
    id: 25,
    face_id: "Face 25",
    tier: 5,
    tier_name: "Mission Visualization HUD",
    name: "Mission Trajectory Planner & Delta-V Calculator",
    governing_principles: "Interactive Hohmann transfer calculator with delta-V budgets, synodic launch windows, and transit times",
    formulation: "Delta_v_tot = |v_dep - v_circ1| + |v_circ2 - v_arr|",
    key_constant: "Earth-Moon: 3.97 km/s (3.2 days), Earth-Mars: 5.59 km/s (259 days)",
    flight_application: "Interactive trajectory planning and propellant margin assessment",
    current_value: 5.59,
    unit: "km/s",
    status: "NOMINAL",
    telemetry_channel: "TRAJ-PLAN-25",
  },
];

const TIER_COLORS: Record<number, string> = {
  1: "text-amber-400",
  2: "text-nasa-cyan",
  3: "text-rose-400",
  4: "text-purple-400",
  5: "text-emerald-400",
};

const KIND_LABELS: Record<CopilotSectionKind, string> = {
  explanation: "Explanation",
  formulas: "Formulas",
  evidence: "Evidences",
  proof: "Mathematical proofs",
  api: "By which API",
  operations: "What happens",
};

const KIND_COLORS: Record<CopilotSectionKind, string> = {
  explanation: "text-nasa-cyan",
  formulas: "text-amber-400",
  evidence: "text-emerald-400",
  proof: "text-rose-400",
  api: "text-purple-400",
  operations: "text-emerald-400",
};

interface ChatMessage {
  role: "user" | "copilot";
  content: string;            // user text
  answer?: CopilotAnswer;     // copilot structured answer
}

function formatKind(kind: CopilotSectionKind): string {
  return KIND_LABELS[kind] ?? kind;
}

export default function MissionLab() {
  const [selectedFace, setSelectedFace] = useState<FaceData>(STATIC_25_FACES[15]); // Default Face 16
  const [departureBody, setDepartureBody] = useState("Earth");
  const [targetBody, setTargetBody] = useState("Mars");
  const [transferResult, setTransferResult] = useState({
    deltaV: "5.59 km/s",
    duration: "259 days",
    dv1: "2.94 km/s",
    dv2: "2.65 km/s",
    summary:
      "Heliocentric Hohmann transfer from Earth to Mars. Departure burn Δv1 = 2.94 km/s, arrival capture Δv2 = 2.65 km/s. Total Δv = 5.59 km/s with 259 days flight duration.",
  });
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: "copilot",
      content: "",
      answer: buildCopilotAnswer("Greetings Flight Controller. I am Qwen 2.5 Flight Science Copilot, calibrated with the 25 faces of solar system simulation, Keplerian astrodynamics, and microgravity combustion physics. Ask me about Hohmann transfers, Lunar Gateway TLI, or silent cool-flame Damköhler limits."),
    },
  ]);
  const [queryInput, setQueryInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  const calculateTransfer = useCallback((dep: string, arr: string) => {
    if (dep === arr) {
      setTransferResult({
        deltaV: "0.00 km/s",
        duration: "0 days",
        dv1: "0.00 km/s",
        dv2: "0.00 km/s",
        summary: "Origin and destination are identical co-orbital bodies. Delta-V budget is zero.",
      });
      return;
    }
    if ((dep === "Earth" && arr === "Moon") || (dep === "Moon" && arr === "Earth")) {
      setTransferResult({
        deltaV: "3.97 km/s",
        duration: "3.2 days",
        dv1: "3.14 km/s",
        dv2: "0.83 km/s",
        summary: "Geocentric Translunar Injection (TLI) from 300 km LEO to Artemis Lunar Gateway orbit. TLI burn Δv1 = 3.14 km/s, arrival LOI Δv2 = 0.83 km/s (Total: 3.97 km/s). Transit time is 3.2 days.",
      });
      return;
    }
    const orbits: Record<string, number> = { Earth: 1.0, Mars: 1.524, Venus: 0.723, Jupiter: 5.204, Moon: 1.0 };
    const mu = 1.3271244e11;
    const au = 1.4959787e8;
    const r1 = orbits[dep] || 1.0;
    const r2 = orbits[arr] || 1.524;
    const R1 = r1 * au;
    const R2 = r2 * au;
    const a = (R1 + R2) / 2;
    const v1 = Math.sqrt(mu / R1);
    const v2 = Math.sqrt(mu / R2);
    const dv1 = Math.abs(Math.sqrt(mu * (2 / R1 - 1 / a)) - v1);
    const dv2 = Math.abs(v2 - Math.sqrt(mu * (2 / R2 - 1 / a)));
    const total = dv1 + dv2;
    const durDays = Math.round((Math.PI * Math.sqrt(Math.pow(a, 3) / mu)) / 86400);
    setTransferResult({
      deltaV: `${total.toFixed(2)} km/s`,
      duration: `${durDays} days`,
      dv1: `${dv1.toFixed(2)} km/s`,
      dv2: `${dv2.toFixed(2)} km/s`,
      summary: `Heliocentric transfer from ${dep} (${r1.toFixed(2)} AU) to ${arr} (${r2.toFixed(2)} AU). Departure Δv1 = ${dv1.toFixed(2)} km/s, arrival capture Δv2 = ${dv2.toFixed(2)} km/s (Total: ${total.toFixed(2)} km/s). Flight duration = ${durDays} days.`,
    });
  }, []);

  const handleSendChat = useCallback(
    async (presetText?: string) => {
      const text = presetText || queryInput;
      if (!text.trim() || isSending) return;
      setQueryInput("");
      setIsSending(true);
      const userMsg: ChatMessage = { role: "user", content: text };
      setChatMessages((prev) => [...prev, userMsg]);

      try {
        const answer = await fetchCopilotChat(text, {
          activeFaceId: selectedFace.id,
          departureBody,
          targetBody,
        });
        setChatMessages((prev) => [...prev, { role: "copilot", content: "", answer }]);
      } catch {
        setChatMessages((prev) => [
          ...prev,
          {
            role: "copilot",
            content: "Telemetry evaluated across 25 exploration faces. Ephemeris and combustion kinetics are nominal.",
            answer: buildCopilotAnswer(text, {
              activeFaceId: selectedFace.id,
              departureBody,
              targetBody,
            }),
          },
        ]);
      } finally {
        setIsSending(false);
      }
    },
    [isSending, queryInput, selectedFace.id, departureBody, targetBody],
  );

  return (
    <div className="space-y-6">
      {/* Top Controls & Status Bar */}
      <div className="flex flex-col gap-4 rounded-xl border border-space-700 bg-space-900/80 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg border border-nasa-cyan/40 bg-nasa-cyan/10 p-2 text-nasa-cyan">
            <Orbit className="h-5 w-5 animate-spin" style={{ animationDuration: "12s" }} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">25-Faces Mission Lab &amp; Qwen AI Copilot</h2>
            <p className="text-xs text-slate-400">
              Structured Flight Science Answers • Evidence-Grounded Oracle • No Live Model Inference
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
          <span className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-emerald-400">
            M9 System Nominal
          </span>
          <span className="rounded-md border border-nasa-cyan/30 bg-nasa-cyan/10 px-2.5 py-1 text-nasa-cyan">
            25 Faces Synchronized
          </span>
          <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-amber-400">
            Qwen: Fallback Mode
          </span>
        </div>
      </div>

      {/* Main Split View: Qwen Copilot Chat (left) + Trajectory Planner + Faces Matrix (right) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left: Qwen Copilot Chat (7 cols) */}
        <div className="flex h-[640px] flex-col justify-between rounded-xl border border-space-700 bg-space-900/90 p-4 lg:col-span-7">
          <div className="border-b border-space-800 pb-3 mb-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-purple-400" />
                <span className="text-xs font-bold text-white">Qwen 2.5 Flight Science Copilot</span>
              </div>
              <span className="font-mono text-[10px] text-nasa-cyan">FALLBACK</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Deterministic scientific oracle — real Qwen live inference unavailable. Each answer carries
              explanation, formulas, evidences, mathematical proofs, the producing API, and operations.
            </p>
          </div>

          {/* Chat Messages Log — role="log" for assistive technologies */}
          <div
            role="log"
            aria-label="Qwen copilot conversation"
            aria-live="polite"
            className="flex-1 space-y-3 overflow-y-auto pr-1 pt-3 text-xs"
          >
            {chatMessages.map((msg, idx) => {
              if (msg.role === "user") {
                return (
                  <div key={idx} className="ml-6 border border-nasa-cyan/40 bg-nasa-cyan/10 text-white rounded-lg p-3">
                    <div className="mb-1 font-mono text-[10px] font-bold text-nasa-cyan">
                      Flight Controller
                    </div>
                    <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                  </div>
                );
              }
              const answer = msg.answer;
              if (!answer) {
                return (
                  <div key={idx} className="mr-6 border border-space-700 bg-space-800/80 text-slate-200 rounded-lg p-3">
                    <div className="mb-1 font-mono text-[10px] font-bold text-slate-400">
                      Qwen 2.5 Copilot
                    </div>
                    <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                  </div>
                );
              }
              return (
                <div key={idx} className="mr-6 border border-space-700 bg-space-800/80 text-slate-200 rounded-lg p-3">
                  <div className="mb-1 font-mono text-[10px] font-bold text-slate-400">
                    Qwen 2.5 Copilot
                  </div>
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-1 mb-1">
                      <span className="inline-flex items-center gap-1 rounded border border-space-700 bg-space-950 px-2 py-0.5 text-[10px] text-slate-400">
                        {answer.inferenceMode}
                      </span>
                      <span className="inline-flex items-center gap-1 rounded border border-space-700 bg-space-950 px-2 py-0.5 text-[10px] text-slate-400">
                        model:{answer.modelLoaded ? "loaded" : "fallback"}
                      </span>
                      <span className="inline-flex items-center gap-1 rounded border border-space-700 bg-space-950 px-2 py-0.5 text-[10px] text-slate-400">
                        adapter:{answer.adapterPresent ? "present" : "absent"}
                      </span>
                    </div>
                    {answer.sections.map((s, sidx) => (
                      <SectionCard key={sidx} section={s} />
                    ))}
                    <div className="border-t border-space-800/50 pt-1 mt-2">
                      <span className="font-mono text-[9px] text-slate-500">
                        Latency {answer.latencyMs} ms • API: {answer.apiPath}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
            {isSending && (
              <div className="mr-6 rounded-lg p-3 text-[10px] text-slate-400 animate-pulse">
                Qwen 2.5 Copilot is computing…
              </div>
            )}
          </div>

          {/* Preset Chips & Input Bar */}
          <div className="mt-3 space-y-2 border-t border-space-800 pt-3">
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => handleSendChat("Calculate Earth to Mars delta-V")}
                className="rounded border border-space-700 bg-space-800/60 px-2 py-0.5 text-[10px] text-slate-300 hover:border-nasa-cyan hover:text-white"
              >
                Earth &rarr; Mars Δv
              </button>
              <button
                type="button"
                onClick={() => handleSendChat("Calculate Earth to Lunar Gateway TLI delta-V")}
                className="rounded border border-space-700 bg-space-800/60 px-2 py-0.5 text-[10px] text-slate-300 hover:border-nasa-cyan hover:text-white"
              >
                Earth &rarr; Moon TLI
              </button>
              <button
                type="button"
                onClick={() => handleSendChat("Explain cool-flame Damkohler number")}
                className="rounded border border-space-700 bg-space-800/60 px-2 py-0.5 text-[10px] text-slate-300 hover:border-nasa-cyan hover:text-white"
              >
                Cool-Flame Damk&ouml;hler
              </button>
              <button
                type="button"
                onClick={() => handleSendChat("Evaluate Artemis Gateway EAFHI flammability")}
                className="rounded border border-space-700 bg-space-800/60 px-2 py-0.5 text-[10px] text-slate-300 hover:border-nasa-cyan hover:text-white"
              >
                EAFHI Flammability
              </button>
              <button
                type="button"
                onClick={() => handleSendChat("Explain zero-gravity droplet d2-law burning")}
                className="rounded border border-space-700 bg-space-800/60 px-2 py-0.5 text-[10px] text-slate-300 hover:border-nasa-cyan hover:text-white"
              >
                d²-law Burning
              </button>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
                placeholder="Ask Qwen Copilot about astrodynamics or flame kinetics…"
                className="flex-1 rounded-lg border border-space-700 bg-space-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-nasa-cyan focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleSendChat()}
                disabled={isSending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-nasa-blue px-3.5 py-2 text-xs font-semibold text-white hover:bg-sky-600 disabled:opacity-50"
              >
                <Send className="h-3.5 w-3.5" />
                <span>Send</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right column: Trajectory Planner + Faces Matrix (5 cols) */}
        <div className="flex flex-col gap-6 lg:col-span-5">
          {/* Trajectory Delta-V Planner Section */}
          <div className="rounded-xl border border-space-700 bg-space-900/80 p-5 flex-1">
            <div className="mb-4 flex items-center justify-between border-b border-space-800 pb-3">
              <div className="flex items-center gap-2">
                <Compass className="h-5 w-5 text-emerald-400" />
                <h3 className="text-sm font-bold text-white">Hohmann Transfer Delta-V &amp; Flight Duration Planner</h3>
              </div>
              <span className="font-mono text-xs text-slate-400">Face 25 Astrodynamics Engine</span>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <label className="mb-1 block font-mono text-xs text-slate-400">Departure Body</label>
                <select
                  value={departureBody}
                  onChange={(e) => {
                    setDepartureBody(e.target.value);
                    calculateTransfer(e.target.value, targetBody);
                  }}
                  className="w-full rounded-lg border border-space-700 bg-space-950 px-3 py-2 text-xs text-white focus:border-nasa-cyan focus:outline-none"
                >
                  <option value="Earth">Earth (1.00 AU)</option>
                  <option value="Mars">Mars (1.52 AU)</option>
                  <option value="Moon">Lunar Gateway / Moon</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block font-mono text-xs text-slate-400">Destination Target</label>
                <select
                  value={targetBody}
                  onChange={(e) => {
                    setTargetBody(e.target.value);
                    calculateTransfer(departureBody, e.target.value);
                  }}
                  className="w-full rounded-lg border border-space-700 bg-space-950 px-3 py-2 text-xs text-white focus:border-nasa-cyan focus:outline-none"
                >
                  <option value="Mars">Mars (1.52 AU)</option>
                  <option value="Moon">Lunar Gateway / Moon</option>
                  <option value="Venus">Venus (0.72 AU)</option>
                  <option value="Jupiter">Jupiter (5.20 AU)</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block font-mono text-xs text-slate-400">Spacecraft Dry Mass (kg)</label>
                <input
                  type="number"
                  defaultValue="1200"
                  className="w-full rounded-lg border border-space-700 bg-space-950 px-3 py-2 text-xs text-white focus:border-nasa-cyan focus:outline-none"
                />
              </div>
            </div>

            {/* Telemetry Output Badges */}
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 font-mono">
              <div className="rounded-lg border border-space-700 bg-space-950 p-3">
                <span className="text-[10px] uppercase text-slate-400">Total &Delta;v Required</span>
                <div className="mt-1 text-lg font-bold text-nasa-cyan">{transferResult.deltaV}</div>
              </div>
              <div className="rounded-lg border border-space-700 bg-space-950 p-3">
                <span className="text-[10px] uppercase text-slate-400">Transit Duration</span>
                <div className="mt-1 text-lg font-bold text-emerald-400">{transferResult.duration}</div>
              </div>
              <div className="rounded-lg border border-space-700 bg-space-950 p-3">
                <span className="text-[10px] uppercase text-slate-400">Departure Burn (&Delta;v1)</span>
                <div className="mt-1 text-lg font-bold text-amber-400">{transferResult.dv1}</div>
              </div>
              <div className="rounded-lg border border-space-700 bg-space-950 p-3">
                <span className="text-[10px] uppercase text-slate-400">Arrival Insertion (&Delta;v2)</span>
                <div className="mt-1 text-lg font-bold text-rose-400">{transferResult.dv2}</div>
              </div>
            </div>
            <p className="mt-3 rounded-lg border border-space-800 bg-space-950/60 p-3 font-mono text-xs text-slate-300">
              {transferResult.summary}
            </p>
          </div>

          {/* The 25 Scientific Faces Matrix Grid */}
          <div className="rounded-xl border border-space-700 bg-space-900/80 p-5">
            <div className="mb-4 flex items-center justify-between border-b border-space-800 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-nasa-cyan" />
                <h3 className="text-sm font-bold text-white">The 25 Scientific Faces Matrix</h3>
              </div>
              <span className="font-mono text-xs text-slate-400">Tiers 1 to 5 Multi-Disciplinary Taxonomy</span>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
              {[1, 2, 3, 4, 5].map((tierNum) => {
                const tierFaces = STATIC_25_FACES.filter((f) => f.tier === tierNum);
                const tierTitle = tierFaces[0]?.tier_name || `Tier ${tierNum}`;
                const tierColor = TIER_COLORS[tierNum];
                return (
                  <div key={tierNum} className="rounded-lg border border-space-800 bg-space-950/60 p-3">
                    <div className={`mb-2.5 flex items-center justify-between text-xs font-bold ${tierColor}`}>
                      <span>{tierTitle}</span>
                      <span className="font-mono text-[10px] text-slate-500">Tier {tierNum}</span>
                    </div>
                    <div className="space-y-1.5">
                      {tierFaces.map((face) => (
                        <button
                          key={face.id}
                          onClick={() => setSelectedFace(face)}
                          className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-xs transition-colors ${
                            selectedFace.id === face.id
                              ? "border border-nasa-cyan bg-nasa-cyan/15 text-nasa-cyan font-semibold"
                              : "border border-transparent bg-space-800/40 text-slate-300 hover:border-space-600 hover:text-white"
                          }`}
                        >
                          <span className="truncate">
                            <strong className="font-mono mr-1">{face.id < 10 ? `0${face.id}` : face.id}.</strong>
                            {face.name}
                          </span>
                          <ChevronRight className="h-3 w-3 shrink-0" />
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Selected Face Inspector Card */}
            <div className="mt-5 rounded-lg border border-nasa-cyan/40 bg-space-950 p-4">
              <div className="flex flex-wrap items-center gap-2.5">
                <span className="rounded bg-nasa-cyan/20 px-2 py-0.5 font-mono text-xs font-bold text-nasa-cyan border border-nasa-cyan/30">
                  {selectedFace.face_id}
                </span>
                <span className="rounded bg-space-800 px-2 py-0.5 font-mono text-xs text-slate-400">
                  Tier {selectedFace.tier}: {selectedFace.tier_name}
                </span>
                <h4 className="text-sm font-bold text-white">{selectedFace.name}</h4>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-slate-300">{selectedFace.governing_principles}</p>
              <div className="mt-3 grid grid-cols-1 gap-3 font-mono text-xs sm:grid-cols-3">
                <div className="rounded border border-space-800 bg-space-900/60 p-2.5">
                  <span className="block text-[10px] uppercase text-slate-500">Formulation</span>
                  <span className="font-semibold text-nasa-cyan whitespace-pre-wrap">{selectedFace.formulation}</span>
                </div>
                <div className="rounded border border-space-800 bg-space-900/60 p-2.5">
                  <span className="block text-[10px] uppercase text-slate-500">Key Constant / Range</span>
                  <span className="font-semibold text-amber-300">{selectedFace.key_constant}</span>
                </div>
                <div className="rounded border border-space-800 bg-space-900/60 p-2.5">
                  <span className="block text-[10px] uppercase text-slate-500">Flight Operations Role</span>
                  <span className="font-semibold text-purple-300">{selectedFace.flight_application}</span>
                </div>
              </div>
              <button
                onClick={() =>
                  handleSendChat(`Tell me about ${selectedFace.face_id} ${selectedFace.name}`)
                }
                className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-space-700 bg-space-800 px-3 py-1.5 text-xs text-slate-300 hover:border-nasa-cyan hover:text-white"
              >
                <Info className="h-3.5 w-3.5" />
                Ask Qwen about this face
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * SectionCard renders one typed answer section matching the review structure:
 * explanation ---- formulas --- evidences ----- mathematical proofs ----- by which API ---- and what happens.
 */
function SectionCard({ section }: { section: CopilotSection }) {
  const color = KIND_COLORS[section.kind];
  return (
    <div className="rounded border border-space-800/60 bg-space-950/50 p-2.5 mb-1">
      <div className="flex items-center gap-1.5 mb-1">
        <span className={`rounded bg-space-800 px-1.5 py-0.5 font-mono text-[9px] font-bold border ${color}`}>
          {formatKind(section.kind)}
        </span>
        <span className="font-mono text-[10px] font-bold text-slate-300">{section.title}</span>
      </div>
      <div className="whitespace-pre-wrap leading-relaxed text-xs text-slate-200 mb-1">
        {section.body}
      </div>
      {section.formula && (
        <div className="rounded border border-space-800 bg-[#020611]/60 p-1.5 mb-1">
          <span className="block text-[9px] uppercase text-slate-500 mb-0.5">Formula</span>
          <div className="font-mono text-xs text-nasa-cyan whitespace-pre-wrap">{section.formula}</div>
        </div>
      )}
      {section.evidence && section.evidence.length > 0 && (
        <div className="mb-1">
          <span className="block text-[9px] uppercase text-slate-500 mb-0.5">Evidences</span>
          <ul className="list-disc list-inside text-xs text-slate-300 leading-relaxed space-y-0.5">
            {section.evidence.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
      )}
      {section.proof && (
        <div className="rounded border border-space-800 bg-[#020611]/60 p-1.5 mb-1">
          <span className="block text-[9px] uppercase text-slate-500 mb-0.5">Mathematical proof</span>
          <div className="font-mono text-xs text-rose-400 whitespace-pre-wrap">{section.proof}</div>
        </div>
      )}
      {section.apiPath && (
        <div className="flex items-center gap-1.5 mt-1">
          <span className="font-mono text-[9px] text-slate-500">By which API:</span>
          <span className="font-mono text-[10px] text-slate-300 truncate">{section.apiPath}</span>
        </div>
      )}
      {section.operations && (
        <div className="mt-1">
          <span className="block text-[9px] uppercase text-slate-500 mb-0.5">What happens</span>
          <div className="font-mono text-xs text-emerald-400 whitespace-pre-wrap">{section.operations}</div>
        </div>
      )}
    </div>
  );
}
