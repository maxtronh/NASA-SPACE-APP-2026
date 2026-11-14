# NASA SPACE APP 2026 - System Architecture & Pipeline Flow Diagrams

This document contains Mermaid diagrams capturing the project task workflows, architecture components, and scientific pipelines for **Flame in Freefall**.

For the detailed pipeline specifications, refer to [PIPELINE_FLOW_DIAGRAMS.md](docs/PIPELINE_FLOW_DIAGRAMS.md).

---

## Diagram 1: Complete Project Task Workflow

```mermaid
graph TD
    classDef agent fill:#e94560,color:#f1f1f1,stroke:#f1f1f1,stroke-width:2;
    classDef phase fill:#16213e,color:#f1f1f1,stroke:#e94560;
    
    P1[Phase 1: Backend Foundation]:::phase
    P1 --> T1[Create backend/app/core/gravity.py]
    P1 --> T2[Update schemas/compare.py]
    P1 --> T3[Update ml/entity_extractor.py]
    
    P2[Phase 2: Services]:::phase
    P2 --> T4[Update investigation_service.py]
    P2 --> T5[Update comparison_service.py]
    P2 --> T6[Create antigravity_service.py]
    
    P3[Phase 3: API]:::phase
    P3 --> T7[Create endpoints/antigravity.py]
    P3 --> T8[Update router.py]
    
    P4[Phase 4: Data & Seed]:::phase
    P4 --> T9[Update seed_data.py]
    P4 --> T10[Update PROJECT.md]
    
    P5[Phase 5: Frontend]:::phase
    P5 --> T11[Update types/index.ts]
    P5 --> T12[Update lib/api.ts]
    P5 --> T13[Create GravityRegimeBadge.tsx]
    P5 --> T14[Create AntigravityWarning.tsx]
    P5 --> T15[Create antigravity/page.tsx]
    P5 --> T16[Update Navbar.tsx]
    P5 --> T17[Update investigations/page.tsx]
    P5 --> T18[Update compare/page.tsx]
    
    P6[Phase 6: Testing]:::phase
    P6 --> T19[Run frontend build]
    P6 --> T20[Create backend/tests/test_antigravity.py]
    P6 --> T21[Create tests/e2e/test_tier1_antigravity.py]
    P6 --> T22[Create tests/e2e/test_tier4_antigravity_journey.py]
    P6 --> T23[Update conftest.py]
    P6 --> T24[Update test_tier3_cross_feature.py]
    
    P7[Phase 7: Finalization]:::phase
    P7 --> T25[Run full test suite]
    P7 --> T26[Update README.md]
    P7 --> T27[Commit all changes]
```

---

## Diagram 2: Backend Architecture

```mermaid
graph TB
    classDef api fill:#0f3460,color:#f1f1f1,stroke:#e94560;
    classDef service fill:#16213e,color:#f1f1f1,stroke:#e94560;
    classDef core fill:#085d7e,color:#f1f1f1,stroke:#e94560;
    classDef db fill:#06d6a0,color:#1a1a2e,stroke:#e94560;
    classDef model fill:#7f9cf5,color:#1a1a2e,stroke:#e94560;
    
    app[FastAPI App app/main.py]:::api
    config[Core Config app/core/config.py]:::core
    gravity[Gravity Module app/core/gravity.py]:::core
    session[DB Session app/db/session.py]:::core
    compare[Comparison Service]:::service
    antigravity[Antigravity Service]:::service
    seed[Seed Data Service]:::service
    entity[ML Entity Extractor]:::service
    
    antigw_endpoint[API: /api/v1/antigravity/compare]:::api
    cmp_endpoint[API: /api/v1/compare]:::api
    
    inv_model[Investigation Model]:::model
    cmp_model[Comparison Model]:::model
    ant_model[Antigravity Model]:::model
    
    pg_db[(PostgreSQL + pgvector)]:::db
    
    app --> config & gravity & session & compare & antigravity & seed & entity
    config --> pg_db
    session --> pg_db
    
    compare --> inv_model & pg_db
    antigravity --> inv_model & cmp_model & pg_db
    entity --> inv_model
    
    antigw_endpoint --> app
    cmp_endpoint --> app
```

