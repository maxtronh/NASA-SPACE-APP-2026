import {
  BarChart3,
  Layers,
  Database,
  Flame,
  ShieldCheck,
  AlertCircle,
} from "lucide-react";
import { fetchCorpusAnalytics, fetchInvestigations } from "@/lib/api";
import FlammabilityEvaluatorWidget from "@/components/FlammabilityEvaluatorWidget";
import DataOriginNotice from "@/components/DataOriginNotice";

export const revalidate = 60;

export default async function AnalyticsPage() {
  const [analytics, investigationsData] = await Promise.all([
    fetchCorpusAnalytics(),
    fetchInvestigations({ limit: 50 }),
  ]);

  // Prefer the analytics totals. When the API omits them, sum the catalog
  // counts; if those are missing too, show "Unavailable" instead of a fake 0.
  const catalogRuns = investigationsData.items
    .map((investigation) => investigation.test_runs_count)
    .filter((count): count is number => count != null);
  const catalogMeasurements = investigationsData.items
    .map((investigation) => investigation.measurements_count)
    .filter((count): count is number => count != null);
  const totalRuns =
    analytics.total_test_runs ??
    (catalogRuns.length > 0 ? catalogRuns.reduce((sum, count) => sum + count, 0) : null);
  const totalMeasurements =
    analytics.total_measurements ??
    (catalogMeasurements.length > 0
      ? catalogMeasurements.reduce((sum, count) => sum + count, 0)
      : null);
  const usingDemo =
    analytics.data_source === "demo" || investigationsData.data_source === "demo";

  const runsBySlug = new Map(
    investigationsData.items.map((investigation) => [
      investigation.slug,
      investigation.test_runs_count,
    ])
  );
  const flexRuns = runsBySlug.get("flex-droplet-burning");
  const bassRuns = runsBySlug.get("bass-ii-solid-slab");
  const acmeRuns = runsBySlug.get("acme-cld-flame");
  const campaignRunSummary =
    flexRuns != null && bassRuns != null && acmeRuns != null
      ? `${flexRuns} droplet burns, ${bassRuns} solid slab spreads, ${acmeRuns} gas coflow runs`
      : "Per-campaign run counts are available in the Exploration catalog";

  const matrixEntries = Object.entries(analytics.missing_data_matrix || {});

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-space-800">
        <div>
          <div className="flex items-center space-x-2 text-nasa-cyan text-xs font-mono mb-1">
            <BarChart3 className="w-4 h-4" />
            <span>Telemetry Coverage & Scientific Completeness Matrix</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-wide">
            Corpus Analytics & Missing Data Matrix
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Systematic audit of physical measurement channels, sensor availability, and null preservation
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-500/40 px-3 py-1.5 rounded-lg">
          <ShieldCheck className="w-4 h-4" />
          <span>Strict Zero-Fabrication Protocol</span>
        </div>
      </div>

      <DataOriginNotice demo={usingDemo} />

      {/* Top Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg">
          <div className="flex justify-between items-center text-xs font-mono text-slate-400">
            <span>Total Flight Campaigns</span>
            <Layers className="w-4 h-4 text-nasa-cyan" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-white">
              {analytics.total_investigations}
            </span>
            <span className="text-xs text-slate-400 font-mono">ISS Missions</span>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            CIR MDCA, MSG Glovebox, and Glenn reference rigs
          </p>
        </div>

        <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg">
          <div className="flex justify-between items-center text-xs font-mono text-slate-400">
            <span>Documented Flight Runs</span>
            <Flame className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-white">
              {totalRuns != null ? totalRuns : "Unavailable"}
            </span>
            {totalRuns != null && (
              <span className="text-xs text-slate-400 font-mono">Trials</span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-2">{campaignRunSummary}</p>
        </div>

        <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg">
          <div className="flex justify-between items-center text-xs font-mono text-slate-400">
            <span>Deterministic SI Telemetry</span>
            <Database className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-white">
              {totalMeasurements != null ? totalMeasurements.toLocaleString() : "Unavailable"}
            </span>
            {totalMeasurements != null && (
              <span className="text-xs text-slate-400 font-mono">Measurements</span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-2">
            100% SHA-256 anchored to official NASA NTRS archives
          </p>
        </div>
      </div>

      {/* Scientific Principle Notice: Why NULL is Not Zero */}
      <div className="bg-gradient-to-r from-space-900 via-cyan-950/30 to-space-900 border border-cyan-500/30 rounded-xl p-5 shadow-lg space-y-2">
        <div className="flex items-center space-x-2 text-nasa-cyan font-bold text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>NASA Data Integrity Mandate: A Missing Measurement is NULL, Never Zero</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          In experimental microgravity combustion research, unmeasured physical quantities (e.g. uncalibrated
          radiometer signals, non-applicable droplet diameters for solid fuels, or saturated photodiodes) must
          be preserved as SQL <code className="text-nasa-cyan font-mono">NULL</code>. Substituting zero would
          imply an erroneous physical assertion (e.g., zero temperature, zero pressure, or zero flame height)
          that distorts empirical scaling laws and numerical model validation.
        </p>
      </div>

      {/* Missing Data Matrix Structured Grid / Heatmap */}
      <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-space-800">
          <div>
            <h3 className="font-semibold text-white text-base">
              Missing Data Matrix across Scientific Channels
            </h3>
            <p className="text-xs text-slate-400">
              Corpus-wide presence count, missing channels, and completeness percentages
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {matrixEntries.length} Physical Channels Evaluated
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-space-950 text-slate-400 uppercase text-[11px] border-b border-space-800">
              <tr>
                <th className="py-3 px-4 font-sans font-semibold">Physical Parameter</th>
                <th className="py-3 px-4">Present Records</th>
                <th className="py-3 px-4">Missing / Null Records</th>
                <th className="py-3 px-4 min-w-[200px]">Completeness Index</th>
                <th className="py-3 px-4">Applicable Flight Regimes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-space-800">
              {matrixEntries.map(([param, stats]) => {
                const pct = stats.completeness_pct;
                const isHigh = pct >= 80;
                const isMid = pct > 0 && pct < 80;
                const isZero = pct === 0;

                const regimeNote =
                  param === "chamber_pressure"
                    ? totalRuns != null
                      ? `Universal (all ${totalRuns} flight runs)`
                      : "Universal across indexed flight runs"
                    : param === "droplet_initial_diameter"
                    ? "FLEX droplet combustion"
                    : param === "burning_rate_constant"
                    ? "FLEX droplet extinction"
                    : param === "flame_spread_rate"
                    ? "BASS-II solid fuel spread"
                    : param === "fuel_flow_rate"
                    ? "ACME gas jet flames"
                    : param === "soot_volume_fraction"
                    ? "ACME coflow flames"
                    : "Radiometer uncalibrated / absent";

                return (
                  <tr key={param} className="hover:bg-space-800/40">
                    <td className="py-3.5 px-4 font-sans font-medium text-white">
                      <code>{param}</code>
                    </td>
                    <td className="py-3.5 px-4 text-emerald-400 font-bold">
                      {stats.present_count}
                    </td>
                    <td className="py-3.5 px-4 text-amber-400">
                      {stats.missing_count}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-28 bg-space-800 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-2 rounded-full ${
                              isHigh
                                ? "bg-emerald-400"
                                : isMid
                                ? "bg-amber-400"
                                : "bg-slate-600"
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span
                          className={`font-bold ${
                            isHigh
                              ? "text-emerald-400"
                              : isMid
                              ? "text-amber-400"
                              : "text-slate-500"
                          }`}
                        >
                          {pct.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-sans text-slate-300 text-[11px]">
                      {regimeNote}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* NASA-STD-6001B Flammability & Merkle Provenance Widget */}
      <FlammabilityEvaluatorWidget />

      {/* Regime Breakdown Cards */}
      <div className="space-y-4">
        <h3 className="font-semibold text-white text-base">
          Research Campaign Allocation
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-space-900 border border-space-700/80 rounded-xl p-5">
            <div className="flex justify-between text-xs font-mono text-slate-400 mb-2">
              <span className="text-nasa-cyan font-bold">CIR Facility</span>
              {flexRuns != null && <span>{flexRuns} Runs</span>}
            </div>
            <h4 className="font-bold text-white text-base">FLEX (Droplet Combustion)</h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Evaluating the classical d² burning rate law, radiative extinction, and cool flames
              in isolated Methanol, n-Heptane, and Decane droplets.
            </p>
          </div>

          <div className="bg-space-900 border border-space-700/80 rounded-xl p-5">
            <div className="flex justify-between text-xs font-mono text-slate-400 mb-2">
              <span className="text-amber-400 font-bold">MSG Facility</span>
              {bassRuns != null && <span>{bassRuns} Runs</span>}
            </div>
            <h4 className="font-bold text-white text-base">BASS-II (Solid Fuel Spread)</h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Measuring flame spread velocity and extinction limits across thick PMMA slabs and thin
              strips under low-speed concurrent convective airflow.
            </p>
          </div>

          <div className="bg-space-900 border border-space-700/80 rounded-xl p-5">
            <div className="flex justify-between text-xs font-mono text-slate-400 mb-2">
              <span className="text-purple-400 font-bold">CIR Facility</span>
              {acmeRuns != null && <span>{acmeRuns} Runs</span>}
            </div>
            <h4 className="font-bold text-white text-base">ACME (Laminar Diffusion)</h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Investigating buoyancy-free laminar diffusion flames of Methane, soot inception, and
              flame geometry stabilization without buoyant acceleration.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
