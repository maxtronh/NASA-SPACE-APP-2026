"use client";

import React, { useState } from "react";
import { Sigma, Copy, Check, Maximize2, Info } from "lucide-react";
import { EquationArtifact as EquationArtifactType } from "@/types/artifacts";

interface Props {
  artifact: EquationArtifactType;
  onExpand?: () => void;
}

export default function EquationArtifact({ artifact, onExpand }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.latex);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Human-readable formatted representation of common combustion equations
  const formattedEquation = () => {
    const raw = artifact.latex;
    if (raw.includes("d^2(t)") || raw.includes("d_0^2")) {
      return (
        <span className="text-xl sm:text-2xl font-serif tracking-wider text-cyan-200">
          <i>d</i>²(<i>t</i>) = <i>d</i>₀² − <i>K</i> · <i>t</i>
        </span>
      );
    }
    if (raw.includes("V_f") || raw.includes("u_\\infty")) {
      return (
        <span className="text-xl sm:text-2xl font-serif tracking-wider text-cyan-200">
          <i>V</i><sub>f</sub> ∝ <i>u</i><sub>∞</sub> · <i>δ</i><sup>−0.6</sup>
        </span>
      );
    }
    if (raw.includes("L_f") || raw.includes("dot{m}")) {
      return (
        <span className="text-xl sm:text-2xl font-serif tracking-wider text-cyan-200">
          <i>L</i><sub>f</sub> ~ ṁ<sub>f</sub> / (<i>ρ</i><sub>∞</sub> · <i>D</i> · <i>Y</i><sub>O₂</sub>)
        </span>
      );
    }
    return (
      <span className="text-lg sm:text-xl font-mono text-cyan-300">
        {artifact.latex}
      </span>
    );
  };

  return (
    <div className="bg-space-950/90 border border-nasa-cyan/40 rounded-xl p-4 shadow-xl space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-space-800">
        <div className="flex items-center space-x-2">
          <Sigma className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white tracking-wide">{artifact.title}</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-800 text-cyan-300 border border-cyan-800/60 uppercase">
            Governing Law
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

      {/* Mathematical Formula Render Box */}
      <div className="py-6 px-4 bg-gradient-to-r from-space-900/80 via-space-850 to-space-900/80 rounded-xl border border-space-800 flex flex-col items-center justify-center space-y-2">
        <div className="text-center">
          {formattedEquation()}
        </div>
        <div className="text-[11px] font-mono text-slate-500">
          LaTeX: <code className="text-slate-400">{artifact.latex}</code>
        </div>
      </div>

      {/* Context Description */}
      {artifact.context && (
        <div className="bg-space-900/60 p-2.5 rounded-lg border border-space-800/80 text-xs text-slate-300 flex items-start space-x-2">
          <Info className="w-3.5 h-3.5 text-nasa-cyan flex-shrink-0 mt-0.5" />
          <p>{artifact.context}</p>
        </div>
      )}

      {/* Copy Actions */}
      <div className="flex justify-end pt-1">
        <button
          onClick={handleCopy}
          className="text-xs font-mono px-3 py-1.5 rounded-lg bg-space-900 hover:bg-space-800 text-slate-200 border border-space-800 flex items-center space-x-1.5 transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
          <span>{copied ? "Copied LaTeX" : "Copy LaTeX"}</span>
        </button>
      </div>
    </div>
  );
}
