"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import {
  Cpu,
  Sliders,
  TrendingUp,
  Target,
  Sparkles,
  Info,
  Layers,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Compass,
  Rocket,
  Shield,
  Activity,
} from "lucide-react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { optimizeOEDParameters } from "@/lib/api";
import {
  OEDOptimizationRequest,
  OEDOptimizationResponse,
  OEDCandidateProposal,
  GPSurrogatePoint,
} from "@/types";

export default function OptimizerPage() {
  // 4D Parameters
  const [pressure, setPressure] = useState<number>(101.3);
  const [oxygen, setOxygen] = useState<number>(21.0);
  const [ventilation, setVentilation] = useState<number>(2.0);
  const [diameter, setDiameter] = useState<number>(2.5);

  // Bayesian Acquisition Settings
  const [kappa, setKappa] = useState<number>(1.96);
  const [varyingAxis, setVaryingAxis] = useState<
    "pressure_kpa" | "oxygen_pct" | "ventilation_velocity_cm_s" | "droplet_diameter_mm"
  >("pressure_kpa");
  const [targetMetric, setTargetMetric] = useState<"burning_rate_k" | "extinction_time" | "information_gain">(
    "burning_rate_k"
  );

  const [loading, setLoading] = useState<boolean>(true);
  const [oedData, setOedData] = useState<OEDOptimizationResponse | null>(null);
  const [selectedProposal, setSelectedProposal] = useState<OEDCandidateProposal | null>(null);

  // Flight presets
  const PRESETS = [
    {
      name: "ISS CIR Baseline",
      icon: "🛰️",
      p: 101.3,
      o2: 21.0,
      v: 0.0,
      d: 2.5,
      desc: "Standard atmospheric sea-level ISS Columbus module environment.",
    },
    {
      name: "Artemis Gateway Orbit",
      icon: "🌖",
      p: 56.5,
      o2: 34.0,
      v: 2.0,
      d: 2.0,
      desc: "Hypobaric oxygen-enriched exploration atmosphere (0.166 g lunar).",
    },
    {
      name: "Sub-Atmospheric Cool Flame",
      icon: "❄️",
      p: 45.0,
      o2: 30.0,
      v: 1.5,
      d: 3.0,
      desc: "Extinction transition targeting low-temperature chemical kinetics.",
    },
    {
      name: "High-Pressure Quench",
      icon: "⚡",
      p: 150.0,
      o2: 18.0,
      v: 5.0,
      d: 3.5,
      desc: "Dense soot-cloud radiative extinction boundary at 1.5 bar.",
    },
  ];

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setPressure(preset.p);
    setOxygen(preset.o2);
    setVentilation(preset.v);
    setDiameter(preset.d);
  };

  const applyProposal = (proposal: OEDCandidateProposal) => {
    setPressure(proposal.pressure_kpa);
    setOxygen(proposal.oxygen_pct);
    setVentilation(proposal.ventilation_velocity_cm_s);
    setDiameter(proposal.droplet_diameter_mm);
    setSelectedProposal(proposal);
  };

  const debouncedPressure = useDebouncedValue(pressure, 300);
  const debouncedOxygen = useDebouncedValue(oxygen, 300);
  const debouncedVentilation = useDebouncedValue(ventilation, 300);
  const debouncedDiameter = useDebouncedValue(diameter, 300);
  const debouncedKappa = useDebouncedValue(kappa, 300);

  useEffect(() => {
    let active = true;
    async function runOptimization() {
      setLoading(true);
      try {
        const payload: OEDOptimizationRequest = {
          kappa: debouncedKappa,
          target_metric: targetMetric,
          varying_parameter: varyingAxis,
          fixed_parameters: {
            pressure_kpa: debouncedPressure,
            oxygen_pct: debouncedOxygen,
            ventilation_velocity_cm_s: debouncedVentilation,
            droplet_diameter_mm: debouncedDiameter,
          },
        };
        const res = await optimizeOEDParameters(payload);
        if (active) {
          setOedData(res);
          if (res.top_proposals && res.top_proposals.length > 0) {
            setSelectedProposal(res.top_proposals[0]);
          }
        }
      } catch (err) {
        console.error("OED optimization error:", err);
      } finally {
        if (active) setLoading(false);
      }
    }
    runOptimization();
    return () => {
      active = false;
    };
  }, [debouncedPressure, debouncedOxygen, debouncedVentilation, debouncedDiameter, debouncedKappa, varyingAxis, targetMetric]);

  // Chart data formatting: calculate upper and lower bounds for the epistemic uncertainty band
  const chartData = useMemo(() => {
    if (!oedData || !oedData.curve_points) return [];
    return oedData.curve_points.map((pt) => {
      const lower = Math.max(0, pt.mean - kappa * pt.std);
      const upper = pt.mean + kappa * pt.std;
      return {
        coordinate: pt.coordinate,
        mean: pt.mean,
        std: pt.std,
        lowerBound: Number(lower.toFixed(3)),
        upperBound: Number(upper.toFixed(3)),
        bandHeight: Number((upper - lower).toFixed(3)),
        ucb: pt.ucb,
        observed: pt.observed_value !== null && pt.observed_value !== undefined ? pt.observed_value : null,
      };
    });
  }, [oedData, kappa]);

  const axisLabel =
    varyingAxis === "pressure_kpa"
      ? "Chamber Pressure P [kPa]"
      : varyingAxis === "oxygen_pct"
      ? "Oxygen Mole Fraction X_O2 [%]"
      : varyingAxis === "ventilation_velocity_cm_s"
      ? "Ventilation Flow Velocity V_vent [cm/s]"
      : "Initial Droplet Diameter d_0 [mm]";

  return (
    <div className="min-h-screen bg-space-950 text-slate-100 pb-16">
      {/* Page Header */}
      <div className="bg-space-900 border-b border-space-700/80 px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-nasa-cyan mb-1">
                <span>Experiment Planning & AI</span>
                <span>/</span>
                <span>Upgrade E-08</span>
                <span className="px-2 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-500/40 text-[10px] text-nasa-cyan">
                  Bayesian OED
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                <Cpu className="w-8 h-8 text-nasa-cyan" />
                Active Learning Bayesian OED Optimizer
              </h1>
              <p className="text-slate-400 text-sm mt-1 max-w-3xl">
                Solves microgravity flight resource scarcity by constructing Gaussian Process surrogate models over 4D parameter 
                space (P, X_O2, V_vent, d_0) and maximizing Upper Confidence Bound (α_UCB = μ + κ·σ) 
                for maximum physical information gain.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 rounded-lg bg-space-800 border border-space-700 text-xs font-mono text-slate-300 flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-amber-400" />
                UCB Acquisition
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-space-800 border border-space-700 text-xs font-mono text-slate-300 flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                Matérn 5/2 ARD
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        {/* Quick Flight Presets */}
        <div className="mb-6">
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Rocket className="w-3.5 h-3.5 text-nasa-cyan" />
            Quick Flight Regime Presets:
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {PRESETS.map((p) => {
              const isMatch =
                Math.abs(pressure - p.p) < 0.2 &&
                Math.abs(oxygen - p.o2) < 0.2 &&
                Math.abs(ventilation - p.v) < 0.2 &&
                Math.abs(diameter - p.d) < 0.2;

              return (
                <button
                  key={p.name}
                  onClick={() => applyPreset(p)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    isMatch
                      ? "bg-cyan-950/40 border-nasa-cyan shadow-md shadow-cyan-500/10"
                      : "bg-space-900 border-space-700 hover:border-slate-500 hover:bg-space-850"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold text-white flex items-center gap-1.5">
                      <span>{p.icon}</span>
                      {p.name}
                    </span>
                    {isMatch && (
                      <span className="w-2 h-2 rounded-full bg-nasa-cyan animate-pulse" />
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-1 mb-2">{p.desc}</p>
                  <div className="text-[10px] font-mono text-slate-500 flex gap-2">
                    <span>{p.p} kPa</span>
                    <span>•</span>
                    <span>{p.o2}% O2</span>
                    <span>•</span>
                    <span>{p.d} mm</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Grid: Controls + Visualizer */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: 4D Parameter Sliders & Acquisition Config (4 Cols) */}
          <div className="lg:col-span-4 space-y-5">
            {/* 4D Parameter Explorer */}
            <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg space-y-4">
              <div className="flex items-center justify-between border-b border-space-800 pb-3">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-nasa-cyan" />
                  4D Space Coordinates
                </h2>
                <button
                  onClick={() => {
                    setPressure(101.3);
                    setOxygen(21.0);
                    setVentilation(2.0);
                    setDiameter(2.5);
                    setKappa(1.96);
                  }}
                  className="text-[11px] font-mono text-slate-400 hover:text-white flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" />
                  Reset
                </button>
              </div>

              {/* Slider 1: Pressure */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-300">Chamber Pressure (P)</span>
                  <span className="text-nasa-cyan font-semibold">{pressure.toFixed(1)} kPa</span>
                </div>
                <input
                  type="range"
                  aria-label="Chamber Pressure (kPa)"
                  min="40.0"
                  max="150.0"
                  step="1.0"
                  value={pressure}
                  onChange={(e) => setPressure(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-space-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                />
                <div className="flex justify-between text-[10px] font-mono text-slate-500">
                  <span>40.0 kPa (Sub-Atm)</span>
                  <span>101.3 kPa</span>
                  <span>150.0 kPa</span>
                </div>
              </div>

              {/* Slider 2: Oxygen Fraction */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-300">Oxygen Mole Fraction (X_O2)</span>
                  <span className="text-amber-400 font-semibold">{oxygen.toFixed(1)} %</span>
                </div>
                <input
                  type="range"
                  aria-label="Oxygen Mole Fraction (vol %)"
                  min="15.0"
                  max="40.0"
                  step="0.5"
                  value={oxygen}
                  onChange={(e) => setOxygen(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-space-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
                />
                <div className="flex justify-between text-[10px] font-mono text-slate-500">
                  <span>15.0% (Hypoxic)</span>
                  <span>21.0% (Air)</span>
                  <span>40.0% (Enriched)</span>
                </div>
              </div>

              {/* Slider 3: Forced Ventilation */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-300">Forced Ventilation (V_vent)</span>
                  <span className="text-emerald-400 font-semibold">{ventilation.toFixed(1)} cm/s</span>
                </div>
                <input
                  type="range"
                  aria-label="Forced Ventilation Velocity (cm/s)"
                  min="0.0"
                  max="20.0"
                  step="0.2"
                  value={ventilation}
                  onChange={(e) => setVentilation(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-space-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
                />
                <div className="flex justify-between text-[10px] font-mono text-slate-500">
                  <span>0.0 cm/s (Quiescent)</span>
                  <span>5.0 cm/s</span>
                  <span>20.0 cm/s</span>
                </div>
              </div>

              {/* Slider 4: Droplet Initial Diameter */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-300">Droplet Diameter (d_0)</span>
                  <span className="text-purple-400 font-semibold">{diameter.toFixed(1)} mm</span>
                </div>
                <input
                  type="range"
                  aria-label="Initial Droplet Diameter (mm)"
                  min="1.0"
                  max="5.0"
                  step="0.1"
                  value={diameter}
                  onChange={(e) => setDiameter(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-space-800 rounded-lg appearance-none cursor-pointer accent-purple-400"
                />
                <div className="flex justify-between text-[10px] font-mono text-slate-500">
                  <span>1.0 mm</span>
                  <span>2.5 mm</span>
                  <span>5.0 mm</span>
                </div>
              </div>
            </div>

            {/* Acquisition Function Configuration */}
            <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg space-y-4">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-space-800 pb-3">
                <Target className="w-4 h-4 text-amber-400" />
                Acquisition Function Tuning
              </h2>

              {/* Exploration weight kappa */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-300">Exploration Tradeoff (κ)</span>
                  <span className="text-amber-400 font-semibold">κ = {kappa.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  aria-label="Exploration Tradeoff Kappa"
                  min="0.5"
                  max="5.0"
                  step="0.1"
                  value={kappa}
                  onChange={(e) => setKappa(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-space-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
                />
                <div className="flex justify-between text-[10px] font-mono text-slate-500">
                  <span>κ=0.5 (Exploit μ)</span>
                  <span>κ=1.96 (95% CI)</span>
                  <span>κ=5.0 (Explore σ)</span>
                </div>
              </div>

              {/* Target response */}
              <div className="space-y-1">
                <span className="text-xs font-mono text-slate-400">Optimization Target</span>
                <select
                  value={targetMetric}
                  onChange={(e) => setTargetMetric(e.target.value as any)}
                  className="w-full px-3 py-2 bg-space-850 border border-space-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-nasa-cyan"
                >
                  <option value="burning_rate_k">Burning Rate Constant K [mm²/s]</option>
                  <option value="extinction_time">Radiative Extinction Time t_ext [s]</option>
                  <option value="information_gain">Epistemic Information Gain [bits]</option>
                </select>
              </div>

              {/* Varying Axis for 1D Slice */}
              <div className="space-y-1">
                <span className="text-xs font-mono text-slate-400">Surrogate 1D Cut Axis</span>
                <select
                  value={varyingAxis}
                  onChange={(e) => setVaryingAxis(e.target.value as any)}
                  className="w-full px-3 py-2 bg-space-850 border border-space-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-nasa-cyan"
                >
                  <option value="pressure_kpa">Chamber Pressure (P)</option>
                  <option value="oxygen_pct">Oxygen Mole Fraction (X_O2)</option>
                  <option value="ventilation_velocity_cm_s">Forced Ventilation (V_vent)</option>
                  <option value="droplet_diameter_mm">Initial Diameter (d_0)</option>
                </select>
              </div>
            </div>

            {/* GP Covariance Model Stats */}
            {oedData && (
              <div className="bg-space-900 border border-space-700 rounded-xl p-4 shadow-lg space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                  <span className="flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-nasa-cyan" />
                    GP Covariance & ARD Status
                  </span>
                  <span className="font-mono text-[10px] text-emerald-400">CONVERGED</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2 rounded bg-space-850 border border-space-800">
                    <span className="text-slate-500 text-[10px] block">PRIOR FLIGHT RUNS</span>
                    <span className="text-white font-semibold">{oedData.surrogate_stats.total_training_runs}</span>
                  </div>
                  <div className="p-2 rounded bg-space-850 border border-space-800">
                    <span className="text-slate-500 text-[10px] block">VARIANCE REDUCTION</span>
                    <span className="text-emerald-400 font-semibold">-{oedData.surrogate_stats.variance_reduction_pct}%</span>
                  </div>
                  <div className="p-2 rounded bg-space-850 border border-space-800">
                    <span className="text-slate-500 text-[10px] block">MODEL FIT R²</span>
                    <span className="text-nasa-cyan font-semibold">{oedData.surrogate_stats.r2_score}</span>
                  </div>
                  <div className="p-2 rounded bg-space-850 border border-space-800">
                    <span className="text-slate-500 text-[10px] block">KERNEL</span>
                    <span className="text-slate-300">Matérn 5/2</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Surrogate Chart & Proposals Table (8 Cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Recharts GP Posterior & Acquisition Chart */}
            <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-nasa-cyan" />
                    Gaussian Process Posterior Mean & Epistemic Uncertainty Band
                  </h2>
                  <p className="text-xs text-slate-400">
                    Solid Cyan: μ(x) • Shaded Envelope: μ ± κ·σ • Dashed Amber: α_UCB(x)
                  </p>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono">
                  <span className="flex items-center gap-1.5 text-nasa-cyan">
                    <span className="w-3 h-0.5 bg-nasa-cyan inline-block" /> Mean μ(x)
                  </span>
                  <span className="flex items-center gap-1.5 text-amber-400">
                    <span className="w-3 h-0.5 bg-amber-400 border-t border-dashed inline-block" /> UCB
                  </span>
                  <span className="flex items-center gap-1.5 text-slate-400">
                    <span className="w-2.5 h-2.5 rounded-full bg-slate-300 inline-block" /> Historical
                  </span>
                </div>
              </div>

              {/* Chart Viewport */}
              <div className="h-80 w-full pt-2">
                {loading ? (
                  <div className="h-full flex items-center justify-center">
                    <div className="animate-spin w-8 h-8 border-2 border-nasa-cyan border-t-transparent rounded-full" />
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis
                        dataKey="coordinate"
                        stroke="#64748b"
                        tick={{ fontSize: 11 }}
                        label={{ value: axisLabel, position: "insideBottom", offset: -12, fill: "#94a3b8", fontSize: 11 }}
                      />
                      <YAxis
                        stroke="#64748b"
                        tick={{ fontSize: 11 }}
                        domain={["auto", "auto"]}
                        label={{ value: "Predicted Response", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 11 }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#0b1120",
                          borderColor: "#334155",
                          fontSize: "12px",
                          color: "#f8fafc",
                        }}
                      />

                      {/* Uncertainty Envelope Band (Area from lowerBound with height bandHeight) */}
                      <Area
                        type="monotone"
                        dataKey="upperBound"
                        stroke="none"
                        fill="#00e5ff"
                        fillOpacity={0.15}
                        name="Upper Envelope"
                      />
                      <Area
                        type="monotone"
                        dataKey="lowerBound"
                        stroke="none"
                        fill="#0b1120"
                        fillOpacity={1.0}
                        name="Lower Cut"
                      />

                      {/* Posterior Mean Curve */}
                      <Line
                        type="monotone"
                        dataKey="mean"
                        stroke="#00e5ff"
                        strokeWidth={2.5}
                        dot={false}
                        name="Posterior Mean μ(x)"
                      />

                      {/* Upper Confidence Bound Acquisition Curve */}
                      <Line
                        type="monotone"
                        dataKey="ucb"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        strokeDasharray="4 4"
                        dot={false}
                        name="UCB Acquisition Score"
                      />

                      {/* Historical Prior Points */}
                      <Scatter
                        dataKey="observed"
                        fill="#f8fafc"
                        stroke="#0284c7"
                        strokeWidth={1.5}
                        name="Prior Flight Trials"
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* Candidate Experiment Proposals Table */}
            <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <Target className="w-4 h-4 text-amber-400" />
                    Ranked Optimal Experiment Design Candidates (Top 5)
                  </h2>
                  <p className="text-xs text-slate-400">
                    Highest Expected Information Gain ΔH(x) = 0.5·ln(2πe·σ²) under NASA flight constraints
                  </p>
                </div>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-space-800 text-slate-300 border border-space-700">
                  Target: {targetMetric}
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-space-800 text-slate-400 bg-space-850/50">
                      <th className="py-2.5 px-3">RANK</th>
                      <th className="py-2.5 px-3">P (kPa)</th>
                      <th className="py-2.5 px-3">O₂ (%)</th>
                      <th className="py-2.5 px-3">V (cm/s)</th>
                      <th className="py-2.5 px-3">d₀ (mm)</th>
                      <th className="py-2.5 px-3">PRED μ</th>
                      <th className="py-2.5 px-3">UNCERT σ</th>
                      <th className="py-2.5 px-3 text-amber-400">UCB</th>
                      <th className="py-2.5 px-3 text-emerald-400">GAIN (bits)</th>
                      <th className="py-2.5 px-3">ACTION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-space-800">
                    {oedData?.top_proposals.map((prop) => {
                      const isSelected = selectedProposal?.rank === prop.rank;
                      return (
                        <tr
                          key={prop.rank}
                          className={`hover:bg-space-850/80 transition-colors ${
                            isSelected ? "bg-cyan-950/30" : ""
                          }`}
                        >
                          <td className="py-2.5 px-3 font-bold text-white">
                            <span className="w-5 h-5 rounded-full bg-space-800 border border-space-700 inline-flex items-center justify-center text-[10px]">
                              {prop.rank}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-slate-200">{prop.pressure_kpa.toFixed(1)}</td>
                          <td className="py-2.5 px-3 text-slate-200">{prop.oxygen_pct.toFixed(1)}%</td>
                          <td className="py-2.5 px-3 text-slate-200">{prop.ventilation_velocity_cm_s.toFixed(1)}</td>
                          <td className="py-2.5 px-3 text-slate-200">{prop.droplet_diameter_mm.toFixed(1)}</td>
                          <td className="py-2.5 px-3 text-slate-300">{prop.predicted_mean.toFixed(3)}</td>
                          <td className="py-2.5 px-3 text-slate-400">±{prop.epistemic_uncertainty.toFixed(3)}</td>
                          <td className="py-2.5 px-3 font-semibold text-amber-400">{prop.ucb_score.toFixed(3)}</td>
                          <td className="py-2.5 px-3 font-semibold text-emerald-400">+{prop.expected_information_gain_bits.toFixed(2)}</td>
                          <td className="py-2.5 px-3">
                            <button
                              onClick={() => applyProposal(prop)}
                              className="px-2 py-1 rounded bg-space-800 hover:bg-space-700 text-nasa-cyan border border-space-700 text-[10px] transition-colors"
                            >
                              Load
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Selected Proposal Physical Rationale Deep Dive */}
              {selectedProposal && (
                <div className="p-3.5 bg-space-850 border border-space-800 rounded-lg text-xs space-y-1.5">
                  <div className="flex items-center justify-between text-slate-300 font-semibold">
                    <span className="flex items-center gap-1.5 text-nasa-cyan">
                      <Sparkles className="w-3.5 h-3.5" />
                      Physical Discovery Rationale for Proposal #{selectedProposal.rank}
                    </span>
                    <span className="font-mono text-[10px] text-slate-500">
                      Expected Gain: +{selectedProposal.expected_information_gain_bits} bits
                    </span>
                  </div>
                  <p className="text-slate-300 leading-relaxed">
                    {selectedProposal.physical_rationale}
                  </p>
                  <div className="text-[11px] font-mono text-slate-400 flex items-center gap-2 pt-1 border-t border-space-800">
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Flight Facility Compatibility:
                    </span>
                    <span>ISS Combustion Integrated Rack (MDCA insert) & Glenn 5.18s Zero-G Tower</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
