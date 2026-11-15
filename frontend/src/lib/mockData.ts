import {
  CorpusAnalyticsResponse,
  InvestigationDetailResponse,
  InvestigationSummary,
  VideoFrameRAGItem,
  FrameRAGSearchQuery,
  FrameRAGSearchResponse,
  OEDOptimizationRequest,
  OEDOptimizationResponse,
  EAFHIEnvironmentInput,
  EAFHIResult,
  EAFHISensitivityResponse,
  SensitivityCurvePoint,
  GPSurrogatePoint,
  OEDCandidateProposal,
  FlammabilityRiskClass,
  CCSDSTelemetryFrame,
  WaveletFilterRequest,
  WaveletFilterResponse,
  RekindleRiskRequest,
  RekindleRiskResponse,
  RekindleRiskLevel,
} from "@/types";

export const MOCK_INVESTIGATIONS: InvestigationSummary[] = [
  {
    slug: "flex-droplet-burning",
    title: "Detailed Results from the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011",
    project_acronym: "FLEX",
    facility: "Combustion Integrated Rack (CIR)",
    combustion_regime: "droplet_combustion",
    fuel_type: "Methanol / n-Heptane / Decane",
    gravity_level: "microgravity (~10^-6 g)",
    summary: "The Flame Extinguishment Experiment (FLEX) conducted isolated droplet combustion tests aboard the ISS inside the Combustion Integrated Rack (CIR). Investigated radiative and convective extinction, burning rates, and cool-flame chemistry of single alkane and alcohol droplets.",
    nasa_source_url: "https://ntrs.nasa.gov/citations/20150023456",
    source_repository: "NASA NTRS",
    data_completeness_index: 94.5,
    test_runs_count: 276,
    measurements_count: 1104,
    sha256_checksum: "60b5c4bbfbd48464cd07f17ec3e619c329aa7e098206899c270a9b1a7335b16c",
  },
  {
    slug: "bass-ii-solid-slab",
    title: "Burning and Suppression of Solids–II (BASS-II) Summary Report",
    project_acronym: "BASS-II",
    combustion_regime: "solid_flame_spread",
    facility: "Microgravity Science Glovebox (MSG)",
    fuel_type: "Polymethylmethacrylate (PMMA)",
    gravity_level: "microgravity (~10^-6 g)",
    summary: "BASS-II investigated the burning and extinction characteristics of solid fuels in microgravity. Conducted in the Microgravity Science Glovebox (MSG), BASS-II evaluated thick PMMA slabs and thin fuel strips under varying low-speed concurrent and opposed convective flows.",
    nasa_source_url: "https://ntrs.nasa.gov/citations/20210011385",
    source_repository: "NASA NTRS",
    data_completeness_index: 91.0,
    test_runs_count: 20,
    measurements_count: 80,
    sha256_checksum: "56ee5bd7702b5c8235f9934468bb9d6e4ea143c4570d7eaa1da11d904b42ea3f",
  },
  {
    slug: "acme-cld-flame",
    title: "Recent Research on Flames of Gaseous Fuel Aboard the International Space Station",
    project_acronym: "ACME",
    facility: "Combustion Integrated Rack (CIR)",
    combustion_regime: "laminar_diffusion",
    fuel_type: "Methane (CH4)",
    gravity_level: "microgravity (~10^-6 g)",
    summary: "The Advanced Combustion via Microgravity Experiments (ACME) project comprised six modular flight investigations in the Combustion Integrated Rack (CIR) on the ISS: CLD Flame, BRE, E-FIELD Flames, Flame Design, s-Flame, and CFI-G. ACME investigated fundamental soot processes and non-buoyant diffusion flames.",
    nasa_source_url: "https://ntrs.nasa.gov/citations/20190001859",
    source_repository: "NASA NTRS",
    data_completeness_index: 96.0,
    test_runs_count: 4,
    measurements_count: 24,
    sha256_checksum: "9d89dd87cfcf844770a67a012b82bc03ea6172914e68a314ea357ba73c0d1727",
  },
  {
    slug: "acme-cld-ground-1g",
    title: "ACME Terrestrial 1g Baseline - Coflow Laminar Diffusion Flame",
    project_acronym: "ACME-1G",
    facility: "NASA Glenn 1g Terrestrial Burner Rig",
    combustion_regime: "laminar_diffusion",
    fuel_type: "Methane (CH4)",
    gravity_level: "normal_gravity (1.0 g)",
    summary: "Ground-based normal-gravity comparative baseline for ACME Coflow Laminar Diffusion flame tests at NASA Glenn Research Center, exhibiting strong buoyancy-induced acceleration and soot flickering.",
    nasa_source_url: "https://ntrs.nasa.gov/citations/20190001860",
    source_repository: "NASA NTRS",
    data_completeness_index: 88.5,
    test_runs_count: 4,
    measurements_count: 20,
    sha256_checksum: "3e5a4d9c72e411b0e99812401f83c16a19f24b890a59f63567d268d098e72b41",
  },
];

export const MOCK_CORPUS_ANALYTICS: CorpusAnalyticsResponse = {
  total_investigations: 3,
  total_test_runs: 300,
  total_measurements: 1208,
  combustion_regimes: {
    droplet_combustion: 1,
    solid_flame_spread: 1,
    laminar_diffusion: 1,
  },
  missing_data_matrix: {
    chamber_pressure: {
      present_count: 300,
      missing_count: 0,
      completeness_pct: 100.0,
    },
    droplet_initial_diameter: {
      present_count: 276,
      missing_count: 24,
      completeness_pct: 92.0,
    },
    burning_rate_constant: {
      present_count: 260,
      missing_count: 40,
      completeness_pct: 86.7,
    },
    flame_spread_rate: {
      present_count: 20,
      missing_count: 280,
      completeness_pct: 6.7,
    },
    fuel_flow_rate: {
      present_count: 4,
      missing_count: 296,
      completeness_pct: 1.3,
    },
    soot_volume_fraction: {
      present_count: 4,
      missing_count: 296,
      completeness_pct: 1.3,
    },
    radiative_flux: {
      present_count: 0,
      missing_count: 300,
      completeness_pct: 0.0,
    },
  },
};

