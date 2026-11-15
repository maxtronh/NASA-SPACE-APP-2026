import type { Metadata } from "next";
import type { ReactNode } from "react";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata(
  "Flight Investigation Catalog",
  "Browse and filter NASA microgravity combustion investigations by regime, facility, gravity level, and data completeness."
);

export default function InvestigationsLayout({ children }: { children: ReactNode }) {
  return children;
}
