import Link from "next/link";
import { ArrowLeft, Compass, Flame } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex-1 max-w-3xl w-full mx-auto px-4 py-20 flex flex-col items-center justify-center text-center space-y-6">
      <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
        <Flame className="w-8 h-8" />
      </div>

      <div className="space-y-2">
        <span className="text-xs font-mono uppercase tracking-widest text-nasa-cyan">
          404 — Microgravity Archive Signal Lost
        </span>
        <h1 className="text-3xl font-extrabold text-white">
          Investigation Record Not Found
        </h1>
        <p className="text-slate-400 text-sm max-w-md">
          The requested flight investigation, telemetry run, or scientific resource could not be located in the indexed NASA archives.
        </p>
      </div>

      <div className="flex items-center space-x-3 pt-2">
        <Link
          href="/"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-space-800 hover:bg-space-700 text-white text-xs font-semibold border border-space-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </Link>
        <Link
          href="/investigations"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-nasa-cyan hover:bg-cyan-400 text-space-950 text-xs font-semibold transition-colors"
        >
          <Compass className="w-4 h-4" />
          <span>Browse Catalog</span>
        </Link>
      </div>
    </div>
  );
}
