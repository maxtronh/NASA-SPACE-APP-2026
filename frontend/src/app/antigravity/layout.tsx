import type { Metadata } from "next";
import type { ReactNode } from "react";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata(
  "Antigravity Combustion Comparison",
  "Compare combustion behavior across microgravity, lunar, and Martian gravity environments."
);

export default function AntigravityLayout({ children }: { children: ReactNode }) {
  return children;
}
