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

export interface SIQueryResponse {
  query: string;
  answer: string;
  confidence_score: number;
  abstention_flag: boolean;
  citations: SICitation[];
  explainability: SIExplainability;
}
