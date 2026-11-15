import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "subtle" | "glow" | "danger";
  children: React.ReactNode;
  className?: string;
}

export function Card({
  variant = "default",
  children,
  className = "",
  ...props
}: CardProps) {
  const variantStyles = {
    default: "bg-space-900 border-space-800 shadow-xl",
    subtle: "bg-space-850/80 border-space-800/80",
    glow: "bg-space-900/90 border-nasa-cyan/40 shadow-xl shadow-cyan-500/5",
    danger: "bg-space-900/90 border-rose-500/40 shadow-xl shadow-rose-500/5",
  };

  return (
    <div
      className={`rounded-xl border p-4 sm:p-6 transition-all ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
