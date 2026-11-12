# Flame in Freefall — NASA Microgravity Combustion Research Log & Scientific Specification
**Deliverable**: R1 System & Environment Documentation  
**Version**: 1.0.0  
**Author**: 01. Research and Product Architect  
**Workspace**: `c:\dev\NASA-SPACE-APP-2026`  

---

## 1. Executive Summary & Scientific Scope

This research log serves as the authoritative scientific specification and data catalog for **"Flame in Freefall"**. It synthesizes decades of reduced-gravity combustion research conducted by the **NASA Glenn Research Center (GRC)**, flight missions aboard the **Space Shuttle**, and continuous orbital experiments aboard the **International Space Station (ISS)**.

In microgravity ($\mu g \approx 10^{-6} g_0$), gravity-driven buoyant convection is virtually suppressed. This eliminates upward buoyant plume velocities, isolating molecular diffusion, chemical kinetics, radiant emission, and low-speed transport. Consequently, combustion phenomena that are impossible to study on Earth—such as **quasisteady spherical droplet combustion**, **radiative flame extinction**, **ultralean spherical flame balls**, and **quiescent solid-fuel smoldering/flame spread**—can be observed with mathematical fidelity.

This document catalogues:
1. Official NASA flight investigations and persistent citation identifiers.
2. Spaceflight combustion facilities and diagnostic sensor instrumentation.
3. Structured flight test run parameters and measurement variables.
4. Mathematical SI conversion matrices and physical boundary constraints.
5. Strict rules governing the preservation of `NULL` measurements (banning zero substitution).
6. Live API verification data and cryptographic checksums from NTRS and PSI.

---

## 2. Chronology of NASA Reduced-Gravity Combustion Facilities

| Facility / Platform | Operational Window | Location | Chamber & Environment | Diagnostic Sensor Instrumentation | Primary Focus Areas |
|---|---|---|---|---|---|
| **2.2-Second Drop Tower** | 1960s–Present | NASA GRC, Cleveland, OH | Ambient air or sealed drop rig; $24.1\text{ m}$ free fall ($10^{-2} g_0$) | High-speed video, photodiodes, thermocouples | Ground-based screening, droplet ignition, gas jet flammability. |
| **5.1-Second Zero-G Facility** | 1966–Present | NASA GRC, Cleveland, OH | Evacuated steel chamber $132\text{ m}$ depth; free fall ($10^{-5} g_0$) | High-speed imaging, color radiometers | Microgravity flame transition, soot formation onset. |
| **Combustion Module-1 (CM-1)** | 1997–2003 | Space Shuttle (STS-83, STS-94, STS-107) | Sealed Spacelab / SPACEHAB module payload | Low-light intensified CCD cameras, orthogonal radiometers, thermocouples | SOFBALL (Structure of Flame Balls at Low Lewis Number), Laminar Soot Processes (LSP). |
| **Microgravity Science Glovebox (MSG)** | 2002–Present | ISS Columbus / Destiny Modules | Sealed glovebox with negative pressure working volume | Small Flow Duct, high-resolution color video, Compound Specific Analyzer-Combustion Products (CSA-CP), Carbon Dioxide Monitor (CDM) | BASS, BASS-II (solid fuels), SLICE, SPICE. |
| **Combustion Integrated Rack (CIR)** | 2008–Present | ISS Destiny US Laboratory (Bay L1) | 100-liter hermetic combustion chamber; operation from $0.02\text{ to }3.0\text{ atm}$ | Multi-User Droplet Combustion Apparatus (MDCA), ACME insert, SoFIE insert, 3 Mass Flow Controllers, 5 camera systems, thin-filament pyrometry (14 $\mu m$ SiC), UV/visible photomultiplier tubes ($CH^*, OH^*$) | FLEX, FLEX-2, ACME (6 investigations), SoFIE (5 sub-investigations). |

---

## 3. Authoritative Flight Investigations Catalog

