import type { Metadata } from "next";
import type { ReactNode } from "react";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata(
  "Mission Control Telemetry",
  "Interactive console for ISS combustion telemetry, wavelet jitter filtering, cool-flame rekindling risk, and suppression interlocks."
);

export default function MissionControlLayout({ children }: { children: ReactNode }) {
  return children;
}