export const MOCK_INVESTIGATION_DETAILS: Record<string, InvestigationDetailResponse> = {
  "flex-droplet-burning": {
    investigation: {
      id: "inv-flex-001",
      slug: "flex-droplet-burning",
      title: "Detailed Results from the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011",
      short_name: "FLEX Droplet Burning",
      project_acronym: "FLEX",
      facility: "Combustion Integrated Rack (CIR)",
      combustion_regime: "droplet_combustion",
      fuel_type: "Methanol / n-Heptane / Decane",
      oxidizer_type: "Air",
      diluents: "Nitrogen / Carbon Dioxide / Helium",
      gravity_level: "microgravity (~10^-6 g)",
      start_date: "2009-03-01",
      end_date: "2011-12-31",
      principal_investigators: [
        {
          name: "Forman A. Williams",
          affiliation: "University of California San Diego",
          role: "Lead Principal Investigator",
        },
        {
          name: "Frederick L. Dryer",
          affiliation: "Princeton University",
          role: "Co-Investigator",
        },
        {
          name: "Vedha Nayagam",
          affiliation: "Case Western Reserve University",
          role: "Project Scientist",
        },
      ],
      summary: "The Flame Extinguishment Experiment (FLEX) investigated the extinction dynamics and burning rates of isolated fuel droplets in microgravity aboard the International Space Station (ISS) within the Combustion Integrated Rack (CIR). It provided the first systematic observational evidence of cool-flame droplet burning following hot flame extinction.",
      objectives: "Characterize microgravity droplet burning rates (d² law), radiative and convective extinction diameters, and low-temperature quasi-steady cool flame phenomena.",
      apparatus_description: "Multi-user Droplet Combustion Apparatus (MDCA) mounted inside the 100-liter CIR chamber on the ISS US Destiny Laboratory.",
      data_completeness_index: 94.5,
      nasa_source_url: "https://ntrs.nasa.gov/citations/20150023456",
      source_repository: "NASA NTRS",
      test_runs_count: 276,
      measurements_count: 1104,
    },
    provenance: {
      id: "prov-flex-001",
      investigation_id: "inv-flex-001",
      source_url: "https://ntrs.nasa.gov/citations/20150023456",
      retrieval_timestamp: "2026-11-12T18:35:12Z",
      sha256_checksum: "60b5c4bbfbd48464cd07f17ec3e619c329aa7e098206899c270a9b1a7335b16c",
      http_etag: "\"1b4a-5f098a12\"",
      byte_size: 766110,
      parser_module: "backend.app.ingestion.parsers.flex_parser",
      parser_version: "1.0.0",
      validation_status: "VALIDATED",
      original_measurements: {
        pressure_mmHg: "757.7",
        initial_diameter_mm: "1.69",
        extinction_diameter_mm: "0.89",
        burning_rate_mm2_s: "0.52",
        soot_volume_fraction: null,
        radiative_flux: null,
      },
      si_measurements: {
        chamber_pressure_pa: 101018.358,
        droplet_initial_diameter_m: 0.00169,
        extinction_diameter_m: 0.00089,
        burning_rate_m2_s: 5.2e-07,
        soot_volume_fraction: null,
        radiative_flux_w_m2: null,
      },
      conversion_method: "deterministic_si_table_v1",
    },
    test_runs: [
      {
        run_identifier: "FLEX-001",
        fuel_phase: "liquid_droplet",
        chamber_pressure_kpa: 101.02,
        ambient_temperature_k: 298.15,
        oxygen_percentage: 21.0,
        fuel_flow_rate_sccm: null,
        droplet_initial_diameter_mm: 1.69,
        burn_duration_s: 5.4,
        extinction_type: "radiative",
        burning_rate_constant_k_mm2_s: 0.52,
        flame_spread_rate_mm_s: null,
        raw_parameters: { fuel: "Methanol", d0_mm: 1.69, k_burn: 0.52, soot: null },
      },
      {
        run_identifier: "FLEX-002",
        fuel_phase: "liquid_droplet",
        chamber_pressure_kpa: 101.59,
        ambient_temperature_k: 298.15,
        oxygen_percentage: 21.0,
        fuel_flow_rate_sccm: null,
        droplet_initial_diameter_mm: 1.86,
        burn_duration_s: 6.2,
        extinction_type: "radiative",
        burning_rate_constant_k_mm2_s: 0.60,
        flame_spread_rate_mm_s: null,
        raw_parameters: { fuel: "Methanol", d0_mm: 1.86, k_burn: 0.60, soot: null },
      },
      {
        run_identifier: "FLEX-003",
        fuel_phase: "liquid_droplet",
        chamber_pressure_kpa: 101.32,
        ambient_temperature_k: 298.15,
        oxygen_percentage: 21.0,
        fuel_flow_rate_sccm: null,
        droplet_initial_diameter_mm: 2.14,
        burn_duration_s: 7.8,
        extinction_type: "cool_flame_transition",
        burning_rate_constant_k_mm2_s: 0.48,
        flame_spread_rate_mm_s: null,
        raw_parameters: { fuel: "n-Heptane", d0_mm: 2.14, k_burn: 0.48, soot: null },
      },
      {
        run_identifier: "FLEX-015",
        fuel_phase: "liquid_droplet",
        chamber_pressure_kpa: 50.66,
        ambient_temperature_k: 297.15,
        oxygen_percentage: 30.0,
        fuel_flow_rate_sccm: null,
        droplet_initial_diameter_mm: 2.45,
        burn_duration_s: 9.1,
        extinction_type: "diffusive",
        burning_rate_constant_k_mm2_s: 0.65,
        flame_spread_rate_mm_s: null,
        raw_parameters: { fuel: "n-Heptane", d0_mm: 2.45, k_burn: 0.65, soot: null },
      },
      {
        run_identifier: "FLEX-042",
        fuel_phase: "liquid_droplet",
        chamber_pressure_kpa: 101.32,
        ambient_temperature_k: 298.15,
        oxygen_percentage: 18.0,
        fuel_flow_rate_sccm: null,
        droplet_initial_diameter_mm: 2.70,
        burn_duration_s: 11.4,
        extinction_type: "cool_flame_transition",
        burning_rate_constant_k_mm2_s: 0.43,
        flame_spread_rate_mm_s: null,
        raw_parameters: { fuel: "n-Decane", d0_mm: 2.70, k_burn: 0.43, soot: null },
      },
      {
        run_identifier: "FLEX-118",
        fuel_phase: "liquid_droplet",
        chamber_pressure_kpa: 101.20,
        ambient_temperature_k: 298.15,
        oxygen_percentage: 21.0,
        fuel_flow_rate_sccm: null,
        droplet_initial_diameter_mm: 3.10,
        burn_duration_s: 14.5,
        extinction_type: "radiative",
        burning_rate_constant_k_mm2_s: 0.41,
        flame_spread_rate_mm_s: null,
        raw_parameters: { fuel: "n-Heptane", d0_mm: 3.10, k_burn: 0.41, soot: null },
      },
    ],
  },
  "bass-ii-solid-slab": {
    investigation: {
      id: "inv-bass-001",
      slug: "bass-ii-solid-slab",
      title: "Burning and Suppression of Solids–II (BASS-II) Summary Report",
      short_name: "BASS-II Solid Fuel Spread",
      project_acronym: "BASS-II",
      facility: "Microgravity Science Glovebox (MSG)",
      combustion_regime: "solid_flame_spread",
      fuel_type: "Polymethylmethacrylate (PMMA)",
      oxidizer_type: "Air (variable O2: 15% - 21%)",
      diluents: "Nitrogen",
      gravity_level: "microgravity (~10^-6 g)",
      start_date: "2013-05-01",
      end_date: "2016-08-31",
      principal_investigators: [
        {
          name: "Paul V. Ferkul",
          affiliation: "National Center for Space Exploration Research",
          role: "Lead Scientist",
        },
        {
          name: "James S. T'ien",
          affiliation: "Case Western Reserve University",
          role: "Principal Investigator",
        },
        {
          name: "Sandra L. Olson",
          affiliation: "NASA Glenn Research Center",
          role: "Project Scientist",
        },
      ],
      summary: "BASS-II investigated the burning and extinction characteristics of solid fuels in microgravity. Conducted in the Microgravity Science Glovebox (MSG), BASS-II evaluated thick PMMA slabs and thin fuel strips under varying low-speed concurrent and opposed convective flows.",
      objectives: "Determine extinction flow limits, flame spread rates, and suppression effectiveness using inert gas quenches on solid fuels in spacecraft cabins.",
      apparatus_description: "Flow duct insert inside the Microgravity Science Glovebox (MSG) facility on the ISS.",
      data_completeness_index: 91.0,
      nasa_source_url: "https://ntrs.nasa.gov/citations/20210011385",
      source_repository: "NASA NTRS",
      test_runs_count: 20,
      measurements_count: 80,
    },
    provenance: {
      id: "prov-bass-001",
      investigation_id: "inv-bass-001",
      source_url: "https://ntrs.nasa.gov/citations/20210011385",
      retrieval_timestamp: "2026-11-12T18:40:00Z",
      sha256_checksum: "56ee5bd7702b5c8235f9934468bb9d6e4ea143c4570d7eaa1da11d904b42ea3f",
      byte_size: 61223,
      parser_module: "backend.app.ingestion.parsers.bass_parser",
      parser_version: "1.0.0",
      validation_status: "VALIDATED",
      original_measurements: {
        chamber_pressure_atm: "1.0",
        fuel_sample_thickness_mm: "10.0",
        flame_spread_rate_mm_s: "0.22",
        flow_velocity_cm_s: "2.5",
        droplet_initial_diameter: null,
        radiative_flux: null,
      },
      si_measurements: {
        chamber_pressure_pa: 101325.0,
        fuel_sample_thickness_m: 0.010,
        flame_spread_rate_m_s: 0.00022,
        flow_velocity_m_s: 0.025,
        droplet_initial_diameter_m: null,
        radiative_flux_w_m2: null,
      },
      conversion_method: "deterministic_si_table_v1",
    },
    test_runs: [
      {
        run_identifier: "BASS-II-SLAB-01",
        fuel_phase: "solid_slab",
        chamber_pressure_kpa: 101.325,
        ambient_temperature_k: 296.15,
        oxygen_percentage: 21.0,
        fuel_flow_rate_sccm: null,
        droplet_initial_diameter_mm: null,
        burn_duration_s: 480.0,
        extinction_type: "opposed_blowoff",
        burning_rate_constant_k_mm2_s: null,
        flame_spread_rate_mm_s: 0.22,
        raw_parameters: { fuel: "PMMA Slab", velocity_cm_s: 2.5, spread_mm_s: 0.22 },
      },
      {
        run_identifier: "BASS-II-SLAB-02",
        fuel_phase: "solid_slab",
        chamber_pressure_kpa: 101.325,
        ambient_temperature_k: 296.15,
        oxygen_percentage: 18.0,
        fuel_flow_rate_sccm: null,
        droplet_initial_diameter_mm: null,
        burn_duration_s: 320.0,
        extinction_type: "quench",
        burning_rate_constant_k_mm2_s: null,
        flame_spread_rate_mm_s: 0.16,
        raw_parameters: { fuel: "PMMA Slab", velocity_cm_s: 1.8, spread_mm_s: 0.16 },
      },
      {
        run_identifier: "BASS-II-THIN-03",
        fuel_phase: "solid_thin",
        chamber_pressure_kpa: 101.325,
        ambient_temperature_k: 295.15,
        oxygen_percentage: 21.0,
        fuel_flow_rate_sccm: null,
        droplet_initial_diameter_mm: null,
        burn_duration_s: 140.0,
        extinction_type: "concurrent_burnout",
        burning_rate_constant_k_mm2_s: null,
        flame_spread_rate_mm_s: 1.15,
        raw_parameters: { fuel: "PMMA Thin Strip", velocity_cm_s: 5.0, spread_mm_s: 1.15 },
      },
    ],
  },
  "acme-cld-flame": {
    investigation: {
      id: "inv-acme-001",
      slug: "acme-cld-flame",
      title: "Recent Research on Flames of Gaseous Fuel Aboard the International Space Station",
      short_name: "ACME Laminar Diffusion Flame",
      project_acronym: "ACME",
      facility: "Combustion Integrated Rack (CIR)",
      combustion_regime: "laminar_diffusion",
      fuel_type: "Methane (CH4)",
      oxidizer_type: "Air",
      diluents: "Nitrogen",
      gravity_level: "microgravity (~10^-6 g)",
      start_date: "2017-11-01",
      end_date: "2022-02-28",
      principal_investigators: [
        {
          name: "Dennis P. Stocker",
          affiliation: "NASA Glenn Research Center",
          role: "Project Scientist",
        },
        {
          name: "Peter B. Sunderland",
          affiliation: "University of Maryland",
          role: "Principal Investigator (CLD Flame)",
        },
      ],
      summary: "The Advanced Combustion via Microgravity Experiments (ACME) project investigated laminar diffusion flames inside the ISS CIR chamber to study soot formation, flame stability, and soot-free cool-gas combustion.",
      objectives: "Understand soot inception and oxidation in buoyancy-free laminar diffusion flames, quantify radiative heat loss, and validate non-premixed combustion kinetics models.",
      apparatus_description: "ACME modular burner insert inside the 100-liter Combustion Integrated Rack (CIR) chamber aboard the ISS.",
      data_completeness_index: 96.0,
      nasa_source_url: "https://ntrs.nasa.gov/citations/20190001859",
      source_repository: "NASA NTRS",
      test_runs_count: 4,
      measurements_count: 24,
    },
    provenance: {
      id: "prov-acme-001",
      investigation_id: "inv-acme-001",
      source_url: "https://ntrs.nasa.gov/citations/20190001859",
      retrieval_timestamp: "2026-11-12T18:45:35Z",
      sha256_checksum: "9d89dd87cfcf844770a67a012b82bc03ea6172914e68a314ea357ba73c0d1727",
      byte_size: 18161,
      parser_module: "backend.app.ingestion.parsers.acme_parser",
      parser_version: "1.0.0",
      validation_status: "VALIDATED",
      original_measurements: {
        fuel_flow_rate: "25.0 sccm",
        coflow_air_velocity: "20.0 cm/s",
        chamber_pressure: "1.0 atm",
        flame_height: "18.5 mm",
        soot_volume_fraction: "1.2e-06",
        initial_droplet_diameter: null,
      },
      si_measurements: {
        fuel_flow_rate_m3_s: 4.16667e-7,
        coflow_air_velocity_m_s: 0.2,
        chamber_pressure_pa: 101325.0,
        flame_height_m: 0.0185,
        soot_volume_fraction: 1.2e-6,
        initial_droplet_diameter_m: null,
      },
      conversion_method: "deterministic_si_table_v1",
    },
    test_runs: [
      {
        run_identifier: "ACME-CLD-CH4-01",
        fuel_phase: "gas_jet",
        chamber_pressure_kpa: 101.325,
        ambient_temperature_k: 298.15,
        oxygen_percentage: 21.0,
        fuel_flow_rate_sccm: 25.0,
        droplet_initial_diameter_mm: null,
        burn_duration_s: 300.0,
        extinction_type: null,
        burning_rate_constant_k_mm2_s: null,
        flame_spread_rate_mm_s: null,
        raw_parameters: { fuel: "Methane (CH4)", flow_sccm: 25.0, flame_h_mm: 18.5, soot: 1.2e-6 },
      },
      {
        run_identifier: "ACME-CLD-C2H4-01",
        fuel_phase: "gas_jet",
        chamber_pressure_kpa: 101.325,
        ambient_temperature_k: 297.65,
        oxygen_percentage: 21.0,
        fuel_flow_rate_sccm: 15.0,
        droplet_initial_diameter_mm: null,
        burn_duration_s: 240.0,
        extinction_type: null,
        burning_rate_constant_k_mm2_s: null,
        flame_spread_rate_mm_s: null,
        raw_parameters: { fuel: "Ethylene (C2H4)", flow_sccm: 15.0, flame_h_mm: 14.2, soot: 3.5e-6 },
      },
    ],
  },
};

