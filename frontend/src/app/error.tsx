"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, Home, RefreshCw } from "lucide-react";

export default function GlobalErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Surface the failure in the browser console for reporting; the digest is
    // the only identifier available in production builds.
    console.error(error);
  }, [error]);

  return (
    <div
      role="alert"
      className="flex-1 flex flex-col items-center justify-center gap-4 py-24 px-4 text-center"
    >
      <div
        aria-hidden="true"
        className="p-3 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400"
      >
        <AlertTriangle className="h-8 w-8" />
      </div>
      <p className="font-mono text-sm tracking-widest text-amber-300 uppercase">
        TELEMETRY SIGNAL LOST
      </p>
      <p className="text-slate-400 text-sm max-w-md">
        The scientific data layer encountered an unhandled exception
        {error.digest ? ` (digest: ${error.digest})` : ""}. Retrying re-renders
        this screen; if the failure persists, return to the dashboard and pick a
        different dataset.
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          onClick={reset}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-nasa-cyan text-space-950 font-semibold text-sm hover:bg-cyan-300 transition-colors shadow-lg shadow-cyan-500/10"
        >
          <RefreshCw aria-hidden="true" className="h-4 w-4" />
          Retry Operation
        </button>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-space-800 text-white font-semibold text-sm border border-space-600 hover:bg-space-700 transition-colors"
        >
          <Home aria-hidden="true" className="h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
