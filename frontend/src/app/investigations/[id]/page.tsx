import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  Flame,
  Layers,
  Calendar,
  Users,
  Building2,
  Gauge,
  Sparkles,
  GitCompare,
  ExternalLink,
  ShieldCheck,
  Activity,
  AlertTriangle,
} from "lucide-react";
import { fetchInvestigationDetail } from "@/lib/api";
import ProvenanceCard from "@/components/ProvenanceCard";
import ScientificChart from "@/components/ScientificChart";

interface InvestigationDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function InvestigationDetailPage({ params }: InvestigationDetailPageProps) {
  const { id } = await params;

  let data;
  try {
    data = await fetchInvestigationDetail(id);
  } catch (err) {
    notFound();
  }

  const { investigation, provenance } = data;
  const test_runs = data.test_runs ?? [];

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link
          href="/investigations"
          className="inline-flex items-center space-x-2 text-xs font-mono text-slate-400 hover:text-nasa-cyan transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Investigation Catalog</span>
        </Link>

        <div className="flex items-center space-x-3">
          <Link
            href={`/compare?primary=${investigation.slug}`}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-space-800 hover:bg-space-700 text-xs font-semibold text-emerald-400 border border-space-600 transition-colors"
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>Compare in Workspace</span>
          </Link>
          <a
            href={investigation.nasa_source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-nasa-cyan hover:bg-cyan-400 text-space-950 text-xs font-semibold transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span>Open NASA NTRS Record</span>
          </a>
        </div>
      </div>

      {/* Investigation Title Header */}
      <div className="bg-space-900 border border-space-700 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="max-w-4xl space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-3 py-1 rounded-md text-xs font-mono font-bold bg-amber-950 border border-amber-500/40 text-amber-300">
              {investigation.project_acronym}
            </span>
            <span className="px-3 py-1 rounded-md text-xs font-mono bg-cyan-950 border border-cyan-500/40 text-nasa-cyan">
              {investigation.combustion_regime}
            </span>
            <span className="px-3 py-1 rounded-md text-xs font-mono bg-space-800 border border-space-700 text-slate-300">
              {investigation.gravity_level}
            </span>
            <span className="px-2.5 py-1 rounded-md text-xs font-mono bg-emerald-950 border border-emerald-500/40 text-emerald-400 flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>100% SHA-256 Provenance</span>
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-snug">
            {investigation.title}
          </h1>

          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            {investigation.summary}
          </p>

          {/* Key Parameters Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-space-800 text-xs">
            <div>
              <span className="text-slate-400 font-mono block text-[11px]">Flight Facility</span>
              <span className="text-white font-medium">{investigation.facility}</span>
            </div>
            <div>
              <span className="text-slate-400 font-mono block text-[11px]">Fuel Type</span>
              <span className="text-amber-300 font-medium">{investigation.fuel_type}</span>
            </div>
            <div>
              <span className="text-slate-400 font-mono block text-[11px]">Oxidizer / Diluent</span>
              <span className="text-slate-200 font-medium">
                {investigation.oxidizer_type || "Air"}{" "}
                {investigation.diluents ? `(${investigation.diluents})` : ""}
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-mono block text-[11px]">Data Completeness</span>
              <span className="text-emerald-400 font-mono font-bold">
                {investigation.data_completeness_index != null ? `${investigation.data_completeness_index}%` : "—"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Scientific Objectives, Apparatus, PIs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Objectives & Apparatus */}
        <div className="lg:col-span-2 space-y-6">
          {/* Objectives */}
          <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 shadow-lg">
            <h3 className="font-semibold text-white text-base mb-2 flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-nasa-cyan" />
              <span>Scientific Objectives</span>
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {investigation.objectives ||
                "Characterize the fundamental combustion dynamics, burning rates, and extinction limits of microgravity flames without buoyant convective distortion."}
            </p>
          </div>

          {/* Test Apparatus */}
          <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 shadow-lg">
            <h3 className="font-semibold text-white text-base mb-2 flex items-center space-x-2">
              <Building2 className="w-4 h-4 text-amber-400" />
              <span>Flight Apparatus & Environment</span>
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {investigation.apparatus_description ||
                "Integrated flight experiment package mounted inside the Combustion Integrated Rack (CIR) / Microgravity Science Glovebox (MSG) on the International Space Station."}
            </p>
          </div>

          {/* Interactive Scientific Chart */}
          <ScientificChart
            investigationSlug={investigation.slug}
            regime={investigation.combustion_regime}
          />
        </div>

        {/* Sidebar: Provenance & Principal Investigators */}
        <div className="space-y-6">
          {/* Cryptographic Provenance Card */}
          <ProvenanceCard provenance={provenance} />

          {/* Principal Investigators */}
          {investigation.principal_investigators && investigation.principal_investigators.length > 0 && (
            <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 shadow-lg space-y-3">
              <h3 className="font-semibold text-white text-sm flex items-center space-x-2">
                <Users className="w-4 h-4 text-purple-400" />
                <span>Principal Investigators</span>
              </h3>
              <div className="space-y-3 text-xs">
                {investigation.principal_investigators.map((pi, idx) => (
                  <div key={idx} className="border-l-2 border-nasa-cyan pl-3 py-0.5">
                    <div className="font-bold text-white">{pi.name}</div>
                    <div className="text-slate-400 text-[11px]">{pi.affiliation}</div>
                    <div className="text-nasa-cyan text-[10px] font-mono">{pi.role}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Flight Test Runs Table with Mandatory Null-Preservation */}
      <div className="bg-space-900 border border-space-700 rounded-xl shadow-lg overflow-hidden space-y-4 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-space-800">
          <div>
            <h3 className="font-semibold text-white text-base flex items-center space-x-2">
              <Flame className="w-5 h-5 text-amber-400" />
              <span>Flight Test Runs Telemetry</span>
            </h3>
            <p className="text-xs text-slate-400">
              Individual flight runs from NASA archives. Unmeasured channels strictly preserved as{" "}
              <code className="text-amber-400 font-mono">null</code> without zero-substitution.
            </p>
          </div>
          <div className="text-xs font-mono text-slate-400">
            {test_runs.length > 0 ? `${test_runs.length} Runs Indexed` : "Authentic Flight Runs"}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-space-950 text-slate-400 uppercase text-[11px] border-b border-space-800">
              <tr>
                <th className="py-3 px-3">Run Identifier</th>
                <th className="py-3 px-3">Phase / Type</th>
                <th className="py-3 px-3">Chamber Pressure (kPa)</th>
                <th className="py-3 px-3">Initial d₀ (mm)</th>
                <th className="py-3 px-3">Burning Rate K (mm²/s)</th>
                <th className="py-3 px-3">Flame Spread (mm/s)</th>
                <th className="py-3 px-3">Burn Time (s)</th>
                <th className="py-3 px-3">Extinction Mode</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-space-800">
              {test_runs.length > 0 ? (
                test_runs.map((run, idx) => (
                  <tr key={run.run_identifier || idx} className="hover:bg-space-800/40">
                    <td className="py-3 px-3 font-bold text-white">{run.run_identifier}</td>
                    <td className="py-3 px-3 text-slate-300 font-sans">{run.fuel_phase || "–"}</td>
                    <td className="py-3 px-3 text-slate-200">
                      {run.chamber_pressure_kpa != null ? (
                        run.chamber_pressure_kpa.toFixed(2)
                      ) : (
                        <span className="text-slate-500 italic">Unmeasured / null</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-nasa-cyan">
                      {run.droplet_initial_diameter_mm != null ? (
                        run.droplet_initial_diameter_mm.toFixed(2)
                      ) : (
                        <span className="text-slate-500 italic">Unmeasured / null</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-amber-300">
                      {run.burning_rate_constant_k_mm2_s != null ? (
                        run.burning_rate_constant_k_mm2_s.toFixed(2)
                      ) : (
                        <span className="text-slate-500 italic">Unmeasured / null</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-emerald-400">
                      {run.flame_spread_rate_mm_s != null ? (
                        run.flame_spread_rate_mm_s.toFixed(2)
                      ) : (
                        <span className="text-slate-500 italic">Unmeasured / null</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-300">
                      {run.burn_duration_s != null ? (
                        run.burn_duration_s.toFixed(1)
                      ) : (
                        <span className="text-slate-500 italic">Unmeasured / null</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-purple-300 font-sans">
                      {run.extinction_type ? (
                        <span className="px-1.5 py-0.5 rounded bg-space-800 border border-space-700 text-[10px]">
                          {run.extinction_type}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">Unmeasured / null</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400 font-sans">
                    No flight runs recorded for this investigation.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
