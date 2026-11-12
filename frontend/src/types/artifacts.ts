/**
 * Discriminated TypeScript interfaces for the 6 Generative UI Scientific Artifact types.
 *
 * Direct match to backend/app/schemas/artifacts.py:
 * - chart
 * - flame3d
 * - timeseries
 * - table
 * - citation
 * - equation
 */

export interface ArtifactBase {
  title: string;
  description?: string | null;
}

// 1. Chart Artifact
export interface ChartDataSeries {
  name: string;
  data_key: string;
  color?: string | null;
  unit?: string | null;
}

export interface ChartArtifact extends ArtifactBase {
  artifact_type: "chart";
  chart_type: "line" | "bar" | "scatter" | "area";
  x_label: string;
  y_label: string;
  x_unit?: string | null;
  y_unit?: string | null;
  series: ChartDataSeries[];
  data_points: Record<string, any>[];
}

// 2. Flame3D Artifact
export interface Flame3DArtifact extends ArtifactBase {
  artifact_type: "flame3d";
  droplet_diameter_mm?: number | null;
  burning_rate_mm2_s?: number | null;
  ambient_o2_pct?: number | null;
  flame_mode?: "hot" | "cool" | "dual";
}

// 3. Timeseries Artifact
export interface TimeseriesChannel {
  channel_name: string;
  unit?: string | null;
  color?: string | null;
  data_key?: string | null;
}

export interface TimeseriesArtifact extends ArtifactBase {
  artifact_type: "timeseries";
  investigation_id?: string | null;
  sampling_rate_hz?: number | null;
  channels: TimeseriesChannel[];
  time_range_s?: [number, number] | null;
  data_points: Record<string, any>[];
}

// 4. Table Artifact
export interface TableColumn {
  key: string;
  label: string;
  unit?: string | null;
  format?: string | null;
}

export interface TableArtifact extends ArtifactBase {
  artifact_type: "table";
  columns: TableColumn[];
  rows: Record<string, any>[];
  source_investigation?: string | null;
}

// 5. Citation Artifact
export interface CitationArtifact extends ArtifactBase {
  artifact_type: "citation";
  investigation_id: string;
  authors: string[];
  journal?: string | null;
  year?: number | null;
  doi?: string | null;
  nasa_source_url?: string | null;
  bibtex?: string | null;
}

// 6. Equation Artifact
export interface EquationArtifact extends ArtifactBase {
  artifact_type: "equation";
  latex: string;
  display_mode?: boolean;
  context?: string | null;
}

// Discriminated Union
export type ScientificArtifact =
  | ChartArtifact
  | Flame3DArtifact
  | TimeseriesArtifact
  | TableArtifact
  | CitationArtifact
  | EquationArtifact;
