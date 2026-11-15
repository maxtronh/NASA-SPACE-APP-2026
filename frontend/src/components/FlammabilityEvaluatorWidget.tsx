"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Flame,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Cpu,
  Layers,
  Sparkles,
} from "lucide-react";
import { fetchMerkleRoot } from "@/lib/api";
import { handleTabKeyDown } from "@/lib/tabs";

const WIDGET_TAB_ORDER = ["flammability", "merkle"] as const;

const MATERIALS = [
  { key: "pmma", name: "PMMA (Acrylic)", loi: 17.5, char: false },
  { key: "nomex", name: "Nomex (Aramid)", loi: 29.0, char: true },
  { key: "delrin", name: "Delrin (POM)", loi: 15.0, char: false },
  { key: "polycarbonate", name: "Polycarbonate (Lexan)", loi: 26.0, char: true },
  { key: "teflon", name: "Teflon (PTFE)", loi: 95.0, char: false },
  { key: "kevlar", name: "Kevlar (Para-Aramid)", loi: 29.5, char: true },
];

const CABIN_PRESETS = [
  { name: "ISS Standard", o2: 21.0, pressure: 101.325 },
  { name: "Artemis Gateway", o2: 34.0, pressure: 56.5 },
  { name: "Lunar Habitat", o2: 30.0, pressure: 70.3 },
  { name: "EVA Pre-Breathe", o2: 32.0, pressure: 55.2 },
];

