import type { Metadata } from "next";
import type { ReactNode } from "react";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata(
  "Multimodal Diagnostics",
  "Search combustion diagnostics for flame features, cool flames, soot shells, and Schlieren density."
);

export default function DiagnosticsLayout({ children }: { children: ReactNode }) {
  return children;
}
