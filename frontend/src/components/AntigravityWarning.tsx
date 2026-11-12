"use client";

import React from "react";
import { AlertTriangle, Info, Scale, ShieldAlert } from "lucide-react";

interface AntigravityWarningProps {
  warning?: string | null;
  gravityRegimes?: string[];
  className?: string;
}

export function AntigravityWarning({
  warning,
  gravityRegimes = [],
  className = "",
}: AntigravityWarningProps) {
  if (!warning && gravityRegimes.length <= 1) {
    return null;
  }

  const defaultWarning =
    "Scientific Non-Equivalence Warning: Comparing data across disparate gravitational regimes. Natural buoyant convection shifts flame geometry and oxidizer transport, invalidating direct burning rate comparisons without Grashof and Stefan-diffusion correction scaling.";

  return (
    <div
      className={`bg-amber-950/40 border border-amber-500/60 rounded-xl p-4 text-xs shadow-lg space-y-2 ${className}`}
    >
      <div className="flex items-center space-x-2 text-amber-300 font-bold uppercase tracking-wider font-mono">
        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 animate-pulse" />
        <span>Physical Buoyancy Non-Equivalence Detected</span>
      </div>

      <p className="text-amber-200/90 leading-relaxed font-sans">
        {warning || defaultWarning}
      </p>

      {gravityRegimes.length > 1 && (
        <div className="pt-2 border-t border-amber-500/20 flex flex-wrap items-center gap-2 font-mono text-[11px] text-amber-300/80">
          <span className="flex items-center space-x-1">
            <Scale className="w-3.5 h-3.5" />
            <span>Gravitational Regimes:</span>
          </span>
          <div className="flex flex-wrap gap-1.5">
            {gravityRegimes.map((g, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded bg-amber-900/60 border border-amber-600/50 text-amber-100"
              >
                {g}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default AntigravityWarning;
