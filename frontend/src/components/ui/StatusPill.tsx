import React from "react";

export type StatusTone = "info" | "success" | "warning" | "danger" | "neutral";

interface StatusPillProps {
  label: string;
  tone?: StatusTone;
  pulse?: boolean;
  className?: string;
  icon?: React.ReactNode;
}

export function StatusPill({
  label,
  tone = "neutral",
  pulse = false,
  className = "",
  icon,
}: StatusPillProps) {
  const toneStyles: Record<StatusTone, { badge: string; dot: string }> = {
    info: {
      badge: "bg-cyan-500/10 border-cyan-500/30 text-cyan-400",
      dot: "bg-cyan-400",
    },
    success: {
      badge: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
      dot: "bg-emerald-400",
    },
    warning: {
      badge: "bg-amber-500/10 border-amber-500/30 text-amber-400",
      dot: "bg-amber-400",
    },
    danger: {
      badge: "bg-rose-500/10 border-rose-500/30 text-rose-400",
      dot: "bg-rose-400",
    },
    neutral: {
      badge: "bg-space-800 border-space-700 text-slate-300",
      dot: "bg-slate-400",
    },
  };

  const style = toneStyles[tone];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-xs font-mono font-medium ${style.badge} ${className}`}
    >
      {pulse && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${style.dot} animate-pulse`}
        />
      )}
      {icon && <span className="w-3.5 h-3.5">{icon}</span>}
      <span>{label}</span>
    </span>
  );
}