// ==========================================
// UPGRADE E-07: MULTIMODAL VIDEO & SCHLIEREN RAG MOCK DATA
// ==========================================
export const MOCK_VIDEO_FRAMES: VideoFrameRAGItem[] = [
  {
    id: "frame-flex-003-r04-340",
    investigation_slug: "flex-droplet-burning",
    run_identifier: "FLEX-003-R04",
    timestamp_s: 3.40,
    modality: "pyrometry",
    thumbnail_url: "/frames/flex_340_pyro.png",
    embedding_similarity: 0.962,
    description: "Soot shell formation around isolated n-heptane droplet in CIR chamber. Symmetrical luminous flame zone with high soot volume fraction.",
    ntrs_passage_excerpt: "NASA/TM-2015-218762: FLEX-1 experiments revealed spherical soot shell accumulation trapped between fuel vapor and oxidizer reaction zone under microgravity diffusion.",
    camera_specs: {
      frame_rate_hz: 30.0,
      spatial_resolution_um_per_px: 24.5,
      focal_length_mm: 105.0,
      exposure_ms: 2.5,
    },
    optical_features: {
      flame_detected: true,
      soot_present: true,
      cool_flame_halo: false,
      contour: {
        flame_centroid_px: [128, 128],
        flame_area_px2: 18450,
        equivalent_diameter_mm: 4.82,
        standoff_ratio: 3.21,
        aspect_ratio: 1.03,
        contour_points: [
          [128, 52], [168, 65], [195, 98], [204, 128], [195, 158],
          [168, 191], [128, 204], [88, 191], [61, 158], [52, 128],
          [61, 98], [88, 65]
        ],
        soot_shell_contour: [
          [128, 72], [158, 82], [178, 106], [184, 128], [178, 150],
          [158, 174], [128, 184], [98, 174], [78, 150], [72, 128],
          [78, 106], [98, 82]
        ],
      },
      pyrometry: {
        temperature_peak_k: 1820.0,
        temperature_mean_k: 1540.0,
        temperature_min_k: 920.0,
        colormap: "inferno",
        resolution_wh: [256, 256],
        radial_profile: [
          { radius_mm: 0.0, temperature_k: 365.0, soot_volume_fraction_ppm: 0.0 },
          { radius_mm: 0.75, temperature_k: 620.0, soot_volume_fraction_ppm: 0.15 },
          { radius_mm: 1.5, temperature_k: 1180.0, soot_volume_fraction_ppm: 1.45 },
          { radius_mm: 2.4, temperature_k: 1820.0, soot_volume_fraction_ppm: 4.82 },
          { radius_mm: 3.2, temperature_k: 1690.0, soot_volume_fraction_ppm: 3.10 },
          { radius_mm: 4.0, temperature_k: 1410.0, soot_volume_fraction_ppm: 1.20 },
          { radius_mm: 5.0, temperature_k: 1050.0, soot_volume_fraction_ppm: 0.30 },
          { radius_mm: 6.0, temperature_k: 720.0, soot_volume_fraction_ppm: 0.02 },
        ],
      },
      schlieren: {
        max_density_gradient_kg_m4: 12.4,
        knife_edge_orientation_deg: 90.0,
        boundary_layer_thickness_mm: 4.5,
        gradient_profile: [
          { x_mm: -5.0, density_gradient: 1.2 },
          { x_mm: -2.5, density_gradient: 8.9 },
          { x_mm: 0.0, density_gradient: 12.4 },
          { x_mm: 2.5, density_gradient: 8.9 },
          { x_mm: 5.0, density_gradient: 1.2 },
        ],
      },
    },
  },
  {
    id: "frame-flex-003-r04-810",
    investigation_slug: "flex-droplet-burning",
    run_identifier: "FLEX-003-R04",
    timestamp_s: 8.10,
    modality: "chemiluminescence",
    thumbnail_url: "/frames/flex_810_cool.png",
    embedding_similarity: 0.941,
    description: "Second-stage quasi-steady cool flame combustion following hot radiative extinction. Faint blue/UV formaldehyde chemiluminescence halo.",
    ntrs_passage_excerpt: "NASA/TP-2016-219012: Low-temperature cool flames sustained by low-temperature alkane branching kinetics observed after visible flame extinguishment.",
    camera_specs: {
      frame_rate_hz: 30.0,
      spatial_resolution_um_per_px: 24.5,
      focal_length_mm: 105.0,
      exposure_ms: 10.0,
    },
    optical_features: {
      flame_detected: true,
      soot_present: false,
      cool_flame_halo: true,
      contour: {
        flame_centroid_px: [128, 127],
        flame_area_px2: 24100,
        equivalent_diameter_mm: 5.54,
        standoff_ratio: 4.12,
        aspect_ratio: 1.01,
        contour_points: [
          [128, 40], [172, 54], [202, 92], [214, 127], [202, 162],
          [172, 200], [128, 214], [84, 200], [54, 162], [42, 127],
          [54, 92], [84, 54]
        ],
      },
      pyrometry: {
        temperature_peak_k: 940.0,
        temperature_mean_k: 810.0,
        temperature_min_k: 650.0,
        colormap: "turbo",
        resolution_wh: [256, 256],
        radial_profile: [
          { radius_mm: 0.0, temperature_k: 320.0, soot_volume_fraction_ppm: 0.0 },
          { radius_mm: 1.0, temperature_k: 480.0, soot_volume_fraction_ppm: 0.0 },
          { radius_mm: 2.0, temperature_k: 710.0, soot_volume_fraction_ppm: 0.0 },
          { radius_mm: 3.2, temperature_k: 940.0, soot_volume_fraction_ppm: 0.0 },
          { radius_mm: 4.5, temperature_k: 780.0, soot_volume_fraction_ppm: 0.0 },
          { radius_mm: 6.0, temperature_k: 510.0, soot_volume_fraction_ppm: 0.0 },
        ],
      },
    },
  },
  {
    id: "frame-bass-ii-slab-08-125",
    investigation_slug: "bass-ii-solid-slab",
    run_identifier: "BASS-II-SLAB-08",
    timestamp_s: 12.50,
    modality: "schlieren",
    thumbnail_url: "/frames/bass_slab_schlieren.png",
    embedding_similarity: 0.915,
    description: "Concurrent low-speed flow over PMMA slab inside MSG. Knife-edge Schlieren reveals laminar thermal boundary layer suppression.",
    ntrs_passage_excerpt: "NASA/CR-2021-220451: Reduced buoyant convection allows fuel vapor layer expansion and delayed convective cooling along solid sample surface.",
    camera_specs: {
      frame_rate_hz: 60.0,
      spatial_resolution_um_per_px: 52.0,
      focal_length_mm: 85.0,
      exposure_ms: 1.0,
    },
    optical_features: {
      flame_detected: true,
      soot_present: true,
      cool_flame_halo: false,
      contour: {
        flame_centroid_px: [142, 110],
        flame_area_px2: 32400,
        equivalent_diameter_mm: 8.25,
        standoff_ratio: 2.10,
        aspect_ratio: 2.45,
        contour_points: [
          [60, 90], [120, 80], [190, 85], [230, 105], [210, 135],
          [160, 140], [100, 135], [60, 115]
        ],
      },
      schlieren: {
        max_density_gradient_kg_m4: 14.8,
        knife_edge_orientation_deg: 0.0,
        boundary_layer_thickness_mm: 6.2,
        gradient_profile: [
          { x_mm: 0.0, density_gradient: 14.8 },
          { x_mm: 2.0, density_gradient: 11.2 },
          { x_mm: 4.0, density_gradient: 7.5 },
          { x_mm: 6.0, density_gradient: 3.1 },
          { x_mm: 8.0, density_gradient: 0.8 },
        ],
      },
      pyrometry: {
        temperature_peak_k: 1680.0,
        temperature_mean_k: 1390.0,
        temperature_min_k: 780.0,
        colormap: "inferno",
        resolution_wh: [256, 256],
        radial_profile: [
          { radius_mm: 0.0, temperature_k: 640.0, soot_volume_fraction_ppm: 0.05 },
          { radius_mm: 1.5, temperature_k: 1220.0, soot_volume_fraction_ppm: 0.8 },
          { radius_mm: 3.0, temperature_k: 1680.0, soot_volume_fraction_ppm: 2.4 },
          { radius_mm: 5.0, temperature_k: 1350.0, soot_volume_fraction_ppm: 1.1 },
          { radius_mm: 7.0, temperature_k: 920.0, soot_volume_fraction_ppm: 0.1 },
        ],
      },
    },
  },
  {
    id: "frame-acme-cld-ch4-01-150",
    investigation_slug: "acme-cld-flame",
    run_identifier: "ACME-CLD-CH4-01",
    timestamp_s: 15.00,
    modality: "pyrometry",
    thumbnail_url: "/frames/acme_cld_pyro.png",
    embedding_similarity: 0.958,
    description: "Non-buoyant coflow laminar diffusion flame. Symmetrical spherical flame front with complete absence of buoyant flicker.",
    ntrs_passage_excerpt: "NASA/TM-2019-220184: ACME CLD flame exhibits extended residence times enabling soot inception and radiative cooling dominant regime.",
    camera_specs: {
      frame_rate_hz: 30.0,
      spatial_resolution_um_per_px: 35.0,
      focal_length_mm: 135.0,
      exposure_ms: 3.0,
    },
    optical_features: {
      flame_detected: true,
      soot_present: true,
      cool_flame_halo: false,
      contour: {
        flame_centroid_px: [128, 120],
        flame_area_px2: 28500,
        equivalent_diameter_mm: 6.80,
        standoff_ratio: 2.85,
        aspect_ratio: 1.25,
        contour_points: [
          [128, 45], [165, 60], [190, 100], [195, 140], [180, 185],
          [128, 205], [76, 185], [61, 140], [66, 100], [91, 60]
        ],
      },
      pyrometry: {
        temperature_peak_k: 1910.0,
        temperature_mean_k: 1620.0,
        temperature_min_k: 1050.0,
        colormap: "inferno",
        resolution_wh: [256, 256],
        radial_profile: [
          { radius_mm: 0.0, temperature_k: 850.0, soot_volume_fraction_ppm: 0.0 },
          { radius_mm: 1.2, temperature_k: 1420.0, soot_volume_fraction_ppm: 0.9 },
          { radius_mm: 2.6, temperature_k: 1910.0, soot_volume_fraction_ppm: 3.8 },
          { radius_mm: 4.2, temperature_k: 1590.0, soot_volume_fraction_ppm: 2.2 },
          { radius_mm: 6.0, temperature_k: 1120.0, soot_volume_fraction_ppm: 0.4 },
        ],
      },
      schlieren: {
        max_density_gradient_kg_m4: 18.2,
        knife_edge_orientation_deg: 90.0,
        boundary_layer_thickness_mm: 5.1,
        gradient_profile: [
          { x_mm: -4.0, density_gradient: 2.1 },
          { x_mm: 0.0, density_gradient: 18.2 },
          { x_mm: 4.0, density_gradient: 2.1 },
        ],
      },
    },
  },
  {
    id: "frame-flex-012-r01-050",
    investigation_slug: "flex-droplet-burning",
    run_identifier: "FLEX-012-R01",
    timestamp_s: 0.50,
    modality: "direct_video",
    thumbnail_url: "/frames/flex_050_ignition.png",
    embedding_similarity: 0.885,
    description: "Initial spark discharge and droplet deployment in quiescent microgravity environment. Unmeasured post-spark thermal state.",
    ntrs_passage_excerpt: "NASA/TP-2014-217890: Droplet deployment needle retraction dynamics and initial droplet oscillation damping prior to steady combustion.",
    camera_specs: {
      frame_rate_hz: 100.0,
      spatial_resolution_um_per_px: 24.5,
      focal_length_mm: 105.0,
      exposure_ms: 0.5,
    },
    optical_features: {
      flame_detected: false,
      soot_present: false,
      cool_flame_halo: false,
      // Zero-Fabrication Mandate: missing / pre-ignition metrics strictly omitted / null
    },
  },
  {
    id: "frame-acme-bre-02-220",
    investigation_slug: "acme-cld-flame",
    run_identifier: "ACME-BRE-02",
    timestamp_s: 22.00,
    modality: "schlieren",
    thumbnail_url: "/frames/acme_bre_schlieren.png",
    embedding_similarity: 0.932,
    description: "High-pressure (150 kPa) Schlieren optical interrogation of soot precursor formation and annular boundary currents.",
    ntrs_passage_excerpt: "NASA/TM-2020-220556: Pressure scaling accelerates soot inception kinetics while maintaining spherical boundary geometry.",
    camera_specs: {
      frame_rate_hz: 60.0,
      spatial_resolution_um_per_px: 30.0,
      focal_length_mm: 120.0,
      exposure_ms: 1.5,
    },
    optical_features: {
      flame_detected: true,
      soot_present: true,
      cool_flame_halo: false,
      contour: {
        flame_centroid_px: [128, 128],
        flame_area_px2: 31000,
        equivalent_diameter_mm: 7.10,
        standoff_ratio: 3.55,
        aspect_ratio: 1.08,
        contour_points: [
          [128, 40], [175, 55], [205, 95], [210, 135], [195, 175],
          [160, 205], [128, 215], [90, 205], [55, 175], [45, 135],
          [50, 95], [80, 55]
        ],
      },
      schlieren: {
        max_density_gradient_kg_m4: 28.4,
        knife_edge_orientation_deg: 90.0,
        boundary_layer_thickness_mm: 3.8,
        gradient_profile: [
          { x_mm: -6.0, density_gradient: 1.5 },
          { x_mm: -3.0, density_gradient: 14.2 },
          { x_mm: 0.0, density_gradient: 28.4 },
          { x_mm: 3.0, density_gradient: 14.2 },
          { x_mm: 6.0, density_gradient: 1.5 },
        ],
      },
    },
  },
];

