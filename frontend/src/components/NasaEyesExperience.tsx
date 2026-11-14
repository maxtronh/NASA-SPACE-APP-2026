"use client";

import { ExternalLink, Orbit } from "lucide-react";

const NASA_EYES_URL =
  "https://eyes.nasa.gov/apps/solar-system/#/home?interactPrompt=true&collapseTimeControls=true&surfaceMapTiling=true&hd=true&minorMoons=true&heliosphere=true&lighting=natural";

export default function NasaEyesExperience() {
  return (
    <section className="mx-auto w-full max-w-7xl flex-1 space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <header className="flex flex-col gap-5 border-b border-space-800 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-nasa-cyan">
            <Orbit className="h-4 w-4" />
            <span>NASA / Jet Propulsion Laboratory</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Eyes on the Solar System
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">
            Explore NASA/JPL&apos;s interactive 3D view of planets, moons, spacecraft, and missions.
          </p>
        </div>
        <a
          href={NASA_EYES_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border border-nasa-cyan/50 bg-space-900 px-4 py-2.5 text-sm font-medium text-nasa-cyan transition-colors hover:bg-space-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-nasa-cyan"
        >
          Open NASA Eyes in a new tab
          <ExternalLink className="h-4 w-4" />
        </a>
      </header>

      <div className="overflow-hidden rounded-xl border border-space-700 bg-black shadow-[0_24px_70px_rgba(0,0,0,0.35)]">
        <iframe
          title="NASA Eyes on the Solar System — NASA/JPL"
          src={NASA_EYES_URL}
          loading="eager"
          allow="fullscreen"
          referrerPolicy="strict-origin-when-cross-origin"
          className="h-[75vh] min-h-[480px] w-full"
        />
      </div>

      <p className="text-xs leading-relaxed text-slate-500">
        NASA Eyes is hosted by NASA/JPL and requires an internet connection. If the embedded
        experience is unavailable, use the direct link above.
      </p>
    </section>
  );
}
