"use client";

import { useState } from "react";
import { ProvenanceInfo } from "@/types";
import { ShieldCheck, Copy, Check, ExternalLink, Hash, Clock, FileCode2 } from "lucide-react";

interface ProvenanceCardProps {
  provenance: ProvenanceInfo;
  className?: string;
}

export default function ProvenanceCard({ provenance, className = "" }: ProvenanceCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (provenance.sha256_checksum) {
      navigator.clipboard.writeText(provenance.sha256_checksum);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formattedDate = provenance.retrieval_timestamp
    ? new Date(provenance.retrieval_timestamp).toLocaleString("en-US", {
        timeZone: "UTC",
        dateStyle: "medium",
        timeStyle: "medium",
      }) + " UTC"
    : "Timestamp Authenticated";

  return (
    <div
      className={`bg-space-900 border border-space-700/80 rounded-xl p-5 shadow-lg relative overflow-hidden ${className}`}
    >
      {/* Background subtle glow */}
      <div className="absolute top-0 right-0 w-48 h-48 bg-cyan-500/5 rounded-full blur-3xl -z-10 pointer-events-none" />

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-space-800">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-white text-base">Cryptographic Provenance</h3>
            <p className="text-xs text-slate-400">Authentic NASA Physical Sciences Data Record</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold uppercase tracking-wider bg-emerald-950/80 border border-emerald-500 text-emerald-300 flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>{provenance.validation_status || "VALIDATED"}</span>
          </span>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 text-xs">
        {/* Source URL */}
        <div className="space-y-1">
          <span className="text-slate-400 font-mono uppercase text-[11px] flex items-center space-x-1">
            <ExternalLink className="w-3.5 h-3.5 text-nasa-cyan" />
            <span>NASA Source Document</span>
          </span>
          <a
            href={provenance.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-nasa-cyan hover:underline font-mono break-all flex items-center space-x-1"
          >
            <span>{provenance.source_url}</span>
          </a>
        </div>

        {/* Retrieval Timestamp */}
        <div className="space-y-1">
          <span className="text-slate-400 font-mono uppercase text-[11px] flex items-center space-x-1">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>Archive Ingestion Timestamp</span>
          </span>
          <p className="text-slate-200 font-mono">{formattedDate}</p>
        </div>

        {/* SHA-256 Checksum with Copy */}
        <div className="space-y-1 md:col-span-2">
          <span className="text-slate-400 font-mono uppercase text-[11px] flex items-center space-x-1">
            <Hash className="w-3.5 h-3.5 text-emerald-400" />
            <span>SHA-256 Digest (Zero-Fabrication Anchor)</span>
          </span>
          <div className="flex items-center space-x-2 bg-space-950 p-2 rounded-lg border border-space-800">
            <code className="text-emerald-400 font-mono text-[11px] sm:text-xs break-all flex-1 select-all">
              {provenance.sha256_checksum}
            </code>
            <button
              onClick={handleCopy}
              className="p-1.5 rounded bg-space-800 hover:bg-space-700 text-slate-300 hover:text-white transition-colors flex-shrink-0"
              title="Copy SHA-256 Checksum"
              aria-label="Copy SHA-256 Checksum"
            >
              {copied ? (
                <Check className="w-4 h-4 text-emerald-400" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Conversion Method & Parser */}
        <div className="space-y-1">
          <span className="text-slate-400 font-mono uppercase text-[11px] flex items-center space-x-1">
            <FileCode2 className="w-3.5 h-3.5 text-purple-400" />
            <span>Unit Conversion Method</span>
          </span>
          <p className="text-slate-300 font-mono">
            {provenance.conversion_method || "deterministic_si_table_v1"}
          </p>
        </div>

        {provenance.parser_module && (
          <div className="space-y-1">
            <span className="text-slate-400 font-mono uppercase text-[11px]">
              Ingestion Parser
            </span>
            <p className="text-slate-300 font-mono break-all">{provenance.parser_module}</p>
          </div>
        )}
      </div>

      {/* Original vs SI Measurements Snippet */}
      {provenance.original_measurements && Object.keys(provenance.original_measurements).length > 0 && (
        <div className="mt-4 pt-3 border-t border-space-800">
          <div className="text-[11px] font-mono text-slate-400 mb-2">
            Sample Preserved Physical Measurements (Original Raw → Deterministic SI):
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {Object.entries(provenance.original_measurements).slice(0, 6).map(([key, rawVal]) => {
              const siKey = Object.keys(provenance.si_measurements || {}).find((k) =>
                k.startsWith(key.replace(/_atm|_mm|_mmHg/g, ""))
              );
              const siVal = siKey ? provenance.si_measurements[siKey] : null;

              return (
                <div
                  key={key}
                  className="bg-space-950/70 border border-space-800 rounded p-2 text-xs"
                >
                  <div className="text-slate-400 font-mono text-[10px] truncate">{key}</div>
                  <div className="font-mono text-slate-200">
                    Raw: {rawVal === null ? <span className="text-slate-500 italic">null</span> : String(rawVal)}
                  </div>
                  {siVal !== undefined && (
                    <div className="font-mono text-nasa-cyan text-[11px]">
                      SI: {siVal === null ? <span className="text-slate-500 italic">null</span> : String(siVal)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