export default function FlammabilityEvaluatorWidget() {
  const [selectedMaterial, setSelectedMaterial] = useState(MATERIALS[0]);
  const [oxygenPct, setOxygenPct] = useState(21.0);
  const [pressureKpa, setPressureKpa] = useState(101.325);
  const [thicknessMm, setThicknessMm] = useState(2.0);
  const [activeTab, setActiveTab] = useState<"flammability" | "merkle">("flammability");

  // Live provenance root. Deliberately no placeholder hash: if the API is
  // unavailable the panel says so instead of inventing a digest.
  const [merkle, setMerkle] = useState<{
    root: string;
    leaves: number;
    depth: number;
  } | null>(null);
  const [merkleError, setMerkleError] = useState(false);

  useEffect(() => {
    let active = true;
    fetchMerkleRoot()
      .then((data) => {
        if (!active) return;
        setMerkle({
          root: data.merkle_root,
          leaves: data.total_leaves,
          depth: data.tree_depth,
        });
      })
      .catch(() => {
        if (active) setMerkleError(true);
      });
    return () => {
      active = false;
    };
  }, []);

  // Physics-based NASA-STD-6001B calculation
  const loi = selectedMaterial.loi;
  const o2Delta = oxygenPct - loi;
  const pFactor = Math.pow(pressureKpa / 101.325, 0.3);
  const tFactor = Math.pow(2.0 / Math.max(thicknessMm, 0.2), 0.5);

  let burnLength = 1.0;
  if (o2Delta < -2.0) {
    burnLength = Math.max(1.0, 4.0 + o2Delta * 0.8);
  } else if (o2Delta <= 0.0) {
    burnLength = Math.max(3.0, 8.5 + o2Delta * 2.0);
  } else {
    burnLength = Math.min(30.0, 8.5 + o2Delta * 3.2 * pFactor * tFactor * 0.85);
  }

  const test1Pass = burnLength < 15.24 && !(selectedMaterial.key === "delrin" && oxygenPct >= 18);
  const test1Marginal = !test1Pass && burnLength < 17.5;
  const test1Status = test1Pass ? "PASS" : test1Marginal ? "MARGINAL" : "FAIL";

  const baseHrr = 28.0 * 3.0 * (oxygenPct / 21.0) * pFactor * (selectedMaterial.char ? 0.55 : 1.35);
  const peakHrr = Math.round(Math.min(350, Math.max(5, baseHrr)));
  const test7Pass = peakHrr < 100.0;
  const test7Status = test7Pass ? "PASS" : "FAIL";

  const isCompliant = test1Status === "PASS" && test7Status === "PASS";
  const isRestricted =
    ["PASS", "MARGINAL"].includes(test1Status) && test7Status === "PASS";

  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl overflow-hidden shadow-xl space-y-4">
      {/* Top Banner with Tabs */}
      <div className="bg-space-950 px-5 py-3 border-b border-space-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
            Spacecraft Safety & Provenance Verification Engine
          </h3>
        </div>

        <div
          role="tablist"
          aria-label="Verification engine view"
          className="flex items-center space-x-1 bg-space-900 p-0.5 rounded-lg border border-space-800 text-xs font-mono"
        >
          <button
            type="button"
            role="tab"
            id="widget-tab-flammability"
            aria-selected={activeTab === "flammability"}
            aria-controls="widget-panel"
            tabIndex={activeTab === "flammability" ? 0 : -1}
            data-tab-value="flammability"
            onClick={() => setActiveTab("flammability")}
            onKeyDown={(event) =>
              handleTabKeyDown(event, WIDGET_TAB_ORDER, activeTab, setActiveTab)
            }
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === "flammability"
                ? "bg-amber-500 text-space-950 font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            NASA-STD-6001B Flammability
          </button>
          <button
            type="button"
            role="tab"
            id="widget-tab-merkle"
            aria-selected={activeTab === "merkle"}
            aria-controls="widget-panel"
            tabIndex={activeTab === "merkle" ? 0 : -1}
            data-tab-value="merkle"
            onClick={() => setActiveTab("merkle")}
            onKeyDown={(event) =>
              handleTabKeyDown(event, WIDGET_TAB_ORDER, activeTab, setActiveTab)
            }
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === "merkle"
                ? "bg-nasa-cyan text-space-950 font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Merkle Audit Log
          </button>
        </div>
      </div>

      <div
        role="tabpanel"
        id="widget-panel"
        aria-labelledby={`widget-tab-${activeTab}`}
      >
      {activeTab === "flammability" ? (
        <div className="p-5 space-y-6">
          {/* Preset Buttons */}
          <div className="space-y-1.5">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
              NASA Exploration Cabin Presets:
            </span>
            <div className="flex flex-wrap gap-2">
              {CABIN_PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setOxygenPct(p.o2);
                    setPressureKpa(p.pressure);
                  }}
                  className="px-3 py-1 rounded-lg bg-space-950 hover:bg-space-800 border border-space-700 text-slate-300 hover:text-nasa-cyan font-mono text-xs transition-colors flex items-center space-x-1.5"
                >
                  <Sparkles className="w-3 h-3 text-amber-400" />
                  <span>
                    {p.name} ({p.o2}% O₂, {p.pressure} kPa)
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Controls Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
            {/* Material Dropdown */}
            <div className="bg-space-950 p-3 rounded-lg border border-space-800 space-y-1.5">
              <label
                htmlFor="flammability-material"
                className="text-slate-400 uppercase text-[10px] block"
              >
                Material Sample
              </label>
              <select
                id="flammability-material"
                value={selectedMaterial.key}
                onChange={(e) => {
                  const m = MATERIALS.find((x) => x.key === e.target.value);
                  if (m) setSelectedMaterial(m);
                }}
                className="w-full bg-space-900 border border-space-700 rounded px-2.5 py-1.5 text-white focus:outline-none focus:border-nasa-cyan"
              >
                {MATERIALS.map((m) => (
                  <option key={m.key} value={m.key}>
                    {m.name} (LOI: {m.loi}%)
                  </option>
                ))}
              </select>
            </div>

            {/* O2 Slider */}
            <div className="bg-space-950 p-3 rounded-lg border border-space-800 space-y-1">
              <div className="flex justify-between text-slate-400 text-[11px]">
                <span>Oxygen Level (O₂)</span>
                <span className="text-nasa-cyan font-bold">{oxygenPct.toFixed(1)}%</span>
              </div>
              <input
                type="range"
                aria-label="Oxygen level"
                aria-valuetext={`${oxygenPct.toFixed(1)} percent`}
                min="15.0"
                max="40.0"
                step="0.5"
                value={oxygenPct}
                onChange={(e) => setOxygenPct(parseFloat(e.target.value))}
                className="w-full accent-nasa-cyan cursor-pointer"
              />
            </div>

            {/* Pressure Slider */}
            <div className="bg-space-950 p-3 rounded-lg border border-space-800 space-y-1">
              <div className="flex justify-between text-slate-400 text-[11px]">
                <span>Cabin Pressure</span>
                <span className="text-amber-400 font-bold">{pressureKpa.toFixed(1)} kPa</span>
              </div>
              <input
                type="range"
                aria-label="Cabin pressure"
                aria-valuetext={`${pressureKpa.toFixed(1)} kilopascals`}
                min="45.0"
                max="105.0"
                step="1.0"
                value={pressureKpa}
                onChange={(e) => setPressureKpa(parseFloat(e.target.value))}
                className="w-full accent-amber-400 cursor-pointer"
              />
            </div>

            {/* Thickness Slider */}
            <div className="bg-space-950 p-3 rounded-lg border border-space-800 space-y-1">
              <div className="flex justify-between text-slate-400 text-[11px]">
                <span>Sample Thickness</span>
                <span className="text-purple-400 font-bold">{thicknessMm.toFixed(1)} mm</span>
              </div>
              <input
                type="range"
                aria-label="Sample thickness"
                aria-valuetext={`${thicknessMm.toFixed(1)} millimetres`}
                min="0.5"
                max="6.0"
                step="0.5"
                value={thicknessMm}
                onChange={(e) => setThicknessMm(parseFloat(e.target.value))}
                className="w-full accent-purple-400 cursor-pointer"
              />
            </div>
          </div>

          {/* Test 1 & Test 7 Compliance Verdict Card */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            {/* Test 1 */}
            <div className="bg-space-950 border border-space-800 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-[10px] uppercase font-bold">
                  NASA-STD-6001B Test 1 (Upward Propagation)
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    test1Status === "PASS"
                      ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                      : test1Status === "MARGINAL"
                      ? "bg-amber-950 text-amber-300 border border-amber-800"
                      : "bg-rose-950 text-rose-300 border border-rose-800"
                  }`}
                >
                  {test1Status}
                </span>
              </div>
              <div className="text-sm font-bold text-white">
                Burn Length:{" "}
                <span
                  className={
                    burnLength < 15.24
                      ? "text-emerald-400"
                      : burnLength < 17.5
                      ? "text-amber-400"
                      : "text-rose-400"
                  }
                >
                  {burnLength.toFixed(1)} cm
                </span>{" "}
                <span className="text-slate-400 text-xs font-normal">/ 15.24 cm limit</span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Sample must self-extinguish before reaching 15.2 cm without dripping flaming particles.
              </p>
            </div>

            {/* Test 7 */}
            <div className="bg-space-950 border border-space-800 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-[10px] uppercase font-bold">
                  NASA-STD-6001B Test 7 (Heat Release)
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    test7Status === "PASS"
                      ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                      : "bg-rose-950 text-rose-300 border border-rose-800"
                  }`}
                >
                  {test7Status}
                </span>
              </div>
              <div className="text-sm font-bold text-white">
                Peak HRR:{" "}
                <span className={test7Pass ? "text-emerald-400" : "text-rose-400"}>
                  {peakHrr} kW/m²
                </span>{" "}
                <span className="text-slate-400 text-xs font-normal">/ 100 kW/m² limit</span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Peak heat release rate must not exceed 100 kW/m² to prevent rapid cabin flashover.
              </p>
            </div>

            {/* Overall Verdict */}
            <div
              className={`rounded-xl p-4 border flex flex-col justify-between ${
                isCompliant
                  ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-200"
                  : isRestricted
                  ? "bg-amber-950/40 border-amber-500/40 text-amber-200"
                  : "bg-rose-950/40 border-rose-500/40 text-rose-200"
              }`}
            >
              <div className="flex items-center space-x-2 font-bold uppercase text-[11px]">
                {isCompliant ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                )}
                <span>
                  {isCompliant
                    ? "Flight Interior Approved"
                    : isRestricted
                    ? "Waiver Required"
                    : "Non-Compliant"}
                </span>
              </div>
              <p className="text-[11px] leading-relaxed font-sans text-slate-300 mt-2">
                {isCompliant
                  ? `Material ${selectedMaterial.name} satisfies all fire safety standards at ${oxygenPct}% O₂.`
                  : isRestricted
                  ? `Material ${selectedMaterial.name} exceeds standard margin; M&P Engineering Waiver mandatory.`
                  : `Material ${selectedMaterial.name} presents excessive flammability risk under selected conditions.`}
              </p>
            </div>
          </div>
        </div>
      ) : (
        /* Merkle Tree Provenance Inspector */
        <div className="p-5 space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between pb-3 border-b border-space-800">
            <div className="flex items-center space-x-2 text-nasa-cyan">
              <Lock className="w-4 h-4" />
              <span className="font-bold uppercase tracking-wider">
                Cryptographic Flight Archive Merkle Root
              </span>
            </div>
            <span
              className={`px-2 py-0.5 rounded border text-[10px] ${
                merkle
                  ? "bg-cyan-950 text-cyan-300 border-cyan-800"
                  : merkleError
                  ? "bg-amber-950 text-amber-300 border-amber-800"
                  : "bg-space-900 text-slate-400 border-space-700"
              }`}
            >
              {merkle ? "Live API" : merkleError ? "Unavailable" : "Loading"}
            </span>
          </div>

          <div className="bg-space-950 p-3 rounded-lg border border-space-800 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase block">Active Merkle Root Hash (SHA-256)</span>
            {merkle ? (
              <code className="text-nasa-cyan break-all select-all font-bold text-xs">{merkle.root}</code>
            ) : (
              <span className="text-slate-400 text-xs font-sans">
                {merkleError
                  ? "Provenance service unreachable. No placeholder hash is displayed — start the backend to load the live root."
                  : "Fetching the live root from the provenance service…"}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center">
            <div className="bg-space-950 p-2.5 rounded border border-space-800">
              <span className="text-[9px] text-slate-400 uppercase block">Leaves Anchored</span>
              <span className="text-white font-bold text-sm">
                {merkle ? `${merkle.leaves} Investigations` : "—"}
              </span>
            </div>
            <div className="bg-space-950 p-2.5 rounded border border-space-800">
              <span className="text-[9px] text-slate-400 uppercase block">Tree Depth</span>
              <span className="text-emerald-400 font-bold text-sm">
                {merkle ? `${merkle.depth} Levels` : "—"}
              </span>
            </div>
            <div className="bg-space-950 p-2.5 rounded border border-space-800">
              <span className="text-[9px] text-slate-400 uppercase block">Hash Algorithm</span>
              <span className="text-purple-400 font-bold text-sm">SHA-256</span>
            </div>
          </div>

          <p className="text-slate-400 text-xs font-sans leading-relaxed">
            When the provenance service is online, every flight campaign, test run, and
            SI-normalized sensor channel is hashed into a deterministic binary Merkle tree. Any
            modification to a single channel or checksum changes the root, making tampering
            detectable during peer review.
          </p>
        </div>
      )}
      </div>
    </div>
  );
}
