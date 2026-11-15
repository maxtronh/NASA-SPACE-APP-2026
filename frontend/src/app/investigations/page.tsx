"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Compass,
  Search,
  Filter,
  Grid,
  List as ListIcon,
  ArrowRight,
  ShieldCheck,
  Flame,
  CheckCircle2,
  ExternalLink,
  GitCompare,
} from "lucide-react";
import { fetchInvestigations } from "@/lib/api";
import { InvestigationSummary } from "@/types";
import DataOriginNotice from "@/components/DataOriginNotice";

export default function InvestigationsExplorerPage() {
  const [investigations, setInvestigations] = useState<InvestigationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [dataSource, setDataSource] = useState<"live" | "demo">("live");

  // Faceted filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRegime, setSelectedRegime] = useState("all");
  const [selectedFacility, setSelectedFacility] = useState("all");
  const [selectedGravity, setSelectedGravity] = useState("all");
  const [selectedFuel, setSelectedFuel] = useState("all");
  const [minCompleteness, setMinCompleteness] = useState(0);
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      setLoading(true);
      try {
        const res = await fetchInvestigations({ limit: 50 });
        if (mounted) {
          setInvestigations(res.items);
          setDataSource(res.data_source === "demo" ? "demo" : "live");
          setLoading(false);
        }
      } catch (err) {
        if (mounted) setLoading(false);
      }
    }
    loadData();
    return () => {
      mounted = false;
    };
  }, []);

  // Filtered investigations
  const filteredInvestigations = useMemo(() => {
    return investigations.filter((inv) => {
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches =
          inv.title.toLowerCase().includes(q) ||
          inv.slug.toLowerCase().includes(q) ||
          inv.project_acronym.toLowerCase().includes(q) ||
          inv.summary.toLowerCase().includes(q) ||
          inv.fuel_type.toLowerCase().includes(q);
        if (!matches) return false;
      }

      // Regime filter
      if (selectedRegime !== "all" && inv.combustion_regime !== selectedRegime) {
        return false;
      }

      // Facility filter
      if (
        selectedFacility !== "all" &&
        !inv.facility.toLowerCase().includes(selectedFacility.toLowerCase())
      ) {
        return false;
      }

      // Gravity filter
      if (selectedGravity !== "all") {
        if (selectedGravity === "microgravity" && !inv.gravity_level.includes("microgravity")) {
          return false;
        }
        if (selectedGravity === "normal_gravity" && !inv.gravity_level.includes("normal_gravity")) {
          return false;
        }
      }

      // Fuel filter
      if (selectedFuel !== "all" && !inv.fuel_type.toLowerCase().includes(selectedFuel.toLowerCase())) {
        return false;
      }

      // Completeness slider
      const completeness = inv.data_completeness_index ?? 0;
      if (completeness < minCompleteness) {
        return false;
      }

      return true;
    });
  }, [
    investigations,
    searchQuery,
    selectedRegime,
    selectedFacility,
    selectedGravity,
    selectedFuel,
    minCompleteness,
  ]);

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-space-800">
        <div>
          <div className="flex items-center space-x-2 text-nasa-cyan text-xs font-mono mb-1">
            <Compass className="w-4 h-4" />
            <span>NASA Microgravity Combustion Catalog</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-wide">
            Investigation Explorer
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Faceted search across flight investigations from the CIR, MSG, and Glenn research facilities
          </p>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center space-x-2">
          <div className="bg-space-900 border border-space-700 rounded-lg p-1 flex items-center space-x-1">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded ${
                viewMode === "grid"
                  ? "bg-space-800 text-nasa-cyan"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Card Grid View"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={`p-1.5 rounded ${
                viewMode === "table"
                  ? "bg-space-800 text-nasa-cyan"
                  : "text-slate-400 hover:text-white"
              }`}
              title="Table View"
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <DataOriginNotice demo={dataSource === "demo"} />
      <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 shadow-lg space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            aria-label="Search investigations"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by mission, acronym, fuel, facility, or keyword (e.g. Heptane, FLEX, CIR)..."
            className="w-full pl-11 pr-4 py-2.5 rounded-lg bg-space-950 border border-space-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-nasa-cyan transition-colors"
          />
        </div>

        {/* Faceted Filters Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {/* Combustion Regime */}
          <div className="space-y-1.5">
            <label
              htmlFor="filter-regime"
              className="text-slate-300 font-mono uppercase text-[11px] block"
            >
              Combustion Regime
            </label>
            <select
              id="filter-regime"
              value={selectedRegime}
              onChange={(e) => setSelectedRegime(e.target.value)}
              className="w-full bg-space-950 border border-space-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-nasa-cyan"
            >
              <option value="all">All Regimes</option>
              <option value="droplet_combustion">Droplet Combustion (FLEX)</option>
              <option value="solid_flame_spread">Solid Fuel Spread (BASS-II)</option>
              <option value="laminar_diffusion">Laminar Diffusion (ACME)</option>
            </select>
          </div>

          {/* Flight Facility */}
          <div className="space-y-1.5">
            <label
              htmlFor="filter-facility"
              className="text-slate-300 font-mono uppercase text-[11px] block"
            >
              Facility / Rack
            </label>
            <select
              id="filter-facility"
              value={selectedFacility}
              onChange={(e) => setSelectedFacility(e.target.value)}
              className="w-full bg-space-950 border border-space-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-nasa-cyan"
            >
              <option value="all">All Facilities</option>
              <option value="cir">Combustion Integrated Rack (CIR)</option>
              <option value="msg">Microgravity Science Glovebox (MSG)</option>
              <option value="glenn">Glenn 1g Ground Rig</option>
            </select>
          </div>

          {/* Gravitational Regime */}
          <div className="space-y-1.5">
            <label
              htmlFor="filter-gravity"
              className="text-slate-300 font-mono uppercase text-[11px] block"
            >
              Gravity Environment
            </label>
            <select
              id="filter-gravity"
              value={selectedGravity}
              onChange={(e) => setSelectedGravity(e.target.value)}
              className="w-full bg-space-950 border border-space-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-nasa-cyan"
            >
              <option value="all">All Gravity Levels</option>
              <option value="microgravity">Microgravity (~10⁻⁶ g)</option>
              <option value="lunar">Lunar Gravity (0.16 g)</option>
              <option value="mars">Mars Gravity (0.38 g)</option>
              <option value="normal_gravity">Normal Gravity (1.0 g)</option>
              <option value="hypergravity">Hypergravity (2.0g / 5.0g)</option>
            </select>
          </div>

          {/* Completeness Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-300 font-mono uppercase text-[11px]">
              <span>Min Completeness</span>
              <span className="text-nasa-cyan font-bold">{minCompleteness}%</span>
            </div>
            <input
              type="range"
              aria-label="Minimum data completeness"
              aria-valuetext={`${minCompleteness} percent`}
              min="0"
              max="95"
              step="5"
              value={minCompleteness}
              onChange={(e) => setMinCompleteness(Number(e.target.value))}
              className="w-full accent-nasa-cyan h-2 bg-space-950 rounded-lg cursor-pointer"
            />
          </div>
        </div>

        {/* Filter count feedback */}
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 pt-1">
          <span>
            Showing <strong className="text-white">{filteredInvestigations.length}</strong> of{" "}
            {investigations.length} authentic NASA investigations
          </span>
          {(searchQuery ||
            selectedRegime !== "all" ||
            selectedFacility !== "all" ||
            selectedGravity !== "all" ||
            minCompleteness > 0) && (
            <button
              onClick={() => {
                setSearchQuery("");
                setSelectedRegime("all");
                setSelectedFacility("all");
                setSelectedGravity("all");
                setSelectedFuel("all");
                setMinCompleteness(0);
              }}
              className="text-nasa-cyan hover:underline"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Investigation Results */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 font-mono animate-pulse">
          Loading NASA combustion catalog...
        </div>
      ) : filteredInvestigations.length === 0 ? (
        <div className="bg-space-900 border border-space-700 rounded-xl p-12 text-center text-slate-400">
          <p className="text-base font-semibold text-white">No matching investigations found</p>
          <p className="text-xs mt-1">Try adjusting your filters or search terms</p>
        </div>
      ) : viewMode === "grid" ? (
        /* Card Grid View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredInvestigations.map((inv) => (
            <div
              key={inv.slug}
              className="bg-space-900 border border-space-700/80 rounded-xl p-5 hover:border-nasa-cyan/60 hover:shadow-cyan-500/10 hover:shadow-lg transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-2 text-xs font-mono">
                  <span className="px-2 py-0.5 rounded bg-amber-950 border border-amber-500/40 text-amber-300 font-semibold">
                    {inv.project_acronym}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono ${
                      inv.gravity_level.includes("microgravity")
                        ? "bg-cyan-950 border border-cyan-500/30 text-nasa-cyan"
                        : "bg-slate-800 border border-slate-600 text-slate-300"
                    }`}
                  >
                    {inv.gravity_level.includes("microgravity") ? "μg (~10⁻⁶ g)" : "1g Terrestrial"}
                  </span>
                </div>

                <h3 className="font-bold text-white text-base group-hover:text-nasa-cyan transition-colors line-clamp-2 mb-2">
                  {inv.title}
                </h3>

                <p className="text-xs text-slate-400 line-clamp-3 mb-4 leading-relaxed">
                  {inv.summary}
                </p>

                {/* Metadata Tags */}
                <div className="space-y-1.5 text-xs text-slate-300 mb-4 bg-space-950/60 p-3 rounded-lg border border-space-800">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-mono text-[11px]">Facility:</span>
                    <span className="font-medium text-slate-200 truncate max-w-[180px]">{inv.facility}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-mono text-[11px]">Fuel:</span>
                    <span className="font-medium text-amber-300 truncate max-w-[180px]">{inv.fuel_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-mono text-[11px]">Regime:</span>
                    <span className="font-medium text-nasa-cyan font-mono text-[11px]">
                      {inv.combustion_regime}
                    </span>
                  </div>
                </div>
              </div>

              {/* Card Footer */}
              <div className="pt-3 border-t border-space-800 space-y-3">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-slate-400 text-[11px]">
                    {inv.test_runs_count || 0} Flight Runs
                  </span>
                  <span className="text-emerald-400 text-[11px]">
                    {inv.data_completeness_index != null ? `${inv.data_completeness_index}% Complete` : "—"}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <Link
                    href={`/investigations/${inv.slug}`}
                    className="flex-1 text-center py-2 px-3 rounded-lg bg-space-800 hover:bg-space-700 text-nasa-cyan border border-space-600 hover:border-nasa-cyan text-xs font-semibold transition-all flex items-center justify-center space-x-1"
                  >
                    <span>View Scientific Profile</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                  <Link
                    href={`/compare?primary=${inv.slug}`}
                    className="p-2 rounded-lg bg-space-800 hover:bg-space-700 text-slate-300 hover:text-white border border-space-600"
                    title="Compare Investigation"
                  >
                    <GitCompare className="w-4 h-4 text-emerald-400" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Table View */
        <div className="bg-space-900 border border-space-700 rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-space-950 text-slate-400 font-mono uppercase text-[11px] border-b border-space-800">
                <tr>
                  <th className="py-3 px-4">Acronym / Title</th>
                  <th className="py-3 px-4">Combustion Regime</th>
                  <th className="py-3 px-4">Fuel Type</th>
                  <th className="py-3 px-4">Facility</th>
                  <th className="py-3 px-4">Gravity</th>
                  <th className="py-3 px-4">Runs</th>
                  <th className="py-3 px-4">Completeness</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-space-800 font-mono">
                {filteredInvestigations.map((inv) => (
                  <tr key={inv.slug} className="hover:bg-space-800/50 transition-colors">
                    <td className="py-3.5 px-4 font-sans">
                      <div className="font-bold text-white text-sm">{inv.project_acronym}</div>
                      <div className="text-xs text-slate-400 max-w-xs truncate">{inv.title}</div>
                    </td>
                    <td className="py-3.5 px-4 text-nasa-cyan">{inv.combustion_regime}</td>
                    <td className="py-3.5 px-4 text-amber-300 font-sans">{inv.fuel_type}</td>
                    <td className="py-3.5 px-4 text-slate-300 font-sans">{inv.facility}</td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] ${
                          inv.gravity_level.includes("microgravity")
                            ? "bg-cyan-950 text-nasa-cyan border border-cyan-500/30"
                            : "bg-slate-800 text-slate-300 border border-slate-600"
                        }`}
                      >
                        {inv.gravity_level.includes("microgravity") ? "μg (~10⁻⁶ g)" : "1g Ground"}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-200">{inv.test_runs_count || 0}</td>
                    <td className="py-3.5 px-4 text-emerald-400">
                      {inv.data_completeness_index != null ? `${inv.data_completeness_index}%` : "—"}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/investigations/${inv.slug}`}
                        className="text-nasa-cyan hover:underline inline-flex items-center space-x-1"
                      >
                        <span>Profile</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
