"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";

export default function GlobalErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 py-24 px-4 text-center">
      <div className="p-3 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400">
        <AlertTriangle className="h-8 w-8" />
      </div>
      <p className="font-mono text-sm tracking-widest text-amber-300 uppercase">TELEMETRY SIGNAL LOST</p>
      <p className="text-slate-400 text-sm max-w-md">
        The scientific data layer encountered an unhandled exception
        {error.digest ? ` (digest: ${error.digest})` : ""}.
      </p>
      <button
        onClick={reset}
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-nasa-cyan text-space-950 font-semibold text-sm hover:bg-cyan-300 transition-colors shadow-lg shadow-cyan-500/10"
      >
        <RefreshCw className="h-4 w-4" />
        Retry Operation
      </button>
    </div>
  );
}