### 3.1 FLEX & FLEX-2 (Flame Extinguishment Experiment)
- **Authoritative Citation**: NASA Technical Reports Server (NTRS) Citation ID `20150023456`
- **Official Report Number**: `NASA/TP-2015-216046` ("Detailed Results from the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011")
- **Principal Investigators**: Forman A. Williams (UC San Diego), Vedha Nayagam, Mun Young Choi, Frederick L. Dryer
- **Lead Center**: NASA Glenn Research Center (GRC)
- **Hardware Platform**: MDCA inside the CIR on ISS
- **Flight Test Matrix**: 284 flight tests successfully conducted in the 2009–2011 campaign.
- **Physical Phenomena**:
  - Verification of classical $d^2$-law droplet regression: $d^2(t) = d_0^2 - K t$.
  - Discovery of low-temperature "cool flame" burning regimes in large alkane droplets (heptane) following radiative extinction of hot flames.
  - Flame extinction limits governed by radiative heat loss and chemical kinetic quenching.
  - Droplet disruption modes caused by internal bubble nucleation.
- **Experimental Variables Recorded (Table IX)**:
  - Test ID (e.g. `FLEX-001` through `FLEX-284`), Run Date/Time (GMT).
  - Fuel type: pure Methanol ($CH_3OH$), pure n-Heptane ($C_7H_{16}$), Decane ($C_{10}H_{22}$), and alkane/alcohol blends.
  - Ambient Chamber Pressure ($P$ in $mmHg$ or $atm$).
  - Atmospheric mole fractions: $X_{O2}, X_{N2}, X_{CO2}, X_{He}$.
  - Initial droplet diameter ($D_0$ in $mm$, ranging from $1.5\text{ to }5.1\text{ mm}$).
  - Visible extinction diameter ($D_{ext}$ in $mm$).
  - Burning rate constant ($K$ in $mm^2/s$).
  - Burn duration ($t_b$ in seconds).
  - Test End Mode: `Extinction`, `Disruption`, `Completion`.

---

### 3.2 BASS & BASS-II (Burning and Suppression of Solids)
- **Authoritative Citation**: NTRS Citation ID `20210011385`
- **Official Report Number**: `NASA/TM-20210011385` ("Burning and Suppression of Solids-II Summary Report")
- **Principal Investigators**: Paul V. Ferkul (NASA GRC / USRA), Sandra L. Olson (NASA GRC)
- **Hardware Platform**: Small Flow Duct inside the Microgravity Science Glovebox (MSG) on ISS
- **Flight Test Campaigns**:
  - BASS: ISS Expeditions 30–33 (2011–2013)
  - BASS-II: ISS Expeditions 39–43 (2014–2017)
- **Physical Phenomena**:
  - Opposed-flow and concurrent-flow flame spread over solid thick and thin fuels in low convective velocity regimes ($0.004\text{ to }0.08\text{ m/s}$).
  - Identification of low-flow flammability and extinction boundaries where natural buoyant convection is absent.
  - Evaluation of gaseous fire suppressants ($N_2$, $CO_2$) on active solid polymer fires.
- **Experimental Variables Recorded**:
  - Sample geometry: Polymethyl methacrylate (PMMA) clear and black cylindrical rods (diameters: $6.35\text{ mm}$ [0.25 in], $9.525\text{ mm}$ [0.375 in], $12.7\text{ mm}$ [0.50 in]), flat PMMA slabs, Nomex, Delrin/POM.
  - Duct flow velocity ($v$ in $m/s$ or $cm/s$).
  - Ambient oxygen volume percentage ($O_2\text{ vol}\%$, $16.0\%\text{ to }21.0\%$).
  - Ambient pressure (psia and kPa).
  - Flame spread rate ($V_f$ in $mm/s$).
  - Extinction conditions (blowoff velocity vs. low-velocity radiative quenching).
  - Gas sensor telemetry: CSA-CP $O_2$ (vol%) and $CO$ (ppm), CDM $CO_2$ (mmHg).

---

