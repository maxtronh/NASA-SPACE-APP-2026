"use client";

import React from "react";
import { ScientificArtifact } from "@/types/artifacts";
import ScientificChartArtifact from "./ScientificChartArtifact";
import Flame3DArtifact from "./Flame3DArtifact";
import TimeseriesArtifact from "./TimeseriesArtifact";
import TableArtifact from "./TableArtifact";
import CitationArtifact from "./CitationArtifact";
import EquationArtifact from "./EquationArtifact";

interface Props {
  artifact: ScientificArtifact;
  onExpand?: (art: ScientificArtifact) => void;
}

export default function ArtifactRenderer({ artifact, onExpand }: Props) {
  const handleExpand = onExpand ? () => onExpand(artifact) : undefined;

  switch (artifact.artifact_type) {
    case "chart":
      return <ScientificChartArtifact artifact={artifact} onExpand={handleExpand} />;
    case "flame3d":
      return <Flame3DArtifact artifact={artifact} onExpand={handleExpand} />;
    case "timeseries":
      return <TimeseriesArtifact artifact={artifact} onExpand={handleExpand} />;
    case "table":
      return <TableArtifact artifact={artifact} onExpand={handleExpand} />;
    case "citation":
      return <CitationArtifact artifact={artifact} onExpand={handleExpand} />;
    case "equation":
      return <EquationArtifact artifact={artifact} onExpand={handleExpand} />;
    default:
      return (
        <div className="bg-space-950 p-3 rounded-lg border border-rose-500/50 text-xs text-rose-300 font-mono">
          Unsupported scientific artifact type
        </div>
      );
  }
}
