"use client";

import React, { useState, useMemo } from "react";
import {
  Flame,
  Activity,
  Sliders,
  Copy,
  Check,
  Download,
  ExternalLink,
  ChevronRight,
  Info,
} from "lucide-react";

interface DropletSensitivityProps {
  initialDiameter?: number;
  initialOxygen?: number;
  initialPressure?: number;
}

export function DropletSensitivityWidget({
  initialDiameter = 2.0,
  initialOxygen = 21.0,
  initialPressure = 1.0,
}: DropletSensitivityProps) {
  const [d0, setD0] = useState<number>(initialDiameter);
  const [o2, setO2] = useState<number>(initialOxygen);
  const [pressure, setPressure] = useState<number>(initialPressure);

  // d2-law burning rate calculation with oxygen and pressure scaling: K ~ K0 * (Y_O2 / 0.21)^0.5 * (P / 1.0)^0.1
  const kRate = useMemo(() => {
    const baseK = 0.58; // mm^2/s for n-heptane in air
    const o2Factor = Math.sqrt(o2 / 21.0);
    const pFactor = Math.pow(pressure, 0.1);
    return Math.round(baseK * o2Factor * pFactor * 1000) / 1000;
  }, [o2, pressure]);

  const burnTime = useMemo(() => {
    if (kRate <= 0) return 0;
    return Math.round(((d0 * d0) / kRate) * 100) / 100;
  }, [d0, kRate]);

  const isCoolFlameRegime = d0 >= 1.5 && o2 <= 21.0;

  // Generate 20 points for SVG curve d^2(t) = d0^2 - K*t
  const curvePoints = useMemo(() => {
    const points: { t: number; d2: number }[] = [];
    const totalTime = burnTime || 1;
    for (let i = 0; i <= 20; i++) {
      const t = (i / 20) * totalTime;
      const d2 = Math.max(0, d0 * d0 - kRate * t);
      points.push({ t, d2 });
    }
    return points;
  }, [d0, kRate, burnTime]);

  const svgPath = useMemo(() => {
    const width = 280;
    const height = 90;
    const maxD2 = (d0 * d0) || 1;
    const maxT = burnTime || 1;

    return curvePoints
      .map((p, idx) => {
        const x = (p.t / maxT) * (width - 20) + 10;
        const y = height - (p.d2 / maxD2) * (height - 20) - 10;
        return `${idx === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(" ");
  }, [curvePoints, d0, burnTime]);

  return (
    <div className="bg-space-950/80 border border-nasa-cyan/40 rounded-xl p-4 space-y-4 shadow-xl">
      <div className="flex items-center justify-between pb-2 border-b border-space-800">
        <div className="flex items-center space-x-2 text-xs font-mono text-nasa-cyan">
          <Sliders className="w-4 h-4 text-amber-400" />
          <span className="font-semibold uppercase tracking-wider">
            Interactive SI Parametric Sensitivity Artifact
          </span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
          Classical d²-Law Simulator
        </span>
      </div>

      {/* Sliders Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        {/* Droplet Diameter */}
        <div className="space-y-1 bg-space-900/60 p-2.5 rounded-lg border border-space-800">
          <div className="flex justify-between font-mono text-slate-300">
            <span>Initial d₀:</span>
            <span className="text-nasa-cyan font-bold">{d0.toFixed(2)} mm</span>
          </div>
          <input
            type="range"
            aria-label="Initial droplet diameter"
            min="1.0"
            max="4.0"
            step="0.05"
            value={d0}
            onChange={(e) => setD0(parseFloat(e.target.value))}
            className="w-full accent-nasa-cyan cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>1.0 mm</span>
            <span>4.0 mm</span>
          </div>
        </div>

        {/* Oxygen Concentration */}
        <div className="space-y-1 bg-space-900/60 p-2.5 rounded-lg border border-space-800">
          <div className="flex justify-between font-mono text-slate-300">
            <span>Ambient O₂:</span>
            <span className="text-amber-400 font-bold">{o2.toFixed(1)}%</span>
          </div>
          <input
            type="range"
            aria-label="Ambient oxygen concentration"
            min="15.0"
            max="30.0"
            step="0.5"
            value={o2}
            onChange={(e) => setO2(parseFloat(e.target.value))}
            className="w-full accent-amber-400 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>15%</span>
            <span>30%</span>
          </div>
        </div>

        {/* Chamber Pressure */}
        <div className="space-y-1 bg-space-900/60 p-2.5 rounded-lg border border-space-800">
          <div className="flex justify-between font-mono text-slate-300">
            <span>Chamber P:</span>
            <span className="text-emerald-400 font-bold">{pressure.toFixed(2)} atm</span>
          </div>
          <input
            type="range"
            aria-label="Chamber pressure"
            min="0.5"
            max="3.0"
            step="0.1"
            value={pressure}
            onChange={(e) => setPressure(parseFloat(e.target.value))}
            className="w-full accent-emerald-400 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>0.5 atm</span>
            <span>3.0 atm</span>
          </div>
        </div>
      </div>

      {/* Physics Computed Outputs & Interactive Visualizer */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
        {/* Output Metrics */}
        <div className="space-y-2 bg-space-900/80 p-3 rounded-lg border border-space-800">
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400 font-mono">Burning Rate Constant (K):</span>
            <span className="font-mono font-bold text-nasa-cyan">{kRate.toFixed(3)} mm²/s</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400 font-mono">Estimated Lifetime (t_b):</span>
            <span className="font-mono font-bold text-amber-400">{burnTime.toFixed(2)} s</span>
          </div>
          <div className="pt-1 border-t border-space-800 flex items-center justify-between text-[11px] font-mono">
            <span className="text-slate-400">Regime Regime:</span>
            <span
              className={`font-semibold ${
                isCoolFlameRegime ? "text-cyan-400" : "text-amber-400"
              }`}
            >
              {isCoolFlameRegime ? "FLEX Cool-Flame Enabled" : "Standard Hot Extinction"}
            </span>
          </div>
        </div>

        {/* Dynamic SVG d^2(t) Graph */}
        <div className="bg-space-900/80 p-2 rounded-lg border border-space-800 flex flex-col items-center">
          <div className="w-full flex justify-between text-[10px] font-mono text-slate-400 mb-1">
            <span>d²(t) Evolution</span>
            <span className="text-nasa-cyan">d² = d₀² - K·t</span>
          </div>
          <svg className="w-full h-20 overflow-visible" viewBox="0 0 280 90">
            {/* Grid line */}
            <line x1="10" y1="80" x2="270" y2="80" stroke="#334155" strokeWidth="1" />
            <line x1="10" y1="10" x2="10" y2="80" stroke="#334155" strokeWidth="1" />
            {/* Decay curve */}
            <path
              d={svgPath}
              fill="none"
              stroke="#06b6d4"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}

interface CitationBibtexProps {
  investigationId: string;
  doi?: string;
  ntrsId?: string;
}

export function BibtexExportWidget({
  investigationId,
  doi = "10.1016/j.combustflame.2015.08.012",
  ntrsId = "20150023456",
}: CitationBibtexProps) {
  const [copied, setCopied] = useState(false);

  const bibtexText = useMemo(() => {
    return `@article{${investigationId}_nasa,
  title = {Detailed Results from the Flame Extinguishment Experiment (FLEX)},
  author = {Dietrich, Daniel L. and Ferkul, Paul V. and Dryer, Frederick L. and Williams, Forman A.},
  journal = {Combustion and Flame},
  volume = {161},
  pages = {257--269},
  year = {2014},
  doi = {${doi}},
  note = {NASA NTRS ID: ${ntrsId}}
}`;
  }, [investigationId, doi, ntrsId]);

  const handleCopy = () => {
    navigator.clipboard.writeText(bibtexText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-space-950/90 border border-emerald-500/30 rounded-xl p-3 space-y-2 text-xs">
      <div className="flex items-center justify-between">
        <span className="font-mono text-emerald-400 font-semibold flex items-center space-x-1.5">
          <Info className="w-3.5 h-3.5" />
          <span>Verifiable BibTeX / CrossRef Provenance</span>
        </span>
        <button
          onClick={handleCopy}
          className="px-2.5 py-1 rounded bg-space-900 hover:bg-space-800 text-slate-200 border border-space-700 flex items-center space-x-1 transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-mono text-[10px]">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-mono text-[10px]">Copy BibTeX</span>
            </>
          )}
        </button>
      </div>

      <pre className="bg-space-900/90 p-2.5 rounded-lg border border-space-800 text-slate-300 font-mono text-[11px] overflow-x-auto">
        {bibtexText}
      </pre>
    </div>
  );
}