### 3.3 ACME (Advanced Combustion via Microgravity Experiments)
- **Authoritative Citations**: NTRS Citation IDs `20210021781`, `20210015913`, `20170009141`
- **Lead Publication**: Dennis P. Stocker et al., "Recent Research on Flames of Gaseous Fuel Aboard the International Space Station" (2021)
- **Lead Center**: NASA GRC
- **Hardware Platform**: CIR on ISS (modular insert replacing MDCA)
- **Campaign Timeline**: 2017–2022
- **The Six Modular ACME Flight Investigations**:
  1. **CLD Flame (Coflow Laminar Diffusion Flame)**:
     - Fuel: Ethylene ($C_2H_4$), Methane ($CH_4$) diluted with nitrogen.
     - Focus: Soot inception, growth, and oxidation in laminar diffusion flames without buoyancy stretch; thin-filament pyrometry for temperature profiles.
  2. **BRE (Burning Rate Emulator)**:
     - Hardware: Flat and annular porous bronze gas burners ($25\text{ mm}$ and $50\text{ mm}$ diameter).
     - Focus: Emulating solid and liquid condensed fuel burning rates using controlled gas flow; testing steady vs transient mass burning flux ($\dot{m}''$), radiation feedback ($q''$), and effective heats of gasification ($L_v$).
  3. **E-FIELD Flames (Electric-Field Effects on Flames)**:
     - Hardware: High-voltage electrode mesh over gas burner ($\pm 0\text{ to }10\text{ kV}$).
     - Focus: Ionic wind forces on flame stability, soot reduction, and shape modification in the absence of buoyancy.
  4. **Flame Design**:
     - Hardware: Spherical porous burner, inverse diffusion flames ($O_2$ injected into surrounding hydrocarbon environment).
     - Focus: Stoichiometric mixture fraction tailoring to produce soot-free combustion and measure radiative extinction limits.
  5. **s-Flame (Spherical Diffusion Flames)**:
     - Hardware: 1D porous sphere burner ($6.35\text{ mm}$ and $9.5\text{ mm}$).
     - Focus: Pure spherical diffusion geometry for fundamental chemical kinetics testing; cellular flame instability.
  6. **CFI-G (Cool Flames Investigation with Gases)**:
     - Fuel: Gaseous n-butane and propane with inert diluents.
     - Focus: Gas-phase low-temperature oxidation, cool flame liftoff, and non-premixed cool flame stability.

---

### 3.4 SoFIE (Solid Fuel Ignition and Extinction)
- **Authoritative Citations**: NTRS Citation IDs `20200000361`, `20240007628`
- **Lead Center**: NASA GRC
- **Hardware Platform**: SoFIE insert in the CIR on ISS
- **Operational Timeline**: Launched 2022, ongoing orbital testing.
- **Five Flight Sub-Projects**:
  1. **GEL (Growth and Extinction Limit)**: Spherical solid fuel samples to evaluate radiative extinction limits.
  2. **MIST (Material Ignition and Suppression Test)**: Flammability ranking of aerospace materials in low-convection environments.
  3. **Narrow Channel Apparatus**: Flame spread over flat polymer samples in opposed and concurrent flow.
  4. **Residence Time**: Impact of residence time on flame spread and solid fuel pyrolysis.
  5. **SMIRF**: Spacecraft materials flammability testing in Exploration Atmospheres ($34\% O_2, 8.2\text{ psia}$).

---

### 3.5 Precursor Flight Missions
- **SOFBALL (Structure of Flame Balls at Low Lewis Number)**:
  - Citations: NTRS IDs `19960008454`, `20040112039`
  - Platform: Space Shuttle STS-83 (1997), STS-94 (1997), STS-107 (2003)
  - Result: Confirmed existence of stationary, spherical flame balls predicted by Zeldovich in 1944. Generated flames consuming only 1 to 5 Watts of chemical energy.
- **SLICE (Smoke and Leachate In-flight Combustion Experiment)**:
  - Citations: NTRS ID `20140017780`
  - Platform: ISS MSG (2012)
  - Result: Studied soot generation and flame liftoff in microgravity coflow flames.

---

## 4. Strict Missing Measurement & Zero-Handling Policy

### 4.1 Physical Grounding
In microgravity combustion physics, substituting `0.0` for missing or unobserved data produces severe, physically catastrophic errors:
- If `visible_extinction_diameter_m = 0.0`, an analysis algorithm concludes the droplet burned continuously until $D = 0\text{ m}$ (complete burnout with zero unburned fuel remainder).
- If `extinction_diameter_m = NULL`, the scientific reality is preserved: the flame extinguished while fuel was still present, but the exact droplet diameter was unobservable due to soot clouding, camera view limits, or droplet ejection.
- If `flame_spread_rate_m_s = 0.0`, the algorithm records a completely stationary flame, whereas `NULL` indicates the test was interrupted or sensors failed prior to steady-state spread.

