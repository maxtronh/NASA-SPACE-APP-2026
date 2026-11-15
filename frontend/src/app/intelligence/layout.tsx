import type { Metadata } from "next";
import type { ReactNode } from "react";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata(
  "Scientific Intelligence Assistant",
  "Ask evidence-grounded questions about NASA microgravity combustion archives with verifiable citations and explicit abstention."
);

export default function IntelligenceLayout({ children }: { children: ReactNode }) {
  return children;
}
