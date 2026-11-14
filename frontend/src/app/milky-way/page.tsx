import type { Metadata } from "next";
import MilkyWayExperience from "@/components/MilkyWayExperience";

export const metadata: Metadata = {
  title: "Milky Way & Solar System Explorer | Flame in Freefall",
  description:
    "Explore an illustrative procedural Milky Way visualization and NASA's Eyes on the Solar System.",
};

export default function MilkyWayPage() {
  return <MilkyWayExperience />;
}
