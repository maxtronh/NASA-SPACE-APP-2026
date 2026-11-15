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
} from "recharts";
import { Activity, Maximize2, Radio, Check } from "lucide-react";
import { TimeseriesArtifact as TimeseriesArtifactType } from "@/types/artifacts";

interface Props {
  artifact: TimeseriesArtifactType;
  onExpand?: () => void;
}

export default function TimeseriesArtifact({ artifact, onExpand }: Props) {
  const { data, channels } = useMemo(() => {
    let chanList = artifact.channels;
    if (!chanList || chanList.length === 0) {
      chanList = [
        { channel_name: "TC-01 Chamber Core", unit: "K", color: "#ef4444", data_key: "tc1" },
        { channel_name: "TC-02 Flame Shell", unit: "K", color: "#f59e0b", data_key: "tc2" },
        { channel_name: "Chamber Pressure", unit: "kPa", color: "#06b6d4", data_key: "press" },
      ];
    }

    const points = artifact.data_points && artifact.data_points.length > 0 ? artifact.data_points : [];
    return { data: points, channels: chanList };
  }, [artifact]);

  const [activeChannels, setActiveChannels] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    channels.forEach((c) => {
      if (c.data_key) init[c.data_key] = true;
    });
    return init;
  });

  const toggleChannel = (key: string) => {
    setActiveChannels((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="bg-space-950/90 border border-nasa-cyan/40 rounded-xl p-4 shadow-xl space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-space-800">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white tracking-wide">{artifact.title}</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-800 text-emerald-300 border border-emerald-800/60 uppercase">
            Telemetry Stream
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

      {/* Channel Toggles */}
      <div className="flex flex-wrap gap-2 text-xs">
        {channels.map((ch) => {
          const key = ch.data_key || ch.channel_name;
          const isActive = activeChannels[key] ?? true;
          return (
            <button
              key={key}
              onClick={() => toggleChannel(key)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-mono flex items-center space-x-1.5 transition-colors border ${
                isActive
                  ? "bg-space-900 text-white border-space-700"
                  : "bg-space-950 text-slate-500 border-space-900 opacity-60"
              }`}
            >
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: ch.color || "#06b6d4" }}
              />
              <span>{ch.channel_name}</span>
              {ch.unit && <span className="text-slate-400">({ch.unit})</span>}
            </button>
          );
        })}
      </div>

      {/* Multi-channel Chart */}
      <div className="h-64 w-full bg-space-900/50 rounded-lg p-2 border border-space-800/80">
        {data.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 font-mono text-xs">
            <Activity className="w-6 h-6 mb-2 text-slate-600" />
            <span>NO TELEMETRY DATA POINTS RECORDED FOR THIS STREAM</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time_s" stroke="#64748b" tick={{ fontSize: 11 }} unit=" s" />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#020617", borderColor: "#334155", borderRadius: "8px" }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {channels.map((ch) => {
                const key = ch.data_key || ch.channel_name;
                if (!activeChannels[key]) return null;
                return (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    name={`${ch.channel_name}${ch.unit ? ` (${ch.unit})` : ""}`}
                    stroke={ch.color || "#06b6d4"}
                    strokeWidth={2}
                    dot={false}
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Sampling and Metadata */}
      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
        <span>Investigation: <span className="text-slate-200">{artifact.investigation_id ?? "Authenticated Flight Telemetry"}</span></span>
        <span>Sampling: <span className="text-nasa-cyan">{artifact.sampling_rate_hz ? `${artifact.sampling_rate_hz} Hz` : "Continuous"}</span></span>
      </div>
    </div>
  );
}
