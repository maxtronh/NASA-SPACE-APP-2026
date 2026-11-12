"use client";

import React, { useState, useMemo } from "react";
import { Flame, Maximize2, Sliders, RefreshCw, Sparkles } from "lucide-react";
import { Flame3DArtifact as Flame3DArtifactType } from "@/types/artifacts";

interface Props {
  artifact: Flame3DArtifactType;
  onExpand?: () => void;
}

export default function Flame3DArtifact({ artifact, onExpand }: Props) {
  // Configurable parameter overrides
  const [d0, setD0] = useState<number>(artifact.droplet_diameter_mm ?? 2.5);
  const [o2, setO2] = useState<number>(artifact.ambient_o2_pct ?? 21.0);
  const [flameMode, setFlameMode] = useState<"hot" | "cool" | "dual">(
    artifact.flame_mode ?? "dual"
  );

  // Dynamic combustion metrics
  const burningRate = useMemo(() => {
    if (artifact.burning_rate_mm2_s !== null && artifact.burning_rate_mm2_s !== undefined) {
      return artifact.burning_rate_mm2_s;
    }
    // Estimated burning rate: K ≈ 0.58 * sqrt(O2 / 21)
    return Math.round(0.58 * Math.sqrt(o2 / 21.0) * 1000) / 1000;
  }, [artifact.burning_rate_mm2_s, o2]);

  // Flame radius scaling based on d0 and mode
  const dropletRadiusPx = Math.max(8, d0 * 9);
  const hotFlameRadiusPx = dropletRadiusPx * 2.8;
  const coolFlameRadiusPx = dropletRadiusPx * 4.2;

  return (
    <div className="bg-space-950/90 border border-nasa-cyan/40 rounded-xl p-4 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-space-800">
        <div className="flex items-center space-x-2">
          <Flame className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-white tracking-wide">{artifact.title}</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-800 text-amber-300 border border-amber-800/60 uppercase">
            3D Spherical Flame
          </span>
          {onExpand && (
            <button
              onClick={onExpand}
              className="p-1 rounded bg-space-900 hover:bg-space-800 text-slate-300 hover:text-white transition-colors"
              title="Expand to Canvas"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {artifact.description && (
        <p className="text-xs text-slate-400">{artifact.description}</p>
      )}

      {/* 3D Flame Visualization Stage */}
      <div className="relative h-64 bg-radial-gradient from-space-900 via-space-950 to-black rounded-lg border border-space-800 flex items-center justify-center overflow-hidden">
        {/* Ambient Grid Reference Lines */}
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#06b6d4_1px,transparent_1px)] [background-size:16px_16px]" />

        {/* Outer Cool Flame Shell (Pale Cyan/Blue glow in microgravity) */}
        {(flameMode === "cool" || flameMode === "dual") && (
          <div
            className="absolute rounded-full border border-cyan-400/40 animate-pulse transition-all duration-300"
            style={{
              width: `${coolFlameRadiusPx * 2}px`,
              height: `${coolFlameRadiusPx * 2}px`,
              background: "radial-gradient(circle, rgba(6,182,212,0.15) 0%, rgba(6,182,212,0.05) 60%, rgba(6,182,212,0) 100%)",
              boxShadow: "0 0 25px rgba(6, 182, 212, 0.3)",
            }}
          />
        )}

        {/* Inner Hot Flame Envelope (Luminous Amber / Orange) */}
        {(flameMode === "hot" || flameMode === "dual") && (
          <div
            className="absolute rounded-full border border-amber-500/50 transition-all duration-300"
            style={{
              width: `${hotFlameRadiusPx * 2}px`,
              height: `${hotFlameRadiusPx * 2}px`,
              background: "radial-gradient(circle, rgba(245,158,11,0.25) 0%, rgba(239,68,68,0.1) 70%, rgba(245,158,11,0) 100%)",
              boxShadow: "0 0 20px rgba(245, 158, 11, 0.4)",
            }}
          />
        )}

        {/* Central Liquid Fuel Droplet */}
        <div
          className="relative rounded-full bg-gradient-to-br from-slate-200 via-cyan-200 to-slate-400 border border-cyan-300 shadow-inner z-10 transition-all duration-300 flex items-center justify-center"
          style={{
            width: `${dropletRadiusPx * 2}px`,
            height: `${dropletRadiusPx * 2}px`,
          }}
        >
          <div className="w-1.5 h-1.5 rounded-full bg-white/70 animate-ping" />
        </div>

        {/* Microgravity Spherical Symmetry Callout */}
        <div className="absolute top-2 left-2 text-[10px] font-mono text-slate-400 bg-space-950/80 px-2 py-1 rounded border border-space-800">
          Buoyancy: <span className="text-emerald-400">g ≈ 0 (Spherical)</span>
        </div>

        {/* Active Flame Mode Badge */}
        <div className="absolute bottom-2 right-2 text-[10px] font-mono bg-space-950/80 px-2 py-1 rounded border border-space-800 flex items-center space-x-1">
          <Sparkles className="w-3 h-3 text-cyan-400" />
          <span className="text-cyan-300 capitalize">{flameMode} Flame Envelope</span>
        </div>
      </div>

      {/* Simulation Controls & Authentic Parameters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs bg-space-900/60 p-3 rounded-lg border border-space-800">
        <div>
          <div className="flex justify-between font-mono text-slate-300 pb-1">
            <span>d₀ Droplet:</span>
            <span className="text-nasa-cyan font-bold">{d0.toFixed(2)} mm</span>
          </div>
          <input
            type="range"
            min="1.0"
            max="4.0"
            step="0.1"
            value={d0}
            onChange={(e) => setD0(parseFloat(e.target.value))}
            className="w-full h-1 bg-space-800 rounded-lg appearance-none cursor-pointer accent-nasa-cyan"
          />
        </div>

        <div>
          <div className="flex justify-between font-mono text-slate-300 pb-1">
            <span>Ambient O₂:</span>
            <span className="text-nasa-cyan font-bold">{o2.toFixed(1)}%</span>
          </div>
          <input
            type="range"
            min="12.0"
            max="30.0"
            step="0.5"
            value={o2}
            onChange={(e) => setO2(parseFloat(e.target.value))}
            className="w-full h-1 bg-space-800 rounded-lg appearance-none cursor-pointer accent-nasa-cyan"
          />
        </div>

        <div className="flex flex-col justify-between">
          <div className="font-mono text-slate-300 pb-1">Envelope Mode:</div>
          <div className="flex space-x-1">
            {(["hot", "cool", "dual"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setFlameMode(m)}
                className={`flex-1 py-1 text-[10px] font-mono rounded uppercase transition-colors ${
                  flameMode === m
                    ? "bg-nasa-cyan text-space-950 font-bold"
                    : "bg-space-800 text-slate-400 hover:text-white"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Telemetry Metrics Readout (Strict NULL preservation) */}
      <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono bg-space-950 p-2 rounded border border-space-800">
        <div>
          <span className="text-slate-500 block text-[10px]">RAW DIAMETER</span>
          <span className="text-slate-200">
            {artifact.droplet_diameter_mm !== null && artifact.droplet_diameter_mm !== undefined
              ? `${artifact.droplet_diameter_mm} mm`
              : "-- (NULL)"}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px]">BURNING RATE K</span>
          <span className="text-nasa-cyan font-semibold">{burningRate} mm²/s</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px]">CABIN O₂</span>
          <span className="text-slate-200">
            {artifact.ambient_o2_pct !== null && artifact.ambient_o2_pct !== undefined
              ? `${artifact.ambient_o2_pct}%`
              : "-- (NULL)"}
          </span>
        </div>
      </div>
    </div>
  );
}
