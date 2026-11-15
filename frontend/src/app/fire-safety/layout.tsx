import type { Metadata } from "next";
import type { ReactNode } from "react";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata(
  "Spacecraft Fire Safety",
  "Evaluate spacecraft material flammability and fire-safety margins across cabin atmospheres and gravity levels."
);

export default function FireSafetyLayout({ children }: { children: ReactNode }) {
  return children;
}
