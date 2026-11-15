"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import {
  ShieldAlert,
  ShieldCheck,
  Shield,
  AlertTriangle,
  Flame,
  Activity,
  Sliders,
  RotateCcw,
  Compass,
  Info,
  TrendingUp,
  Wind,
  Layers,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ExternalLink,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";
import { evaluateEAFHI, fetchEAFHISensitivity } from "@/lib/api";
import {
  EAFHIEnvironmentInput,
  EAFHIResult,
  EAFHISensitivityResponse,
  SensitivityCurvePoint,
} from "@/types";

export default function FireSafetyPage() {
  // Environmental Conditions (defaulting to Artemis Lunar Gateway baseline)
  const [gravity, setGravity] = useState<number>(0.166); // Lunar g
  const [pressure, setPressure] = useState<number>(56.5); // kPa (8.2 psia)
  const [oxygen, setOxygen] = useState<number>(34.0); // 34% O2
  const [ventilation, setVentilation] = useState<number>(3.0); // cm/s
  const [material, setMaterial] = useState<string>("pmma");

  // Sensitivity sweep parameter
  const [sweepParam, setSweepParam] = useState<
    "oxygen_pct" | "pressure_kpa" | "gravity_g" | "ventilation_velocity_cm_s"
  >("oxygen_pct");

  const [loading, setLoading] = useState<boolean>(true);
  const [eafhiResult, setEafhiResult] = useState<EAFHIResult | null>(null);
  const [sensitivityData, setSensitivityData] = useState<EAFHISensitivityResponse | null>(null);

  // Aerospace Material Catalog
  const MATERIALS = [
    { key: "pmma", name: "PMMA (Acrylic)", loi: 17.3, desc: "Standard reference polymer, test windows & optical shielding." },
    { key: "nomex", name: "Nomex (Aramid)", loi: 28.5, desc: "Thermal insulation, crew flight suits & sleeping compartment liners." },
    { key: "delrin", name: "Delrin (POM)", loi: 15.0, desc: "Mechanical gears, structural bushings & latch components." },
    { key: "polycarbonate", name: "Polycarbonate (Lexan)", loi: 25.0, desc: "Helmet visors, display covers & structural panels." },
    { key: "teflon", name: "Teflon (PTFE)", loi: 95.0, desc: "Wire harness insulation & chemical containment seals." },
    { key: "kevlar", name: "Kevlar (Para-Aramid)", loi: 29.0, desc: "Micrometeoroid debris shielding & structural containment." },
  ];

  // Quick gravity presets
  const GRAVITY_PRESETS = [
    { label: "ISS Microgravity (~10⁻⁶ g)", g: 0.000001, icon: "🛰️" },
    { label: "Lunar Gateway (0.166 g)", g: 0.166, icon: "🌖" },
    { label: "Mars Surface (0.38 g)", g: 0.38, icon: "🔴" },
    { label: "Earth 1g Baseline (1.0 g)", g: 1.0, icon: "🌍" },
  ];

  const resetToGateway = () => {
    setGravity(0.166);
    setPressure(56.5);
    setOxygen(34.0);
    setVentilation(3.0);
    setMaterial("pmma");
  };

  const debouncedGravity = useDebouncedValue(gravity, 300);
  const debouncedPressure = useDebouncedValue(pressure, 300);
  const debouncedOxygen = useDebouncedValue(oxygen, 300);
  const debouncedVentilation = useDebouncedValue(ventilation, 300);

  useEffect(() => {
    let active = true;
    async function evaluateSafety() {
      setLoading(true);
      try {
        const payload: EAFHIEnvironmentInput = {
          gravity_g: debouncedGravity,
          pressure_kpa: debouncedPressure,
          oxygen_pct: debouncedOxygen,
          ventilation_velocity_cm_s: debouncedVentilation,
          material_key: material,
          characteristic_length_m: 0.05,
        };

        const [res, sens] = await Promise.all([
          evaluateEAFHI(payload),
          fetchEAFHISensitivity(sweepParam, payload),
        ]);

        if (active) {
          setEafhiResult(res);
          setSensitivityData(sens);
        }
      } catch (err) {
        console.error("EAFHI evaluation error:", err);
      } finally {
        if (active) setLoading(false);
      }
    }
    evaluateSafety();
    return () => {
      active = false;
    };
  }, [debouncedGravity, debouncedPressure, debouncedOxygen, debouncedVentilation, material, sweepParam]);

  // Circular Gauge Math: 270 degree arc from 135 deg to 405 deg
  const gaugeScore = eafhiResult?.risk_score ?? 0.5;
  const gaugeAngle = 135 + gaugeScore * 270;
  const needleRad = (gaugeAngle * Math.PI) / 180;
  const needleX = 100 + 65 * Math.cos(needleRad);
  const needleY = 100 + 65 * Math.sin(needleRad);

  const riskClass = eafhiResult?.classification ?? "moderate";
  const riskColor =
    riskClass === "critical"
      ? "text-red-500"
      : riskClass === "high"
      ? "text-orange-500"
      : riskClass === "moderate"
      ? "text-amber-400"
      : "text-emerald-400";

  const riskBg =
    riskClass === "critical"
      ? "bg-red-950/40 border-red-500/50"
      : riskClass === "high"
      ? "bg-orange-950/40 border-orange-500/50"
      : riskClass === "moderate"
      ? "bg-amber-950/40 border-amber-500/50"
      : "bg-emerald-950/40 border-emerald-500/50";

  return (
    <div className="min-h-screen bg-space-950 text-slate-100 pb-16">
      {/* Page Header */}
      <div className="bg-space-900 border-b border-space-700/80 px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-nasa-cyan mb-1">
                <span>Spacecraft Life Support & Fire Safety</span>
                <span>/</span>
                <span>Upgrade E-10</span>
                <span className="px-2 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-500/40 text-[10px] text-nasa-cyan">
                  EAFHI Buoyancy Formulation
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                <ShieldAlert className="w-8 h-8 text-nasa-cyan" />
                Artemis Lunar Gateway Fire Safety & EAFHI Dashboard
              </h1>
              <p className="text-slate-400 text-sm mt-1 max-w-3xl">
                Exploration Atmosphere Fire Hazard Index (EAFHI) for reduced-gravity (0.166 g), hypobaric (56.5 kPa), 
                and oxygen-enriched (34% O₂) spacecraft habitats. Evaluates suppressed Grashof buoyancy convection and flammability margins.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={resetToGateway}
                className="px-3 py-1.5 rounded-lg bg-space-800 hover:bg-space-700 border border-space-700 text-xs font-mono text-nasa-cyan flex items-center gap-1.5 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Reset to Artemis Gateway
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        {/* Gateway Telemetry HUD Strip */}
        <div className="bg-space-900 border border-space-700 rounded-xl p-4 shadow-lg mb-6">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase tracking-wider mb-3">
            <span className="flex items-center gap-1.5 text-nasa-cyan">
              <Compass className="w-3.5 h-3.5" />
              Active Spacecraft Telemetry HUD
            </span>
            <span>NASA-STD-6001B Test 1 Assessment</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3 text-xs font-mono">
            <div className="p-2.5 rounded-lg bg-space-850 border border-space-800">
              <span className="text-slate-500 text-[10px] block">GRAVITY REGIME</span>
              <span className="text-white font-semibold text-sm">
                {gravity === 0.166 ? "0.166 g (Lunar)" : `${gravity.toFixed(3)} g`}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {(gravity * 9.80665).toFixed(3)} m/s²
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-space-850 border border-space-800">
              <span className="text-slate-500 text-[10px] block">CABIN PRESSURE</span>
              <span className="text-nasa-cyan font-semibold text-sm">{pressure.toFixed(1)} kPa</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {(pressure * 0.145038).toFixed(1)} psia
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-space-850 border border-space-800">
              <span className="text-slate-500 text-[10px] block">OXYGEN CONCENTRATION</span>
              <span className="text-amber-400 font-semibold text-sm">{oxygen.toFixed(1)} % O₂</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                P_O2 = {((pressure * oxygen) / 100).toFixed(1)} kPa
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-space-850 border border-space-800">
              <span className="text-slate-500 text-[10px] block">CABIN VENTILATION</span>
              <span className="text-emerald-400 font-semibold text-sm">{ventilation.toFixed(1)} cm/s</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Forced crossflow</span>
            </div>

            <div className="p-2.5 rounded-lg bg-space-850 border border-space-800 col-span-2 sm:col-span-1">
              <span className="text-slate-500 text-[10px] block">SAMPLE MATERIAL</span>
              <span className="text-white font-semibold text-sm uppercase">{material}</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Std LOI: {MATERIALS.find((m) => m.key === material)?.loi ?? 18.0}%
              </span>
            </div>
          </div>
        </div>

        {/* Main Grid: HUD Circular Gauge + Controls + Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Circular HUD Gauge & Operational Advisory (4 Cols) */}
          <div className="lg:col-span-4 space-y-6">
            {/* Circular SVG HUD Gauge */}
            <div className="bg-space-900 border border-space-700 rounded-xl p-6 shadow-xl text-center space-y-4">
              <div className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center justify-center gap-1.5">
                <Flame className="w-3.5 h-3.5 text-amber-400" />
                Deterministic EAFHI Risk Score
              </div>

              {/* Gauge Arc Graphic */}
              <div className="relative w-56 h-56 mx-auto">
                <svg className="w-full h-full" viewBox="0 0 200 200">
                  {/* Gauge Background Track (270 degrees) */}
                  <circle
                    cx="100"
                    cy="100"
                    r="65"
                    fill="none"
                    stroke="#1e293b"
                    strokeWidth="12"
                    strokeDasharray="306 408"
                    strokeDashoffset="-51"
                    strokeLinecap="round"
                  />

                  {/* Colored Arc Segments: Low (Green), Mod (Yellow), High (Orange), Critical (Red) */}
                  {/* 1. Low: 0.0 - 0.35 */}
                  <circle
                    cx="100"
                    cy="100"
                    r="65"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="12"
                    strokeDasharray="107 408"
                    strokeDashoffset="-51"
                    opacity="0.85"
                  />
                  {/* 2. Mod: 0.35 - 0.65 */}
                  <circle
                    cx="100"
                    cy="100"
                    r="65"
                    fill="none"
                    stroke="#f59e0b"
                    strokeWidth="12"
                    strokeDasharray="92 408"
                    strokeDashoffset="-158"
                    opacity="0.85"
                  />
                  {/* 3. High: 0.65 - 0.85 */}
                  <circle
                    cx="100"
                    cy="100"
                    r="65"
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="12"
                    strokeDasharray="61 408"
                    strokeDashoffset="-250"
                    opacity="0.85"
                  />
                  {/* 4. Critical: 0.85 - 1.0 */}
                  <circle
                    cx="100"
                    cy="100"
                    r="65"
                    fill="none"
                    stroke="#ef4444"
                    strokeWidth="12"
                    strokeDasharray="46 408"
                    strokeDashoffset="-311"
                    strokeLinecap="round"
                    opacity="0.85"
                  />

                  {/* Indicator Needle */}
                  <line
                    x1="100"
                    y1="100"
                    x2={needleX}
                    y2={needleY}
                    stroke="#f8fafc"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />
                  <circle cx="100" cy="100" r="6" fill="#00e5ff" stroke="#0b1120" strokeWidth="2" />
                </svg>

                {/* Score Number in Center of Gauge */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pt-8">
                  <span className={`text-4xl font-extrabold font-mono tracking-tight ${riskColor}`}>
                    {gaugeScore.toFixed(3)}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 uppercase mt-0.5">
                    Range [0.0 - 1.0]
                  </span>
                </div>
              </div>

              {/* Status Badge */}
              <div>
                <div
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider border ${riskBg} ${riskColor}`}
                >
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {eafhiResult?.flammability_status?.replace(/_/g, " ") ?? "EVALUATING"}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Classification: <span className="font-semibold text-slate-200 uppercase">{riskClass}</span>
                </div>
              </div>

              {/* Hydrodynamic Grashof Buoyancy Metrics */}
              {eafhiResult && (
                <div className="p-3 bg-space-850 rounded-lg border border-space-800 text-left space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">Grashof Number (Gr)</span>
                    <span className="text-nasa-cyan font-semibold">
                      {eafhiResult.grashof_number.toExponential(2)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">Gr / Gr_1g Ratio</span>
                    <span className="text-white font-semibold">
                      {(eafhiResult.grashof_ratio_to_1g * 100).toFixed(2)}% of Earth 1g
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">Buoyancy Suppression</span>
                    <span className="text-amber-400 font-semibold">
                      {((1.0 - eafhiResult.grashof_ratio_to_1g) * 100).toFixed(1)}% Suppressed
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono pt-1 border-t border-space-800">
                    <span className="text-slate-400">Hypobaric MOC</span>
                    <span className="text-emerald-400 font-semibold">
                      {eafhiResult.minimum_extinguishing_o2_pct.toFixed(1)}% O₂
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">Oxygen Margin (ΔO₂)</span>
                    <span
                      className={`font-semibold ${
                        eafhiResult.oxygen_margin_pct > 0 ? "text-red-400" : "text-emerald-400"
                      }`}
                    >
                      {eafhiResult.oxygen_margin_pct > 0 ? "+" : ""}
                      {eafhiResult.oxygen_margin_pct.toFixed(1)}%
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Flight Controller Advisory Card */}
            {eafhiResult && (
              <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg space-y-3">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-nasa-cyan" />
                    Artemis Flight Protocol
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      eafhiResult.operational_protocol.eva_status === "AUTHORIZED"
                        ? "bg-emerald-950/80 text-emerald-400 border border-emerald-500/40"
                        : "bg-red-950/80 text-red-400 border border-red-500/40"
                    }`}
                  >
                    EVA: {eafhiResult.operational_protocol.eva_status}
                  </span>
                </div>

                <div className="p-3 bg-space-850 rounded-lg border border-space-800 text-xs space-y-2">
                  <div>
                    <span className="text-[10px] font-mono text-slate-500 block uppercase">
                      SUPPRESSION ACTION
                    </span>
                    <p className="text-slate-300 leading-relaxed mt-0.5">
                      {eafhiResult.operational_protocol.suppression_recommendation}
                    </p>
                  </div>
                  <div className="pt-2 border-t border-space-800">
                    <span className="text-[10px] font-mono text-slate-500 block uppercase">
                      VENTILATION GUIDANCE
                    </span>
                    <p className="text-slate-300 leading-relaxed mt-0.5">
                      {eafhiResult.operational_protocol.ventilation_adjustment_advice}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Environmental Controls + Sensitivity Sweep (8 Cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Environmental Sensitivity Controls */}
            <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg space-y-4">
              <div className="flex items-center justify-between border-b border-space-800 pb-3">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-nasa-cyan" />
                  Atmospheric & Gravity Parameters
                </h2>
                <span className="text-xs font-mono text-slate-400">
                  Real-time Grashof recomputation
                </span>
              </div>

              {/* Material Selector Chips */}
              <div>
                <span id="material-label" className="text-xs font-mono text-slate-400 block mb-2">
                  Select Aerospace Cabin Material:
                </span>
                <div
                  role="group"
                  aria-labelledby="material-label"
                  className="grid grid-cols-2 sm:grid-cols-3 gap-2"
                >
                  {MATERIALS.map((m) => (
                    <button
                      key={m.key}
                      type="button"
                      aria-pressed={material === m.key}
                      onClick={() => setMaterial(m.key)}
                      className={`p-2 rounded-lg border text-left text-xs transition-all ${
                        material === m.key
                          ? "bg-cyan-950/40 border-nasa-cyan text-white"
                          : "bg-space-850 border-space-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      <div className="font-semibold">{m.name}</div>
                      <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                        LOI: {m.loi}% O₂
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Gravity Regime Preset Buttons */}
              <div>
                <span id="gravity-label" className="text-xs font-mono text-slate-400 block mb-2">
                  Gravitational Acceleration (g):
                </span>
                <div
                  role="group"
                  aria-labelledby="gravity-label"
                  className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-2"
                >
                  {GRAVITY_PRESETS.map((p) => (
                    <button
                      key={p.label}
                      type="button"
                      aria-pressed={Math.abs(gravity - p.g) < 0.001}
                      onClick={() => setGravity(p.g)}
                      className={`px-2.5 py-1.5 rounded-lg border text-xs font-mono transition-all flex items-center gap-1.5 ${
                        Math.abs(gravity - p.g) < 0.001
                          ? "bg-nasa-cyan/20 border-nasa-cyan text-nasa-cyan font-semibold"
                          : "bg-space-850 border-space-800 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <span>{p.icon}</span>
                      <span>{p.g === 0.166 ? "0.166 g" : `${p.g} g`}</span>
                    </button>
                  ))}
                </div>
                <input
                  type="range"
                  aria-label="Gravity Acceleration (g)"
                  min="0.001"
                  max="1.5"
                  step="0.01"
                  value={gravity}
                  onChange={(e) => setGravity(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-space-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                />
              </div>

              {/* Sliders Grid: Pressure, Oxygen, Ventilation */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                {/* Pressure Slider */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-slate-400">Total Pressure</span>
                    <span className="text-nasa-cyan font-semibold">{pressure.toFixed(1)} kPa</span>
                  </div>
                  <input
                    type="range"
                    aria-label="Total Cabin Pressure (kPa)"
                    min="40.0"
                    max="110.0"
                    step="0.5"
                    value={pressure}
                    onChange={(e) => setPressure(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-space-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                  />
                  <div className="flex justify-between text-[10px] font-mono text-slate-500">
                    <span>40 kPa</span>
                    <span>56.5 kPa</span>
                    <span>101.3 kPa</span>
                  </div>
                </div>

                {/* Oxygen Slider */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-slate-400">Oxygen Conc.</span>
                    <span className="text-amber-400 font-semibold">{oxygen.toFixed(1)} %</span>
                  </div>
                  <input
                    type="range"
                    aria-label="Oxygen Concentration (vol %)"
                    min="15.0"
                    max="45.0"
                    step="0.5"
                    value={oxygen}
                    onChange={(e) => setOxygen(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-space-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
                  />
                  <div className="flex justify-between text-[10px] font-mono text-slate-500">
                    <span>15%</span>
                    <span>21% (Earth)</span>
                    <span>34% (Gateway)</span>
                  </div>
                </div>

                {/* Ventilation Slider */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-slate-400">Cabin Flow</span>
                    <span className="text-emerald-400 font-semibold">{ventilation.toFixed(1)} cm/s</span>
                  </div>
                  <input
                    type="range"
                    aria-label="Forced Ventilation Airspeed (cm/s)"
                    min="0.0"
                    max="30.0"
                    step="0.5"
                    value={ventilation}
                    onChange={(e) => setVentilation(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-space-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
                  />
                  <div className="flex justify-between text-[10px] font-mono text-slate-500">
                    <span>0 cm/s</span>
                    <span>3 cm/s</span>
                    <span>30 cm/s</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Dynamic Recharts Sensitivity Sweep Curve */}
            <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-nasa-cyan" />
                    Environmental Flammability Sensitivity Curve
                  </h2>
                  <p className="text-xs text-slate-400">
                    Dynamic sweep of EAFHI risk score vs NASA safety thresholds (0.35, 0.65, 0.85)
                  </p>
                </div>

                {/* Sweep Parameter Selector */}
                <div className="flex items-center gap-1 bg-space-850 p-1 rounded-lg border border-space-800 text-xs font-mono">
                  <span className="text-slate-500 px-1 text-[10px]">SWEEP:</span>
                  <button
                    onClick={() => setSweepParam("oxygen_pct")}
                    className={`px-2 py-1 rounded transition-colors ${
                      sweepParam === "oxygen_pct"
                        ? "bg-nasa-cyan/20 text-nasa-cyan font-bold"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    O₂ %
                  </button>
                  <button
                    onClick={() => setSweepParam("pressure_kpa")}
                    className={`px-2 py-1 rounded transition-colors ${
                      sweepParam === "pressure_kpa"
                        ? "bg-nasa-cyan/20 text-nasa-cyan font-bold"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    Pressure
                  </button>
                  <button
                    onClick={() => setSweepParam("gravity_g")}
                    className={`px-2 py-1 rounded transition-colors ${
                      sweepParam === "gravity_g"
                        ? "bg-nasa-cyan/20 text-nasa-cyan font-bold"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    Gravity
                  </button>
                </div>
              </div>

              {/* Chart */}
              <div className="h-72 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={sensitivityData?.curve || []}
                    margin={{ top: 10, right: 20, left: 0, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="parameter_value"
                      stroke="#64748b"
                      tick={{ fontSize: 11 }}
                      label={{
                        value:
                          sweepParam === "oxygen_pct"
                            ? "Oxygen Mole Fraction X_O2 [%]"
                            : sweepParam === "pressure_kpa"
                            ? "Chamber Pressure P [kPa]"
                            : "Gravitational Level [g]",
                        position: "insideBottom",
                        offset: -12,
                        fill: "#94a3b8",
                        fontSize: 11,
                      }}
                    />
                    <YAxis
                      stroke="#64748b"
                      tick={{ fontSize: 11 }}
                      domain={[0, 1.0]}
                      label={{ value: "EAFHI Score", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0b1120",
                        borderColor: "#334155",
                        fontSize: "12px",
                        color: "#f8fafc",
                      }}
                    />

                    {/* Hazard Threshold Reference Lines */}
                    <ReferenceLine y={0.35} stroke="#10b981" strokeDasharray="3 3" label={{ value: "Low / Mod (0.35)", fill: "#10b981", fontSize: 10 }} />
                    <ReferenceLine y={0.65} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: "Mod / High (0.65)", fill: "#f59e0b", fontSize: 10 }} />
                    <ReferenceLine y={0.85} stroke="#ef4444" strokeDasharray="3 3" label={{ value: "Critical Flashover (0.85)", fill: "#ef4444", fontSize: 10 }} />

                    {/* EAFHI Response Curve */}
                    <Line
                      type="monotone"
                      dataKey="risk_score"
                      stroke="#00e5ff"
                      strokeWidth={2.5}
                      dot={{ r: 3, fill: "#00e5ff" }}
                      name="EAFHI Score"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Operating Pin Info */}
              <div className="flex items-center justify-between p-3 bg-space-850 rounded-lg border border-space-800 text-xs font-mono">
                <span className="text-slate-400">
                  Current Operating Coordinate:{" "}
                  <span className="text-white font-semibold">
                    {gravity} g • {pressure} kPa • {oxygen}% O₂
                  </span>
                </span>
                <span className={`font-bold ${riskColor}`}>
                  EAFHI: {gaugeScore.toFixed(3)} ({riskClass.toUpperCase()})
                </span>
              </div>
            </div>

            {/* Flight Safe Operating Envelope Map */}
            <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg space-y-3">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Exploration Atmosphere Physiological & Flammability Envelope
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 bg-space-850 rounded-lg border border-space-800">
                  <span className="font-semibold text-white block mb-1">Hypoxia Limit (P_O2 &gt; 16 kPa)</span>
                  <p className="text-slate-400 text-[11px] leading-relaxed">
                    Gateway P_O2 = {((pressure * oxygen) / 100).toFixed(1)} kPa. Crew oxygenation is nominal; no hypoxia hazard.
                  </p>
                </div>
                <div className="p-3 bg-space-850 rounded-lg border border-space-800">
                  <span className="font-semibold text-white block mb-1">Hyperoxia Limit (P_O2 &lt; 30 kPa)</span>
                  <p className="text-slate-400 text-[11px] leading-relaxed">
                    Well below central nervous system toxicity threshold (30 kPa). Safe for prolonged 30-day lunar stays.
                  </p>
                </div>
                <div className="p-3 bg-space-850 rounded-lg border border-space-800">
                  <span className="font-semibold text-amber-400 block mb-1">Flammability Elevation</span>
                  <p className="text-slate-400 text-[11px] leading-relaxed">
                    34% O2 with 94.8% buoyancy suppression increases polymer flame spread risks. Strict adherence to NASA-STD-6001B enforced.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
