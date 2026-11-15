"use client";

import { useState } from "react";
import { ExternalLink, Orbit, RotateCw, Satellite, Sparkles } from "lucide-react";
import MilkyWayScene from "@/components/MilkyWayScene";
import SolarSystem25FacesHUD from "@/components/SolarSystem25FacesHUD";
import { handleTabKeyDown } from "@/lib/tabs";

type View = "milky-way" | "solar-system" | "faces-lab";

const VIEW_ORDER: View[] = ["faces-lab", "milky-way", "solar-system"];

const NASA_EYES_URL =
  "https://eyes.nasa.gov/apps/solar-system/#/home?interactPrompt=true&collapseTimeControls=true&surfaceMapTiling=true&hd=true&minorMoons=true&heliosphere=true&lighting=natural";

export default function MilkyWayExperience() {
  const [view, setView] = useState<View>("faces-lab");
  const [autoRotate, setAutoRotate] = useState(true);

  return (
    <section className="mx-auto w-full max-w-7xl flex-1 space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <header className="flex flex-col gap-4 border-b border-space-800 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-nasa-cyan">
            <Orbit className="h-4 w-4" />
            <span>Space Visualization Layer &bull; Milestone M9</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Milky Way, Solar System &amp; 25-Faces Lab
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">
            Explore procedural galaxy mechanics, live JPL NASA Eyes telemetry, or the unified 25-Faces
            Solar System Mission Lab with extracted Qwen 2.5 AI Copilot.
          </p>
        </div>
        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Choose space visualization">
          <button
            type="button"
            role="tab"
            id="faces-lab-tab"
            aria-selected={view === "faces-lab"}
            aria-controls="space-view-panel"
            tabIndex={view === "faces-lab" ? 0 : -1}
            data-tab-value="faces-lab"
            onClick={() => setView("faces-lab")}
            onKeyDown={(event) => handleTabKeyDown(event, VIEW_ORDER, view, setView)}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-nasa-cyan ${
              view === "faces-lab"
                ? "border-nasa-cyan bg-space-800 text-white font-semibold shadow-[0_0_12px_rgba(104,229,255,0.2)]"
                : "border-space-700 bg-space-900 text-slate-300 hover:border-space-500"
            }`}
          >
            <Sparkles className="h-4 w-4 text-nasa-cyan" />
            25-Faces Mission Lab &amp; Qwen AI
          </button>
          <button
            type="button"
            role="tab"
            id="milky-way-tab"
            aria-selected={view === "milky-way"}
            aria-controls="space-view-panel"
            tabIndex={view === "milky-way" ? 0 : -1}
            data-tab-value="milky-way"
            onClick={() => setView("milky-way")}
            onKeyDown={(event) => handleTabKeyDown(event, VIEW_ORDER, view, setView)}
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
            tabIndex={view === "solar-system" ? 0 : -1}
            data-tab-value="solar-system"
            onClick={() => setView("solar-system")}
            onKeyDown={(event) => handleTabKeyDown(event, VIEW_ORDER, view, setView)}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-nasa-cyan ${
              view === "solar-system"
                ? "border-nasa-cyan bg-space-800 text-white"
                : "border-space-700 bg-space-900 text-slate-300 hover:border-space-500"
            }`}
          >
            <Satellite className="h-4 w-4" />
            NASA Eyes (JPL)
          </button>
        </div>
      </header>

      <div
        id="space-view-panel"
        role="tabpanel"
        aria-labelledby={
          view === "faces-lab"
            ? "faces-lab-tab"
            : view === "milky-way"
            ? "milky-way-tab"
            : "solar-system-tab"
        }
      >
        {view === "faces-lab" ? (
          <SolarSystem25FacesHUD />
        ) : view === "milky-way" ? (
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
