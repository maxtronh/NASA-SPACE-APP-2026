export interface HealthResponse {
  status: string;
  database: string;
  tier?: string | null;
  pgvector_ready: boolean;
  version: string;
}

export interface PrincipalInvestigator {
  name: string;
  affiliation: string;
  role: string;
}

export interface InvestigationSummary {
  slug: string;
  title: string;
  project_acronym: string;
  facility: string;
  combustion_regime: string;
  fuel_type: string;
  gravity_level: string;
  summary: string;
  nasa_source_url: string;
  source_repository: string;
  data_completeness_index?: number;
  test_runs_count?: number;
  measurements_count?: number;
  sha256_checksum?: string;
}

export interface PaginatedInvestigationsResponse {
  total: number;
  limit: number;
  offset: number;
  items: InvestigationSummary[];
}

export interface ProvenanceInfo {
  id?: string | null;
  investigation_id?: string | null;
  source_url: string;
  retrieval_timestamp: string;
  sha256_checksum: string;
  original_measurements: Record<string, any>;
  si_measurements: Record<string, any>;
  conversion_method: string;
  validation_status: string;
  http_etag?: string | null;
  byte_size?: number | null;
  parser_module?: string;
  parser_version?: string;
}

export interface TestRun {
  id?: string | null;
  investigation_id?: string | null;
  run_identifier: string;
  run_date?: string | null;
  fuel_phase?: string | null;
  chamber_pressure_kpa?: number | null;
  ambient_temperature_k?: number | null;
  oxygen_percentage?: number | null;
  fuel_flow_rate_sccm?: number | null;
  droplet_initial_diameter_mm?: number | null;
  burn_duration_s?: number | null;
  extinction_type?: string | null;
  burning_rate_constant_k_mm2_s?: number | null;
  flame_spread_rate_mm_s?: number | null;
  raw_parameters?: Record<string, any>;
  si_normalized_parameters?: Record<string, any>;
}

export interface InvestigationDetail {
  id?: string | null;
  slug: string;
  title: string;
  short_name?: string;
  project_acronym: string;
  facility: string;
  combustion_regime: string;
  fuel_type: string;
  oxidizer_type?: string;
  diluents?: string;
  gravity_level: string;
  start_date?: string | null;
  end_date?: string | null;
  principal_investigators?: PrincipalInvestigator[];
  summary: string;
  objectives?: string;
  apparatus_description?: string;
  data_completeness_index?: number;
  nasa_source_url: string;
  source_repository: string;
  test_runs_count?: number;
  measurements_count?: number;
}

export interface InvestigationDetailResponse {
  investigation: InvestigationDetail;
  provenance: ProvenanceInfo;
  test_runs?: TestRun[] | null;
}

export interface EquivalenceAssessment {
  equivalent: boolean;
  reasons: string[];
  buoyancy_warning?: string | null;
}

export interface CompareResponse {
  investigation_ids: string[];
  equivalence_assessment: EquivalenceAssessment;
  comparison_grid: Record<string, any>;
}

export interface GravityRegimeProfile {
  gravity_level: string;
  category: string;
  buoyancy_parameter: number;
  convection_regime: string;
  flame_geometry: string;
  soot_behavior: string;
}

export interface AntigravityCompareRequest {
  investigation_ids: string[];
  gravity_regimes?: string[] | null;
  include_equivalence_matrix?: boolean;
}

export interface AntigravityCompareResponse {
  investigation_ids: string[];
  gravity_regimes_compared: string[];
  equivalence_assessment: EquivalenceAssessment;
  gravity_matrix: Record<string, GravityRegimeProfile>;
  comparison_grid: Record<string, any>;
  buoyancy_warning?: string | null;
}

export interface MissingDataMetric {
  present_count: number;
  missing_count: number;
  completeness_pct: number;
}

export interface CorpusAnalyticsResponse {
  total_investigations: number;
  combustion_regimes: Record<string, number>;
  missing_data_matrix: Record<string, MissingDataMetric>;
}

export interface SICitation {
  investigation_id: string;
  title: string;
  nasa_source_url: string;
  relevance_score: number;
}

export interface SIExplainability {
  matched_entities: string[];
  retrieval_method: string;
  abstention_reason?: string | null;
}

export * from "./artifacts";

export interface SIQueryResponse {
  query: string;
  answer: string;
  confidence_score: number;
  abstention_flag: boolean;
  citations: SICitation[];
  explainability: SIExplainability;
  artifacts?: import("./artifacts").ScientificArtifact[];
}

// ==========================================
// UPGRADE E-07: MULTIMODAL SCHLIEREN & VIDEO RAG
// ==========================================
export type DiagnosticModality = "schlieren" | "pyrometry" | "chemiluminescence" | "direct_video";

export interface ContourExtractionResult {
  flame_centroid_px: [number, number];
  flame_area_px2: number;
  equivalent_diameter_mm: number;
  standoff_ratio: number;
  aspect_ratio: number;
  contour_points: [number, number][];
  soot_shell_contour?: [number, number][];
}

