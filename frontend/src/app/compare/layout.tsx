import type { Metadata } from "next";
import type { ReactNode } from "react";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata(
  "Gravity Comparison Workspace",
  "Compare burning rates, flame spread, and gravity regimes across NASA microgravity investigations."
);

export default function CompareLayout({ children }: { children: ReactNode }) {
  return children;
}
