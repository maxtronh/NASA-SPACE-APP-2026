"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  Flame,
  Compass,
  GitCompare,
  Sparkles,
  BarChart3,
  Orbit,
  Menu,
  X,
  ShieldCheck,
  Video,
  Cpu,
  ShieldAlert,
  Radio,
  ChevronDown,
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

// Twelve links cannot fit on one row between 1024px and 1536px. The six most
// visited destinations stay inline and the remainder move into a disclosure
// menu, so nothing is clipped or pushed off-screen at intermediate widths.
const PRIMARY_HREFS = new Set([
  "/",
  "/investigations",
  "/mission-control",
  "/fire-safety",
  "/analytics",
  "/handbook",
]);
const PRIMARY_LINKS = NAV_LINKS.filter((item) => PRIMARY_HREFS.has(item.href));
const SECONDARY_LINKS = NAV_LINKS.filter((item) => !PRIMARY_HREFS.has(item.href));

function isLinkActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

export default function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const moreRef = useRef<HTMLDivElement>(null);
  const moreButtonRef = useRef<HTMLButtonElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    let mounted = true;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let inFlight = false;
    let healthy = false;

    async function checkHealth() {
      // Skip while the tab is hidden; visibilitychange triggers a fresh check.
      if (inFlight || document.hidden) return;
      inFlight = true;
      try {
        const res = await fetchHealth();
        if (!mounted) return;
        healthy = res.status === "healthy";
        setHealth(res);
      } catch {
        if (!mounted) return;
        healthy = false;
        setHealth(null);
      } finally {
        inFlight = false;
        if (mounted) {
          setLoadingHealth(false);
          // Poll aggressively only when live; back off when the API is down.
          timer = setTimeout(checkHealth, healthy ? 30000 : 120000);
        }
      }
    }

    function handleVisibilityChange() {
      if (document.hidden) return;
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      checkHealth();
    }

    checkHealth();
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      mounted = false;
      if (timer) clearTimeout(timer);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  // Any navigation closes both menus.
  useEffect(() => {
    setMobileMenuOpen(false);
    setMoreOpen(false);
  }, [pathname]);

  // Escape closes the open menu and returns focus to the button that opened it.
  useEffect(() => {
    if (!moreOpen && !mobileMenuOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (moreOpen) {
        setMoreOpen(false);
        moreButtonRef.current?.focus();
      }
      if (mobileMenuOpen) {
        setMobileMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [moreOpen, mobileMenuOpen]);

  // Clicking anywhere outside the disclosure dismisses it.
  useEffect(() => {
    if (!moreOpen) return;
    const handlePointerDown = (event: PointerEvent) => {
      if (!moreRef.current?.contains(event.target as Node)) setMoreOpen(false);
    };
    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [moreOpen]);

  const isHealthy = health?.status === "healthy";
  const healthLabel = loadingHealth
    ? "SYNCING..."
    : isHealthy
    ? "BACKEND LIVE"
    : health
    ? "BACKEND DEGRADED"
    : "BACKEND OFFLINE";
  const healthTitle = health
    ? `Backend: ${health.status} (${health.database}) | v${health.version}`
    : loadingHealth
    ? "Checking backend health..."
    : "Backend unreachable — live data and provenance are unavailable";
  const isSecondaryActive = SECONDARY_LINKS.some((item) =>
    isLinkActive(pathname, item.href)
  );

  return (
    <nav
      aria-label="Main"
      className="sticky top-0 z-50 bg-space-950/90 backdrop-blur-md border-b border-space-700/60 shadow-lg"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-3">
          {/* Logo & Brand */}
          <Link href="/" className="flex items-center space-x-3 group shrink-0">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-md shadow-orange-500/20 group-hover:scale-105 transition-transform">
              <Flame className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold tracking-wider text-white text-base sm:text-lg">
                  FLAME <span className="text-nasa-cyan">IN FREEFALL</span>
                </span>
                <span className="hidden xl:inline text-[10px] uppercase tracking-widest px-1.5 py-0.5 rounded bg-space-800 border border-space-700 text-slate-400 font-mono">
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
            {PRIMARY_LINKS.map((item) => {
              const Icon = item.icon;
              const active = isLinkActive(pathname, item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center space-x-1.5 px-2 py-1.5 rounded-lg text-xs 2xl:text-sm font-medium transition-colors ${
                    active
                      ? "bg-space-800 text-nasa-cyan border border-nasa-cyan/40 shadow-sm shadow-cyan-500/10"
                      : "text-slate-300 hover:text-white hover:bg-space-800/60"
                  }`}
                >
                  <Icon
                    className={`w-3.5 h-3.5 2xl:w-4 2xl:h-4 ${
                      active ? "text-nasa-cyan" : "text-slate-400"
                    }`}
                  />
                  <span>{item.label}</span>
                </Link>
              );
            })}

            {/* Secondary destinations, collapsed so the row never overflows */}
            <div ref={moreRef} className="relative">
              <button
                ref={moreButtonRef}
                type="button"
                onClick={() => setMoreOpen((open) => !open)}
                aria-expanded={moreOpen}
                aria-controls="more-navigation"
                aria-haspopup="true"
                className={`flex items-center space-x-1.5 px-2 py-1.5 rounded-lg text-xs 2xl:text-sm font-medium transition-colors ${
                  moreOpen || isSecondaryActive
                    ? "bg-space-800 text-nasa-cyan border border-nasa-cyan/40"
                    : "text-slate-300 hover:text-white hover:bg-space-800/60 border border-transparent"
                }`}
              >
                <span>More</span>
                <ChevronDown
                  aria-hidden="true"
                  className={`w-3 h-3 transition-transform ${moreOpen ? "rotate-180" : ""}`}
                />
              </button>

              {moreOpen && (
                <div
                  id="more-navigation"
                  className="absolute right-0 mt-2 w-56 rounded-xl border border-space-700 bg-space-900/95 backdrop-blur-md shadow-xl p-1.5 space-y-0.5"
                >
                  {SECONDARY_LINKS.map((item) => {
                    const Icon = item.icon;
                    const active = isLinkActive(pathname, item.href);

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setMoreOpen(false)}
                        aria-current={active ? "page" : undefined}
                        className={`flex items-center space-x-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                          active
                            ? "bg-space-800 text-nasa-cyan"
                            : "text-slate-300 hover:text-white hover:bg-space-800/60"
                        }`}
                      >
                        <Icon
                          className={`w-4 h-4 ${active ? "text-nasa-cyan" : "text-slate-400"}`}
                        />
                        <span>{item.label}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Right side: Live Health Badge */}
          <div className="hidden xl:flex items-center space-x-3 shrink-0">
            <div
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono border transition-all ${
                isHealthy
                  ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-400"
                  : "bg-amber-950/40 border-amber-500/40 text-amber-300"
              }`}
              title={healthTitle}
            >
              <span
                aria-hidden="true"
                className={`w-2 h-2 rounded-full animate-pulse ${
                  isHealthy ? "bg-emerald-400" : "bg-amber-400"
                }`}
              />
              <span className="font-semibold tracking-wide">{healthLabel}</span>
              <ShieldCheck aria-hidden="true" className="w-3.5 h-3.5 opacity-80" />
            </div>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex lg:hidden items-center space-x-2">
            <button
              ref={menuButtonRef}
              type="button"
              onClick={() => setMobileMenuOpen((open) => !open)}
              className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-space-800"
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-navigation"
              aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            >
              {mobileMenuOpen ? (
                <X aria-hidden="true" className="w-6 h-6" />
              ) : (
                <Menu aria-hidden="true" className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div
          id="mobile-navigation"
          className="lg:hidden bg-space-900 border-b border-space-700 px-4 pt-2 pb-4 space-y-2 max-h-[calc(100dvh-4rem)] overflow-y-auto custom-scrollbar"
        >
          {NAV_LINKS.map((item) => {
            const Icon = item.icon;
            const active = isLinkActive(pathname, item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                aria-current={active ? "page" : undefined}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium ${
                  active
                    ? "bg-space-800 text-nasa-cyan border border-nasa-cyan/40"
                    : "text-slate-300 hover:text-white hover:bg-space-800/60"
                }`}
              >
                <Icon
                  className={`w-5 h-5 ${active ? "text-nasa-cyan" : "text-slate-400"}`}
                />
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
              {healthLabel}
            </span>
          </div>
        </div>
      )}
    </nav>
  );
}
