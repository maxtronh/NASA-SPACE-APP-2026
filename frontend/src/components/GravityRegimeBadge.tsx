"use client";

import React from "react";
import { Sparkles, Globe, Rocket, Compass, Zap } from "lucide-react";

interface GravityRegimeBadgeProps {
  gravityLevel: string;
  className?: string;
  showIcon?: boolean;
}

export function GravityRegimeBadge({
  gravityLevel,
  className = "",
  showIcon = true,
}: GravityRegimeBadgeProps) {
  const gLower = (gravityLevel || "").toLowerCase();

  let badgeColor = "bg-cyan-950/80 text-cyan-300 border-cyan-500/50";
  let icon = <Sparkles className="w-3 h-3 text-cyan-400" />;
  let label = gravityLevel;

  if (gLower.includes("lunar") || gLower.includes("0.16")) {
    badgeColor = "bg-amber-950/80 text-amber-300 border-amber-500/50";
    icon = <Rocket className="w-3 h-3 text-amber-400" />;
    label = "Lunar Gravity (0.16g)";
  } else if (gLower.includes("mars") || gLower.includes("0.38")) {
    badgeColor = "bg-rose-950/80 text-rose-300 border-rose-500/50";
    icon = <Compass className="w-3 h-3 text-rose-400" />;
    label = "Mars Gravity (0.38g)";
  } else if (gLower.includes("hyper") || gLower.includes("2g") || gLower.includes("5g")) {
    badgeColor = "bg-purple-950/80 text-purple-300 border-purple-500/50";
    icon = <Zap className="w-3 h-3 text-purple-400" />;
    label = gLower.includes("5") ? "Hypergravity (5.0g)" : "Hypergravity (2.0g)";
  } else if (gLower.includes("normal") || gLower.includes("1.0") || gLower.includes("ground")) {
    badgeColor = "bg-blue-950/80 text-blue-300 border-blue-500/50";
    icon = <Globe className="w-3 h-3 text-blue-400" />;
    label = "Normal Gravity (1.0g)";
  } else {
    // Microgravity default
    label = "Microgravity (~10⁻⁶ g)";
  }

  return (
    <span
      className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md border text-xs font-mono font-medium shadow-sm ${badgeColor} ${className}`}
    >
      {showIcon && icon}
      <span>{label}</span>
    </span>
  );
}

export default GravityRegimeBadge;
