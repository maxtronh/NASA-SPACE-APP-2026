import type { Metadata } from "next";
import type { ReactNode } from "react";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata(
  "Experiment Optimizer",
  "Design-of-experiments optimizer that proposes the next most informative microgravity combustion experiment."
);

export default function OptimizerLayout({ children }: { children: ReactNode }) {
  return children;
}
