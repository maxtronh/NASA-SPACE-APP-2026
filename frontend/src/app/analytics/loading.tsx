export default function AnalyticsLoading() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6"
    >
      <span className="sr-only">Loading corpus analytics…</span>
      <div className="h-10 w-64 rounded-lg bg-space-800 border border-space-700 animate-pulse" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-28 rounded-xl bg-space-900 border border-space-700 animate-pulse" />
        ))}
      </div>
      <div className="h-96 rounded-2xl bg-space-900 border border-space-700 animate-pulse" />
    </div>
  );
}
