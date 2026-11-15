"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  Scale,
  Activity,
  Flame,
  ArrowRight,
  ShieldCheck,
  Zap,
  Globe,
  Rocket,
  Compass,
  Sliders,
  ExternalLink,
} from "lucide-react";
import { fetchAntigravityCompare, fetchGravityRegimes, fetchInvestigations } from "@/lib/api";
import { AntigravityCompareResponse, GravityRegimeProfile, InvestigationSummary } from "@/types";
import GravityRegimeBadge from "@/components/GravityRegimeBadge";
import AntigravityWarning from "@/components/AntigravityWarning";

export default function AntigravityWorkspacePage() {
  const [regimes, setRegimes] = useState<GravityRegimeProfile[]>([]);
  const [investigations, setInvestigations] = useState<InvestigationSummary[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([
    "flex-2-heptane-droplet",
    "acme-cld-ground-1g",
  ]);
  const [comparison, setComparison] = useState<AntigravityCompareResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedRegimeFilter, setSelectedRegimeFilter] = useState<string>("all");

  useEffect(() => {
    async function loadData() {
      try {
        const [regimesData, invData] = await Promise.all([
          fetchGravityRegimes(),
          fetchInvestigations({ limit: 50 }),
        ]);
        setRegimes(regimesData);
        setInvestigations(invData.items || []);

        // Initial comparison
        const cmp = await fetchAntigravityCompare(["flex-2-heptane-droplet", "acme-cld-ground-1g"]);
        setComparison(cmp);
      } catch (err) {
        console.error("Error loading antigravity data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleToggleInvestigation = async (slug: string) => {
    let next: string[];
    if (selectedIds.includes(slug)) {
      if (selectedIds.length <= 2) return; // Keep at least 2
      next = selectedIds.filter((id) => id !== slug);
    } else {
      if (selectedIds.length >= 5) return; // At most 5
      next = [...selectedIds, slug];
    }
    setSelectedIds(next);
    setLoading(true);
    try {
      const cmp = await fetchAntigravityCompare(next);
      setComparison(cmp);
    } catch (err) {
      console.error("Comparison error:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredInvestigations = investigations.filter((inv) => {
    if (selectedRegimeFilter === "all") return true;
    return inv.gravity_level.toLowerCase().includes(selectedRegimeFilter.toLowerCase());
  });

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-space-800">
        <div>
          <div className="flex items-center space-x-2 text-nasa-cyan text-xs font-mono mb-1">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Multi-Gravity Regime Analysis Platform</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Antigravity Comparison Workspace
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl">
            Evaluate combustion aerodynamics, buoyancy divergence, and flame structure
            across microgravity, lunar (0.16g), Mars (0.38g), terrestrial (1g), and centrifuge hypergravity.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="px-3 py-2 rounded-lg bg-space-900 border border-space-700 text-slate-300 flex items-center space-x-2">
            <Scale className="w-4 h-4 text-nasa-cyan" />
            <span>Selected: {selectedIds.length} / 5</span>
          </div>
        </div>
      </div>

      {/* Physics Regimes Spectrum Banner */}
      <div className="bg-space-900/60 border border-space-700/80 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
            <Activity className="w-4 h-4 text-nasa-cyan" />
            <span>Gravitational Spectrum & Buoyancy Scaling (Grashof Parameter)</span>
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            Gr = g · β · ΔT · L³ / ν²
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {regimes.map((r, idx) => (
            <div
              key={idx}
              className="bg-space-950 p-3 rounded-xl border border-space-800 flex flex-col justify-between space-y-2 hover:border-nasa-cyan/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-bold text-slate-200">
                  {r.category.toUpperCase()}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-space-900 text-nasa-cyan border border-space-800">
                  B = {r.buoyancy_parameter}
                </span>
              </div>
              <div className="space-y-0.5">
                <div className="text-xs font-bold text-white truncate">{r.gravity_level}</div>
                <div className="text-[10px] text-slate-400 font-mono">
                  Flame: <span className="text-slate-300">{r.flame_geometry}</span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono">
                  Convection: <span className="text-slate-300">{r.convection_regime}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Investigation Selector Chips */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            Select Investigations for Comparison:
          </span>
          {/* Regime Filter Tabs */}
          <div className="flex flex-wrap gap-1 font-mono text-[11px]">
            {["all", "microgravity", "normal_gravity", "lunar", "mars"].map((filter) => (
              <button
                key={filter}
                onClick={() => setSelectedRegimeFilter(filter)}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  selectedRegimeFilter === filter
                    ? "bg-nasa-cyan text-space-950 font-bold"
                    : "bg-space-900 text-slate-400 hover:text-white border border-space-800"
                }`}
              >
                {filter === "all" ? "All Regimes" : filter}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {filteredInvestigations.map((inv) => {
            const isSelected = selectedIds.includes(inv.slug);
            return (
              <button
                key={inv.slug}
                onClick={() => handleToggleInvestigation(inv.slug)}
                className={`p-3.5 rounded-xl border text-left transition-all flex flex-col justify-between space-y-2.5 ${
                  isSelected
                    ? "bg-space-900/90 border-nasa-cyan shadow-lg shadow-cyan-500/10 ring-1 ring-nasa-cyan"
                    : "bg-space-950/80 border-space-800 hover:border-space-700 text-slate-400"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-1 mb-1.5">
                    <span className="font-mono text-xs font-bold text-nasa-cyan truncate">
                      {inv.project_acronym}
                    </span>
                    <GravityRegimeBadge gravityLevel={inv.gravity_level} showIcon={false} />
                  </div>
                  <div className="text-xs font-semibold text-white line-clamp-1">
                    {inv.title}
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-space-800/80 text-[11px] font-mono text-slate-400">
                  <span>Fuel: {inv.fuel_type}</span>
                  <span className={isSelected ? "text-nasa-cyan font-bold" : "text-slate-500"}>
                    {isSelected ? "Selected" : "+ Add"}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Comparison Grid & Warnings */}
      {comparison && (
        <div className="space-y-6">
          {/* Buoyancy Warning Banner */}
          <AntigravityWarning
            warning={comparison.buoyancy_warning}
            gravityRegimes={comparison.gravity_regimes_compared}
          />

          {/* Side-by-Side Physical Grid */}
          <div className="bg-space-900/90 border border-space-700 rounded-2xl overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-space-800 flex items-center justify-between">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-nasa-cyan" />
                <span>Multi-Gravity Comparative Parameters Matrix</span>
              </span>
              <span
                className={`text-xs font-mono px-2.5 py-1 rounded-md border ${
                  comparison.equivalence_assessment?.equivalent
                    ? "bg-emerald-950 text-emerald-300 border-emerald-600"
                    : "bg-amber-950 text-amber-300 border-amber-600"
                }`}
              >
                {comparison.equivalence_assessment?.equivalent
                  ? "✓ Equivalent Conditions"
                  : "⚠ Non-Equivalent Aerodynamics"}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans">
                <thead className="bg-space-950 text-slate-400 font-mono text-[11px] border-b border-space-800">
                  <tr>
                    <th className="p-4 w-48">Parameter Channel</th>
                    {comparison.investigation_ids.map((id) => {
                      const item = comparison.comparison_grid[id];
                      return (
                        <th key={id} className="p-4 min-w-[220px]">
                          <div className="font-bold text-white text-sm">{item?.acronym || id}</div>
                          <div className="text-[10px] text-slate-400 line-clamp-1">{item?.title}</div>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody className="divide-y divide-space-800/80 font-mono text-slate-300">
                  {/* Gravitational Regime */}
                  <tr className="hover:bg-space-800/30">
                    <td className="p-4 font-semibold text-slate-400">Gravity Level</td>
                    {comparison.investigation_ids.map((id) => (
                      <td key={id} className="p-4">
                        <GravityRegimeBadge
                          gravityLevel={comparison.comparison_grid[id]?.gravity}
                        />
                      </td>
                    ))}
                  </tr>

                  {/* Buoyancy Parameter */}
                  <tr className="hover:bg-space-800/30">
                    <td className="p-4 font-semibold text-slate-400">Buoyancy Parameter (B)</td>
                    {comparison.investigation_ids.map((id) => {
                      const p = comparison.gravity_matrix[id];
                      return (
                        <td key={id} className="p-4 font-bold text-nasa-cyan">
                          {p?.buoyancy_parameter.toFixed(4) || "—"}
                        </td>
                      );
                    })}
                  </tr>

                  {/* Convection Regime */}
                  <tr className="hover:bg-space-800/30">
                    <td className="p-4 font-semibold text-slate-400">Convection Regime</td>
                    {comparison.investigation_ids.map((id) => {
                      const p = comparison.gravity_matrix[id];
                      return (
                        <td key={id} className="p-4 capitalize text-slate-200">
                          {p?.convection_regime || "—"}
                        </td>
                      );
                    })}
                  </tr>

                  {/* Flame Macro-Geometry */}
                  <tr className="hover:bg-space-800/30">
                    <td className="p-4 font-semibold text-slate-400">Flame Geometry</td>
                    {comparison.investigation_ids.map((id) => {
                      const p = comparison.gravity_matrix[id];
                      return (
                        <td key={id} className="p-4 capitalize text-amber-300 font-semibold">
                          {p?.flame_geometry || "—"}
                        </td>
                      );
                    })}
                  </tr>

                  {/* Soot Behavior */}
                  <tr className="hover:bg-space-800/30">
                    <td className="p-4 font-semibold text-slate-400">Soot Transport Mode</td>
                    {comparison.investigation_ids.map((id) => {
                      const p = comparison.gravity_matrix[id];
                      return (
                        <td key={id} className="p-4 capitalize text-slate-300">
                          {p?.soot_behavior || "—"}
                        </td>
                      );
                    })}
                  </tr>

                  {/* Combustion Regime */}
                  <tr className="hover:bg-space-800/30">
                    <td className="p-4 font-semibold text-slate-400">Combustion Regime</td>
                    {comparison.investigation_ids.map((id) => (
                      <td key={id} className="p-4 font-sans text-white">
                        {comparison.comparison_grid[id]?.regime || "—"}
                      </td>
                    ))}
                  </tr>

                  {/* Fuel Type */}
                  <tr className="hover:bg-space-800/30">
                    <td className="p-4 font-semibold text-slate-400">Fuel Type</td>
                    {comparison.investigation_ids.map((id) => (
                      <td key={id} className="p-4 font-sans text-white">
                        {comparison.comparison_grid[id]?.fuel || "—"}
                      </td>
                    ))}
                  </tr>

                  {/* Facility */}
                  <tr className="hover:bg-space-800/30">
                    <td className="p-4 font-semibold text-slate-400">Flight Facility</td>
                    {comparison.investigation_ids.map((id) => (
                      <td key={id} className="p-4 font-sans text-slate-300 text-xs">
                        {comparison.comparison_grid[id]?.facility || "—"}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