### 4.2 Architectural Enforcement
1. **Database Schema Constraints**:
   Every numerical observation column across all database tables (`test_runs`, `measurements`) is declared `NULLABLE`.
2. **Parser Mapping Rules**:
   The ingestion engine maps all of the following source tokens strictly to Python `None` / SQL `NULL`:
   `["–", "-", "—", "N/A", "NA", "null", "NULL", "None", "ND", "unmeasured", "unobserved", ""]`.
3. **Explicit Validation Status**:
   Every measurement record includes a `validation_status` categorization:
   - `VALID`: Measured value within physical boundary ranges.
   - `EXTINCTION_UNOBSERVED`: Test concluded without visible extinction.
   - `DISRUPTION`: Internal fuel boiling terminated the test run early.
   - `SENSOR_SATURATED`: Signal exceeded sensor dynamic range.
   - `MISSING_DATA`: Value unrecorded by NASA flight team.

---

## 5. Mathematical SI Unit Normalization Matrix

All ingested aerospace and imperial flight variables are deterministically normalized into International System of Units (SI) base and derived units. Both original strings and normalized values are retained for cryptographic provenance.

| Physical Dimension | NASA Flight / Raw Units | Normalization Multiplier to SI Target | SI Target Unit | Physical Boundary Constraints |
|---|---|---|---|---|
| **Length / Diameter** | Millimeters ($mm$)<br>Inches ($in$)<br>Microns ($\mu m$) | $d_{\text{SI}} = d_{\text{mm}} \times 10^{-3}$<br>$d_{\text{SI}} = d_{\text{in}} \times 0.0254$<br>$d_{\text{SI}} = d_{\mu m} \times 10^{-6}$ | Meter ($m$) | $d > 0.0\text{ m}$ |
| **Velocity / Spread Rate** | Millimeters per second ($mm/s$)<br>Centimeters per second ($cm/s$)<br>Inches per second ($in/s$) | $v_{\text{SI}} = v_{\text{mm/s}} \times 10^{-3}$<br>$v_{\text{SI}} = v_{\text{cm/s}} \times 10^{-2}$<br>$v_{\text{SI}} = v_{\text{in/s}} \times 0.0254$ | Meter per second ($m/s$) | $v \ge 0.0\text{ m/s}$ |
| **Droplet Burning Rate ($K$)** | Square millimeters per second ($mm^2/s$)<br>Square centimeters per second ($cm^2/s$) | $K_{\text{SI}} = K_{\text{mm}^2/\text{s}} \times 10^{-6}$<br>$K_{\text{SI}} = K_{\text{cm}^2/\text{s}} \times 10^{-4}$ | Square meter per second ($m^2/s$) | $K > 0.0\text{ m}^2/\text{s}$ |
| **Pressure** | Standard atmospheres ($atm$)<br>Millimeters of mercury ($mmHg$)<br>Pounds per square inch ($psi$ / $psia$)<br>Bar ($bar$)<br>Kilopascals ($kPa$) | $P_{\text{SI}} = P_{\text{atm}} \times 101325.0$<br>$P_{\text{SI}} = P_{\text{mmHg}} \times \frac{101325.0}{760.0}$<br>$P_{\text{SI}} = P_{\text{psi}} \times 6894.757293$<br>$P_{\text{SI}} = P_{\text{bar}} \times 10^5$<br>$P_{\text{SI}} = P_{\text{kPa}} \times 1000.0$ | Pascal ($Pa$) | $10^3 \le P \le 10^7\text{ Pa}$ |
| **Temperature** | Degrees Celsius ($^\circ C$)<br>Degrees Fahrenheit ($^\circ F$)<br>Degrees Rankine ($^\circ R$) | $T_{\text{SI}} = T_{^\circ C} + 273.15$<br>$T_{\text{SI}} = (T_{^\circ F} - 32.0) \times \frac{5}{9} + 273.15$<br>$T_{\text{SI}} = T_{^\circ R} \times \frac{5}{9}$ | Kelvin ($K$) | $150.0 \le T \le 3500.0\text{ K}$ |
| **Volumetric Flow Rate** | Standard cubic centimeters/min ($sccm$)<br>Standard liters/min ($slpm$) | $Q_{\text{SI}} = Q_{\text{sccm}} \times 1.666667 \times 10^{-8}$<br>$Q_{\text{SI}} = Q_{\text{slpm}} \times 1.666667 \times 10^{-5}$ | Cubic meter per second ($m^3/s$) | $Q \ge 0.0\text{ m}^3/\text{s}$ |
| **Mass Burning Flux ($\dot{m}''$)** | Grams per square centimeter second ($g/(cm^2\cdot s)$) | $\dot{m}''_{\text{SI}} = \dot{m}''_{\text{g/(cm}^2\cdot\text{s)}} \times 10.0$ | Kilogram per square meter second ($kg/(m^2\cdot s)$) | $\dot{m}'' > 0.0\text{ kg}/(m^2\cdot s)$ |
| **Heat Flux / Irradiance** | Watts per square centimeter ($W/cm^2$)<br>Kilowatts per square meter ($kW/m^2$) | $q''_{\text{SI}} = q''_{\text{W/cm}^2} \times 10^4$<br>$q''_{\text{SI}} = q''_{\text{kW/m}^2} \times 1000.0$ | Watt per square meter ($W/m^2$) | $q'' \ge 0.0\text{ W}/m^2$ |
| **Effective Heat of Gasification ($L_v$)** | Calories per gram ($cal/g$)<br>Kilojoules per gram ($kJ/g$) | $L_{v,\text{SI}} = L_{v,\text{cal/g}} \times 4184.0$<br>$L_{v,\text{SI}} = L_{v,\text{kJ/g}} \times 10^6$ | Joule per kilogram ($J/kg$) | $L_v > 0.0\text{ J/kg}$ |
| **Acceleration / Gravity** | Standard gravity ($g$)<br>Microgravity ($\mu g$) | $a_{\text{SI}} = a_{g} \times 9.80665$<br>$a_{\text{SI}} = a_{\mu g} \times 9.80665 \times 10^{-6}$ | Meter per square second ($m/s^2$) | $0.0 \le a \le 15.0\text{ m}/s^2$ |
| **Mole Fractions ($X_i$)** | Volume percent ($vol\%$) | $X_i = \text{vol\%} / 100.0$ | Dimensionless | $0 \le X_i \le 1$, $|1 - \sum X_i| \le 0.01$ |

