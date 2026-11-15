import type { Metadata } from "next";
import { SITE_URL } from "@/lib/site";
import MissionLab from "@/components/MissionLab";

export const metadata: Metadata = {
  title: "25-Faces Mission Lab & Qwen AI | Flame in Freefall",
  description:
    "Structured Qwen 2.5 Flight Science Copilot answers — explanation, formulas, evidences, mathematical proofs, the producing API, and what happens operationally — across the 25 scientific faces of solar system simulation.",
  openGraph: {
    url: `${SITE_URL}/mission-lab`,
    title: "25-Faces Mission Lab & Qwen AI | Flame in Freefall",
    description: "Structured, evidence-grounded Qwen flight-science answers and the 25-Faces telemetry matrix.",
    type: "website",
  },
};

export default function MissionLabPage() {
  return <MissionLab />;
}