---

## Diagram 3: Frontend Architecture

```mermaid
graph TD
    classDef page fill:#0f3460,color:#f1f1f1,stroke:#e94560;
    classDef component fill:#16213e,color:#f1f1f1,stroke:#e94560;
    classDef lib fill:#085d7e,color:#f1f1f1,stroke:#e94560;
    classDef type fill:#7f9cf5,color:#1a1a2e,stroke:#e94560;
    
    home[Home Page /]:::page
    investigations[Investigations /investigations]:::page
    compare[Compare /compare]:::page
    antigravity[Antigravity /antigravity]:::page
    analytics[Analytics /analytics]:::page
    intelligence[Intelligence /intelligence]:::page
    
    navbar[Navbar components/Navbar.tsx]:::component
    scientific_chart[ScientificChart]:::component
    provenance[ProvenanceCard components/ProvenanceCard.tsx]:::component
    generative_art[GenerativeArtifacts]:::component
    gravity_badge[GravityRegimeBadge]:::component
    antigravity_warning[AntigravityWarning]:::component
    
    api_client[API Client lib/api.ts]:::lib
    types[TypeScript Types src/types/index.ts]:::type
    
    home --> navbar & scientific_chart
    investigations --> navbar & provenance
    compare --> navbar & gravity_badge & antigravity_warning
    antigravity --> navbar & gravity_badge & antigravity_warning
    analytics --> navbar
    intelligence --> navbar
    
    navbar --> api_client
    scientific_chart --> api_client
    antigravity --> api_client
    gravity_badge --> api_client
    antigravity_warning --> api_client
    
    api_client --> types
    gravity_badge --> types
    antigravity_warning --> types
```

---

## Diagram 4: Docker & Deployment Architecture

```mermaid
graph LR
    classDef service fill:#16213e,color:#f1f1f1,stroke:#e94560;
    classDef db fill:#06d6a0,color:#1a1a2e,stroke:#e94560;
    classDef network fill:#0f3460,color:#f1f1f1,stroke:#e94560;
    
    frontend[Frontend Next.js 15]:::service
    backend[Backend FastAPI]:::service
    database[Database PostgreSQL 16 + pgvector]:::db
    
    net[Network flame_net bridge]:::network
    pg_vol[(Volume pg_data)]:::db
    
    frontend -->|depends on| backend
    backend -->|depends on| database
    frontend -->|network: flame_net| net
    backend -->|network: flame_net| net
    database -->|network: flame_net| net
    database --- pg_vol
```

---

## Diagram 5: Gravity Level Classification Taxonomy

```mermaid
graph TD
    classDef gravity fill:#16213e,color:#f1f1f1,stroke:#e94560;
    classDef enum fill:#0f3460,color:#f1f1f1,stroke:#e94560;
    
    subgraph GravityLevels["Gravity Level Taxonomy (GravityLevel Enum)"]
        direction TB
        MICRO["microgravity (~10^-6 g)<br/>ISS CIR, Drop Towers"]:::gravity
        LUNAR["lunar_gravity (0.16 g)<br/>Artemis Lunar Gateway"]:::gravity
        MARS["mars_gravity (0.38 g)<br/>Mars Surface Habitats"]:::gravity
        NORMAL["normal_gravity (1.0 g)<br/>Terrestrial Baseline Labs"]:::gravity
        HYPER2["hypergravity_2g (2.0 g)<br/>Centrifuge Facilities"]:::gravity
        HYPER5["hypergravity_5g (5.0 g)<br/>Extreme Acceleration Tests"]:::gravity
    end
```