export interface PyrometryMappingResult {
  temperature_peak_k: number;
  temperature_mean_k: number;
  temperature_min_k: number;
  radial_profile: { radius_mm: number; temperature_k: number; soot_volume_fraction_ppm: number }[];
  colormap: "inferno" | "turbo" | "plasma" | "jet";
  resolution_wh: [number, number];
}

export interface SchlierenGradientResult {
  max_density_gradient_kg_m4: number;
  knife_edge_orientation_deg: number;
  boundary_layer_thickness_mm: number;
  gradient_profile: { x_mm: number; density_gradient: number }[];
}

export interface VideoFrameRAGItem {
  id: string;
  investigation_slug: string;
  run_identifier: string;
  timestamp_s: number; // 10 Hz keyframe interval
  modality: DiagnosticModality;
  thumbnail_url?: string;
  optical_features: {
    flame_detected: boolean;
    soot_present: boolean;
    cool_flame_halo: boolean;
    contour?: ContourExtractionResult;
    pyrometry?: PyrometryMappingResult;
    schlieren?: SchlierenGradientResult;
  };
  embedding_similarity?: number;
  description: string;
  ntrs_passage_excerpt?: string;
  camera_specs: {
    frame_rate_hz: number;
    spatial_resolution_um_per_px: number;
    focal_length_mm: number;
    exposure_ms: number;
  };
}

export interface FrameRAGSearchQuery {
  query: string;
  modality?: DiagnosticModality | "all";
  investigation_slug?: string;
  min_similarity?: number;
  limit?: number;
}

export interface FrameRAGSearchResponse {
  total: number;
  query: string;
  results: VideoFrameRAGItem[];
}

// ==========================================
// UPGRADE E-08: ACTIVE LEARNING BAYESIAN OED
// ==========================================
export interface GPSurrogatePoint {
  coordinate: number;
  mean: number;       // \mu(x)
  std: number;        // \sigma(x)
  ucb: number;        // \mu + \kappa * \sigma
  observed_value?: number | null;
}

export interface OEDCandidateProposal {
  rank: number;
  pressure_kpa: number;
  oxygen_pct: number;
  ventilation_velocity_cm_s: number;
  droplet_diameter_mm: number;
  predicted_mean: number;
  epistemic_uncertainty: number;
  ucb_score: number;
  expected_information_gain_bits: number;
  physical_rationale: string;
}

export interface OEDOptimizationRequest {
  kappa: number;
  target_metric: "burning_rate_k" | "extinction_time" | "information_gain";
  fixed_parameters?: {
    pressure_kpa?: number;
    oxygen_pct?: number;
    ventilation_velocity_cm_s?: number;
    droplet_diameter_mm?: number;
  };
  varying_parameter: "pressure_kpa" | "oxygen_pct" | "ventilation_velocity_cm_s" | "droplet_diameter_mm";
}

export interface OEDOptimizationResponse {
  acquisition_function: "UCB";
  kappa: number;
  varying_axis: string;
  curve_points: GPSurrogatePoint[];
  top_proposals: OEDCandidateProposal[];
  surrogate_stats: {
    total_training_runs: number;
    length_scales: Record<string, number>;
    variance_reduction_pct: number;
    r2_score: number;
  };
}

// ==========================================
// UPGRADE E-10: EXPLORATION ATMOSPHERE FIRE HAZARD (EAFHI)
// ==========================================
export type FlammabilityRiskClass = "low" | "moderate" | "high" | "critical";

export interface EAFHIEnvironmentInput {
  gravity_g: number;
  pressure_kpa: number;
  oxygen_pct: number;
  ventilation_velocity_cm_s: number;
  material_key: string;
  characteristic_length_m?: number;
}

export interface EAFHIResult {
  risk_score: number; // [0.0, 1.0]
  classification: FlammabilityRiskClass;
  grashof_number: number;
  grashof_ratio_to_1g: number;
  buoyancy_factor_phi: number;
  minimum_extinguishing_o2_pct: number;
  oxygen_margin_pct: number;
  flammability_status: "SELF_EXTINGUISHING" | "MARGINAL_PROPAGATION" | "VIGOROUS_COMBUSTION" | "ACCELERATED_FLASHOVER";
  risk_contributions: {
    oxygen_enrichment_pct: number;
    hypobaric_decompression_pct: number;
    buoyancy_suppression_pct: number;
  };
  operational_protocol: {
    eva_status: "AUTHORIZED" | "RESTRICTED" | "LOCKDOWN";
    suppression_recommendation: string;
    ventilation_adjustment_advice: string;
  };
}

export interface SensitivityCurvePoint {
  parameter_value: number;
  risk_score: number;
  moc_pct: number;
  grashof_ratio: number;
  classification: FlammabilityRiskClass;
}

export interface EAFHISensitivityResponse {
  swept_parameter: "oxygen_pct" | "pressure_kpa" | "gravity_g" | "ventilation_velocity_cm_s";
  curve: SensitivityCurvePoint[];
  current_operating_point: EAFHIResult;
}

