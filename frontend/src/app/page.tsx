import Link from "next/link";
import {
  Flame,
  FileCheck2,
  Layers,
  Database,
  ArrowRight,
  ShieldCheck,
  Compass,
  GitCompare,
  Sparkles,
  BarChart3,
  ExternalLink,
} from "lucide-react";
import { fetchCorpusAnalytics, fetchInvestigations } from "@/lib/api";

export const revalidate = 60;

export default async function DashboardPage() {
  const [analytics, investigationsData] = await Promise.all([
    fetchCorpusAnalytics(),
    fetchInvestigations({ limit: 4 }),
  ]);

  const totalRuns = analytics?.total_test_runs ?? (investigationsData?.items?.reduce((acc, i) => acc + (i.test_runs_count ?? 0), 0) || 0);
  const totalMeasurements = analytics?.total_measurements ?? (investigationsData?.items?.reduce((acc, i) => acc + (i.measurements_count ?? 0), 0) || 0);

  // Per-campaign run counts come from the catalog itself so the dashboard can
  // never drift from the API data.
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
      ? `${flexRuns} droplet burns, ${bassRuns} solid slabs, ${acmeRuns} gas coflow runs`
      : "Per-campaign run counts are available in the Exploration catalog";

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Mission Hero Banner */}
      <div className="relative rounded-2xl overflow-hidden bg-gradient-to-r from-space-900 via-space-850 to-space-900 border border-space-700/80 p-6 sm:p-10 shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl -z-10 pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-amber-500/5 rounded-full blur-3xl -z-10 pointer-events-none" />

        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-space-800/80 border border-space-700 text-nasa-cyan text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-nasa-cyan animate-pulse" />
            <span>NASA Microgravity Physical Sciences Informatics (PSI)</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Scientific Intelligence for{" "}
            <span className="bg-gradient-to-r from-cyan-400 via-amber-300 to-orange-400 bg-clip-text text-transparent">
              Combustion in Microgravity
            </span>
          </h1>

          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Exploring fundamental flame dynamics, cool-flame transitions, and extinction limits in buoyancy-free spaceflight environments aboard the International Space Station.
          </p>

          {/* Quick CTA Actions */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              href="/investigations"
              className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-nasa-cyan hover:bg-cyan-400 text-space-950 font-semibold text-sm transition-all shadow-md shadow-cyan-500/20"
            >
              <Compass className="w-4 h-4" />
              <span>Explore Flight Investigations</span>
            </Link>
            <Link
              href="/intelligence"
              className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-space-800 hover:bg-space-700 border border-space-600 text-white font-medium text-sm transition-all"
            >
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>Query SI Assistant</span>
            </Link>
            <Link
              href="/compare"
              className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-space-800 hover:bg-space-700 border border-space-600 text-white font-medium text-sm transition-all"
            >
              <GitCompare className="w-4 h-4 text-emerald-400" />
              <span>Compare Conditions</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 4 Mission Critical Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {/* Metric 1 */}
        <div className="bg-space-900/90 border border-space-700 rounded-xl p-5 shadow-lg relative overflow-hidden group hover:border-nasa-cyan/50 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Flight Investigations
            </span>
            <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-500/30 text-nasa-cyan">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-white">
              {analytics.total_investigations}
            </span>
            <span className="text-xs text-slate-400 font-mono">ISS CIR & MSG</span>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            FLEX, ACME, and BASS-II spaceflight mission programs
          </p>
        </div>

        {/* Metric 2 */}
        <div className="bg-space-900/90 border border-space-700 rounded-xl p-5 shadow-lg relative overflow-hidden group hover:border-amber-500/50 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Flight Test Runs
            </span>
            <div className="p-2 rounded-lg bg-amber-950/60 border border-amber-500/30 text-amber-400">
              <Flame className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-white">{totalRuns}</span>
            <span className="text-xs text-slate-400 font-mono">Individual Trials</span>
          </div>
          <p className="mt-2 text-xs text-slate-400">{campaignRunSummary}</p>
        </div>

        {/* Metric 3 */}
        <div className="bg-space-900/90 border border-space-700 rounded-xl p-5 shadow-lg relative overflow-hidden group hover:border-purple-500/50 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Discrete Measurements
            </span>
            <div className="p-2 rounded-lg bg-purple-950/60 border border-purple-500/30 text-purple-400">
              <Database className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-white">
              {totalMeasurements.toLocaleString()}
            </span>
            <span className="text-xs text-slate-400 font-mono">Telemetry Points</span>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Deterministic SI conversions with strict null preservation
          </p>
        </div>

        {/* Metric 4 */}
        <div className="bg-space-900/90 border border-space-700 rounded-xl p-5 shadow-lg relative overflow-hidden group hover:border-emerald-500/50 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Provenance Security
            </span>
            <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-500/30 text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-emerald-400">100%</span>
            <span className="text-xs text-slate-400 font-mono">SHA-256 Verified</span>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Every record anchored to authentic NASA NTRS citations
          </p>
        </div>
      </div>

      {/* Combustion Regime Distribution Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              Combustion Regimes Across Flight Campaigns
            </h2>
            <p className="text-xs text-slate-400">
              Physical regimes investigated aboard the ISS microgravity racks
            </p>
          </div>
          <Link
            href="/analytics"
            className="text-xs text-nasa-cyan hover:underline flex items-center space-x-1 font-mono"
          >
            <span>View Full Analytics</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Regime 1: Droplet */}
          <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 hover:border-cyan-500/50 transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono uppercase bg-cyan-950 border border-cyan-500/40 text-nasa-cyan">
                  Droplet Combustion
                </span>
                {flexRuns != null && (
                  <span className="text-xs font-mono text-slate-400">{flexRuns} Runs</span>
                )}
              </div>
              <h3 className="font-semibold text-white text-base">FLEX Program</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Methanol, n-Heptane, and Decane isolated droplets in the CIR. Evaluated d² burning laws, radiative extinction, and cool-flame transitions without buoyant plume distortion.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-space-800 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-mono">Facility: CIR / MDCA</span>
              <Link
                href="/investigations/flex-droplet-burning"
                className="text-nasa-cyan hover:underline flex items-center space-x-1"
              >
                <span>Inspect Runs</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Regime 2: Solid Fuel */}
          <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 hover:border-amber-500/50 transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono uppercase bg-amber-950 border border-amber-500/40 text-amber-400">
                  Solid Fuel Spread
                </span>
                {bassRuns != null && (
                  <span className="text-xs font-mono text-slate-400">{bassRuns} Runs</span>
                )}
              </div>
              <h3 className="font-semibold text-white text-base">BASS-II Program</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                PMMA solid slabs and thin fuel strips in the Microgravity Science Glovebox (MSG). Determined extinction flow limits, low-speed concurrent flame spread, and space cabin fire safety.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-space-800 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-mono">Facility: MSG Flow Duct</span>
              <Link
                href="/investigations/bass-ii-solid-slab"
                className="text-nasa-cyan hover:underline flex items-center space-x-1"
              >
                <span>Inspect Runs</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Regime 3: Laminar Diffusion */}
          <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 hover:border-purple-500/50 transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono uppercase bg-purple-950 border border-purple-500/40 text-purple-400">
                  Laminar Diffusion
                </span>
                {acmeRuns != null && (
                  <span className="text-xs font-mono text-slate-400">{acmeRuns} Runs</span>
                )}
              </div>
              <h3 className="font-semibold text-white text-base">ACME Program</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Methane and Ethylene coflow diffusion flames in the CIR. Explored non-buoyant soot inception, flame stabilization, and soot-free cool gas combustion.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-space-800 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-mono">Facility: CIR Burner</span>
              <Link
                href="/investigations/acme-cld-flame"
                className="text-nasa-cyan hover:underline flex items-center space-x-1"
              >
                <span>Inspect Runs</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Investigations Quick Access */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              Flight Investigations Catalog
            </h2>
            <p className="text-xs text-slate-400">
              Verified NASA microgravity experiments ready for scientific inspection
            </p>
          </div>
          <Link
            href="/investigations"
            className="text-xs text-nasa-cyan hover:underline flex items-center space-x-1 font-mono"
          >
            <span>View All in Explorer</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {investigationsData.items.slice(0, 3).map((inv) => (
            <div
              key={inv.slug}
              className="bg-space-900 border border-space-700/80 rounded-xl p-5 hover:border-space-600 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
                  <span className="text-amber-400 font-semibold">{inv.project_acronym}</span>
                  <span className="truncate max-w-[150px]">{inv.facility}</span>
                </div>
                <h3 className="font-semibold text-white text-sm line-clamp-2 mb-2">
                  {inv.title}
                </h3>
                <p className="text-xs text-slate-400 line-clamp-3 mb-4">
                  {inv.summary}
                </p>
              </div>

              <div className="space-y-3 pt-3 border-t border-space-800">
                {/* Completeness Bar */}
                <div>
                  <div className="flex justify-between text-[11px] font-mono text-slate-400 mb-1">
                    <span>Data Completeness</span>
                    <span className="text-emerald-400">
                      {inv.data_completeness_index != null ? `${inv.data_completeness_index}%` : "—"}
                    </span>
                  </div>
                  <div className="w-full bg-space-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-emerald-400 h-1.5 rounded-full"
                      style={{ width: `${inv.data_completeness_index ?? 0}%` }}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-slate-400 text-[11px]">
                    {inv.test_runs_count || 0} Test Runs
                  </span>
                  <Link
                    href={`/investigations/${inv.slug}`}
                    className="text-nasa-cyan hover:underline font-medium flex items-center space-x-1"
                  >
                    <span>Inspect Profile</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