export function filterMockFrameRAG(params: FrameRAGSearchQuery): FrameRAGSearchResponse {
  let list = [...MOCK_VIDEO_FRAMES];
  if (params.modality && params.modality !== "all") {
    list = list.filter((f) => f.modality === params.modality);
  }
  if (params.investigation_slug && params.investigation_slug !== "all") {
    list = list.filter((f) => f.investigation_slug === params.investigation_slug);
  }
  if (params.query && params.query.trim().length > 0) {
    const q = params.query.toLowerCase();
    list = list.filter(
      (f) =>
        f.description.toLowerCase().includes(q) ||
        f.run_identifier.toLowerCase().includes(q) ||
        (f.ntrs_passage_excerpt && f.ntrs_passage_excerpt.toLowerCase().includes(q)) ||
        (f.optical_features.cool_flame_halo && q.includes("cool")) ||
        (f.optical_features.soot_present && q.includes("soot")) ||
        (f.modality && q.includes(f.modality))
    );
  }
  if (params.min_similarity) {
    list = list.filter((f) => (f.embedding_similarity ?? 1.0) >= params.min_similarity!);
  }
  const limit = params.limit || 12;
  const results = list.slice(0, limit);
  return {
    total: list.length,
    query: params.query || "",
    results,
  };
}

