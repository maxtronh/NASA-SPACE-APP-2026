'use client';

import React, { useState } from 'react';
import Link from 'next/link';

export default function HandbookPage() {
  const [activeTab, setActiveTab] = useState<'standards' | 'equations' | 'regimes' | 'offline'>('standards');

  return (
    <div className="min-h-screen bg-[#0a0e17] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="border-b border-slate-800 pb-6">
          <div className="flex items-center gap-3 mb-2">
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-blue-900/60 text-blue-300 border border-blue-700/50">
              NASA Technical Handbook
            </span>
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-900/60 text-emerald-300 border border-emerald-700/50">
              PWA Offline Ready
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
            Microgravity Combustion & Spacecraft Fire Safety Handbook
          </h1>
          <p className="text-slate-400 mt-2 text-sm md:text-base">
            Authoritative reference manual grounded in NASA-STD-6001B, ISS flight experiments (FLEX, ACME, BASS-II, SoFIE), and fundamental microgravity kinetics. Available offline via service worker cache.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
          {[
            { id: 'standards', label: 'NASA-STD-6001B Standards' },
            { id: 'equations', label: 'Governing Equations' },
            { id: 'regimes', label: 'Combustion Regimes' },
            { id: 'offline', label: 'PWA & Offline Architecture' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                  : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'standards' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white">Test 1: Upward Flame Propagation</h2>
                <span className="text-xs font-mono text-amber-400">NASA-STD-6001B §6.1</span>
              </div>
              <p className="text-sm text-slate-300">
                Primary flammability acceptance test for materials in crewed spacecraft habitable environments.
              </p>
              <ul className="text-xs text-slate-300 space-y-2 list-disc list-inside bg-slate-950/60 p-4 rounded-lg">
                <li><strong className="text-white">Sample Dimensions:</strong> 30.5 cm × 5.1 cm (12 in × 2 in).</li>
                <li><strong className="text-white">Burn Length Threshold:</strong> Max allowable propagation ≤ 15.2 cm (6.0 in).</li>
                <li><strong className="text-white">Dripping:</strong> No flaming droplets or particle ejection that ignites surgical cotton.</li>
                <li><strong className="text-white">Standard Atmosphere:</strong> 21% to 34% O₂ at 70 to 101.3 kPa.</li>
              </ul>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white">Test 7: Heat & Visible Smoke Release</h2>
                <span className="text-xs font-mono text-amber-400">NASA-STD-6001B §6.7</span>
              </div>
              <p className="text-sm text-slate-300">
                Cone calorimeter measurement determining peak heat release rate (HRR) and toxic obscuration potential.
              </p>
              <ul className="text-xs text-slate-300 space-y-2 list-disc list-inside bg-slate-950/60 p-4 rounded-lg">
                <li><strong className="text-white">Peak HRR Limit:</strong> ≤ 100 kW/m² under 25 or 50 kW/m² external irradiance.</li>
                <li><strong className="text-white">10-Min Total Heat Release:</strong> ≤ 15 MJ/m².</li>
                <li><strong className="text-white">Smoke Extinction:</strong> Monitored via laser photometer extinction cross-section.</li>
                <li><strong className="text-white">Toxic Offgassing:</strong> CO, CO₂, HCN, HCl gas yield thresholds.</li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'equations' && (
          <div className="space-y-6">
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 space-y-3">
              <h2 className="text-lg font-bold text-white">1. Classical d²-Law with Radiative Cooling</h2>
              <div className="bg-slate-950 p-4 rounded-lg font-mono text-sm text-cyan-300 overflow-x-auto">
                {"d²(t) = d₀² - K_eff · t,   where K_eff = K_classical · (1 - f_rad)"}
              </div>
              <p className="text-xs text-slate-400">
                In microgravity, spherical symmetry enables quasi-steady droplet burning. Radiative loss fraction f_rad increases with droplet diameter, triggering flame extinction at d_ext &gt; 0.
              </p>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 space-y-3">
              <h2 className="text-lg font-bold text-white">2. Grashof & Richardson Buoyancy Dimensionless Numbers</h2>
              <div className="bg-slate-950 p-4 rounded-lg font-mono text-sm text-cyan-300 overflow-x-auto">
                {"Gr = (g · β · (T_f - T_∞) · L³) / ν²,   Ri = Gr / Re²"}
              </div>
              <p className="text-xs text-slate-400">
                At microgravity (g ≈ 10⁻⁶ g₀), Gr → 0 and Ri ≪ 1. Forced convection and pure molecular diffusion completely dominate over natural buoyant convection.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'regimes' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-2">
              <h3 className="text-base font-bold text-white">Droplet Combustion (FLEX)</h3>
              <p className="text-xs text-slate-300">
                Single and bi-component isolated fuel droplets (n-heptane, decane, methanol). Exhibits spherical soot shells and cool flame low-temp chemistry.
              </p>
            </div>
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-2">
              <h3 className="text-base font-bold text-white">Laminar Diffusion (ACME)</h3>
              <p className="text-xs text-slate-300">
                Coflow gas burner flames (methane, ethylene). Widened flame base, extended residence time, and altered soot inception pathways.
              </p>
            </div>
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-2">
              <h3 className="text-base font-bold text-white">Solid Flame Spread (BASS / SoFIE)</h3>
              <p className="text-xs text-slate-300">
                PMMA acrylic and fabric slabs in concurrent/opposed low-speed airflow. Flame spread governed by ventilation speed rather than buoyancy.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'offline' && (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 className="text-lg font-bold text-white">Progressive Web Application (PWA) Offline Engine</h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              CORTEXX incorporates a service worker with cache-first static shell strategy and stale-while-revalidate data strategy. When deployed in flight environments or field research with intermittent network connectivity, the platform operates seamlessly offline.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800/80">
                <span className="text-xs font-semibold text-blue-400">Manifest</span>
                <p className="text-xs text-slate-400 mt-1">Standalone display mode with NASA blue theme (#0b3d91).</p>
              </div>
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800/80">
                <span className="text-xs font-semibold text-emerald-400">Cache Storage</span>
                <p className="text-xs text-slate-400 mt-1">Pre-cached handbook, comparison matrix, and offline fallback.</p>
              </div>
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800/80">
                <span className="text-xs font-semibold text-purple-400">Data Integrity</span>
                <p className="text-xs text-slate-400 mt-1">Merkle tree hashes cached locally for offline provenance verification.</p>
              </div>
            </div>
          </div>
        )}

        {/* Back Link */}
        <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
          <Link href="/" className="text-blue-400 hover:text-blue-300 font-medium">
            &larr; Back to CORTEXX Platform Dashboard
          </Link>
          <span>NASA Space Apps 2026 &bull; CORTEXX Swarm</span>
        </div>
      </div>
    </div>
  );
}
