export default function InvestigationDetailLoading() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8"
    >
      <span className="sr-only">Loading investigation profile…</span>

      {/* Breadcrumb */}
      <div className="h-4 w-48 rounded bg-space-800 animate-pulse" />

      {/* Header */}
      <div className="space-y-3 pb-6 border-b border-space-800">
        <div className="h-6 w-40 rounded-full bg-space-900 border border-space-700 animate-pulse" />
        <div className="h-10 w-3/4 rounded-lg bg-space-800 animate-pulse" />
        <div className="h-4 w-1/2 rounded bg-space-900 animate-pulse" />
      </div>

      {/* Metadata grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-24 rounded-xl bg-space-900 border border-space-700 animate-pulse"
          />
        ))}
      </div>

      {/* Provenance + chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="h-64 rounded-xl bg-space-900 border border-space-700 animate-pulse" />
        <div className="lg:col-span-2 h-64 rounded-xl bg-space-900 border border-space-700 animate-pulse" />
      </div>

      {/* Run table */}
      <div className="h-96 rounded-2xl bg-space-900 border border-space-700 animate-pulse" />
    </div>
  );
}
