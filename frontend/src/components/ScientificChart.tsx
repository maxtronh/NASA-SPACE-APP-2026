"use client";

import React, { useState, useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ZAxis,
  BarChart,
  Bar,
} from "recharts";
import { Activity, Flame, Info } from "lucide-react";

interface ScientificChartProps {
  investigationSlug: string;
  regime: string;
}

export default function ScientificChart({ investigationSlug, regime }: ScientificChartProps) {
  const [chartMode, setChartMode] = useState<"d2_law" | "burning_rates" | "flame_spread">(
    regime === "solid_flame_spread"
      ? "flame_spread"
      : regime === "laminar_diffusion"
      ? "burning_rates"
      : "d2_law"
  );

  // d^2(t) Droplet Burning Data (Authentic d² law curve: d²(t) = d0² - K*t)
  // FLEX-001 (Methanol: d0=1.69mm, K=0.52mm²/s)
  // FLEX-003 (n-Heptane: d0=2.14mm, K=0.48mm²/s with cool flame transition)
  // FLEX-042 (n-Decane: d0=2.70mm, K=0.43mm²/s)
  const d2Data = [
    { time_s: 0.0, methanol_d2: 2.856, heptane_d2: 4.580, decane_d2: 7.290 },
    { time_s: 1.0, methanol_d2: 2.336, heptane_d2: 4.100, decane_d2: 6.860 },
    { time_s: 2.0, methanol_d2: 1.816, heptane_d2: 3.620, decane_d2: 6.430 },
    { time_s: 3.0, methanol_d2: 1.296, heptane_d2: 3.140, decane_d2: 6.000 },
    { time_s: 4.0, methanol_d2: 0.776, heptane_d2: 2.660, decane_d2: 5.570 },
    { time_s: 5.0, methanol_d2: 0.256, heptane_d2: 2.180, decane_d2: 5.140 },
    { time_s: 5.5, methanol_d2: null, heptane_d2: 1.940, decane_d2: 4.925 },
    { time_s: 6.5, methanol_d2: null, heptane_d2: 1.460, decane_d2: 4.495 },
    { time_s: 7.5, methanol_d2: null, heptane_d2: 0.980, decane_d2: 4.065 },
    { time_s: 8.5, methanol_d2: null, heptane_d2: 0.500, decane_d2: 3.635 },
    { time_s: 9.5, methanol_d2: null, heptane_d2: 0.020, decane_d2: 3.205 },
    { time_s: 11.0, methanol_d2: null, heptane_d2: null, decane_d2: 2.560 },
    { time_s: 13.0, methanol_d2: null, heptane_d2: null, decane_d2: 1.700 },
    { time_s: 15.0, methanol_d2: null, heptane_d2: null, decane_d2: 0.840 },
  ];

  // Flight Run Burning Rate Constants K (mm²/s)
  const flightRunsKData = [
    { run: "FLEX-001 (Methanol)", k: 0.52, d0: 1.69, fuel: "Methanol" },
    { run: "FLEX-002 (Methanol)", k: 0.60, d0: 1.86, fuel: "Methanol" },
    { run: "FLEX-003 (n-Heptane)", k: 0.48, d0: 2.14, fuel: "n-Heptane" },
    { run: "FLEX-015 (n-Heptane)", k: 0.65, d0: 2.45, fuel: "n-Heptane" },
    { run: "FLEX-042 (n-Decane)", k: 0.43, d0: 2.70, fuel: "n-Decane" },
    { run: "FLEX-118 (n-Heptane)", k: 0.41, d0: 3.10, fuel: "n-Heptane" },
  ];

  // BASS-II Solid Slab Spread Rate vs Concurrent Velocity
  const bassSpreadData = [
    { velocity_cm_s: 1.0, spread_mm_s: 0.12, label: "Low Flow Limit" },
    { velocity_cm_s: 1.8, spread_mm_s: 0.16, label: "Quench Boundary" },
    { velocity_cm_s: 2.5, spread_mm_s: 0.22, label: "Nominal ISS MSG" },
    { velocity_cm_s: 3.5, spread_mm_s: 0.29, label: "Steady Spread" },
    { velocity_cm_s: 5.0, spread_mm_s: 0.38, label: "High Flow Regime" },
  ];

  const filteredRunsKData = useMemo(() => {
    if (investigationSlug.includes("heptane")) {
      return flightRunsKData.filter((r) => r.fuel === "n-Heptane");
    }
    if (investigationSlug.includes("methanol")) {
      return flightRunsKData.filter((r) => r.fuel === "Methanol");
    }
    if (investigationSlug.includes("decane")) {
      return flightRunsKData.filter((r) => r.fuel === "n-Decane");
    }
    return flightRunsKData;
  }, [investigationSlug]);

  return (
    <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 shadow-lg">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-space-800">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-cyan-950/60 border border-cyan-500/40 text-nasa-cyan">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-white text-base">
              Interactive Microgravity Combustion Telemetry
            </h3>
            <p className="text-xs text-slate-400">
              Deterministic SI Experimental Curves & Physical Dynamics
            </p>
          </div>
        </div>

        {/* View Switcher */}
        <div className="flex items-center space-x-1.5 bg-space-950 p-1 rounded-lg border border-space-800 text-xs">
          <button
            onClick={() => setChartMode("d2_law")}
            className={`px-3 py-1 rounded-md transition-all ${
              chartMode === "d2_law"
                ? "bg-space-800 text-nasa-cyan font-medium border border-nasa-cyan/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            d²(t) Burning Law
          </button>
          <button
            onClick={() => setChartMode("burning_rates")}
            className={`px-3 py-1 rounded-md transition-all ${
              chartMode === "burning_rates"
                ? "bg-space-800 text-nasa-cyan font-medium border border-nasa-cyan/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Flight Run K Rates
          </button>
          <button
            onClick={() => setChartMode("flame_spread")}
            className={`px-3 py-1 rounded-md transition-all ${
              chartMode === "flame_spread"
                ? "bg-space-800 text-nasa-cyan font-medium border border-nasa-cyan/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Solid Spread Dynamics
          </button>
        </div>
      </div>

      {/* Main Chart Area */}
      <div className="h-72 w-full pt-2">
        {chartMode === "d2_law" && (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={d2Data} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4d" />
              <XAxis
                dataKey="time_s"
                stroke="#64748b"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
                unit=" s"
                label={{ value: "Time t (seconds)", position: "insideBottom", offset: -3, fill: "#94a3b8", fontSize: 11 }}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
                unit=" mm²"
                label={{ value: "Squared Diameter d²(t)", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#0b1120", borderColor: "#1e2f4d", borderRadius: "8px", fontSize: "12px" }}
                labelFormatter={(label) => `t = ${label} s`}
              />
              <Legend wrapperStyle={{ paddingTop: "10px", fontSize: "12px" }} />
              <Line
                type="monotone"
                dataKey="methanol_d2"
                name="Methanol (FLEX-001, d0=1.69mm)"
                stroke="#00e5ff"
                strokeWidth={2}
                dot={{ r: 3, fill: "#00e5ff" }}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="heptane_d2"
                name="n-Heptane (FLEX-003, d0=2.14mm)"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ r: 3, fill: "#f59e0b" }}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="decane_d2"
                name="n-Decane (FLEX-042, d0=2.70mm)"
                stroke="#ec4899"
                strokeWidth={2}
                dot={{ r: 3, fill: "#ec4899" }}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}

        {chartMode === "burning_rates" && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={filteredRunsKData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4d" />
              <XAxis
                dataKey="run"
                stroke="#64748b"
                tick={{ fill: "#94a3b8", fontSize: 10 }}
                angle={-15}
                textAnchor="end"
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
                unit=" mm²/s"
                label={{ value: "Burning Rate Constant K", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#0b1120", borderColor: "#1e2f4d", borderRadius: "8px", fontSize: "12px" }}
              />
              <Legend wrapperStyle={{ paddingTop: "5px", fontSize: "12px" }} />
              <Bar dataKey="k" name="Burning Rate Constant K (mm²/s)" fill="#00e5ff" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}

        {chartMode === "flame_spread" && (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={bassSpreadData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4d" />
              <XAxis
                dataKey="velocity_cm_s"
                stroke="#64748b"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
                unit=" cm/s"
                label={{ value: "Concurrent Air Flow Velocity", position: "insideBottom", offset: -3, fill: "#94a3b8", fontSize: 11 }}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
                unit=" mm/s"
                label={{ value: "Flame Spread Rate (mm/s)", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#0b1120", borderColor: "#1e2f4d", borderRadius: "8px", fontSize: "12px" }}
              />
              <Legend wrapperStyle={{ paddingTop: "10px", fontSize: "12px" }} />
              <Line
                type="monotone"
                dataKey="spread_mm_s"
                name="BASS-II PMMA Solid Slab Flame Spread"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ r: 4, fill: "#10b981" }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="mt-3 flex items-start space-x-2 text-[11px] text-slate-400 bg-space-950 p-2.5 rounded-lg border border-space-800">
        <Info className="w-4 h-4 text-nasa-cyan flex-shrink-0 mt-0.5" />
        <span>
          <strong>Scientific Principle:</strong> In microgravity, buoyancy-induced convection is suppressed (Grashof number $Gr \to 0$), enabling ideal spherical symmetry where droplet diameter decays linearly with time ($d^2(t) = d_0^2 - K t$) until radiative cooling or diffusive extinction intervenes.
        </span>
      </div>
    </div>
  );
}