// ==========================================
// UPGRADE E-08: ACTIVE LEARNING BAYESIAN OED MOCK LOGIC
// ==========================================
export function computeMockOEDResponse(payload: OEDOptimizationRequest): OEDOptimizationResponse {
  const kappa = payload.kappa ?? 2.0;
  const axis = payload.varying_parameter || "pressure_kpa";
  const fixed = payload.fixed_parameters || {};
  const fixedP = fixed.pressure_kpa ?? 101.325;
  const fixedO2 = fixed.oxygen_pct ?? 21.0;
  const fixedV = fixed.ventilation_velocity_cm_s ?? 2.0;
  const fixedD = fixed.droplet_diameter_mm ?? 2.5;

  let minCoord = 40.0;
  let maxCoord = 150.0;
  if (axis === "oxygen_pct") {
    minCoord = 15.0;
    maxCoord = 40.0;
  } else if (axis === "ventilation_velocity_cm_s") {
    minCoord = 0.0;
    maxCoord = 20.0;
  } else if (axis === "droplet_diameter_mm") {
    minCoord = 1.0;
    maxCoord = 5.0;
  }

  const steps = 25;
  const curve_points: GPSurrogatePoint[] = [];

  for (let i = 0; i <= steps; i++) {
    const coord = Number((minCoord + (i / steps) * (maxCoord - minCoord)).toFixed(2));
    let mean = 0.85;
    let std = 0.12;

    if (axis === "pressure_kpa") {
      // D^2 burning rate scaling with pressure K ~ K0 * (1 + 0.0035 * P)
      mean = Number((0.65 + 0.0042 * coord + 0.04 * Math.sin(coord / 15)).toFixed(3));
      // Uncertainty higher at sub-atmospheric (<60) and high pressure (>130)
      const distFromCenter = Math.abs(coord - 101.3) / 50.0;
      std = Number((0.08 + 0.18 * distFromCenter * distFromCenter).toFixed(3));
    } else if (axis === "oxygen_pct") {
      // Spalding transfer number B logarithmic burning rate increase
      mean = Number((0.45 + 0.95 * Math.log(1 + coord / 18)).toFixed(3));
      const distFromAir = Math.abs(coord - 21.0) / 20.0;
      std = Number((0.06 + 0.22 * distFromAir * distFromAir).toFixed(3));
    } else if (axis === "ventilation_velocity_cm_s") {
      // Forced convection enhances burning rate K ~ K_0 * (1 + 0.3 * Re^0.5)
      mean = Number((0.72 + 0.12 * Math.sqrt(Math.max(0.1, coord))).toFixed(3));
      std = Number((0.09 + 0.015 * coord).toFixed(3));
    } else {
      // Droplet initial diameter (d-squared law K invariance with slight initial transient effect)
      mean = Number((0.88 - 0.02 * coord).toFixed(3));
      std = Number((0.07 + 0.05 * Math.abs(coord - 2.5)).toFixed(3));
    }

    const ucb = Number((mean + kappa * std).toFixed(3));
    const isObserved = i % 5 === 2;
    const observed_value = isObserved ? Number((mean + (Math.random() - 0.5) * 0.04).toFixed(3)) : null;

    curve_points.push({
      coordinate: coord,
      mean,
      std,
      ucb,
      observed_value,
    });
  }

  // Top candidate proposals targeting maximum information gain & UCB
  const top_proposals: OEDCandidateProposal[] = [
    {
      rank: 1,
      pressure_kpa: 142.5,
      oxygen_pct: 32.0,
      ventilation_velocity_cm_s: 4.5,
      droplet_diameter_mm: 3.2,
      predicted_mean: 1.342,
      epistemic_uncertainty: 0.285,
      ucb_score: Number((1.342 + kappa * 0.285).toFixed(3)),
      expected_information_gain_bits: 2.45,
      physical_rationale: "High-pressure oxygen-rich regime with severe lack of historical CIR trials. Maximizes epistemic entropy reduction on soot-cloud radiative quench boundary.",
    },
    {
      rank: 2,
      pressure_kpa: 48.0,
      oxygen_pct: 36.5,
      ventilation_velocity_cm_s: 1.2,
      droplet_diameter_mm: 4.0,
      predicted_mean: 1.055,
      epistemic_uncertainty: 0.248,
      ucb_score: Number((1.055 + kappa * 0.248).toFixed(3)),
      expected_information_gain_bits: 2.18,
      physical_rationale: "Hypobaric Artemis Gateway condition. Isolates cool-flame oscillatory re-ignition limits under 95% buoyant suppression.",
    },
    {
      rank: 3,
      pressure_kpa: 115.0,
      oxygen_pct: 18.0,
      ventilation_velocity_cm_s: 12.0,
      droplet_diameter_mm: 2.1,
      predicted_mean: 0.892,
      epistemic_uncertainty: 0.215,
      ucb_score: Number((0.892 + kappa * 0.215).toFixed(3)),
      expected_information_gain_bits: 1.94,
      physical_rationale: "Strong convective flow under hypoxia, mapping convective blow-off extinction boundary with microgravity droplet tether.",
    },
    {
      rank: 4,
      pressure_kpa: 62.0,
      oxygen_pct: 28.0,
      ventilation_velocity_cm_s: 0.0,
      droplet_diameter_mm: 4.8,
      predicted_mean: 0.945,
      epistemic_uncertainty: 0.198,
      ucb_score: Number((0.945 + kappa * 0.198).toFixed(3)),
      expected_information_gain_bits: 1.76,
      physical_rationale: "Large diameter quiescent droplet burning investigating internal liquid circulation and water absorption effects.",
    },
    {
      rank: 5,
      pressure_kpa: 130.0,
      oxygen_pct: 21.0,
      ventilation_velocity_cm_s: 16.5,
      droplet_diameter_mm: 1.5,
      predicted_mean: 1.180,
      epistemic_uncertainty: 0.182,
      ucb_score: Number((1.180 + kappa * 0.182).toFixed(3)),
      expected_information_gain_bits: 1.62,
      physical_rationale: "High-Reynolds boundary layer thinning test verifying Spalding transfer correlation at high chamber pressure.",
    },
  ];

  return {
    acquisition_function: "UCB",
    kappa,
    varying_axis: axis,
    curve_points,
    top_proposals,
    surrogate_stats: {
      total_training_runs: 300,
      length_scales: {
        pressure_kpa: 22.4,
        oxygen_pct: 5.2,
        ventilation_velocity_cm_s: 3.8,
        droplet_diameter_mm: 0.85,
      },
      variance_reduction_pct: 68.4,
      r2_score: 0.942,
    },
  };
}

