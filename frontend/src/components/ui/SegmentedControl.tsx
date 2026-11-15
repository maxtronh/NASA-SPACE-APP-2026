import React from "react";

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
  icon?: React.ReactNode;
}

interface SegmentedControlProps<T extends string> {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
  size?: "sm" | "md";
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className = "",
  size = "md",
}: SegmentedControlProps<T>) {
  const sizeClasses = size === "sm" ? "px-2.5 py-1 text-xs" : "px-3.5 py-1.5 text-sm";

  return (
    <div
      className={`inline-flex items-center p-1 rounded-xl bg-space-950/80 border border-space-800 gap-1 ${className}`}
      role="tablist"
    >
      {options.map((opt) => {
        const isSelected = opt.value === value;
        return (
          <button
            key={opt.value}
            role="tab"
            aria-selected={isSelected}
            onClick={() => onChange(opt.value)}
            className={`flex items-center gap-1.5 rounded-lg font-mono font-medium transition-all ${sizeClasses} ${
              isSelected
                ? "bg-nasa-cyan text-space-950 shadow-md shadow-cyan-500/20"
                : "text-slate-400 hover:text-white hover:bg-space-850"
            }`}
          >
            {opt.icon && <span className="w-3.5 h-3.5">{opt.icon}</span>}
            <span>{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
