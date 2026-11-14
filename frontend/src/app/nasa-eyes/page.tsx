import type { Metadata } from "next";
import NasaEyesExperience from "@/components/NasaEyesExperience";

export const metadata: Metadata = {
  title: "NASA Eyes (JPL) | Flame in Freefall",
  description:
    "Explore the Solar System with NASA/JPL's interactive Eyes on the Solar System experience.",
};

export default function NasaEyesPage() {
  return <NasaEyesExperience />;
}
