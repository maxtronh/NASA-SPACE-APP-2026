import type { Metadata } from "next";
import type { ReactNode } from "react";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata(
  "Microgravity Combustion Handbook",
  "Reference handbook covering NASA-STD-6001B flammability requirements, governing equations, and microgravity combustion regimes."
);

export default function HandbookLayout({ children }: { children: ReactNode }) {
  return children;
}
