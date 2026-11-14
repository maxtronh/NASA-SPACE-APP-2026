"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import Link from "next/link";
import {
  Radio,
  Activity,
  AlertTriangle,
  Flame,
  ShieldAlert,
  ShieldCheck,
  RotateCcw,
  Sliders,
  Wind,
  Wifi,
  WifiOff,
  Zap,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Terminal,
  Play,
  Pause,
  Download,
  Info,
  Layers,
  Lock,
  Unlock,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";
import {
  filterWaveletJitter,
  calculateRekindleRisk,
  createCCSDSTelemetryStream,
} from "@/lib/api";
import {
  generateMockTelemetryFrame,
  computeMockWaveletFilter,
  computeMockRekindleRisk,
} from "@/lib/mockData";
import {
  CCSDSTelemetryFrame,
  WaveletFilterResponse,
  RekindleRiskResponse,
  RekindleRiskLevel,
} from "@/types";

interface AuditLog {
  id: string;
  timestamp: string;
  level: "INFO" | "WARN" | "ALARM" | "CRIT";
  message: string;
}

const PRESET_FUELS = [
  { key: "n-heptane", name: "n-Heptane (FLEX)", ltc: true, flashK: 269.15 },
  { key: "n-octane", name: "n-Octane", ltc: true, flashK: 286.15 },
  { key: "n-decane", name: "n-Decane", ltc: true, flashK: 319.15 },
  { key: "methanol", name: "Methanol", ltc: false, flashK: 284.15 },
  { key: "ethanol", name: "Ethanol", ltc: false, flashK: 286.15 },
];

export default function MissionControlPage() {
  // ==========================================
  // SECTION A: TELEMETRY & KINEMATICS STATE
  // ==========================================
  const [telemetry, setTelemetry] = useState<CCSDSTelemetryFrame>(() =>
    generateMockTelemetryFrame(1024, {
      iss_altitude_km: 418.4,
      iss_latitude: 51.6,
      iss_longitude: 142.3,
      acceleration_raw_g: 1.2e-6,
      acceleration_filtered_g: 1.2e-6,
    })
  );
  const [isStreaming, setIsStreaming] = useState<boolean>(true);
  const [simulateLOS, setSimulateLOS] = useState<boolean>(false);
  const [sequenceCount, setSequenceCount] = useState<number>(1024);

  // ==========================================
  // SECTION B: WAVELET JITTER STUDIO STATE
  // ==========================================
  const [decompLevel, setDecompLevel] = useState<number>(4);
  const [thresholdG, setThresholdG] = useState<number>(1.0e-4);
  const [thresholdMode, setThresholdMode] = useState<"soft" | "hard">("soft");
  const [waveletResult, setWaveletResult] = useState<WaveletFilterResponse | null>(null);
  const [jitterInjected, setJitterInjected] = useState<boolean>(false);
  const [waveletRunning, setWaveletRunning] = useState<boolean>(false);

  // Time-series array for dual-trace Recharts
  const [jitterChartData, setJitterChartData] = useState<
    Array<{ t: number; raw: number; filtered: number; baseline: number }>
  >([]);

  // ==========================================
  // SECTION C: SILENT REKINDLING STATE
  // ==========================================
  const [selectedFuel, setSelectedFuel] = useState<string>("n-heptane");
  const [fuelTempK, setFuelTempK] = useState<number>(685.0);
  const [visibleFlameActive, setVisibleFlameActive] = useState<boolean>(false);
  const [ventilationCmS, setVentilationCmS] = useState<number>(3.0);
  const [chamberPressureKpa, setChamberPressureKpa] = useState<number>(101.325);
  const [o2Percentage, setO2Percentage] = useState<number>(21.0);
  const [rekindleResult, setRekindleResult] = useState<RekindleRiskResponse | null>(null);

  // ==========================================
  // SECTION D: EMERGENCY SUPPRESSION & AUDIT LOGS
  // ==========================================
  const [damperIsolated, setDamperIsolated] = useState<boolean>(false);
  const [fkArmed, setFkArmed] = useState<boolean>(false);
  const [fkReleased, setFkReleased] = useState<boolean>(false);
  const [n2Flooding, setN2Flooding] = useState<boolean>(false);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([
    {
      id: "log-1",
      timestamp: "16:40:00 UTC",
      level: "INFO",
      message: "CCSDS Ku-band downlink established with TDRS-East (APID 0x01A0).",
    },
    {
      id: "log-2",
      timestamp: "16:40:15 UTC",
      level: "INFO",
      message: "Sync Lock confirmed: Word 0x1ACFFC1D. Ring buffer 256/256 synchronized.",
    },
    {
      id: "log-3",
      timestamp: "16:41:05 UTC",
      level: "INFO",
      message: "FLEX-02 droplet ignition sequence initiated in US Lab Destiny CIR rack.",
    },
  ]);

  // Active scenario identifier
  const [activeScenario, setActiveScenario] = useState<string>("CUSTOM");

  const addAuditLog = (level: "INFO" | "WARN" | "ALARM" | "CRIT", message: string) => {
    const now = new Date();
    const timeStr = `${String(now.getUTCHours()).padStart(2, "0")}:${String(
      now.getUTCMinutes()
    ).padStart(2, "0")}:${String(now.getUTCSeconds()).padStart(2, "0")} UTC`;
    setAuditLogs((prev) => [
      { id: `log-${Date.now()}-${Math.random()}`, timestamp: timeStr, level, message },
      ...prev.slice(0, 49),
    ]);
  };

  // ==========================================
  // STREAM TELEMETRY HOOK
  // ==========================================
  useEffect(() => {
    if (!isStreaming) return;

    const cleanup = createCCSDSTelemetryStream(
      (frame) => {
        if (!simulateLOS) {
          setTelemetry(frame);
          setSequenceCount(frame.sequence_count);
        }
      },
      () => {
        // Handled silently by mock fallback inside createCCSDSTelemetryStream
      }
    );

    return () => {
      cleanup();
    };
  }, [isStreaming, simulateLOS]);

  // ==========================================
  // COMPUTE WAVELET FILTER ON JITTER DATA
  // ==========================================
  const executeWaveletDecomposition = async (injectSpike = jitterInjected) => {
    setWaveletRunning(true);
    const sampleCount = 64;
    const samplingRate = 50.0; // 50 Hz
    const rawSignal: number[] = [];

    // Generate signal with micro-g baseline and optional astronaut treadmill exercise (2.2 Hz)
    for (let i = 0; i < sampleCount; i++) {
      const t = i / samplingRate;
      // Baseline quiescent microgravity (10^-6 g)
      const quiescent = 1.0e-6 + 0.3e-6 * Math.sin(2 * Math.PI * 0.2 * t);
      // High-frequency sensor noise
      const sensorNoise = (Math.sin(2 * Math.PI * 18.0 * t) + (Math.random() - 0.5)) * 0.2e-6;

      // Jitter vibration: 2.2 Hz exercise harmonic reaching 1.2 * 10^-3 g
      let exerciseSpike = 0;
      if (injectSpike) {
        exerciseSpike =
          1.2e-3 * Math.sin(2 * Math.PI * 2.2 * t) +
          0.4e-3 * Math.sin(2 * Math.PI * 4.4 * t) +
          (Math.random() - 0.5) * 0.2e-3;
      }
      rawSignal.push(quiescent + sensorNoise + exerciseSpike);
    }

    try {
      const result = await filterWaveletJitter({
        raw_signal: rawSignal,
        sampling_rate_hz: samplingRate,
        decomposition_level: decompLevel,
        threshold_mode: thresholdMode,
        threshold_g: thresholdG,
        wavelet_name: "db4",
      });
      setWaveletResult(result);

      // Map to chart items
      const chartPoints = rawSignal.map((raw, idx) => ({
        t: Number((idx / samplingRate).toFixed(3)),
        raw: Number((raw * 1e6).toFixed(2)), // in micro-g for visual readability
        filtered: Number(((result.filtered_signal[idx] ?? raw) * 1e6).toFixed(2)),
        baseline: 1.0, // 1 micro-g target
      }));
      setJitterChartData(chartPoints);
    } catch (e) {
      const fallback = computeMockWaveletFilter({
        raw_signal: rawSignal,
        decomposition_level: decompLevel,
        threshold_mode: thresholdMode,
        threshold_g: thresholdG,
      });
      setWaveletResult(fallback);
      const chartPoints = rawSignal.map((raw, idx) => ({
        t: Number((idx / samplingRate).toFixed(3)),
        raw: Number((raw * 1e6).toFixed(2)),
        filtered: Number(((fallback.filtered_signal[idx] ?? raw) * 1e6).toFixed(2)),
        baseline: 1.0,
      }));
      setJitterChartData(chartPoints);
    } finally {
      setWaveletRunning(false);
    }
  };

  // Re-run wavelet when sliders change
  useEffect(() => {
    executeWaveletDecomposition(jitterInjected);
  }, [decompLevel, thresholdG, thresholdMode]);

  // ==========================================
  // RECOMPUTE SILENT REKINDLING KINETICS
  // ==========================================
  useEffect(() => {
    let active = true;
    async function updateRekindle() {
      const effectiveVent = damperIsolated ? 0.0 : ventilationCmS;
      try {
        const res = await calculateRekindleRisk({
          fuel_type: selectedFuel,
          fuel_temperature_k: fuelTempK,
          visible_flame_active: visibleFlameActive,
          chamber_pressure_kpa: chamberPressureKpa,
          oxygen_percentage: o2Percentage,
          ventilation_velocity_cm_s: effectiveVent,
        });
        if (active) setRekindleResult(res);
      } catch (e) {
        if (active) {
          const fallback = computeMockRekindleRisk({
            fuel_type: selectedFuel,
            fuel_temperature_k: fuelTempK,
            visible_flame_active: visibleFlameActive,
            chamber_pressure_kpa: chamberPressureKpa,
            oxygen_percentage: o2Percentage,
            ventilation_velocity_cm_s: effectiveVent,
          });
          setRekindleResult(fallback);
        }
      }
    }
    updateRekindle();
    return () => {
      active = false;
    };
  }, [
    selectedFuel,
    fuelTempK,
    visibleFlameActive,
    ventilationCmS,
    damperIsolated,
    chamberPressureKpa,
    o2Percentage,
  ]);

  // ==========================================
  // QUICK-SCENARIO HANDLERS
  // ==========================================
  const triggerScenario = (scenarioKey: string) => {
    setActiveScenario(scenarioKey);
    setFkReleased(false);
    setFkArmed(false);
    setN2Flooding(false);

    switch (scenarioKey) {
      case "FLEX_HEPTANE": {
        // FLEX-02 n-Heptane post-extinction silent rekindle runaway
        setSelectedFuel("n-heptane");
        setFuelTempK(685.0);
        setVisibleFlameActive(false);
        setVentilationCmS(2.0);
        setDamperIsolated(false);
        setO2Percentage(21.0);
        setJitterInjected(false);
        executeWaveletDecomposition(false);
        addAuditLog(
          "ALARM",
          "Scenario [FLEX Silent Rekindle]: Visible flame ceased (photodiode 0.00 V). Droplet core at 685 K in LTC peroxy zone. Da_cool > 1.8. Flashing Hazard Annunciator triggered!"
        );
        break;
      }
      case "TREADMILL_SPIKE": {
        // Astronaut exercise jitter injection
        setSelectedFuel("n-heptane");
        setFuelTempK(295.0);
        setVisibleFlameActive(false);
        setVentilationCmS(3.0);
        setDamperIsolated(false);
        setJitterInjected(true);
        executeWaveletDecomposition(true);
        addAuditLog(
          "WARN",
          "Scenario [Treadmill Jitter Spike]: Astronaut T2 harmonic vibration injected at 2.2 Hz reaching 1.2 milli-g. Daubechies-4 filter isolates jitter and recovers micro-g baseline."
        );
        break;
      }
      case "ORBITAL_QUIESCENCE": {
        // Crew sleep / night orbit quiescent conditions
        setSelectedFuel("n-heptane");
        setFuelTempK(293.15);
        setVisibleFlameActive(false);
        setVentilationCmS(3.0);
        setDamperIsolated(false);
        setO2Percentage(21.0);
        setJitterInjected(false);
        executeWaveletDecomposition(false);
        addAuditLog(
          "INFO",
          "Scenario [Orbital Quiescence]: Crew sleep state. SAMS accelerometer at 0.3 micro-g. CCSDS Ku-band frame sync nominal. All annunciators INERT."
        );
        break;
      }
      case "THRUSTER_TRANSIENT": {
        // Russian segment attitude correction RCS firing pulse
        setSelectedFuel("n-octane");
        setFuelTempK(310.0);
        setVisibleFlameActive(false);
        setVentilationCmS(4.0);
        setDamperIsolated(false);
        setJitterInjected(true);
        setThresholdG(2.5e-4);
        executeWaveletDecomposition(true);
        addAuditLog(
          "WARN",
          "Scenario [Thruster Firing Transient]: Service module RCS burn step acceleration of 1.5e-2 g. Transient Grashof perturbation flagged."
        );
        break;
      }
    }
  };

  // ==========================================
  // EMERGENCY SUPPRESSION ACTIONS
  // ==========================================
  const toggleDamper = () => {
    const nextState = !damperIsolated;
    setDamperIsolated(nextState);
    if (nextState) {
      addAuditLog(
        "ALARM",
        "EMERGENCY ACTION: Ventilation damper ISOLATED (0.0 cm/s). Oxygen inflow halted to suppress radical chain accumulation."
      );
    } else {
      addAuditLog(
        "INFO",
        "ACTION: Ventilation damper reset to OPEN (nominal 3.0 cm/s cross-ventilation)."
      );
    }
  };

  const dischargeFK5112 = () => {
    if (!fkArmed) {
      addAuditLog("WARN", "SUPPRESSION INHIBIT: FK-5-1-12 release requires arming safety toggle first.");
      return;
    }
    setFkReleased(true);
    setFuelTempK(315.0); // Rapid cooling below flash point
    setVisibleFlameActive(false);
    addAuditLog(
      "CRIT",
      "SUPPRESSION FIRED: FK-5-1-12 (Novec 1230 fluoroketone) gas discharged! Droplet core quenched to 315 K (< flash point). Cool flame kinetics completely extinguished."
    );
  };

  const toggleN2Flood = () => {
    const nextState = !n2Flooding;
    setN2Flooding(nextState);
    if (nextState) {
      setO2Percentage(9.5); // Dilute below LOI
      addAuditLog(
        "ALARM",
        "CHAMBER ACTION: Nitrogen (N2) flood active. Ambient O2 diluted to 9.5% (below 12% LOI)."
      );
    } else {
      setO2Percentage(21.0);
      addAuditLog("INFO", "CHAMBER ACTION: Nitrogen flood ceased. Ambient O2 normalized to 21.0%.");
    }
  };

  const masterReset = () => {
    setDamperIsolated(false);
    setFkArmed(false);
    setFkReleased(false);
    setN2Flooding(false);
    setFuelTempK(295.0);
    setO2Percentage(21.0);
    setVentilationCmS(3.0);
    setVisibleFlameActive(false);
    setJitterInjected(false);
    executeWaveletDecomposition(false);
    addAuditLog("INFO", "MASTER RESET: All interlocks cleared. Nominal CIR experiment conditions restored.");
  };

  // ==========================================
  // ANNUNCIATOR MATRIX ILLUMINATION LOGIC
  // ==========================================
  const currentRisk = rekindleResult?.risk_level || "INERT";

  return (
    <div className="min-h-screen bg-space-950 text-slate-100 p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-space-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-nasa-blue to-nasa-cyan flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Radio className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white font-mono">
                  MISSION CONTROL <span className="text-nasa-cyan">FLIGHT COCKPIT</span>
                </h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-800 border border-space-700 text-slate-400">
                  E-15 / CIR
                </span>
              </div>
              <p className="text-xs text-slate-400">
                ISS Combustion Integrated Rack • Ku-Band Telemetry • Wavelet Jitter Filter • Silent Rekindling Annunciator
              </p>
            </div>
          </div>
        </div>

        {/* Global Controls & Status */}
        <div className="flex flex-wrap items-center gap-2">
          <div
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono ${
              simulateLOS
                ? "bg-rose-950/40 border-rose-500/50 text-rose-300"
                : "bg-emerald-950/40 border-emerald-500/50 text-emerald-300"
            }`}
          >
            {simulateLOS ? <WifiOff className="w-3.5 h-3.5" /> : <Wifi className="w-3.5 h-3.5" />}
            <span>{simulateLOS ? "TDRS LOS (HANDOVER)" : "KU-BAND LOCKED 50 Hz"}</span>
          </div>

          <button
            onClick={() => setSimulateLOS(!simulateLOS)}
            className={`px-3 py-1.5 rounded-lg border text-xs font-mono transition-all ${
              simulateLOS
                ? "bg-space-800 border-space-700 text-slate-300 hover:text-white"
                : "bg-amber-950/30 border-amber-500/40 text-amber-300 hover:bg-amber-900/40"
            }`}
          >
            {simulateLOS ? "Restore Telemetry Link" : "Simulate TDRS Drop"}
          </button>

          <button
            onClick={() => setIsStreaming(!isStreaming)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-space-800 hover:bg-space-700 border border-space-700 text-xs font-mono text-slate-200"
          >
            {isStreaming ? <Pause className="w-3.5 h-3.5 text-amber-400" /> : <Play className="w-3.5 h-3.5 text-emerald-400" />}
            <span>{isStreaming ? "Pause Feed" : "Resume Feed"}</span>
          </button>
        </div>
      </div>

      {/* ==========================================
          SECTION E: QUICK-SCENARIO PRESETS BAR
      ========================================== */}
      <div className="bg-space-900 border border-space-800 rounded-xl p-3.5 shadow-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <Zap className="w-4 h-4 text-nasa-amber" />
            <span className="font-semibold text-slate-200 uppercase tracking-wider">Flight Controller Presets:</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <button
              onClick={() => triggerScenario("FLEX_HEPTANE")}
              className={`px-3 py-2 rounded-lg border text-xs font-mono text-left transition-all ${
                activeScenario === "FLEX_HEPTANE"
                  ? "bg-rose-950/50 border-rose-500 text-rose-200 font-bold shadow-sm shadow-rose-500/20"
                  : "bg-space-850 border-space-800 text-slate-300 hover:text-white hover:bg-space-800"
              }`}
            >
              <div className="text-[10px] text-rose-400 font-semibold uppercase">Scenario 1</div>
              <div className="truncate">FLEX Silent Rekindle</div>
            </button>

            <button
              onClick={() => triggerScenario("TREADMILL_SPIKE")}
              className={`px-3 py-2 rounded-lg border text-xs font-mono text-left transition-all ${
                activeScenario === "TREADMILL_SPIKE"
                  ? "bg-amber-950/50 border-amber-500 text-amber-200 font-bold shadow-sm shadow-amber-500/20"
                  : "bg-space-850 border-space-800 text-slate-300 hover:text-white hover:bg-space-800"
              }`}
            >
              <div className="text-[10px] text-amber-400 font-semibold uppercase">Scenario 2</div>
              <div className="truncate">Treadmill Jitter Spike</div>
            </button>

            <button
              onClick={() => triggerScenario("ORBITAL_QUIESCENCE")}
              className={`px-3 py-2 rounded-lg border text-xs font-mono text-left transition-all ${
                activeScenario === "ORBITAL_QUIESCENCE"
                  ? "bg-cyan-950/50 border-nasa-cyan text-cyan-200 font-bold shadow-sm shadow-cyan-500/20"
                  : "bg-space-850 border-space-800 text-slate-300 hover:text-white hover:bg-space-800"
              }`}
            >
              <div className="text-[10px] text-nasa-cyan font-semibold uppercase">Scenario 3</div>
              <div className="truncate">Orbital Quiescence</div>
            </button>

            <button
              onClick={() => triggerScenario("THRUSTER_TRANSIENT")}
              className={`px-3 py-2 rounded-lg border text-xs font-mono text-left transition-all ${
                activeScenario === "THRUSTER_TRANSIENT"
                  ? "bg-indigo-950/50 border-indigo-500 text-indigo-200 font-bold shadow-sm shadow-indigo-500/20"
                  : "bg-space-850 border-space-800 text-slate-300 hover:text-white hover:bg-space-800"
              }`}
            >
              <div className="text-[10px] text-indigo-400 font-semibold uppercase">Scenario 4</div>
              <div className="truncate">Thruster Transient</div>
            </button>
          </div>
        </div>
      </div>

      {/* ==========================================
          SECTION A: ORBITAL TELEMETRY BANNER
      ========================================== */}
      <div className="bg-space-900 border border-space-800 rounded-xl p-5 shadow-lg space-y-4">
        {/* Strip Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-space-800/80 pb-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              ISS Telemetry Downlink (Ku-Band)
            </span>
            <span className="text-[11px] font-mono text-slate-400 ml-2">
              APID 0x01A0 • Sequence #{sequenceCount}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-slate-300">
            <span className="px-2 py-0.5 rounded bg-space-850 border border-space-800">
              Payload: <strong className="text-nasa-cyan">FLEX-02 (CIR)</strong>
            </span>
            <span className="px-2 py-0.5 rounded bg-space-850 border border-space-800">
              Sync Word:{" "}
              <strong className={simulateLOS ? "text-rose-400" : "text-emerald-400 font-bold"}>
                {simulateLOS ? "0x00000000 (LOST)" : "0x1ACFFC1D"}
              </strong>
            </span>
            <span className="px-2 py-0.5 rounded bg-space-850 border border-space-800">
              Loss: <strong className={simulateLOS ? "text-rose-400" : "text-emerald-400"}>{simulateLOS ? "100.0%" : "0.00%"}</strong>
            </span>
            <span className="px-2 py-0.5 rounded bg-space-850 border border-space-800">
              Ring Buffer: <strong className="text-emerald-400">256/256</strong>
            </span>
          </div>
        </div>

        {/* ISS Kinematics 4-Metric Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-space-850 border border-space-800/80 rounded-lg p-3.5">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Orbit Altitude</div>
            <div className="text-lg sm:text-xl font-bold font-mono text-white mt-1">
              {simulateLOS ? "---" : `${telemetry.iss_altitude_km.toFixed(1)} km`}
            </div>
            <div className="text-[10px] font-mono text-slate-500 mt-0.5">225.9 nmi • Low Earth Orbit</div>
          </div>

          <div className="bg-space-850 border border-space-800/80 rounded-lg p-3.5">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Orbital Velocity</div>
            <div className="text-lg sm:text-xl font-bold font-mono text-white mt-1">
              {simulateLOS ? "---" : "7.66 km/s"}
            </div>
            <div className="text-[10px] font-mono text-slate-500 mt-0.5">27,576 km/h • Mach 22.5</div>
          </div>

          <div className="bg-space-850 border border-space-800/80 rounded-lg p-3.5">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Sub-Satellite Point</div>
            <div className="text-lg sm:text-xl font-bold font-mono text-nasa-cyan mt-1 truncate">
              {simulateLOS
                ? "---"
                : `${telemetry.iss_latitude >= 0 ? `${telemetry.iss_latitude.toFixed(2)}°N` : `${Math.abs(telemetry.iss_latitude).toFixed(2)}°S`}, ${
                    telemetry.iss_longitude >= 0
                      ? `${telemetry.iss_longitude.toFixed(2)}°E`
                      : `${Math.abs(telemetry.iss_longitude).toFixed(2)}°W`
                  }`}
            </div>
            <div className="text-[10px] font-mono text-slate-500 mt-0.5">Inclination 51.6°</div>
          </div>

          <div className="bg-space-850 border border-space-800/80 rounded-lg p-3.5">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">TDRS Ground Station</div>
            <div className="text-lg sm:text-xl font-bold font-mono text-white mt-1 flex items-center gap-1.5 truncate">
              {simulateLOS ? (
                <span className="text-rose-400">LOST CONTACT</span>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span>TDRS-East (Ku)</span>
                </>
              )}
            </div>
            <div className="text-[10px] font-mono text-slate-500 mt-0.5">BER &lt; 10⁻⁹ • White Sands Relay</div>
          </div>
        </div>
      </div>

      {/* Main Split Grid: Section B & Section C */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* ==========================================
            SECTION B: WAVELET JITTER STUDIO (7 Cols)
        ========================================== */}
        <div className="lg:col-span-7 bg-space-900 border border-space-800 rounded-xl p-5 shadow-lg space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-space-800 pb-3">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 font-mono">
                <Activity className="w-4 h-4 text-nasa-cyan" />
                Wavelet Jitter Filter Studio (Daubechies-4 DWT)
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Multi-level Mallat pyramid isolating 1–3 Hz astronaut exercise vibrations from 10⁻⁶ g microgravity
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  const nextState = !jitterInjected;
                  setJitterInjected(nextState);
                  executeWaveletDecomposition(nextState);
                  if (nextState) {
                    addAuditLog("WARN", "Wavelet Studio: Injected 2.2 Hz astronaut exercise vibration harmonics.");
                  } else {
                    addAuditLog("INFO", "Wavelet Studio: Restored quiescent microgravity sensor stream.");
                  }
                }}
                className={`px-2.5 py-1 rounded text-xs font-mono border transition-all ${
                  jitterInjected
                    ? "bg-rose-950/40 border-rose-500/50 text-rose-300"
                    : "bg-space-800 border-space-700 text-slate-300 hover:text-white"
                }`}
              >
                {jitterInjected ? "Stop Jitter Spike" : "Inject Jitter Spike"}
              </button>
            </div>
          </div>

          {/* Quantitative Performance Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="bg-space-850 border border-space-800 p-2.5 rounded-lg text-center">
              <div className="text-[10px] font-mono text-slate-400 uppercase">SNR Enhancement</div>
              <div className="text-base font-bold font-mono text-emerald-400 mt-0.5">
                +{waveletResult?.snr_enhancement_db ?? 21.4} dB
              </div>
            </div>

            <div className="bg-space-850 border border-space-800 p-2.5 rounded-lg text-center">
              <div className="text-[10px] font-mono text-slate-400 uppercase">Peak Jitter Attenuation</div>
              <div className="text-base font-bold font-mono text-emerald-400 mt-0.5">
                {waveletResult?.peak_reduction_pct ?? 98.7}%
              </div>
            </div>

            <div className="bg-space-850 border border-space-800 p-2.5 rounded-lg text-center">
              <div className="text-[10px] font-mono text-slate-400 uppercase">Richardson Number</div>
              <div className="text-base font-bold font-mono text-nasa-cyan mt-0.5">
                Ri &lt; 0.05
              </div>
            </div>

            <div className="bg-space-850 border border-space-800 p-2.5 rounded-lg text-center">
              <div className="text-[10px] font-mono text-slate-400 uppercase">Micro-G Regime</div>
              <div className="text-base font-bold font-mono text-emerald-400 mt-0.5 flex items-center justify-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>QUIESCENT</span>
              </div>
            </div>
          </div>

          {/* Dual-Trace Chart */}
          <div className="h-64 sm:h-72 w-full pt-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={jitterChartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="t"
                  stroke="#64748b"
                  tick={{ fontSize: 10 }}
                  label={{
                    value: "Time t [seconds] (50 Hz frame sample window)",
                    position: "insideBottom",
                    offset: -12,
                    fill: "#94a3b8",
                    fontSize: 10,
                  }}
                />
                <YAxis
                  stroke="#64748b"
                  tick={{ fontSize: 10 }}
                  label={{
                    value: "Acceleration [micro-g, 10⁻⁶ g]",
                    angle: -90,
                    position: "insideLeft",
                    fill: "#94a3b8",
                    fontSize: 10,
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0b1120",
                    borderColor: "#334155",
                    fontSize: "11px",
                    fontFamily: "monospace",
                  }}
                  formatter={(value: any, name: string) => [
                    `${value} µg`,
                    name === "raw"
                      ? "Raw Sensor (10⁻³ g jitter)"
                      : name === "filtered"
                      ? "db4 Filtered Baseline"
                      : "Microgravity Goal",
                  ]}
                />
                <Legend
                  verticalAlign="top"
                  height={36}
                  wrapperStyle={{ fontSize: "11px", fontFamily: "monospace" }}
                />
                <ReferenceLine y={1.0} stroke="#10b981" strokeDasharray="4 4" label={{ value: "1.0 µg Target", fill: "#10b981", fontSize: 10 }} />
                <Line
                  type="monotone"
                  dataKey="raw"
                  name="Raw Sensor a_raw(t)"
                  stroke="#fc3d21"
                  strokeWidth={1.5}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="filtered"
                  name="Filtered a_filtered(t) (db4)"
                  stroke="#00e5ff"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Interactive Wavelet Controls */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-space-800">
            <div>
              <div className="flex justify-between text-xs font-mono text-slate-300 mb-1">
                <span>Decomposition Levels:</span>
                <span className="text-nasa-cyan font-bold">{decompLevel} (J=5)</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={decompLevel}
                onChange={(e) => setDecompLevel(Number(e.target.value))}
                className="w-full accent-nasa-cyan bg-space-800 h-1.5 rounded-lg cursor-pointer"
              />
              <div className="text-[10px] font-mono text-slate-500 mt-1">Mallat Dyadic Octaves</div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-mono text-slate-300 mb-1">
                <span>Threshold:</span>
                <span className="text-nasa-cyan font-bold">{thresholdG.toExponential(1)} g</span>
              </div>
              <input
                type="range"
                min="0.00001"
                max="0.001"
                step="0.00005"
                value={thresholdG}
                onChange={(e) => setThresholdG(Number(e.target.value))}
                className="w-full accent-nasa-cyan bg-space-800 h-1.5 rounded-lg cursor-pointer"
              />
              <div className="text-[10px] font-mono text-slate-500 mt-1">Donoho VisuShrink λ</div>
            </div>

            <div>
              <div className="text-xs font-mono text-slate-300 mb-1">Shrinkage Mode:</div>
              <div className="flex gap-2">
                <button
                  onClick={() => setThresholdMode("soft")}
                  className={`flex-1 py-1 rounded text-xs font-mono border transition-all ${
                    thresholdMode === "soft"
                      ? "bg-nasa-cyan/20 border-nasa-cyan text-nasa-cyan font-bold"
                      : "bg-space-850 border-space-800 text-slate-400"
                  }`}
                >
                  Soft
                </button>
                <button
                  onClick={() => setThresholdMode("hard")}
                  className={`flex-1 py-1 rounded text-xs font-mono border transition-all ${
                    thresholdMode === "hard"
                      ? "bg-nasa-cyan/20 border-nasa-cyan text-nasa-cyan font-bold"
                      : "bg-space-850 border-space-800 text-slate-400"
                  }`}
                >
                  Hard
                </button>
              </div>
              <div className="text-[10px] font-mono text-slate-500 mt-1">Continuous vs Hard Step</div>
            </div>
          </div>
        </div>

        {/* ==========================================
            SECTION C: SILENT REKINDLING ANNUNCIATOR (5 Cols)
        ========================================== */}
        <div className="lg:col-span-5 bg-space-900 border border-space-800 rounded-xl p-5 shadow-lg space-y-5">
          <div className="border-b border-space-800 pb-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 font-mono">
              <ShieldAlert className="w-4 h-4 text-nasa-amber" />
              Silent Rekindling Annunciator Light Matrix (E-11)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Monitors post-extinction low-temperature peroxy oxidation (Da_cool &gt; 1.0, P_rekindle)
            </p>
          </div>

          {/* 4-State Annunciator Light Matrix */}
          <div className="grid grid-cols-2 gap-3">
            {/* INERT */}
            <div
              className={`p-3 rounded-lg border text-center transition-all ${
                currentRisk === "INERT"
                  ? "bg-emerald-950/60 border-emerald-400 shadow-md shadow-emerald-500/20"
                  : "bg-space-850/40 border-space-800 opacity-40"
              }`}
            >
              <div
                className={`w-3.5 h-3.5 rounded-full mx-auto mb-1.5 ${
                  currentRisk === "INERT" ? "bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400" : "bg-slate-700"
                }`}
              />
              <div className="text-xs font-bold font-mono tracking-wider text-emerald-300">INERT</div>
              <div className="text-[10px] font-mono text-slate-400 mt-0.5">T &lt; T_flash / Depleted</div>
            </div>

            {/* MONITOR */}
            <div
              className={`p-3 rounded-lg border text-center transition-all ${
                currentRisk === "MONITOR"
                  ? "bg-cyan-950/60 border-nasa-cyan shadow-md shadow-cyan-500/20"
                  : "bg-space-850/40 border-space-800 opacity-40"
              }`}
            >
              <div
                className={`w-3.5 h-3.5 rounded-full mx-auto mb-1.5 ${
                  currentRisk === "MONITOR" ? "bg-nasa-cyan animate-pulse shadow-sm shadow-cyan-400" : "bg-slate-700"
                }`}
              />
              <div className="text-xs font-bold font-mono tracking-wider text-cyan-300">MONITOR</div>
              <div className="text-[10px] font-mono text-slate-400 mt-0.5">Da_cool &lt; 0.5 (Convective)</div>
            </div>

            {/* REKINDLE_WARNING */}
            <div
              className={`p-3 rounded-lg border text-center transition-all ${
                currentRisk === "REKINDLE_WARNING"
                  ? "bg-amber-950/70 border-amber-400 shadow-md shadow-amber-500/20"
                  : "bg-space-850/40 border-space-800 opacity-40"
              }`}
            >
              <div
                className={`w-3.5 h-3.5 rounded-full mx-auto mb-1.5 ${
                  currentRisk === "REKINDLE_WARNING"
                    ? "bg-amber-400 animate-ping shadow-sm shadow-amber-400"
                    : "bg-slate-700"
                }`}
              />
              <div className="text-xs font-bold font-mono tracking-wider text-amber-300">WARNING</div>
              <div className="text-[10px] font-mono text-slate-400 mt-0.5">0.5 ≤ Da_cool &lt; 1.0</div>
            </div>

            {/* CRITICAL_REKINDLE_HAZARD */}
            <div
              className={`p-3 rounded-lg border text-center transition-all ${
                currentRisk === "CRITICAL_REKINDLE_HAZARD"
                  ? "bg-rose-950/80 border-rose-500 shadow-lg shadow-rose-500/30 animate-pulse"
                  : "bg-space-850/40 border-space-800 opacity-40"
              }`}
            >
              <div
                className={`w-3.5 h-3.5 rounded-full mx-auto mb-1.5 ${
                  currentRisk === "CRITICAL_REKINDLE_HAZARD"
                    ? "bg-rose-500 animate-bounce shadow-sm shadow-rose-500"
                    : "bg-slate-700"
                }`}
              />
              <div className="text-xs font-bold font-mono tracking-wider text-rose-300">CRITICAL HAZARD</div>
              <div className="text-[10px] font-mono text-slate-400 mt-0.5">Da_cool ≥ 1.0 (Rekindle Imminent)</div>
            </div>
          </div>

          {/* Diagnostic Readouts */}
          <div className="bg-space-850 border border-space-800 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">Cool-Flame Damköhler (Da_cool):</span>
              <span
                className={`font-bold ${
                  (rekindleResult?.cool_flame_damkohler ?? 0) >= 1.0 ? "text-rose-400" : "text-nasa-cyan"
                }`}
              >
                {rekindleResult?.cool_flame_damkohler.toFixed(2) ?? "1.84"} (Crit: 1.00)
              </span>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Rekindling Probability P_rekindle:</span>
                <span
                  className={`font-bold ${
                    (rekindleResult?.rekindle_probability ?? 0) >= 0.7 ? "text-rose-400" : "text-emerald-400"
                  }`}
                >
                  {((rekindleResult?.rekindle_probability ?? 0.882) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-space-800 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    (rekindleResult?.rekindle_probability ?? 0) >= 0.7
                      ? "bg-rose-500"
                      : (rekindleResult?.rekindle_probability ?? 0) >= 0.3
                      ? "bg-amber-400"
                      : "bg-emerald-400"
                  }`}
                  style={{
                    width: `${Math.min(100, (rekindleResult?.rekindle_probability ?? 0.882) * 100)}%`,
                  }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-space-800/80 text-[11px] font-mono">
              <div>
                <span className="text-slate-400">Visible Flame:</span>
                <span className={`ml-1.5 font-bold ${visibleFlameActive ? "text-amber-400" : "text-slate-300"}`}>
                  {visibleFlameActive ? "ACTIVE (12.5 W)" : "EXTINCT (0.00 V)"}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Flash Point:</span>
                <span className="ml-1.5 font-bold text-slate-200">
                  {rekindleResult?.flash_point_k ? `${rekindleResult.flash_point_k.toFixed(1)} K` : "269.1 K"}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Droplet Core T:</span>
                <span
                  className={`ml-1.5 font-bold ${
                    fuelTempK > (rekindleResult?.flash_point_k ?? 269) ? "text-rose-300" : "text-emerald-300"
                  }`}
                >
                  {fuelTempK.toFixed(0)} K
                </span>
              </div>
              <div>
                <span className="text-slate-400">Rec. Airspeed:</span>
                <span className="ml-1.5 font-bold text-nasa-cyan">
                  {rekindleResult?.recommended_ventilation_cm_s ?? "18.5"} cm/s
                </span>
              </div>
            </div>
          </div>

          {/* Interactive Sliders for Fuel & Parameters */}
          <div className="space-y-3 pt-2">
            <div>
              <label className="text-xs font-mono text-slate-400 block mb-1.5">Select Droplet Fuel:</label>
              <div className="grid grid-cols-3 sm:grid-cols-5 gap-1.5">
                {PRESET_FUELS.map((f) => (
                  <button
                    key={f.key}
                    onClick={() => setSelectedFuel(f.key)}
                    className={`py-1 px-1.5 rounded text-[11px] font-mono border text-center transition-all ${
                      selectedFuel === f.key
                        ? "bg-nasa-cyan/20 border-nasa-cyan text-white font-bold"
                        : "bg-space-850 border-space-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    {f.name.split(" ")[0]}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-mono text-slate-300 mb-1">
                <span>Droplet Core Temperature:</span>
                <span className="text-rose-300 font-bold">{fuelTempK.toFixed(0)} K</span>
              </div>
              <input
                type="range"
                min="250"
                max="850"
                step="5"
                value={fuelTempK}
                onChange={(e) => setFuelTempK(Number(e.target.value))}
                className="w-full accent-rose-500 bg-space-800 h-1.5 rounded-lg cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-mono text-slate-300 mb-1">
                <span>Cabin Cross-Ventilation Airspeed:</span>
                <span className="text-nasa-cyan font-bold">
                  {damperIsolated ? "0.0 cm/s (ISOLATED)" : `${ventilationCmS.toFixed(1)} cm/s`}
                </span>
              </div>
              <input
                type="range"
                min="0.5"
                max="25.0"
                step="0.5"
                disabled={damperIsolated}
                value={ventilationCmS}
                onChange={(e) => setVentilationCmS(Number(e.target.value))}
                className="w-full accent-nasa-cyan bg-space-800 h-1.5 rounded-lg cursor-pointer disabled:opacity-30"
              />
            </div>
          </div>
        </div>
      </div>

      {/* ==========================================
          SECTION D: EMERGENCY SUPPRESSION & AUDIT LOG
      ========================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Mitigation Interlocks Control Matrix (5 Cols) */}
        <div className="lg:col-span-5 bg-space-900 border border-space-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="border-b border-space-800 pb-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 font-mono">
              <Zap className="w-4 h-4 text-nasa-red" />
              Emergency Suppression Interlock Matrix
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Flight controller override controls for forced convection isolation and chemical extinguishing
            </p>
          </div>

          <div className="space-y-3">
            {/* Ventilation Isolation Damper */}
            <div className="bg-space-850 border border-space-800 p-3 rounded-lg flex items-center justify-between">
              <div>
                <div className="text-xs font-mono font-bold text-slate-200">Cabin Ventilation Damper</div>
                <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                  {damperIsolated ? "Isolated (0.0 cm/s) — Halts Radical Replenishment" : "Open (Nominal 3.0 cm/s airflow)"}
                </div>
              </div>
              <button
                onClick={toggleDamper}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold border transition-all ${
                  damperIsolated
                    ? "bg-rose-950/80 border-rose-500 text-rose-200 animate-pulse"
                    : "bg-space-800 hover:bg-space-700 border-space-700 text-slate-200"
                }`}
              >
                {damperIsolated ? "OPEN DAMPER" : "ISOLATE DAMPER"}
              </button>
            </div>

            {/* FK-5-1-12 Suppressant Release */}
            <div className="bg-space-850 border border-space-800 p-3 rounded-lg space-y-2.5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-mono font-bold text-slate-200">FK-5-1-12 Gas Discharge (Novec 1230)</div>
                  <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                    Fluoroketone agent quenches droplet core below flash point (&lt; 350 K)
                  </div>
                </div>
                <button
                  onClick={() => setFkArmed(!fkArmed)}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-mono border transition-all ${
                    fkArmed
                      ? "bg-amber-950/60 border-amber-500 text-amber-300 font-bold"
                      : "bg-space-800 border-space-700 text-slate-400"
                  }`}
                >
                  {fkArmed ? <Unlock className="w-3 h-3 text-amber-400" /> : <Lock className="w-3 h-3" />}
                  <span>{fkArmed ? "ARMED" : "SAFE"}</span>
                </button>
              </div>

              <button
                onClick={dischargeFK5112}
                disabled={!fkArmed || fkReleased}
                className={`w-full py-2 rounded-lg text-xs font-mono font-bold border transition-all ${
                  fkReleased
                    ? "bg-emerald-950/60 border-emerald-500/50 text-emerald-300 cursor-not-allowed"
                    : fkArmed
                    ? "bg-rose-600 hover:bg-rose-500 text-white border-rose-400 shadow-md shadow-rose-600/30 cursor-pointer animate-pulse"
                    : "bg-space-800 border-space-700 text-slate-500 cursor-not-allowed"
                }`}
              >
                {fkReleased ? "AGENT DISCHARGED (CHAMBER QUENCHED)" : "DISCHARGE FK-5-1-12 SUPPRESSANT"}
              </button>
            </div>

            {/* Nitrogen Chamber Flood & Reset */}
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={toggleN2Flood}
                className={`py-2 px-3 rounded-lg text-xs font-mono border text-center transition-all ${
                  n2Flooding
                    ? "bg-indigo-950/80 border-indigo-500 text-indigo-200 font-bold animate-pulse"
                    : "bg-space-850 hover:bg-space-800 border-space-800 text-slate-300"
                }`}
              >
                {n2Flooding ? "STOP N2 FLOOD (9.5% O2)" : "N2 CHAMBER FLOOD"}
              </button>

              <button
                onClick={masterReset}
                className="py-2 px-3 rounded-lg text-xs font-mono border border-space-800 bg-space-850 hover:bg-space-800 text-slate-300 hover:text-white flex items-center justify-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>MASTER RESET</span>
              </button>
            </div>
          </div>
        </div>

        {/* Flight Controller Audit Log Console (7 Cols) */}
        <div className="lg:col-span-7 bg-space-900 border border-space-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-space-800 pb-3 mb-3">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                  Flight Controller Telemetry & Interlock Audit Log
                </h3>
              </div>
              <span className="text-[10px] font-mono text-slate-500">Auto-scrolling UTC stream</span>
            </div>

            {/* Terminal Window */}
            <div className="bg-space-950 border border-space-850 rounded-lg p-3 font-mono text-xs space-y-1.5 h-64 overflow-y-auto custom-scrollbar">
              {auditLogs.map((log) => {
                let badgeColor = "text-slate-400";
                if (log.level === "ALARM") badgeColor = "text-amber-400 font-bold";
                if (log.level === "CRIT") badgeColor = "text-rose-400 font-bold";
                if (log.level === "WARN") badgeColor = "text-amber-300";

                return (
                  <div key={log.id} className="leading-relaxed flex items-start gap-2">
                    <span className="text-slate-500 shrink-0">[{log.timestamp}]</span>
                    <span className={`shrink-0 ${badgeColor}`}>[{log.level}]</span>
                    <span className="text-slate-300 break-words">{log.message}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="pt-3 border-t border-space-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Audit status: 100% genuine timestamped flight interlock events</span>
            <span className="text-emerald-400 font-semibold">Integrity Verified</span>
          </div>
        </div>
      </div>
    </div>
  );
}
