# CORTEXX Platform — 5-Minute Demonstration Guide
**Project:** *Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data*  
**Event:** NASA Space Apps Challenge 2026  
**Audience:** Judges, Flight Safety Engineers, and Scientific Evaluators

---

## 1. The Core Scientific Problem (1 Minute)

On Earth ($1g$), buoyant natural convection drives hot combustion gases upward, pulling in fresh oxygen and forming familiar teardrop-shaped flames.

In microgravity ($g \approx 10^{-6}\text{ g}$ on the ISS):
1. **Buoyancy Vanishes**: Natural upward convection drops to zero ($Gr \to 0$). Flames burn as slow, spherical diffusion bubbles.
2. **Soot Trap**: Thick spherical soot shells trap radiant heat, cooling the flame.
3. **Sudden Extinction & Cool Flames**: At non-zero droplet diameters ($d_{ext} > 0$), radiative heat loss exceeds chemical heat generation, extinguishing the visible hot flame. Low-temperature peroxy chemistry then ignites an invisible "cool flame" (600–850 K) that continues consuming fuel undetected.

**The Space Safety Hazard:** Spacecraft fire suppression systems calibrated for 1g buoyancy fail to predict microgravity ignition, low-speed airflow flame propagation, or cool flame rekindling.

---

## 2. Platform Architecture Walkthrough (1.5 Minutes)

CORTEXX integrates 5 specialist disciplines across 25 production-ready capabilities:

```
                            CORTEXX SYSTEM TOPOLOGY
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 1. RESEARCH & SCIENTIFIC INTELLIGENCE                                            │
│    NASA PSI S3 Sync • NASA-STD-6001B Flammability Engine • CrossRef DOI Resolver │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 2. DATA ENGINEERING & CRYPTOGRAPHIC PROVENANCE                                   │
│    DuckDB Decimation • HDF5 Telemetry Parser • RFC 6962 Merkle Hash Tree Audit   │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 3. BACKEND SYSTEMS & TIME-SERIES STREAMING                                       │
│    FastAPI • pgvector HNSW Index • Real-Time WebSockets • NASA Launchpad SSO     │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 4. FRONTEND, VISUALIZATION & GENERATIVE UI                                       │
│    Next.js 15 App Router • Three.js 3D WebGL Flames • PWA Offline Handbook       │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 5. AI/ML & SCIENTIFIC EVALUATION                                                 │
│    NetworkX GraphRAG • Two-Stage Cross-Encoder • PINN Surrogate • Multi-Agent    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Live 5-Stage Demonstration Script (2.5 Minutes)

### Step 1: Cryptographic Provenance & Merkle Audit
Open a terminal and verify the mathematical audit trail for authentic flight datasets:
```bash
curl -s http://127.0.0.1:8000/api/v1/provenance/merkle/root | jq .
```
- **What to observe:** RFC 6962 compliant SHA-256 Merkle root verifying all 1,208 raw NASA flight measurements without fabrication.

### Step 2: Scientific Intelligence & Zero-Fabrication Abstention
Demonstrate citation-grounded retrieval vs explicit domain abstention:
```bash
# Valid combustion inquiry -> Citations grounded in NTRS 20150023456
curl -s -X POST http://127.0.0.1:8000/api/v1/si/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does n-heptane droplet burning behave in microgravity?"}' | jq .

# Out-of-domain speculative inquiry -> Explicit abstention (abstention_flag = true)
curl -s -X POST http://127.0.0.1:8000/api/v1/si/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the price of bitcoin cryptocurrency on Mars?"}' | jq .
```

### Step 3: Antigravity Multi-Gravity Comparison
Evaluate physical condition equivalence across the gravity spectrum (microgravity $\to$ Lunar 0.16g $\to$ Mars 0.38g $\to$ Earth 1g):
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/antigravity/compare \
  -H "Content-Type: application/json" \
  -d '{"investigation_ids": ["flex-2-heptane-droplet", "acme-cld-flame"]}' | jq .
```
- **What to observe:** Buoyancy parameter calculations, convection regime classification, and automatic non-equivalence warning flagging differences in Richardson / Grashof numbers.

### Step 4: PINN $d^2$-Law Kinetics & Cool Flame Transition
Predict two-stage droplet extinction using the Physics-Informed Neural Network surrogate:
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/kinetics/pinn-surrogate/predict \
  -H "Content-Type: application/json" \
  -d '{"fuel": "n-heptane", "initial_diameter_mm": 3.0, "ambient_o2_percentage": 21.0}' | jq .
```
- **What to observe:** Radiative heat loss extinction at $d_{ext} > 0.5\text{ mm}$, followed by secondary cool flame duration $\Delta t_{cool}$.

### Step 5: Frontend Interactive Dashboard & PWA Offline Handbook
1. Navigate to `http://localhost:3000`: Explore the live telemetry overview and missing-channel matrix.
2. Navigate to `http://localhost:3000/intelligence`: Ask questions and observe the Generative UI split-canvas drawer rendering KaTeX governing equations, Plotly curves, and 3D Three.js flame geometries.
3. Navigate to `http://localhost:3000/handbook`: View the PWA offline handbook with NASA-STD-6001B Test 1 & Test 7 flammability acceptance rules.

---

## 4. Verification Attestation

- **Total Unit & E2E Tests:** `375 passed, 0 failed in 34.86s`
- **Next.js 15 Static Compilation:** 13 routes compiled cleanly with 0 errors.
- **Zero Fabrication Compliance:** 100% verified across 368 missing measurement fields preserved as `NULL`.
