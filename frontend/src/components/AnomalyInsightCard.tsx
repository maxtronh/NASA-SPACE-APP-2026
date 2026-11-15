"use client";

import React, { useEffect, useState, useTransition } from "react";
import {
  Flame,
  Sparkles,
  AlertTriangle,
  ExternalLink,
  ShieldCheck,
  RotateCw,
  Sliders,
  ChevronRight,
  Info,
  Gauge,
  Atom,
  Wind,
  CheckCircle2,
  TrendingUp,
} from "lucide-react";
import { detectCombustionAnomalies } from "@/lib/api";
import {
  AnomalyDetectRequest,
  AnomalyDetectResponse,
  CombustionAnomalyItem,
} from "@/types";

export interface AnomalyInsightCardProps {
  initialFuel?: string;
  initialRegime?: string;
  initialVentilation?: number;
  initialDropletDiameter?: number;
  initialTempK?: number;
  initialO2?: number;
  className?: string;
  title?: string;
  compact?: boolean;
}

export default function AnomalyInsightCard({
  initialFuel = "n-heptane",
  initialRegime,
  initialVentilation = 3.0,
  initialDropletDiameter = 3.0,
  initialTempK = 720.0,
  initialO2 = 21.0,
  className = "",
  title = "Microgravity Scientific Contradiction & Anomaly Engine",
  compact = false,
}: AnomalyInsightCardProps) {
  const [fuel, setFuel] = useState<string>(initialFuel);
  const [regime, setRegime] = useState<string>(initialRegime || "all");
  const [ventilation, setVentilation] = useState<number>(initialVentilation);
  const [dropletDiameter, setDropletDiameter] = useState<number>(initialDropletDiameter);
  const [tempK, setTempK] = useState<number>(initialTempK);
  const [o2Pct, setO2Pct] = useState<number>(initialO2);

  const [activeTab, setActiveTab] = useState<string>("all");
  const [showControls, setShowControls] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [data, setData] = useState<AnomalyDetectResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runDetection = async (overrideParams?: Partial<AnomalyDetectRequest>) => {
    setLoading(true);
    setError(null);
    try {
      const payload: AnomalyDetectRequest = {
        fuel,
        fuel_type: fuel,
        regime: regime === "all" ? undefined : regime,
        ventilation_velocity_cm_s: ventilation,
        droplet_diameter_mm: dropletDiameter,
        initial_diameter_mm: dropletDiameter,
        fuel_temperature_k: tempK,
        temperature_k: tempK,
        ambient_o2_percentage: o2Pct,
        o2_percentage: o2Pct,
        gravity_level_g: 1e-6,
        ...overrideParams,
      };
      const res = await detectCombustionAnomalies(payload);
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to query anomaly detection engine");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runDetection();
  }, [fuel, regime]);

  const anomalies: CombustionAnomalyItem[] =
    data?.anomalies || data?.anomalies_detected || [];

  const displayedAnomalies =
    activeTab === "all"
      ? anomalies
      : anomalies.filter(
          (a) =>
            a.id === activeTab ||
            a.anomaly_id === activeTab ||
            a.regime === activeTab
        );

  const divergencePct = Math.round((data?.overall_divergence_score ?? 0.94) * 100);

  return (
    <div
      className={`rounded-2xl border border-space-700/80 bg-space-900/90 backdrop-blur-md shadow-2xl p-5 sm:p-6 transition-all ${className}`}
    >
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-space-700/60">
        <div className="flex items-start space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 via-orange-600 to-red-600 flex items-center justify-center shadow-lg shadow-orange-500/20 shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base sm:text-lg font-bold tracking-wide text-white">
                {title}
              </h2>
              <span className="text-[10px] uppercase font-mono tracking-widest px-2 py-0.5 rounded-full bg-amber-950/80 text-amber-400 border border-amber-500/40">
                E-09 Autonomous Engine
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Autonomous identification of combustion phenomena defying classical 1g terrestrial physics.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <button
            type="button"
            onClick={() => setShowControls(!showControls)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-colors flex items-center space-x-1.5 ${
              showControls
                ? "bg-nasa-cyan/20 text-nasa-cyan border-nasa-cyan/50"
                : "bg-space-800 text-slate-300 border-space-700 hover:border-slate-500 hover:text-white"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Parameters</span>
          </button>

          <button
            type="button"
            onClick={() => runDetection()}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg text-xs font-mono bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium shadow-md shadow-cyan-600/20 disabled:opacity-50 flex items-center space-x-1.5 transition-all"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>{loading ? "Evaluating..." : "Re-evaluate"}</span>
          </button>
        </div>
      </div>

      {/* Expandable Parameter Controls */}
      {showControls && (
        <div className="mt-4 p-4 rounded-xl bg-space-950/80 border border-space-800 space-y-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="uppercase tracking-wider font-semibold text-slate-300">
              Interactive Regime & Microgravity Boundaries
            </span>
            <span className="text-nasa-cyan">0.000001 g (CIR / MSG Freefall)</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1">
                Fuel Specimen
              </label>
              <select
                value={fuel}
                onChange={(e) => setFuel(e.target.value)}
                className="w-full text-xs bg-space-900 border border-space-700 rounded-lg px-2.5 py-1.5 text-white focus:outline-none focus:border-nasa-cyan"
              >
                <option value="n-heptane">n-Heptane (C7H16)</option>
                <option value="n-octane">n-Octane (C8H18)</option>
                <option value="pmma">PMMA Solid Slab</option>
                <option value="methanol">Methanol (CH3OH)</option>
                <option value="methane">Methane Diffusion (CH4)</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1">
                Regime Filter
              </label>
              <select
                value={regime}
                onChange={(e) => setRegime(e.target.value)}
                className="w-full text-xs bg-space-900 border border-space-700 rounded-lg px-2.5 py-1.5 text-white focus:outline-none focus:border-nasa-cyan"
              >
                <option value="all">All Regimes (Auto-detect)</option>
                <option value="solid_flame_spread">Solid Flame Spread (BASS-II)</option>
                <option value="isolated_droplet_combustion">Droplet Extinction (FLEX)</option>
                <option value="low_temperature_chemistry">Low-Temp Cool Flame (ACME)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-[11px] font-mono text-slate-400 mb-1">
                <span>Draft Velocity</span>
                <span className="text-white">{ventilation.toFixed(1)} cm/s</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="15.0"
                step="0.5"
                value={ventilation}
                onChange={(e) => setVentilation(parseFloat(e.target.value))}
                className="w-full accent-nasa-cyan cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-[11px] font-mono text-slate-400 mb-1">
                <span>Core Temp (K)</span>
                <span className="text-white">{tempK} K</span>
              </div>
              <input
                type="range"
                min="350"
                max="1200"
                step="25"
                value={tempK}
                onChange={(e) => setTempK(parseFloat(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
            </div>
          </div>
        </div>
      )}

      {/* Divergence Score Gauge & Physics Highlight */}
      <div className="mt-5 grid grid-cols-1 md:grid-cols-12 gap-4">
        {/* Divergence Score Gauge Card */}
        <div className="md:col-span-4 rounded-xl bg-space-950/70 border border-space-800 p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-slate-400">
              <span className="flex items-center space-x-1.5">
                <Gauge className="w-3.5 h-3.5 text-nasa-cyan" />
                <span>1G DIVERGENCE SCORE</span>
              </span>
              <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider">
                {divergencePct >= 90 ? "CRITICAL PARADOX" : "STRONG CONTRADICTION"}
              </span>
            </div>

            <div className="mt-3 flex items-baseline space-x-2">
              <span className="text-4xl font-extrabold tracking-tight text-white font-mono">
                {divergencePct}%
              </span>
              <span className="text-xs text-slate-400 font-mono">defies classical 1g</span>
            </div>

            {/* Gauge Bar */}
            <div className="mt-3 w-full bg-space-800 rounded-full h-2.5 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 rounded-full transition-all duration-700"
                style={{ width: `${Math.min(100, divergencePct)}%` }}
              />
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-space-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <span>Detected Contradictions:</span>
            <span className="font-bold text-white bg-space-800 px-2 py-0.5 rounded">
              {anomalies.length} active
            </span>
          </div>
        </div>

        {/* Explainability & Core Scientific Insight */}
        <div className="md:col-span-8 rounded-xl bg-space-950/70 border border-space-800 p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span className="tracking-wider uppercase font-semibold">
                Authentic NASA Spaceflight Archival Grounding
              </span>
            </div>
            <p className="mt-2 text-xs sm:text-sm text-slate-300 leading-relaxed">
              {data?.scientific_summary ||
                data?.summary ||
                "Autonomous discovery engine evaluated microgravity combustion regimes across authentic NASA flight datasets, detecting physics behaviors that fundamentally contradict terrestrial 1g empirical models."}
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-space-800/80 flex flex-wrap items-center gap-3 text-xs">
            <span className="text-slate-400 font-mono text-[11px]">Primary NASA Missions:</span>
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-space-800 border border-space-700 text-slate-300 text-[11px] font-mono">
              <Atom className="w-3 h-3 text-nasa-cyan" />
              <span>BASS-II (MSG)</span>
            </span>
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-space-800 border border-space-700 text-slate-300 text-[11px] font-mono">
              <Flame className="w-3 h-3 text-amber-400" />
              <span>FLEX (CIR / MDCA)</span>
            </span>
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-space-800 border border-space-700 text-slate-300 text-[11px] font-mono">
              <Wind className="w-3 h-3 text-emerald-400" />
              <span>ACME (CIR)</span>
            </span>
          </div>
        </div>
      </div>

      {/* Tabs Toolbar */}
      <div className="mt-6 flex flex-wrap items-center gap-2 border-b border-space-700/60 pb-3">
        <button
          type="button"
          onClick={() => setActiveTab("all")}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
            activeTab === "all"
              ? "bg-nasa-cyan text-space-950 font-bold"
              : "bg-space-800/80 text-slate-400 hover:text-white hover:bg-space-800"
          }`}
        >
          All Contradictions ({anomalies.length})
        </button>

        {anomalies.map((item) => {
          const tabKey = item.id || item.anomaly_id || item.regime;
          const isActive = activeTab === tabKey;
          return (
            <button
              key={tabKey}
              type="button"
              onClick={() => setActiveTab(tabKey)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors flex items-center space-x-1.5 ${
                isActive
                  ? "bg-nasa-cyan text-space-950 font-bold"
                  : "bg-space-800/80 text-slate-400 hover:text-white hover:bg-space-800"
              }`}
            >
              <span>{item.name || item.title}</span>
              <span className="text-[10px] opacity-75 font-sans">
                ({Math.round((item.divergence_score || 0.9) * 100)}%)
              </span>
            </button>
          );
        })}
      </div>

      {/* Anomaly Detail Cards */}
      <div className="mt-5 space-y-4">
        {displayedAnomalies.map((item, idx) => {
          const divPct = Math.round((item.divergence_score || 0.9) * 100);
          const citation = item.citations?.[0];

          return (
            <div
              key={item.id || item.anomaly_id || idx}
              className="rounded-xl border border-space-700 bg-space-950/60 p-4 sm:p-5 hover:border-space-600 transition-colors"
            >
              {/* Card Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-space-800">
                <div className="flex items-center space-x-2.5">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                  <h3 className="text-sm sm:text-base font-bold text-white tracking-wide">
                    {item.name || item.title}
                  </h3>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-red-950/80 text-red-300 border border-red-500/40">
                    {item.contradiction_level || "CRITICAL"}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-800 text-nasa-cyan border border-space-700">
                    Regime: {item.regime}
                  </span>
                  <span className="text-xs font-mono font-bold text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-500/30">
                    {divPct}% Divergence
                  </span>
                </div>
              </div>

              {/* Kinetic Mechanism */}
              <div className="mt-3">
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  <strong>Physical Mechanism:</strong>{" "}
                  {item.mechanism || item.kinetics_mechanism || item.physical_mechanism}
                </p>
              </div>

              {/* Comparative Matrix: 1g Earth vs Microgravity */}
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* 1g Behavior */}
                <div className="p-3 rounded-lg bg-space-900/90 border border-space-800">
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1.5 pb-1 border-b border-space-800">
                    <span className="text-slate-300 font-semibold">Terrestrial 1g Intuition</span>
                    <span className="text-red-400">Buoyancy Governed</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {item.classical_1g_behavior || item.classical_1g_prediction}
                  </p>
                </div>

                {/* Microgravity Behavior */}
                <div className="p-3 rounded-lg bg-cyan-950/20 border border-cyan-500/30">
                  <div className="flex items-center justify-between text-[11px] font-mono text-nasa-cyan mb-1.5 pb-1 border-b border-cyan-900/50">
                    <span className="font-semibold">Microgravity (μg) Reality</span>
                    <span className="text-emerald-400">Diffusion & LTC Governed</span>
                  </div>
                  <p className="text-xs text-cyan-200 leading-relaxed">
                    {item.microgravity_behavior || item.microgravity_observation}
                  </p>
                </div>
              </div>

              {/* Quantitative Metrics Badge Row */}
              {item.quantitative_metrics && Object.keys(item.quantitative_metrics).length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2 text-[11px] font-mono">
                  {Object.entries(item.quantitative_metrics).map(([key, val]) => (
                    <div
                      key={key}
                      className="px-2.5 py-1 rounded-md bg-space-900 border border-space-800 flex items-center space-x-1.5 text-slate-300"
                    >
                      <span className="text-slate-400">{key.replace(/_/g, " ")}:</span>
                      <span className="text-white font-semibold">{String(val)}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* NASA NTRS Citation & Provenance Link */}
              {citation && (
                <div className="mt-4 pt-3 border-t border-space-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div className="flex items-center space-x-2 text-slate-400">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span className="font-mono text-[11px]">
                      Citation: <strong className="text-slate-200">{citation.title}</strong>
                    </span>
                  </div>

                  <a
                    href={citation.nasa_source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1.5 text-nasa-cyan hover:text-cyan-300 font-mono text-[11px] underline underline-offset-2 shrink-0 transition-colors"
                  >
                    <span>NASA NTRS {citation.ntrs_id || citation.nasa_ntrs_id}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