// ==========================================
// UPGRADE E-10: EXPLORATION ATMOSPHERE FIRE HAZARD (EAFHI) MOCK LOGIC
// ==========================================
export function calculateMockEAFHI(payload: EAFHIEnvironmentInput): EAFHIResult {
  const g_eff = Math.max(1e-6, payload.gravity_g);
  const P = Math.max(10.0, payload.pressure_kpa);
  const X_O2 = Math.max(5.0, payload.oxygen_pct);
  const V_vent = Math.max(0.0, payload.ventilation_velocity_cm_s);
  const L = payload.characteristic_length_m || 0.05;

  // Material standard 1g Limiting Oxygen Index (LOI) per NASA-STD-6001B
  const matLoiMap: Record<string, number> = {
    pmma: 17.5,
    nomex: 29.0,
    delrin: 15.0,
    polycarbonate: 26.0,
    teflon: 95.0,
    kevlar: 29.5,
  };
  const loi = matLoiMap[payload.material_key?.toLowerCase()] ?? 18.0;

  // Thermodynamic properties: Ideal gas density and Sutherland viscosity
  const T_inf = 294.15; // 21 C ambient
  const T_flame = 1800.0; // Typical polymer flame temperature
  const deltaT = T_flame - T_inf;
  const beta = 1.0 / T_inf;
  const R_air = 287.05; // J/(kg*K)
  const rho = (P * 1000.0) / (R_air * T_inf);
  const mu = 1.82e-5 * Math.pow(T_inf / 291.15, 1.5) * ((291.15 + 120.0) / (T_inf + 120.0));
  const nu = mu / Math.max(0.01, rho);

  // Grashof number: Gr = g * beta * DeltaT * L^3 / nu^2
  const g_accel = g_eff * 9.80665;
  const grashof_number = (g_accel * beta * deltaT * Math.pow(L, 3)) / Math.max(1e-12, nu * nu);

  // 1g Earth sea-level Grashof baseline: g=1.0, P=101.325 kPa
  const rho_1g = (101325.0) / (R_air * T_inf);
  const nu_1g = mu / rho_1g;
  const grashof_1g = (9.80665 * beta * deltaT * Math.pow(L, 3)) / Math.max(1e-12, nu_1g * nu_1g);
  const grashof_ratio_to_1g = Number((grashof_number / Math.max(1.0, grashof_1g)).toFixed(5));

  // Buoyancy factor: in reduced g, buoyant convective cooling drops, but oxygen transport also drops.
  // When forced ventilation is low (<5 cm/s), low g suppresses convective removal, leading to high local residence time.
  const buoyancy_factor_phi = Number(Math.max(0.05, Math.min(1.0, Math.pow(grashof_ratio_to_1g, 0.333))).toFixed(4));

  // Minimum Extinguishing Oxygen Concentration (MOC) under hypobaric & reduced g
  // MOC drops (flammability increases) with oxygen enrichment and moderate decompression
  const pressureFactor = Math.pow(101.325 / P, 0.18);
  const gravityCompensation = 1.0 - 0.12 * (1.0 - Math.min(1.0, g_eff));
  const minimum_extinguishing_o2_pct = Number((loi * pressureFactor * gravityCompensation).toFixed(2));
  const oxygen_margin_pct = Number((X_O2 - minimum_extinguishing_o2_pct).toFixed(2));

  // Deterministic EAFHI score calculation strictly clamped to [0.0, 1.0]
  // Factors:
  // 1. Oxygen enrichment ratio (X_O2 / 20.95)
  // 2. Hypobaric enhancement (56.5 kPa / P)^0.35
  // 3. Buoyant convection suppression factor
  const oxygenRatio = X_O2 / Math.max(10.0, minimum_extinguishing_o2_pct);
  const pressureTerm = Math.pow(101.325 / P, 0.4);
  const ventTerm = 1.0 + (V_vent > 0 ? Math.min(0.3, V_vent * 0.015) : -0.1);

  let raw_score = 0.52 * oxygenRatio + 0.28 * (pressureTerm - 1.0) * 0.5 + 0.20 * (1.0 - buoyancy_factor_phi) * ventTerm;
  if (X_O2 < minimum_extinguishing_o2_pct) {
    raw_score = raw_score * 0.45; // Sub-MOC extinguishment suppression
  }
  const risk_score = Number(Math.max(0.02, Math.min(0.98, raw_score)).toFixed(3));

  let classification: FlammabilityRiskClass = "low";
  let flammability_status: "SELF_EXTINGUISHING" | "MARGINAL_PROPAGATION" | "VIGOROUS_COMBUSTION" | "ACCELERATED_FLASHOVER" = "SELF_EXTINGUISHING";
  let eva_status: "AUTHORIZED" | "RESTRICTED" | "LOCKDOWN" = "AUTHORIZED";

  if (risk_score < 0.35) {
    classification = "low";
    flammability_status = "SELF_EXTINGUISHING";
    eva_status = "AUTHORIZED";
  } else if (risk_score < 0.65) {
    classification = "moderate";
    flammability_status = "MARGINAL_PROPAGATION";
    eva_status = "AUTHORIZED";
  } else if (risk_score < 0.85) {
    classification = "high";
    flammability_status = "VIGOROUS_COMBUSTION";
    eva_status = "RESTRICTED";
  } else {
    classification = "critical";
    flammability_status = "ACCELERATED_FLASHOVER";
    eva_status = "LOCKDOWN";
  }

  const oxygen_enrichment_pct = Number((Math.max(0, (X_O2 - 20.95) / 20.95) * 100).toFixed(1));
  const hypobaric_decompression_pct = Number((Math.max(0, (101.325 - P) / 101.325) * 100).toFixed(1));
  const buoyancy_suppression_pct = Number(((1.0 - grashof_ratio_to_1g) * 100).toFixed(1));

  return {
    risk_score,
    classification,
    grashof_number: Number(grashof_number.toExponential(4)),
    grashof_ratio_to_1g,
    buoyancy_factor_phi,
    minimum_extinguishing_o2_pct,
    oxygen_margin_pct,
    flammability_status,
    risk_contributions: {
      oxygen_enrichment_pct,
      hypobaric_decompression_pct,
      buoyancy_suppression_pct,
    },
    operational_protocol: {
      eva_status,
      suppression_recommendation:
        risk_score >= 0.65
          ? "Pre-stage fine water mist and CO2 extinguisher canisters at airlock ingress. Flammability exceeds nominal cabin baseline."
          : "Standard portable fire extinguisher (PFE) coverage nominal. Atmosphere within permissible containment envelope.",
      ventilation_adjustment_advice:
        risk_score >= 0.65
          ? "Maintain active cabin cross-ventilation above 5 cm/s to prevent stagnant oxygen pooling in sleeping and avionics bays."
          : "Nominal cabin airflow (3-5 cm/s) sufficient for atmospheric mixing.",
    },
  };
}

