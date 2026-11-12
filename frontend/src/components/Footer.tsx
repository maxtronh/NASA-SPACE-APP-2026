import Link from "next/link";
import { ShieldCheck, ExternalLink, Database, Cpu } from "lucide-react";

export default function Footer() {
  return (
    <footer className="mt-auto bg-space-950 border-t border-space-800 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand & Mission Statement */}
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-white tracking-wider text-base">
                FLAME <span className="text-nasa-cyan">IN FREEFALL</span>
              </span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-space-800 text-slate-300 border border-space-700">
                v1.0.0
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-md leading-relaxed">
              Advanced Scientific Intelligence platform leveraging authentic NASA microgravity combustion archives from the International Space Station (CIR, MSG) and Glenn Research Center.
            </p>
            <div className="flex items-center space-x-2 text-xs text-emerald-400 font-mono">
              <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Strict Zero-Fabrication • Null-Preserved SI Telemetry • 100% SHA-256 Verified</span>
            </div>
          </div>

          {/* NASA Data Archives */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono mb-3">
              Official NASA Sources
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a
                  href="https://ntrs.nasa.gov/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-nasa-cyan flex items-center space-x-1.5 transition-colors"
                >
                  <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
                  <span>NASA Technical Reports Server (NTRS)</span>
                </a>
              </li>
              <li>
                <a
                  href="https://psi.nasa.gov/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-nasa-cyan flex items-center space-x-1.5 transition-colors"
                >
                  <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
                  <span>Physical Sciences Informatics (PSI)</span>
                </a>
              </li>
              <li>
                <a
                  href="https://www.nasa.gov/glenn/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-nasa-cyan flex items-center space-x-1.5 transition-colors"
                >
                  <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
                  <span>Glenn Research Center (GRC)</span>
                </a>
              </li>
            </ul>
          </div>

          {/* System & Architecture */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono mb-3">
              Platform Architecture
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li className="flex items-center space-x-1.5">
                <Database className="w-3.5 h-3.5 text-slate-500" />
                <span>PostgreSQL 16 + pgvector Hybrid RAG</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <Cpu className="w-3.5 h-3.5 text-slate-500" />
                <span>Next.js 15 App Router + Tailwind CSS</span>
              </li>
              <li className="text-[11px] text-slate-500 pt-1">
                NASA Space Apps Challenge 2026 Prototype Showcase
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-space-850 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500">
          <p>© 2026 Flame in Freefall. Developed for NASA Space Apps Challenge.</p>
          <p className="mt-2 sm:mt-0 font-mono text-[11px]">
            Engineered with Precision & Scientific Integrity
          </p>
        </div>
      </div>
    </footer>
  );
}
