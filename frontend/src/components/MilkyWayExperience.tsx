"use client";

import { useState } from "react";
import { ExternalLink, Orbit, RotateCw, Satellite } from "lucide-react";
import MilkyWayScene from "@/components/MilkyWayScene";

type View = "milky-way" | "solar-system";

const NASA_EYES_URL =
  "https://eyes.nasa.gov/apps/solar-system/#/home?interactPrompt=true&collapseTimeControls=true&surfaceMapTiling=true&hd=true&minorMoons=true&heliosphere=true&lighting=natural";

export default function MilkyWayExperience() {
  const [view, setView] = useState<View>("milky-way");
  const [autoRotate, setAutoRotate] = useState(true);

  return (
    <section className="mx-auto w-full max-w-7xl flex-1 space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <header className="flex flex-col gap-4 border-b border-space-800 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-nasa-cyan">
            <Orbit className="h-4 w-4" />
            <span>Space Visualization Layer</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Milky Way &amp; Solar System
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">
            Explore an illustrative spiral-galaxy view or open NASA&apos;s interactive
            Solar System experience.
          </p>
        </div>
        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Choose space visualization">
          <button
            type="button"
            role="tab"
            id="milky-way-tab"
            aria-selected={view === "milky-way"}
            aria-controls="space-view-panel"
            onClick={() => setView("milky-way")}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-nasa-cyan ${
              view === "milky-way"
                ? "border-nasa-cyan bg-space-800 text-white"
                : "border-space-700 bg-space-900 text-slate-300 hover:border-space-500"
            }`}
          >
            <Orbit className="h-4 w-4" />
            Milky Way
          </button>
          <button
            type="button"
            role="tab"
            id="solar-system-tab"
            aria-selected={view === "solar-system"}
            aria-controls="space-view-panel"
            onClick={() => setView("solar-system")}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-nasa-cyan ${
              view === "solar-system"
                ? "border-nasa-cyan bg-space-800 text-white"
                : "border-space-700 bg-space-900 text-slate-300 hover:border-space-500"
            }`}
          >
            <Satellite className="h-4 w-4" />
            Solar System
          </button>
        </div>
      </header>

      <div
        id="space-view-panel"
        role="tabpanel"
        aria-labelledby={view === "milky-way" ? "milky-way-tab" : "solar-system-tab"}
      >
        {view === "milky-way" ? (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-amber-200">
                Illustrative procedural visualization — not live JPL observations or telemetry.
              </p>
              <button
                type="button"
                aria-pressed={autoRotate}
                onClick={() => setAutoRotate((current) => !current)}
                className="inline-flex items-center gap-2 rounded-lg border border-space-700 bg-space-900 px-3 py-2 text-xs text-slate-200 hover:border-nasa-cyan focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-nasa-cyan"
              >
                <RotateCw className="h-3.5 w-3.5" />
                Auto-rotate {autoRotate ? "on" : "off"}
              </button>
            </div>
            <MilkyWayScene autoRotate={autoRotate} />
            <p className="text-xs text-slate-500">
              Drag to rotate, scroll to zoom. Star positions and the Sun marker are generated
              solely to illustrate a spiral-galaxy shape.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-slate-400">
                NASA Eyes is an external interactive experience and requires an internet connection.
              </p>
              <a
                href={NASA_EYES_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-xs text-nasa-cyan hover:underline"
              >
                Open NASA Eyes in a new tab
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
            <iframe
              title="NASA Eyes on the Solar System interactive simulation"
              src={NASA_EYES_URL}
              loading="lazy"
              allow="fullscreen"
              referrerPolicy="strict-origin-when-cross-origin"
              className="h-[65vh] min-h-[420px] w-full rounded-xl border border-space-700 bg-black"
            />
          </div>
        )}
      </div>
    </section>
  );
}