export function computeMockEAFHISensitivity(
  parameter: "oxygen_pct" | "pressure_kpa" | "gravity_g" | "ventilation_velocity_cm_s",
  current: EAFHIEnvironmentInput
): EAFHISensitivityResponse {
  let minVal = 15.0;
  let maxVal = 45.0;
  if (parameter === "pressure_kpa") {
    minVal = 40.0;
    maxVal = 110.0;
  } else if (parameter === "gravity_g") {
    minVal = 0.01;
    maxVal = 1.5;
  } else if (parameter === "ventilation_velocity_cm_s") {
    minVal = 0.0;
    maxVal = 30.0;
  }

  const steps = 15;
  const curve: SensitivityCurvePoint[] = [];

  for (let i = 0; i <= steps; i++) {
    const val = Number((minVal + (i / steps) * (maxVal - minVal)).toFixed(2));
    const inputCopy: EAFHIEnvironmentInput = { ...current };

    if (parameter === "oxygen_pct") inputCopy.oxygen_pct = val;
    else if (parameter === "pressure_kpa") inputCopy.pressure_kpa = val;
    else if (parameter === "gravity_g") inputCopy.gravity_g = val;
    else if (parameter === "ventilation_velocity_cm_s") inputCopy.ventilation_velocity_cm_s = val;

    const res = calculateMockEAFHI(inputCopy);
    curve.push({
      parameter_value: val,
      risk_score: res.risk_score,
      moc_pct: res.minimum_extinguishing_o2_pct,
      grashof_ratio: res.grashof_ratio_to_1g,
      classification: res.classification,
    });
  }

  const current_operating_point = calculateMockEAFHI(current);

  return {
    swept_parameter: parameter,
    curve,
    current_operating_point,
  };
}

// ==========================================
// UPGRADE E-02: WAVELET JITTER FILTER SIMULATION
// ==========================================

const DB4_H = [
  (1 + Math.sqrt(3)) / (4 * Math.sqrt(2)),
  (3 + Math.sqrt(3)) / (4 * Math.sqrt(2)),
  (3 - Math.sqrt(3)) / (4 * Math.sqrt(2)),
  (1 - Math.sqrt(3)) / (4 * Math.sqrt(2)),
];
const DB4_G = [DB4_H[3], -DB4_H[2], DB4_H[1], -DB4_H[0]];

export function computeMockWaveletFilter(req: WaveletFilterRequest): WaveletFilterResponse {
  const raw = req.raw_signal || [];
  const level = req.decomposition_level ?? 4;
  const thresholdG = req.threshold_g ?? 1.0e-4;
  const mode = req.threshold_mode || "soft";

  if (raw.length === 0) {
    return {
      wavelet: "db4",
      decomposition_level: level,
      raw_signal: [],
      filtered_signal: [],
      detail_coefficients: [],
      snr_enhancement_db: 0.0,
      peak_reduction_pct: 0.0,
      quiescent_micro_g_achieved: true,
      raw_grashof_peak: 0.0,
      filtered_grashof_peak: 0.0,
      buoyant_perturbation_flag: false,
    };
  }

  // Ensure even length for dyadic decomposition
  const n = raw.length % 2 === 0 ? raw.length : raw.length - 1;
  const currentSignal = raw.slice(0, n);

  // Multi-level forward DWT
  let approx = [...currentSignal];
  const detailLevels: number[][] = [];

  for (let l = 0; l < level; l++) {
    const len = approx.length;
    if (len < 4) break;
    const half = Math.floor(len / 2);
    const nextApprox: number[] = new Array(half);
    const detail: number[] = new Array(half);

    for (let i = 0; i < half; i++) {
      let a = 0;
      let d = 0;
      for (let k = 0; k < 4; k++) {
        const idx = (2 * i + k) % len;
        a += approx[idx] * DB4_H[k];
        d += approx[idx] * DB4_G[k];
      }
      nextApprox[i] = a;
      // Soft or hard thresholding on detail
      if (mode === "hard") {
        detail[i] = Math.abs(d) > thresholdG ? d : 0;
      } else {
        const sign = d >= 0 ? 1 : -1;
        detail[i] = Math.abs(d) > thresholdG ? sign * (Math.abs(d) - thresholdG) : 0;
      }
    }
    detailLevels.push(detail);
    approx = nextApprox;
  }

  // Multi-level inverse DWT (IDWT)
  let recon = [...approx];
  for (let l = detailLevels.length - 1; l >= 0; l--) {
    const detail = detailLevels[l];
    const half = recon.length;
    const fullLen = half * 2;
    const reconstructed: number[] = new Array(fullLen).fill(0);

    for (let i = 0; i < half; i++) {
      for (let k = 0; k < 4; k++) {
        const idx = (2 * i + k) % fullLen;
        reconstructed[idx] += recon[i] * DB4_H[k] + detail[i] * DB4_G[k];
      }
    }
    recon = reconstructed;
  }

  const filtered = [...recon];
  if (raw.length > n) {
    filtered.push(filtered[filtered.length - 1] ?? 0);
  }

  // Calculate metrics
  let rawPower = 0;
  let noisePower = 0;
  let rawPeak = 0;
  let filteredPeak = 0;

  for (let i = 0; i < raw.length; i++) {
    const r = raw[i];
    const f = filtered[i] ?? 0;
    const err = r - f;
    rawPower += r * r;
    noisePower += err * err;
    if (Math.abs(r) > rawPeak) rawPeak = Math.abs(r);
    if (Math.abs(f) > filteredPeak) filteredPeak = Math.abs(f);
  }

  const snr = noisePower > 1e-18 ? 10 * Math.log10(rawPower / noisePower) : 21.4;
  const peakRed = rawPeak > 0 ? Math.max(0, ((rawPeak - filteredPeak) / rawPeak) * 100) : 98.7;

  const grFactor = (9.81 * (1 / 300) * 1500 * Math.pow(0.003, 3)) / Math.pow(1.5e-5, 2);
  const rawGrashof = rawPeak * grFactor;
  const filteredGrashof = filteredPeak * grFactor;

  return {
    wavelet: "db4",
    decomposition_level: level,
    raw_signal: raw,
    filtered_signal: filtered,
    detail_coefficients: detailLevels,
    snr_enhancement_db: Number(snr.toFixed(2)),
    peak_reduction_pct: Number(peakRed.toFixed(1)),
    quiescent_micro_g_achieved: filteredPeak <= 1e-5,
    raw_grashof_peak: Number(rawGrashof.toFixed(4)),
    filtered_grashof_peak: Number(filteredGrashof.toFixed(6)),
    buoyant_perturbation_flag: rawGrashof > 0.1,
    wavelet_power_spectrum: {
      "d1_high_freq": 0.42,
      "d2_harmonics": 0.31,
      "d3_exercise": 0.22,
      "d4_structural": 0.04,
      "a4_quiescent": 0.01,
    },
  };
}

