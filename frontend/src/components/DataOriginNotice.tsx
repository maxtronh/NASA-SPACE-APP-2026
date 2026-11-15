import { Info } from "lucide-react";

interface DataOriginNoticeProps {
  /** True when the API client served its bundled sample archive instead of the live API. */
  demo: boolean;
  className?: string;
}

/**
 * Discloses that a page is rendering bundled sample records because the
 * provenance API is unreachable. Without this, fallback data is
 * indistinguishable from the live NASA corpus.
 */
export default function DataOriginNotice({ demo, className = "" }: DataOriginNoticeProps) {
  if (!demo) return null;

  return (
    <div
      role="note"
      className={`flex items-start gap-2 rounded-lg border border-amber-500/40 bg-amber-950/30 px-3 py-2 text-xs text-amber-200 ${className}`}
    >
      <Info aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0" />
      <span>
        <strong>Bundled demo dataset.</strong> The provenance API is unreachable, so
        counts and records on this page come from the app&apos;s bundled sample archive,
        not the live NASA corpus.
      </span>
    </div>
  );
}
