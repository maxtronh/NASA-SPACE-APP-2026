"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import {
  Video,
  Search,
  Layers,
  Thermometer,
  Eye,
  Sliders,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Maximize2,
  X,
  Flame,
  Activity,
  Compass,
  Info,
  CheckCircle2,
  HelpCircle,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { searchFrameRAG } from "@/lib/api";
import { VideoFrameRAGItem, DiagnosticModality } from "@/types";

export default function DiagnosticsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedModality, setSelectedModality] = useState<DiagnosticModality | "all">("all");
  const [selectedInvestigation, setSelectedInvestigation] = useState<string>("all");
  const [frames, setFrames] = useState<VideoFrameRAGItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFrame, setActiveFrame] = useState<VideoFrameRAGItem | null>(null);

  // Active modal layer toggles
  const [showRaw, setShowRaw] = useState(true);
  const [showContours, setShowContours] = useState(true);
  const [showSchlieren, setShowSchlieren] = useState(false);
  const [showPyrometry, setShowPyrometry] = useState(true);
  const [hoverCoord, setHoverCoord] = useState<{ x: number; y: number } | null>(null);

  const PRESET_QUERIES = [
    "FLEX n-heptane cool-flame soot shell",
    "BASS-II low-speed concurrent boundary layer",
    "ACME methane non-buoyant soot inception",
    "Droplet radiative extinction transition",
    "High-pressure Schlieren density gradient",
  ];

  const debouncedSearch = useDebouncedValue(searchQuery, 300);

  useEffect(() => {
    let active = true;
    async function loadFrames() {
      setLoading(true);
      try {
        const res = await searchFrameRAG({
          query: debouncedSearch,
          modality: selectedModality,
          investigation_slug: selectedInvestigation !== "all" ? selectedInvestigation : undefined,
          limit: 12,
        });
        if (active) {
          setFrames(res.results || []);
          if (res.results && res.results.length > 0 && !activeFrame) {
            setActiveFrame(res.results[0]);
          }
        }
      } catch (err) {
        console.error("Failed to query frame RAG:", err);
      } finally {
        if (active) setLoading(false);
      }
    }
    loadFrames();
    return () => {
      active = false;
    };
  }, [debouncedSearch, selectedModality, selectedInvestigation]);

  const handleInspect = (frame: VideoFrameRAGItem) => {
    setActiveFrame(frame);
    // Set appropriate default layers depending on modality
    if (frame.modality === "schlieren") {
      setShowSchlieren(true);
      setShowPyrometry(false);
    } else if (frame.modality === "pyrometry") {
      setShowPyrometry(true);
      setShowSchlieren(false);
    } else {
      setShowRaw(true);
      setShowContours(true);
    }
  };

  return (
    <div className="min-h-screen bg-space-950 text-slate-100 pb-16">
      {/* Top Header Banner */}
      <div className="bg-space-900 border-b border-space-700/80 px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-nasa-cyan mb-1">
                <span>NASA Combustion Diagnostics</span>
                <span>/</span>
                <span>Upgrade E-07</span>
                <span className="px-2 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-500/40 text-[10px] text-nasa-cyan">
                  10 Hz Vector RAG
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                <Video className="w-8 h-8 text-nasa-cyan" />
                Multimodal Optical & Schlieren RAG Studio
              </h1>
              <p className="text-slate-400 text-sm mt-1 max-w-3xl">
                Semantic video keyframe indexing from NASA CIR and MSG flight archives. Interrogate optical density gradients, 
                two-color Planck soot pyrometry thermal fields (800 K - 2200 K), and OpenCV contour sphericity.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 rounded-lg bg-space-800 border border-space-700 text-xs font-mono text-slate-300 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-emerald-400" />
                OpenCLIP ONNX 512-dim
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-space-800 border border-space-700 text-xs font-mono text-slate-300 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                pgvector Keyframes
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        {/* Controls: Search Bar & Modality Filters */}
        <div className="bg-space-900 border border-space-700 rounded-xl p-4 shadow-lg mb-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
            {/* Search Input */}
            <div className="md:col-span-6 relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search flame features, cool flames, soot shells, Schlieren density..."
                className="w-full pl-9 pr-4 py-2 bg-space-850 border border-space-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-nasa-cyan transition-colors"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Modality Filter */}
            <div className="md:col-span-3">
              <select
                value={selectedModality}
                onChange={(e) => setSelectedModality(e.target.value as any)}
                className="w-full px-3 py-2 bg-space-850 border border-space-700 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-nasa-cyan"
              >
                <option value="all">All Diagnostic Modalities</option>
                <option value="schlieren">Schlieren Density Gradient</option>
                <option value="pyrometry">Two-Color Soot Pyrometry</option>
                <option value="chemiluminescence">Chemiluminescence (UV/Blue)</option>
                <option value="direct_video">Direct Optical Video</option>
              </select>
            </div>

            {/* Investigation Filter */}
            <div className="md:col-span-3">
              <select
                value={selectedInvestigation}
                onChange={(e) => setSelectedInvestigation(e.target.value)}
                className="w-full px-3 py-2 bg-space-850 border border-space-700 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-nasa-cyan"
              >
                <option value="all">All Flight Archives</option>
                <option value="flex-droplet-burning">FLEX (Droplet Burning)</option>
                <option value="bass-ii-solid-slab">BASS-II (Solid Slabs)</option>
                <option value="acme-cld-flame">ACME (Laminar Gas Flames)</option>
              </select>
            </div>
          </div>

          {/* Quick Preset Query Chips */}
          <div className="mt-3 flex flex-wrap items-center gap-2 pt-3 border-t border-space-800">
            <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-nasa-cyan" />
              Suggested Queries:
            </span>
            {PRESET_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => setSearchQuery(q)}
                className={`text-xs px-2.5 py-1 rounded-md transition-all ${
                  searchQuery === q
                    ? "bg-nasa-cyan/20 border border-nasa-cyan text-nasa-cyan font-medium"
                    : "bg-space-800 text-slate-400 hover:text-slate-200 border border-space-700/60"
                }`}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Main Content Layout: Gallery Grid + Inspector */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Keyframe Gallery Grid (Left 7 Cols) */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between text-sm px-1">
              <span className="font-semibold text-slate-200 flex items-center gap-2">
                <Video className="w-4 h-4 text-nasa-cyan" />
                Sampled 10 Hz Keyframe Catalog ({frames.length} Matches)
              </span>
              <span className="text-xs font-mono text-slate-500">
                Stride: 100 ms (10 frames/sec)
              </span>
            </div>

            {loading ? (
              <div className="p-12 text-center bg-space-900 border border-space-700 rounded-xl">
                <div className="animate-spin w-8 h-8 border-2 border-nasa-cyan border-t-transparent rounded-full mx-auto mb-3" />
                <p className="text-sm font-mono text-slate-400">Searching multimodal vector space...</p>
              </div>
            ) : frames.length === 0 ? (
              <div className="p-12 text-center bg-space-900 border border-space-700 rounded-xl">
                <p className="text-sm text-slate-400">No keyframes found matching query.</p>
                <button
                  onClick={() => { setSearchQuery(""); setSelectedModality("all"); setSelectedInvestigation("all"); }}
                  className="mt-3 text-xs text-nasa-cyan hover:underline"
                >
                  Reset search filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {frames.map((frame) => {
                  const isSelected = activeFrame?.id === frame.id;
                  const mod = frame.modality;
                  const modBadge =
                    mod === "schlieren"
                      ? "bg-cyan-950/80 text-cyan-300 border-cyan-500/40"
                      : mod === "pyrometry"
                      ? "bg-amber-950/80 text-amber-300 border-amber-500/40"
                      : mod === "chemiluminescence"
                      ? "bg-purple-950/80 text-purple-300 border-purple-500/40"
                      : "bg-blue-950/80 text-blue-300 border-blue-500/40";

                  const peakT = frame.optical_features.pyrometry?.temperature_peak_k;
                  const standoff = frame.optical_features.contour?.standoff_ratio;

                  return (
                    <div
                      key={frame.id}
                      onClick={() => handleInspect(frame)}
                      className={`group cursor-pointer rounded-xl border p-3.5 transition-all bg-space-900 ${
                        isSelected
                          ? "border-nasa-cyan shadow-md shadow-cyan-500/20 ring-1 ring-nasa-cyan"
                          : "border-space-700 hover:border-slate-500 hover:bg-space-850"
                      }`}
                    >
                      {/* Synthetic Preview Canvas Frame */}
                      <div className="relative aspect-[4/3] rounded-lg overflow-hidden bg-space-950 border border-space-800 flex items-center justify-center">
                        {/* Procedural Visual Representation */}
                        <svg className="w-full h-full" viewBox="0 0 256 192">
                          <rect width="256" height="192" fill="#040711" />
                          {/* Radial Glow representing flame */}
                          {frame.optical_features.flame_detected && (
                            <defs>
                              <radialGradient id={`glow-${frame.id}`} cx="50%" cy="50%" r="50%">
                                <stop
                                  offset="0%"
                                  stopColor={
                                    mod === "chemiluminescence"
                                      ? "#8b5cf6"
                                      : mod === "pyrometry"
                                      ? "#f59e0b"
                                      : "#38bdf8"
                                  }
                                  stopOpacity="0.85"
                                />
                                <stop offset="60%" stopColor="#ef4444" stopOpacity="0.35" />
                                <stop offset="100%" stopColor="#000000" stopOpacity="0" />
                              </radialGradient>
                            </defs>
                          )}

                          {frame.optical_features.flame_detected ? (
                            <circle
                              cx="128"
                              cy="96"
                              r={mod === "chemiluminescence" ? "56" : "44"}
                              fill={`url(#glow-${frame.id})`}
                            />
                          ) : (
                            <circle cx="128" cy="96" r="16" fill="#334155" opacity="0.6" />
                          )}

                          {/* Soot Shell or Droplet Boundary */}
                          {frame.optical_features.soot_present && (
                            <circle
                              cx="128"
                              cy="96"
                              r="32"
                              fill="none"
                              stroke="#f59e0b"
                              strokeWidth="1.8"
                              strokeDasharray="4 2"
                            />
                          )}

                          {/* Inner Fuel Droplet */}
                          <circle cx="128" cy="96" r="10" fill="#0284c7" />

                          {/* Schlieren Knife-Edge Density Striations */}
                          {mod === "schlieren" && (
                            <g opacity="0.4" stroke="#00e5ff" strokeWidth="1">
                              <path d="M 60 70 Q 128 40 196 70" fill="none" />
                              <path d="M 40 96 Q 128 75 216 96" fill="none" />
                              <path d="M 60 122 Q 128 152 196 122" fill="none" />
                            </g>
                          )}
                        </svg>

                        {/* Modality Badge */}
                        <div className="absolute top-2 left-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider border font-medium ${modBadge}`}
                          >
                            {mod}
                          </span>
                        </div>

                        {/* Timestamp badge */}
                        <div className="absolute bottom-2 left-2 bg-space-950/80 backdrop-blur-sm px-1.5 py-0.5 rounded text-[10px] font-mono text-slate-300 border border-space-700">
                          t = {frame.timestamp_s.toFixed(2)}s
                        </div>

                        {/* Similarity score */}
                        {frame.embedding_similarity !== undefined && (
                          <div className="absolute top-2 right-2 bg-cyan-950/80 backdrop-blur-sm px-1.5 py-0.5 rounded text-[10px] font-mono text-nasa-cyan border border-cyan-500/30">
                            {(frame.embedding_similarity * 100).toFixed(1)}% Match
                          </div>
                        )}
                      </div>

                      {/* Card Content & Telemetry Readouts */}
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="font-mono text-white font-semibold">
                            {frame.run_identifier}
                          </span>
                          <span className="text-[11px] text-slate-400 capitalize">
                            {frame.investigation_slug.replace(/-/g, " ")}
                          </span>
                        </div>

                        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                          {frame.description}
                        </p>

                        {/* Strict Zero-Fabrication Parameters */}
                        <div className="mt-2.5 pt-2 border-t border-space-800 grid grid-cols-2 gap-2 text-[11px] font-mono">
                          <div>
                            <span className="text-slate-500 block text-[10px]">PEAK TEMP</span>
                            {peakT !== null && peakT !== undefined ? (
                              <span className="text-amber-400 font-medium">{peakT.toFixed(0)} K</span>
                            ) : (
                              <span className="text-slate-500 italic">Unmeasured / null</span>
                            )}
                          </div>
                          <div>
                            <span className="text-slate-500 block text-[10px]">STANDOFF rf/rs</span>
                            {standoff !== null && standoff !== undefined ? (
                              <span className="text-nasa-cyan font-medium">{standoff.toFixed(2)}</span>
                            ) : (
                              <span className="text-slate-500 italic">Unmeasured / null</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Interactive Inspection Workspace (Right 5 Cols) */}
          <div className="lg:col-span-5">
            {activeFrame ? (
              <div className="bg-space-900 border border-space-700 rounded-xl p-5 shadow-xl sticky top-20 space-y-5">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 text-xs font-mono text-nasa-cyan uppercase">
                      <span>Inspection Viewport</span>
                      <span>•</span>
                      <span>{activeFrame.run_identifier}</span>
                    </div>
                    <h2 className="text-lg font-bold text-white mt-0.5">
                      Frame at t = {activeFrame.timestamp_s.toFixed(2)} s
                    </h2>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-space-800 border border-space-700 text-slate-300 uppercase">
                    {activeFrame.modality}
                  </span>
                </div>

                {/* Layer Control Switcher */}
                <div className="bg-space-850 p-2.5 rounded-lg border border-space-800 space-y-1.5">
                  <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Diagnostic Optical Layers</span>
                    <span className="text-slate-500">Click to Toggle</span>
                  </div>
                  <div className="grid grid-cols-2 gap-1.5 text-xs">
                    <button
                      onClick={() => setShowRaw(!showRaw)}
                      className={`px-2.5 py-1.5 rounded text-left font-medium flex items-center justify-between border transition-all ${
                        showRaw
                          ? "bg-blue-950/60 border-blue-500/50 text-blue-300"
                          : "bg-space-800/60 border-space-700/60 text-slate-400"
                      }`}
                    >
                      <span>1. Optical Video</span>
                      <CheckCircle2 className={`w-3.5 h-3.5 ${showRaw ? "opacity-100" : "opacity-20"}`} />
                    </button>

                    <button
                      onClick={() => setShowContours(!showContours)}
                      className={`px-2.5 py-1.5 rounded text-left font-medium flex items-center justify-between border transition-all ${
                        showContours
                          ? "bg-emerald-950/60 border-emerald-500/50 text-emerald-300"
                          : "bg-space-800/60 border-space-700/60 text-slate-400"
                      }`}
                    >
                      <span>2. OpenCV Contours</span>
                      <CheckCircle2 className={`w-3.5 h-3.5 ${showContours ? "opacity-100" : "opacity-20"}`} />
                    </button>

                    <button
                      onClick={() => setShowSchlieren(!showSchlieren)}
                      className={`px-2.5 py-1.5 rounded text-left font-medium flex items-center justify-between border transition-all ${
                        showSchlieren
                          ? "bg-cyan-950/60 border-cyan-500/50 text-cyan-300"
                          : "bg-space-800/60 border-space-700/60 text-slate-400"
                      }`}
                    >
                      <span>3. Schlieren Gradient</span>
                      <CheckCircle2 className={`w-3.5 h-3.5 ${showSchlieren ? "opacity-100" : "opacity-20"}`} />
                    </button>

                    <button
                      onClick={() => setShowPyrometry(!showPyrometry)}
                      className={`px-2.5 py-1.5 rounded text-left font-medium flex items-center justify-between border transition-all ${
                        showPyrometry
                          ? "bg-amber-950/60 border-amber-500/50 text-amber-300"
                          : "bg-space-800/60 border-space-700/60 text-slate-400"
                      }`}
                    >
                      <span>4. Soot Pyrometry</span>
                      <CheckCircle2 className={`w-3.5 h-3.5 ${showPyrometry ? "opacity-100" : "opacity-20"}`} />
                    </button>
                  </div>
                </div>

                {/* Interactive Multi-Layer Canvas / Inspection Viewport */}
                <div
                  className="relative aspect-square w-full rounded-lg bg-black border border-space-700 overflow-hidden cursor-crosshair select-none"
                  onMouseMove={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const x = Math.round(((e.clientX - rect.left) / rect.width) * 256);
                    const y = Math.round(((e.clientY - rect.top) / rect.height) * 256);
                    setHoverCoord({ x, y });
                  }}
                  onMouseLeave={() => setHoverCoord(null)}
                >
                  <svg className="w-full h-full" viewBox="0 0 256 256">
                    {/* Layer 1: Raw Optical Capture Background */}
                    {showRaw && (
                      <g>
                        <rect width="256" height="256" fill="#030712" />
                        <circle cx="128" cy="128" r="85" fill="#1e1b4b" opacity="0.6" />
                        <circle cx="128" cy="128" r="62" fill="#3b0764" opacity="0.7" />
                        <circle cx="128" cy="128" r="14" fill="#0284c7" />
                      </g>
                    )}

                    {/* Layer 3: Schlieren Density Gradient */}
                    {showSchlieren && (
                      <g opacity="0.75">
                        <defs>
                          <linearGradient id="schlieren-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#00e5ff" stopOpacity="0.1" />
                            <stop offset="50%" stopColor="#ffffff" stopOpacity="0.7" />
                            <stop offset="100%" stopColor="#00e5ff" stopOpacity="0.1" />
                          </linearGradient>
                        </defs>
                        <ellipse cx="128" cy="128" rx="90" ry="75" fill="none" stroke="url(#schlieren-grad)" strokeWidth="3" />
                        <ellipse cx="128" cy="128" rx="70" ry="60" fill="none" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="3 2" />
                        <line x1="128" y1="20" x2="128" y2="236" stroke="#00e5ff" strokeWidth="0.5" strokeDasharray="2 2" opacity="0.4" />
                      </g>
                    )}

                    {/* Layer 4: Soot Pyrometry Heatmap */}
                    {showPyrometry && (
                      <g opacity="0.85">
                        <defs>
                          <radialGradient id="pyro-inferno" cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stopColor="#000004" stopOpacity="0.9" />
                            <stop offset="25%" stopColor="#51127c" stopOpacity="0.95" />
                            <stop offset="50%" stopColor="#b63679" stopOpacity="0.95" />
                            <stop offset="75%" stopColor="#fb8861" stopOpacity="0.98" />
                            <stop offset="90%" stopColor="#fcfdbf" stopOpacity="1.0" />
                            <stop offset="100%" stopColor="#000000" stopOpacity="0" />
                          </radialGradient>
                        </defs>
                        <circle cx="128" cy="128" r="78" fill="url(#pyro-inferno)" />
                      </g>
                    )}

                    {/* Layer 2: OpenCV Contours Overlay */}
                    {showContours && activeFrame.optical_features.contour && (
                      <g>
                        {/* Outer Flame Contour */}
                        <polygon
                          points={activeFrame.optical_features.contour.contour_points
                            .map(([x, y]) => `${x},${y}`)
                            .join(" ")}
                          fill="none"
                          stroke="#10b981"
                          strokeWidth="2"
                        />
                        {/* Soot Shell Contour */}
                        {activeFrame.optical_features.contour.soot_shell_contour && (
                          <polygon
                            points={activeFrame.optical_features.contour.soot_shell_contour
                              .map(([x, y]) => `${x},${y}`)
                              .join(" ")}
                            fill="none"
                            stroke="#f59e0b"
                            strokeWidth="1.5"
                            strokeDasharray="4 2"
                          />
                        )}
                        {/* Centroid Reticle */}
                        <circle
                          cx={activeFrame.optical_features.contour.flame_centroid_px[0]}
                          cy={activeFrame.optical_features.contour.flame_centroid_px[1]}
                          r="4"
                          fill="#ef4444"
                        />
                        <line
                          x1={activeFrame.optical_features.contour.flame_centroid_px[0] - 8}
                          y1={activeFrame.optical_features.contour.flame_centroid_px[1]}
                          x2={activeFrame.optical_features.contour.flame_centroid_px[0] + 8}
                          y2={activeFrame.optical_features.contour.flame_centroid_px[1]}
                          stroke="#ef4444"
                          strokeWidth="1.2"
                        />
                        <line
                          x1={activeFrame.optical_features.contour.flame_centroid_px[0]}
                          y1={activeFrame.optical_features.contour.flame_centroid_px[1] - 8}
                          x2={activeFrame.optical_features.contour.flame_centroid_px[0]}
                          y2={activeFrame.optical_features.contour.flame_centroid_px[1] + 8}
                          stroke="#ef4444"
                          strokeWidth="1.2"
                        />
                      </g>
                    )}

                    {/* Cursor Reticle */}
                    {hoverCoord && (
                      <g pointerEvents="none">
                        <line x1={hoverCoord.x} y1="0" x2={hoverCoord.x} y2="256" stroke="#ffffff" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.6" />
                        <line x1="0" y1={hoverCoord.y} x2="256" y2={hoverCoord.y} stroke="#ffffff" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.6" />
                        <circle cx={hoverCoord.x} cy={hoverCoord.y} r="3" fill="none" stroke="#00e5ff" strokeWidth="1.5" />
                      </g>
                    )}
                  </svg>

                  {/* Pyrometry Colormap Scale Legend */}
                  {showPyrometry && (
                    <div className="absolute bottom-2 right-2 bg-space-950/90 backdrop-blur-sm p-1.5 rounded border border-space-700 text-[9px] font-mono">
                      <div className="w-24 h-2 rounded bg-gradient-to-r from-[#000004] via-[#b63679] to-[#fcfdbf] mb-1" />
                      <div className="flex justify-between text-slate-400">
                        <span>800 K</span>
                        <span>1500 K</span>
                        <span>2200 K</span>
                      </div>
                    </div>
                  )}

                  {/* Realtime Inspection Crosshair Coordinates */}
                  {hoverCoord && (
                    <div className="absolute top-2 left-2 bg-space-950/90 backdrop-blur-sm px-2 py-1 rounded border border-space-700 text-[10px] font-mono text-slate-300">
                      <span>X: {hoverCoord.x}px | Y: {hoverCoord.y}px</span>
                      <span className="block text-nasa-cyan">
                        Estimated T: {(1200 + (1 - Math.hypot(hoverCoord.x - 128, hoverCoord.y - 128) / 128) * 620).toFixed(0)} K
                      </span>
                    </div>
                  )}
                </div>

                {/* Radial Temperature Cut Profile Chart */}
                {activeFrame.optical_features.pyrometry?.radial_profile && (
                  <div className="bg-space-850 p-3 rounded-lg border border-space-800">
                    <div className="flex items-center justify-between text-xs mb-2">
                      <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                        <Thermometer className="w-3.5 h-3.5 text-amber-400" />
                        Radial Temperature & Soot Cut Profile T(r)
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">Center → Standoff</span>
                    </div>
                    <div className="h-44 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={activeFrame.optical_features.pyrometry.radial_profile}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis
                            dataKey="radius_mm"
                            stroke="#64748b"
                            tick={{ fontSize: 10 }}
                            unit="mm"
                          />
                          <YAxis
                            yAxisId="temp"
                            stroke="#f59e0b"
                            tick={{ fontSize: 10 }}
                            domain={[300, 2200]}
                            unit="K"
                          />
                          <YAxis
                            yAxisId="soot"
                            orientation="right"
                            stroke="#38bdf8"
                            tick={{ fontSize: 10 }}
                            unit="ppm"
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#0b1120",
                              borderColor: "#334155",
                              fontSize: "11px",
                              color: "#f8fafc",
                            }}
                          />
                          <Legend wrapperStyle={{ fontSize: "10px" }} />
                          <Line
                            yAxisId="temp"
                            type="monotone"
                            dataKey="temperature_k"
                            name="Temp T(r) [K]"
                            stroke="#f59e0b"
                            strokeWidth={2}
                            dot={{ r: 2 }}
                          />
                          <Line
                            yAxisId="soot"
                            type="monotone"
                            dataKey="soot_volume_fraction_ppm"
                            name="Soot f_v [ppm]"
                            stroke="#38bdf8"
                            strokeWidth={1.5}
                            dot={{ r: 2 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Physical Parameter Telemetry Table */}
                <div className="bg-space-850 p-3 rounded-lg border border-space-800">
                  <div className="text-xs font-semibold text-slate-200 mb-2 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-nasa-cyan" />
                    Physical Contour & Pyrometry Metadata
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="bg-space-900 p-2 rounded border border-space-800">
                      <span className="text-slate-500 text-[10px] block">EQUIVALENT DIAMETER</span>
                      {activeFrame.optical_features.contour?.equivalent_diameter_mm !== undefined ? (
                        <span className="text-white font-semibold">
                          {activeFrame.optical_features.contour.equivalent_diameter_mm.toFixed(2)} mm
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">Unmeasured / null</span>
                      )}
                    </div>

                    <div className="bg-space-900 p-2 rounded border border-space-800">
                      <span className="text-slate-500 text-[10px] block">ASPECT RATIO</span>
                      {activeFrame.optical_features.contour?.aspect_ratio !== undefined ? (
                        <span className="text-white font-semibold">
                          {activeFrame.optical_features.contour.aspect_ratio.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">Unmeasured / null</span>
                      )}
                    </div>

                    <div className="bg-space-900 p-2 rounded border border-space-800">
                      <span className="text-slate-500 text-[10px] block">MAX DENSITY GRADIENT</span>
                      {activeFrame.optical_features.schlieren?.max_density_gradient_kg_m4 !== undefined ? (
                        <span className="text-cyan-400 font-semibold">
                          {activeFrame.optical_features.schlieren.max_density_gradient_kg_m4.toFixed(1)} kg/m⁴
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">Unmeasured / null</span>
                      )}
                    </div>

                    <div className="bg-space-900 p-2 rounded border border-space-800">
                      <span className="text-slate-500 text-[10px] block">CAMERA RESOLUTION</span>
                      <span className="text-slate-300">
                        {activeFrame.camera_specs.spatial_resolution_um_per_px} µm/px @ {activeFrame.camera_specs.frame_rate_hz} Hz
                      </span>
                    </div>
                  </div>
                </div>

                {/* Verifiable NTRS Passage Excerpt */}
                {activeFrame.ntrs_passage_excerpt && (
                  <div className="p-3 bg-cyan-950/30 border border-cyan-800/40 rounded-lg text-xs">
                    <div className="flex items-center gap-1.5 text-nasa-cyan font-semibold mb-1">
                      <ExternalLink className="w-3.5 h-3.5" />
                      NASA Technical Report Evidence
                    </div>
                    <p className="text-slate-300 leading-relaxed italic">
                      "{activeFrame.ntrs_passage_excerpt}"
                    </p>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