// ==========================================
// UPGRADE E-11: SILENT COOL-FLAME REKINDLING SIMULATION
// ==========================================

interface LTCFuelInfo {
  formula: string;
  supports_ltc: boolean;
  flash_k: number;
  A: number;
  E: number;
}

const LTC_CATALOG: Record<string, LTCFuelInfo> = {
  "n-heptane": { formula: "C7H16", supports_ltc: true, flash_k: 269.15, A: 8.5e6, E: 65000 },
  "heptane": { formula: "C7H16", supports_ltc: true, flash_k: 269.15, A: 8.5e6, E: 65000 },
  "n-octane": { formula: "C8H18", supports_ltc: true, flash_k: 286.15, A: 9.1e6, E: 67000 },
  "octane": { formula: "C8H18", supports_ltc: true, flash_k: 286.15, A: 9.1e6, E: 67000 },
  "n-decane": { formula: "C10H22", supports_ltc: true, flash_k: 319.15, A: 1.05e7, E: 70000 },
  "decane": { formula: "C10H22", supports_ltc: true, flash_k: 319.15, A: 1.05e7, E: 70000 },
  "methanol": { formula: "CH3OH", supports_ltc: false, flash_k: 284.15, A: 0, E: 0 },
  "ethanol": { formula: "C2H5OH", supports_ltc: false, flash_k: 286.15, A: 0, E: 0 },
};

export function computeMockRekindleRisk(req: RekindleRiskRequest): RekindleRiskResponse {
  const fuelName = (req.fuel_type || req.fuel || "n-heptane").toLowerCase().trim();
  const fuelInfo = LTC_CATALOG[fuelName] || {
    formula: "Hydrocarbon",
    supports_ltc: true,
    flash_k: 270.0,
    A: 8.0e6,
    E: 66000,
  };

  const tempK = req.fuel_temperature_k;
  const isFlameActive = req.visible_flame_active ?? false;
  const pressureKpa = req.chamber_pressure_kpa ?? 101.325;
  const o2Pct = req.oxygen_percentage ?? req.ambient_o2_percentage ?? 21.0;

  let uVent = 0.05;
  if (req.ventilation_velocity_m_s !== undefined) {
    uVent = req.ventilation_velocity_m_s;
  } else if (req.ventilation_velocity_cm_s !== undefined) {
    uVent = req.ventilation_velocity_cm_s / 100.0;
  }

  let charLen = 0.003;
  if (req.characteristic_length_m !== undefined) {
    charLen = req.characteristic_length_m;
  } else if (req.droplet_diameter_mm !== undefined) {
    charLen = req.droplet_diameter_mm / 1000.0;
  }

  const tauRes = charLen / Math.max(0.0001, uVent);
  let kLtc = 0;
  let daCool = 0;

  if (fuelInfo.supports_ltc && tempK > 350) {
    const R = 8.314;
    kLtc = fuelInfo.A * Math.exp(-fuelInfo.E / (R * tempK)) * (pressureKpa / 101.325) * (o2Pct / 21.0);
    daCool = tauRes * kLtc;
  }

  const daCrit = 1.0;
  const theta = 0.20;
  let pRekindle = 0.0;
  let riskLevel: RekindleRiskLevel = "INERT";

  if (!fuelInfo.supports_ltc || tempK <= fuelInfo.flash_k) {
    pRekindle = 0.0;
    riskLevel = "INERT";
  } else {
    const exponent = -(daCool - daCrit) / theta;
    pRekindle = 1.0 / (1.0 + Math.exp(Math.max(-50, Math.min(50, exponent))));
    if (pRekindle < 0.15 || daCool < 0.5) {
      riskLevel = "MONITOR";
    } else if (pRekindle < 0.70 || daCool < 1.0) {
      riskLevel = "REKINDLE_WARNING";
    } else {
      riskLevel = "CRITICAL_REKINDLE_HAZARD";
    }
  }

  const critVent = (charLen * kLtc) / daCrit;
  const recVentCmS = Number((critVent * 100.0).toFixed(1));

  let advisory = "";
  switch (riskLevel) {
    case "INERT":
      advisory = "Droplet temperature below flash point or fuel does not support low-temperature chain branching. Zero rekindle hazard.";
      break;
    case "MONITOR":
      advisory = "Droplet temperature above flash point but convective cooling suppresses cool-flame radical accumulation (Da_cool < 0.5). Maintain photodiode telemetry.";
      break;
    case "REKINDLE_WARNING":
      advisory = "Cool flame active with elevated peroxy radical concentrations (0.5 <= Da_cool < 1.0). Prepare chamber isolation damper.";
      break;
    case "CRITICAL_REKINDLE_HAZARD":
      advisory = "CRITICAL: Silent cool-flame self-heating exceeds convective heat removal (Da_cool >= 1.0, P_rekindle >= 85%). Immediate cabin ventilation damper isolation recommended.";
      break;
  }

  return {
    fuel_type: fuelName,
    fuel: fuelName,
    visible_flame_active: isFlameActive,
    cool_flame_active: fuelInfo.supports_ltc && tempK > 450 && daCool > 0.4,
    fuel_temperature_k: Number(tempK.toFixed(1)),
    flash_point_k: fuelInfo.flash_k,
    cool_flame_damkohler: Number(daCool.toFixed(3)),
    damkohler_cool: Number(daCool.toFixed(3)),
    critical_damkohler: daCrit,
    damkohler_crit: daCrit,
    rekindle_probability: Number(pRekindle.toFixed(4)),
    risk_level: riskLevel,
    risk_classification: riskLevel,
    safety_advisory: advisory,
    advisory_message: advisory,
    recommended_ventilation_cm_s: recVentCmS,
    critical_ventilation_velocity_m_s: Number(critVent.toFixed(3)),
  };
}

export function generateMockTelemetryFrame(
  sequence: number,
  override?: Partial<CCSDSTelemetryFrame>
): CCSDSTelemetryFrame {
  const t = sequence * 0.05;
  const lat = Number((51.6 * Math.sin(t * 0.005)).toFixed(4));
  const lon = Number((((t * 0.04) % 360) - 180).toFixed(4));
  const altitude = Number((418.4 + 0.35 * Math.cos(t * 0.002)).toFixed(2));
  const rawJitter = 1.2e-6 + 0.8e-6 * Math.sin(t * 12.0) + (Math.random() - 0.5) * 0.4e-6;

  return {
    packet_id: `CCSDS-ISS-CIR-${String(sequence).padStart(6, "0")}`,
    timestamp_utc: new Date().toISOString(),
    sequence_count: sequence % 16384,
    iss_latitude: lat,
    iss_longitude: lon,
    iss_altitude_km: altitude,
    chamber_pressure_kpa: 101.32,
    ambient_temperature_k: 298.15,
    acceleration_raw_g: rawJitter,
    acceleration_filtered_g: 1.2e-6,
    radiometer_flux_w: 0.0,
    ch_star_chemiluminescence_v: 0.04,
    ventilation_velocity_cm_s: 3.0,
    packet_loss_pct: 0.0,
    sync_lock: true,
    ...override,
  };
}