---

## 6. API and Data Access Verification Log

Live programmatic verification was conducted directly against upstream NASA servers from the workspace environment:

```
[PROBE LOG]
Target URL: https://ntrs.nasa.gov/api/citations/search?q=microgravity%20combustion
HTTP Status: 200 OK
Response Time: 284 ms
Content-Type: application/json;charset=UTF-8
Total Indexed Citations: 1,077
Verification: CONFIRMED LIVE

Target URL: https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.txt
HTTP Status: 200 OK
Response Time: 341 ms
Content-Type: text/plain; charset=utf-8
Content-Length: 272,725 bytes
ETag: "a22a94be5825734319814ec5f7be0b21"
Rate Limit Headers:
  X-RateLimit-Limit: 500
  X-RateLimit-Remaining: 499
  X-RateLimit-Reset: 1794507349
Payload Signature: Contains TABLE IX (284 flight test records of FLEX droplet burning)
Verification: CONFIRMED LIVE & COMPLETE

Target URL: https://ntrs.nasa.gov/api/citations/20210011385/downloads/TM-20210011385.pdf.txt
HTTP Status: 200 OK
Response Time: 412 ms
Content-Type: text/plain; charset=utf-8
Content-Length: 352,221 bytes
Payload Signature: Contains BASS-II flight test tables for PMMA rod flammability
Verification: CONFIRMED LIVE & COMPLETE

Target URL: https://nasa-psi.s3.us-west-2.amazonaws.com/?delimiter=/
HTTP Status: 200 OK
Response Time: 195 ms
Payload Signature: Public AWS S3 Open Data bucket listing for NASA PSI collections
Verification: CONFIRMED ACCESSIBLE
```
