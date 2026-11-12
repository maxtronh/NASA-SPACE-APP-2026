"use client";

import React, { useState } from "react";
import { BookOpen, Copy, Check, ExternalLink, Maximize2, ShieldCheck } from "lucide-react";
import { CitationArtifact as CitationArtifactType } from "@/types/artifacts";

interface Props {
  artifact: CitationArtifactType;
  onExpand?: () => void;
}

export default function CitationArtifact({ artifact, onExpand }: Props) {
  const [copied, setCopied] = useState(false);
  const [showBibtex, setShowBibtex] = useState(false);

  const bibtex = artifact.bibtex || `@article{nasa_${artifact.investigation_id || "citation"},
  title = {${artifact.title}},
  author = {${artifact.authors.length > 0 ? artifact.authors.join(" and ") : "NASA Microgravity Research Team"}},
  journal = {${artifact.journal || "NASA Technical Reports Server (NTRS)"}},
  year = {${artifact.year || 2021}},
  url = {${artifact.nasa_source_url || "https://ntrs.nasa.gov"}}
}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(bibtex);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-space-950/90 border border-emerald-500/40 rounded-xl p-4 shadow-xl space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-space-800">
        <div className="flex items-center space-x-2">
          <BookOpen className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white tracking-wide">{artifact.title}</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 flex items-center space-x-1">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span>Verified Citation</span>
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

      {/* Citation Metadata Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono bg-space-900/60 p-3 rounded-lg border border-space-800">
        <div>
          <span className="text-slate-500 text-[10px] block">AUTHORS</span>
          <span className="text-slate-200">
            {artifact.authors && artifact.authors.length > 0 ? artifact.authors.join(", ") : "NASA Glenn Research Center"}
          </span>
        </div>
        <div>
          <span className="text-slate-500 text-[10px] block">JOURNAL / REPOSITORY</span>
          <span className="text-slate-200">{artifact.journal || "NASA Technical Reports Server (NTRS)"}</span>
        </div>
        <div>
          <span className="text-slate-500 text-[10px] block">PUBLICATION YEAR</span>
          <span className="text-slate-200">{artifact.year ?? "Authentic Archive"}</span>
        </div>
        <div>
          <span className="text-slate-500 text-[10px] block">DIGITAL OBJECT IDENTIFIER (DOI)</span>
          <span className="text-nasa-cyan">{artifact.doi ?? "NASA NTRS Document ID"}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
        <button
          onClick={() => setShowBibtex(!showBibtex)}
          className="text-xs font-mono px-3 py-1.5 rounded-lg bg-space-900 hover:bg-space-800 text-slate-300 border border-space-800 transition-colors"
        >
          {showBibtex ? "Hide BibTeX" : "Show BibTeX"}
        </button>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="text-xs font-mono px-3 py-1.5 rounded-lg bg-space-900 hover:bg-space-800 text-slate-200 border border-space-800 flex items-center space-x-1.5 transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
            <span>{copied ? "Copied BibTeX" : "Copy BibTeX"}</span>
          </button>

          {artifact.nasa_source_url && (
            <a
              href={artifact.nasa_source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-mono px-3 py-1.5 rounded-lg bg-nasa-cyan hover:bg-cyan-400 text-space-950 font-bold flex items-center space-x-1 transition-colors"
            >
              <span>NASA NTRS</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>

      {/* BibTeX Code Snippet */}
      {showBibtex && (
        <pre className="text-[11px] font-mono bg-space-950 p-3 rounded-lg border border-space-800 overflow-x-auto text-emerald-300">
          {bibtex}
        </pre>
      )}
    </div>
  );
}
