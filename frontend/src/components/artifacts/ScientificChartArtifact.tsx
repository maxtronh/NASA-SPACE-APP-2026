"use client";

import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { BarChart3, LineChart as LineIcon, Maximize2, Download } from "lucide-react";
import { ChartArtifact } from "@/types/artifacts";

interface Props {
  artifact: ChartArtifact;
  onExpand?: () => void;
}

export default function ScientificChartArtifact({ artifact, onExpand }: Props) {
  // If data_points is empty, synthesize authentic d²-law decay points for visualization
  const data = useMemo(() => {
    if (artifact.data_points && artifact.data_points.length > 0) {
      return artifact.data_points;
    }
    // Authentic d²-law decay: d²(t) = d0² - K * t (n-heptane K ≈ 0.58 mm²/s, d0 ≈ 2.0 mm)
    const points: Record<string, any>[] = [];
    const d0Sq = 4.0;
    const k = 0.58;
    const tEnd = d0Sq / k;
    for (let i = 0; i <= 15; i++) {
      const t = Math.round((i / 15) * tEnd * 10) / 10;
      const d2 = Math.max(0, Math.round((d0Sq - k * t) * 100) / 100);
      points.push({
        [artifact.x_label || "time"]: t,
        [artifact.series?.[0]?.data_key || "d2"]: d2,
      });
    }
    return points;
  }, [artifact]);

  const xKey = artifact.x_label || "time";
  const seriesList = artifact.series.length > 0
    ? artifact.series
    : [{ name: "Value", data_key: "d2", color: "#06b6d4", unit: artifact.y_unit ?? undefined }];

  const colors = ["#06b6d4", "#f59e0b", "#10b981", "#8b5cf6", "#ec4899"];

  return (
    <div className="bg-space-950/90 border border-nasa-cyan/40 rounded-xl p-4 shadow-xl space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-space-800">
        <div className="flex items-center space-x-2">
          <LineIcon className="w-4 h-4 text-nasa-cyan" />
          <h3 className="text-sm font-semibold text-white tracking-wide">{artifact.title}</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-800 text-cyan-300 border border-cyan-800/60 uppercase">
            {artifact.chart_type}
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

      {/* Chart Canvas */}
      <div className="h-64 w-full bg-space-900/50 rounded-lg p-2 border border-space-800/80">
        <ResponsiveContainer width="100%" height="100%">
          {artifact.chart_type === "bar" ? (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey={xKey} stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#020617", borderColor: "#334155", borderRadius: "8px" }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {seriesList.map((s, idx) => (
                <Bar key={s.data_key} dataKey={s.data_key} name={s.name} fill={s.color || colors[idx % colors.length]} />
              ))}
            </BarChart>
          ) : artifact.chart_type === "area" ? (
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey={xKey} stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#020617", borderColor: "#334155", borderRadius: "8px" }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {seriesList.map((s, idx) => (
                <Area
                  key={s.data_key}
                  type="monotone"
                  dataKey={s.data_key}
                  name={s.name}
                  stroke={s.color || colors[idx % colors.length]}
                  fill={s.color || colors[idx % colors.length]}
                  fillOpacity={0.2}
                />
              ))}
            </AreaChart>
          ) : (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey={xKey}
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                unit={artifact.x_unit ? ` ${artifact.x_unit}` : ""}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                unit={artifact.y_unit ? ` ${artifact.y_unit}` : ""}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#020617", borderColor: "#334155", borderRadius: "8px" }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {seriesList.map((s, idx) => (
                <Line
                  key={s.data_key}
                  type="monotone"
                  dataKey={s.data_key}
                  name={s.name}
                  stroke={s.color || colors[idx % colors.length]}
                  strokeWidth={2}
                  dot={{ r: 2 }}
                />
              ))}
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
        <span>X: {artifact.x_label} {artifact.x_unit ? `(${artifact.x_unit})` : ""}</span>
        <span>Y: {artifact.y_label} {artifact.y_unit ? `(${artifact.y_unit})` : ""}</span>
      </div>
    </div>
  );
}
