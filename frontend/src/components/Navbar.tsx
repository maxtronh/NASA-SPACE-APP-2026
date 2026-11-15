"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Flame,
  Compass,
  GitCompare,
  Sparkles,
  BarChart3,
  Orbit,
  Activity,
  Menu,
  X,
  ShieldCheck,
  Video,
  Cpu,
  ShieldAlert,
  Radio,
} from "lucide-react";
import { fetchHealth } from "@/lib/api";
import { HealthResponse } from "@/types";

const NAV_LINKS = [
  { href: "/", label: "Dashboard", icon: Flame },
  { href: "/investigations", label: "Explorer", icon: Compass },
  { href: "/mission-control", label: "Mission Control", icon: Radio },
  { href: "/diagnostics", label: "Diagnostics", icon: Video },
  { href: "/optimizer", label: "OED Optimizer", icon: Cpu },
  { href: "/fire-safety", label: "Fire Safety", icon: ShieldAlert },
  { href: "/antigravity", label: "Antigravity", icon: Orbit },
  { href: "/milky-way", label: "Galaxy", icon: Orbit },
  { href: "/compare", label: "Compare", icon: GitCompare },
  { href: "/intelligence", label: "SI Chat", icon: Sparkles },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/handbook", label: "Handbook", icon: ShieldCheck },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function checkHealth() {
      try {
        const res = await fetchHealth();
        if (mounted) {
          setHealth(res);
          setLoadingHealth(false);
        }
      } catch (e) {
        if (mounted) setLoadingHealth(false);
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const isHealthy = health?.status === "healthy";

  return (
    <nav className="sticky top-0 z-50 bg-space-950/90 backdrop-blur-md border-b border-space-700/60 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-md shadow-orange-500/20 group-hover:scale-105 transition-transform">
              <Flame className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold tracking-wider text-white text-base sm:text-lg">
                  FLAME <span className="text-nasa-cyan">IN FREEFALL</span>
                </span>
                <span className="text-[10px] uppercase tracking-widest px-1.5 py-0.5 rounded bg-space-800 border border-space-700 text-slate-400 font-mono">
                  NASA SI
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Microgravity Combustion Intelligence
              </p>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden lg:flex items-center space-x-1">
            {NAV_LINKS.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-1.5 px-2 py-1.5 rounded-lg text-xs 2xl:text-sm font-medium transition-all ${
                    isActive
                      ? "bg-space-800 text-nasa-cyan border border-nasa-cyan/40 shadow-sm shadow-cyan-500/10"
                      : "text-slate-300 hover:text-white hover:bg-space-800/60"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 2xl:w-4 2xl:h-4 ${isActive ? "text-nasa-cyan" : "text-slate-400"}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* Right side: Live Health Badge */}
          <div className="hidden sm:flex items-center space-x-3">
            <div
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono border transition-all ${
                isHealthy
                  ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-400"
                  : "bg-amber-950/40 border-amber-500/40 text-amber-300"
              }`}
              title={
                health
                  ? `Backend: ${health.status} (${health.database}) | v${health.version}`
                  : "Checking Backend Health..."
              }
            >
              <span
                className={`w-2 h-2 rounded-full animate-pulse ${
                  isHealthy ? "bg-emerald-400" : "bg-amber-400"
                }`}
              />
              <span className="font-semibold tracking-wide">
                {loadingHealth
                  ? "SYNCING..."
                  : isHealthy
                  ? "BACKEND LIVE"
                  : "CACHED MODE"}
              </span>
              <ShieldCheck className="w-3.5 h-3.5 opacity-80" />
            </div>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex lg:hidden items-center space-x-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-space-800 focus:outline-none"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-space-900 border-b border-space-700 px-4 pt-2 pb-4 space-y-2">
          {NAV_LINKS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium ${
                  isActive
                    ? "bg-space-800 text-nasa-cyan border border-nasa-cyan/40"
                    : "text-slate-300 hover:text-white hover:bg-space-800/60"
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? "text-nasa-cyan" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
          <div className="pt-2 border-t border-space-800 flex items-center justify-between text-xs text-slate-400 px-1">
            <span>Status:</span>
            <span
              className={`font-mono font-medium ${
                isHealthy ? "text-emerald-400" : "text-amber-300"
              }`}
            >
              {isHealthy ? "BACKEND LIVE" : "CACHED MODE"}
            </span>
          </div>
        </div>
      )}
    </nav>
  );
}
