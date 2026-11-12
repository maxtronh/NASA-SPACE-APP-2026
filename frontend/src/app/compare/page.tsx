"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  GitCompare,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  ShieldAlert,
  Flame,
  Layers,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { compareInvestigations, fetchInvestigations } from "@/lib/api";
import { CompareResponse, InvestigationSummary } from "@/types";
import AntigravityWarning from "@/components/AntigravityWarning";

function CompareWorkspaceContent() {
  const searchParams = useSearchParams();
  const primarySlug = searchParams.get("primary");

  const [availableInvestigations, setAvailableInvestigations] = useState<InvestigationSummary[]>([]);
  const [selectedSlugs, setSelectedSlugs] = useState<string[]>([]);
  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);

  // Load available investigations
  useEffect(() => {
    let mounted = true;
    async function loadCatalog() {
      try {
        const res = await fetchInvestigations({ limit: 50 });
        if (mounted) {
          setAvailableInvestigations(res.items);
          const initial = primarySlug
            ? [primarySlug, res.items.find((i) => i.slug !== primarySlug)?.slug || "acme-cld-flame"]
            : ["flex-droplet-burning", "acme-cld-ground-1g"];
          setSelectedSlugs(initial);
          setLoading(false);
        }
      } catch (err) {
        if (mounted) setLoading(false);
      }
    }
    loadCatalog();
    return () => {
      mounted = false;
    };
  }, [primarySlug]);

  // Execute comparison whenever selectedSlugs changes (min 2 items)
  useEffect(() => {
    let mounted = true;
    async function runCompare() {
      if (selectedSlugs.length < 2) {
        setComparison(null);
        return;
      }
      setComparing(true);
      try {
        const result = await compareInvestigations(selectedSlugs);
        if (mounted) {
          setComparison(result);
          setComparing(false);
        }
      } catch (err) {
        if (mounted) setComparing(false);
      }
    }
    runCompare();
    return () => {
      mounted = false;
    };
  }, [selectedSlugs]);

  const toggleSlug = (slug: string) => {
    if (selectedSlugs.includes(slug)) {
      if (selectedSlugs.length > 2) {
        setSelectedSlugs(selectedSlugs.filter((s) => s !== slug));
      }
    } else {
      setSelectedSlugs([...selectedSlugs, slug]);
    }
  };

  const isGravityMismatch = comparison?.equivalence_assessment.reasons.some((r) =>
    r.toLowerCase().includes("gravity")
  );

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-space-800">
        <div>
          <div className="flex items-center space-x-2 text-nasa-cyan text-xs font-mono mb-1">
            <GitCompare className="w-4 h-4" />
            <span>Multi-Condition Scientific Equivalence Workspace</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-wide">
            Experimental Condition Comparison
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Compare research regimes, gravity vectors, fuel phases, and detect experimental divergence
          </p>
        </div>
      </div>

      {/* Selector Toolbar */}
      <div className="bg-space-900 border border-space-700/80 rounded-xl p-5 shadow-lg space-y-3">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-300 uppercase tracking-wider font-semibold">
            Select Investigations to Compare (Minimum 2):
          </span>
          <span className="text-nasa-cyan">{selectedSlugs.length} Selected</span>
        </div>

        <div className="flex flex-wrap gap-2 pt-1">
          {availableInvestigations.map((inv) => {
            const isSelected = selectedSlugs.includes(inv.slug);
            const is1g = inv.gravity_level.includes("normal_gravity");

            return (
              <button
                key={inv.slug}
                onClick={() => toggleSlug(inv.slug)}
                className={`px-3 py-2 rounded-lg text-xs font-mono transition-all flex items-center space-x-2 border ${
                  isSelected
                    ? is1g
                      ? "bg-amber-950/70 border-amber-500 text-amber-200 shadow-sm shadow-amber-500/20"
                      : "bg-cyan-950/70 border-nasa-cyan text-cyan-200 shadow-sm shadow-cyan-500/20"
                    : "bg-space-950 border-space-700 text-slate-400 hover:text-white hover:bg-space-800"
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    isSelected ? (is1g ? "bg-amber-400" : "bg-nasa-cyan") : "bg-slate-600"
                  }`}
                />
                <span className="font-bold">{inv.project_acronym}:</span>
                <span className="truncate max-w-[200px] font-sans">{inv.title}</span>
                {is1g && (
                  <span className="text-[10px] px-1 rounded bg-amber-900/80 text-amber-300 font-mono">
                    1g
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Equivalence Assessment Card */}
      {comparison && (
        <div
          className={`border rounded-xl p-5 shadow-lg relative overflow-hidden transition-all ${
            comparison.equivalence_assessment.equivalent
              ? "bg-emerald-950/30 border-emerald-500/60 text-emerald-200"
              : isGravityMismatch
              ? "bg-amber-950/40 border-amber-500/80 text-amber-200"
              : "bg-rose-950/30 border-rose-500/60 text-rose-200"
          }`}
        >
          <div className="flex items-start space-x-3.5">
            <div className="p-2 rounded-lg bg-space-950/80 flex-shrink-0 mt-0.5">
              {comparison.equivalence_assessment.equivalent ? (
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              ) : isGravityMismatch ? (
                <AlertTriangle className="w-6 h-6 text-amber-400 animate-pulse" />
              ) : (
                <ShieldAlert className="w-6 h-6 text-rose-400" />
              )}
            </div>

            <div className="space-y-2 flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-bold text-white text-base">
                  {comparison.equivalence_assessment.equivalent
                    ? "Equivalence Assessment: EXPERIMENTAL CONDITIONS COMPARABLE"
                    : "Equivalence Assessment: NON-EQUIVALENT SCIENTIFIC CONDITIONS"}
                </h3>
                <span
                  className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold uppercase tracking-wider ${
                    comparison.equivalence_assessment.equivalent
                      ? "bg-emerald-900 border border-emerald-400 text-emerald-200"
                      : "bg-amber-900/90 border border-amber-400 text-amber-200"
                  }`}
                >
                  {comparison.equivalence_assessment.equivalent ? "EQUIVALENT" : "DIVERGENT"}
                </span>
              </div>

              <div className="text-xs sm:text-sm space-y-1">
                {comparison.equivalence_assessment.reasons.map((reason, idx) => (
                  <p key={idx} className="flex items-center space-x-2">
                    <span className="font-mono text-nasa-cyan">•</span>
                    <span>{reason}</span>
                  </p>
                ))}
              </div>

              {comparison.equivalence_assessment.buoyancy_warning ? (
                <div className="mt-3">
                  <AntigravityWarning warning={comparison.equivalence_assessment.buoyancy_warning} />
                </div>
              ) : isGravityMismatch && (
                <div className="mt-3 p-3 rounded-lg bg-space-950/90 border border-amber-500/40 text-xs text-amber-300 leading-relaxed font-sans">
                  <strong>Critical Microgravity Scientific Warning:</strong> Comparing microgravity
                  flames (g ≈ 10⁻⁶ g) against terrestrial 1g reference burns violates
                  quasisteady buoyant equivalence. In 1g, natural convection creates buoyancy-induced upward
                  acceleration, strong soot flickering, and shortened residence times, whereas microgravity
                  enables spherical diffusion-controlled kinetics.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Comparative Parameter Matrix */}
      {comparison && (
        <div className="bg-space-900 border border-space-700 rounded-xl shadow-lg overflow-hidden p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-space-800">
            <h3 className="font-semibold text-white text-base flex items-center space-x-2">
              <Layers className="w-5 h-5 text-nasa-cyan" />
              <span>Side-by-Side Parameter Matrix</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">
              Comparing {Object.keys(comparison.comparison_grid).length} Investigations
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-space-950 text-slate-400 uppercase text-[11px] border-b border-space-800">
                <tr>
                  <th className="py-3 px-4 w-44 font-sans font-semibold">Parameter</th>
                  {Object.entries(comparison.comparison_grid).map(([slug, item]) => (
                    <th key={slug} className="py-3 px-4 min-w-[220px]">
                      <div className="text-white font-sans font-bold text-sm">{item.acronym}</div>
                      <div className="text-[10px] text-slate-400 truncate font-mono">{slug}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-space-800">
                {/* Title */}
                <tr className="hover:bg-space-800/40">
                  <td className="py-3 px-4 font-sans font-medium text-slate-400">Full Title</td>
                  {Object.entries(comparison.comparison_grid).map(([slug, item]) => (
                    <td key={slug} className="py-3 px-4 font-sans text-slate-200">
                      {item.title}
                    </td>
                  ))}
                </tr>

                {/* Gravity Level */}
                <tr className="hover:bg-space-800/40">
                  <td className="py-3 px-4 font-sans font-medium text-slate-400">Gravity Level</td>
                  {Object.entries(comparison.comparison_grid).map(([slug, item]) => {
                    const is1g = item.gravity?.includes("normal_gravity");
                    return (
                      <td key={slug} className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            is1g
                              ? "bg-amber-950 border border-amber-500/60 text-amber-300"
                              : "bg-cyan-950 border border-cyan-500/60 text-nasa-cyan"
                          }`}
                        >
                          {item.gravity}
                        </span>
                      </td>
                    );
                  })}
                </tr>

                {/* Combustion Regime */}
                <tr className="hover:bg-space-800/40">
                  <td className="py-3 px-4 font-sans font-medium text-slate-400">Combustion Regime</td>
                  {Object.entries(comparison.comparison_grid).map(([slug, item]) => (
                    <td key={slug} className="py-3 px-4 text-nasa-cyan font-semibold">
                      {item.regime}
                    </td>
                  ))}
                </tr>

                {/* Fuel Type */}
                <tr className="hover:bg-space-800/40">
                  <td className="py-3 px-4 font-sans font-medium text-slate-400">Fuel Compound</td>
                  {Object.entries(comparison.comparison_grid).map(([slug, item]) => (
                    <td key={slug} className="py-3 px-4 text-amber-300 font-sans font-medium">
                      {item.fuel}
                    </td>
                  ))}
                </tr>

                {/* Facility */}
                <tr className="hover:bg-space-800/40">
                  <td className="py-3 px-4 font-sans font-medium text-slate-400">Flight Facility</td>
                  {Object.entries(comparison.comparison_grid).map(([slug, item]) => (
                    <td key={slug} className="py-3 px-4 font-sans text-slate-300">
                      {item.facility}
                    </td>
                  ))}
                </tr>

                {/* Oxidizer */}
                <tr className="hover:bg-space-800/40">
                  <td className="py-3 px-4 font-sans font-medium text-slate-400">Oxidizer Environment</td>
                  {Object.entries(comparison.comparison_grid).map(([slug, item]) => (
                    <td key={slug} className="py-3 px-4 text-slate-300">
                      {item.oxidizer || "Air (21% O2)"}
                    </td>
                  ))}
                </tr>

                {/* Test Runs Count */}
                <tr className="hover:bg-space-800/40">
                  <td className="py-3 px-4 font-sans font-medium text-slate-400">Total Flight Runs</td>
                  {Object.entries(comparison.comparison_grid).map(([slug, item]) => (
                    <td key={slug} className="py-3 px-4 text-white font-bold">
                      {item.runs_count} trials
                    </td>
                  ))}
                </tr>

                {/* Completeness */}
                <tr className="hover:bg-space-800/40">
                  <td className="py-3 px-4 font-sans font-medium text-slate-400">Completeness</td>
                  {Object.entries(comparison.comparison_grid).map(([slug, item]) => (
                    <td key={slug} className="py-3 px-4 text-emerald-400 font-bold">
                      {item.completeness}%
                    </td>
                  ))}
                </tr>

                {/* Actions */}
                <tr className="hover:bg-space-800/40">
                  <td className="py-3 px-4 font-sans font-medium text-slate-400">Scientific Detail</td>
                  {Object.entries(comparison.comparison_grid).map(([slug, item]) => (
                    <td key={slug} className="py-3 px-4">
                      <Link
                        href={`/investigations/${slug}`}
                        className="inline-flex items-center space-x-1 text-nasa-cyan hover:underline text-xs"
                      >
                        <span>View Deep Profile</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CompareWorkspacePage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 max-w-7xl w-full mx-auto px-4 py-16 text-center text-slate-400 font-mono animate-pulse">
          Loading Multi-Condition Comparison Workspace...
        </div>
      }
    >
      <CompareWorkspaceContent />
    </Suspense>
  );
}
