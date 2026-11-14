/**
 * NASA Deep Space Exploration — Keplerian Orbit Simulation Engine
 * High-DPI Canvas2D Kepler Equation Solver (Newton-Raphson)
 * Supports Mercury to Neptune, Pluto, Moon / Lunar Gateway, and Transfer Orbits
 */

(function () {
  'use strict';

  // Constants
  const AU_M = 1.495978707e11;
  const GM_SUN = 1.32712440018e20;

  // Celestial bodies with Keplerian orbital elements
  const BODIES = [
    {
      name: 'Mercury',
      a_au: 0.387098,
      e: 0.20563,
      i_deg: 7.0,
      period_days: 87.97,
      color: '#94a3b8',
      radius_px: 3.5,
      speed_factor: 4.15,
    },
    {
      name: 'Venus',
      a_au: 0.723332,
      e: 0.00677,
      i_deg: 3.39,
      period_days: 224.7,
      color: '#f59e0b',
      radius_px: 5.0,
      speed_factor: 1.62,
    },
    {
      name: 'Earth',
      a_au: 1.000000,
      e: 0.01671,
      i_deg: 0.0,
      period_days: 365.25,
      color: '#38bdf8',
      radius_px: 5.5,
      speed_factor: 1.0,
      hasMoon: true,
    },
    {
      name: 'Mars',
      a_au: 1.523679,
      e: 0.09341,
      i_deg: 1.85,
      period_days: 686.98,
      color: '#ef4444',
      radius_px: 4.5,
      speed_factor: 0.53,
    },
    {
      name: 'Jupiter',
      a_au: 5.2044,
      e: 0.0485,
      i_deg: 1.3,
      period_days: 4332.59,
      color: '#fb923c',
      radius_px: 9.0,
      speed_factor: 0.084,
    },
    {
      name: 'Saturn',
      a_au: 9.5826,
      e: 0.0555,
      i_deg: 2.49,
      period_days: 10759.2,
      color: '#eab308',
      radius_px: 8.0,
      speed_factor: 0.034,
      hasRings: true,
    },
    {
      name: 'Uranus',
      a_au: 19.2184,
      e: 0.0464,
      i_deg: 0.77,
      period_days: 30685.4,
      color: '#67e8f9',
      radius_px: 6.5,
      speed_factor: 0.012,
    },
    {
      name: 'Neptune',
      a_au: 30.1104,
      e: 0.0095,
      i_deg: 1.77,
      period_days: 60189.0,
      color: '#6366f1',
      radius_px: 6.0,
      speed_factor: 0.006,
    },
    {
      name: 'Pluto',
      a_au: 39.482,
      e: 0.2488,
      i_deg: 17.16,
      period_days: 90560.0,
      color: '#c084fc',
      radius_px: 3.0,
      speed_factor: 0.004,
    },
  ];

  let canvas = null;
  let ctx = null;
  let animId = null;
  let timeEpoch = 0;
  let speedMultiplier = 1;
  let zoomLevel = 1.0;
  let activeFocus = 'Sun';
  let transferArc = null;

  /**
   * Newton-Raphson solver for Kepler's Equation: M = E - e*sin(E)
   */
  function solveKepler(M, e, tol = 1e-8, maxIter = 30) {
    let Mnorm = M % (2 * Math.PI);
    if (Mnorm < 0) Mnorm += 2 * Math.PI;
    let E = Mnorm;
    for (let i = 0; i < maxIter; i++) {
      const dE = (E - e * Math.sin(E) - Mnorm) / (1 - e * Math.cos(E));
      E -= dE;
      if (Math.abs(dE) < tol) break;
    }
    return E;
  }

  /**
   * Calculate true anomaly nu from eccentric anomaly E
   */
  function trueAnomaly(E, e) {
    return 2 * Math.atan2(Math.sqrt(1 + e) * Math.sin(E / 2), Math.sqrt(1 - e) * Math.cos(E / 2));
  }

  /**
   * Set high-DPI resolution backing store for crisp canvas rendering
   */
  function setupHighDPI() {
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const w = rect.width || 900;
    const h = rect.height || 520;

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.resetTransform();
    ctx.scale(dpr, dpr);
  }

  /**
   * Calculate non-linear pixel radius for visual planetary layout
   */
  function getVisualOrbitRadius(a_au) {
    // Non-linear scaling so outer planets remain visible on screen
    return Math.pow(a_au, 0.58) * 85 * zoomLevel;
  }

  /**
   * Main render frame
   */
  function render() {
    if (!ctx || !canvas) return;
    const rect = canvas.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;

    ctx.clearRect(0, 0, w, h);

    // Deep space void gradient
    const bgGrad = ctx.createRadialGradient(w / 2, h / 2, 20, w / 2, h / 2, w / 1.5);
    bgGrad.addColorStop(0, '#060e1e');
    bgGrad.addColorStop(1, '#020611');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h / 2;

    // Draw Central Sun
    ctx.beginPath();
    ctx.arc(cx, cy, 14 * zoomLevel, 0, Math.PI * 2);
    ctx.fillStyle = '#facc15';
    ctx.shadowColor = '#facc15';
    ctx.shadowBlur = 24 * zoomLevel;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Sun core flare
    ctx.beginPath();
    ctx.arc(cx, cy, 7 * zoomLevel, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    let earthPos = null;
    let marsPos = null;

    // Render planetary orbits & bodies
    BODIES.forEach((body) => {
      const visualR = getVisualOrbitRadius(body.a_au);

      // Draw Orbit Ellipse
      ctx.beginPath();
      // Apply eccentricity elongation along x-axis
      const rx = visualR * (1 + body.e);
      const ry = visualR * (1 - body.e);
      ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(30, 58, 95, 0.45)';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Solve position
      const meanMotion = (2 * Math.PI) / (body.period_days * 0.1);
      const M = timeEpoch * meanMotion;
      const E = solveKepler(M, body.e);
      const nu = trueAnomaly(E, body.e);
      const r_inst = visualR * (1 - body.e * Math.cos(E));

      const px = cx + Math.cos(nu) * r_inst;
      const py = cy + Math.sin(nu) * r_inst;

      if (body.name === 'Earth') earthPos = { x: px, y: py };
      if (body.name === 'Mars') marsPos = { x: px, y: py };

      // Draw Planet
      ctx.beginPath();
      ctx.arc(px, py, body.radius_px * zoomLevel, 0, Math.PI * 2);
      ctx.fillStyle = body.color;
      ctx.shadowColor = body.color;
      ctx.shadowBlur = 6 * zoomLevel;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Saturn Rings
      if (body.hasRings) {
        ctx.beginPath();
        ctx.ellipse(px, py, (body.radius_px + 8) * zoomLevel, (body.radius_px + 3) * zoomLevel, Math.PI / 6, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(234, 179, 8, 0.6)';
        ctx.lineWidth = 2 * zoomLevel;
        ctx.stroke();
      }

      // Moon & Artemis Gateway
      if (body.hasMoon) {
        const moonAngle = timeEpoch * 0.12;
        const moonDist = 12 * zoomLevel;
        const mx = px + Math.cos(moonAngle) * moonDist;
        const my = py + Math.sin(moonAngle) * moonDist;

        ctx.beginPath();
        ctx.arc(mx, my, 1.8 * zoomLevel, 0, Math.PI * 2);
        ctx.fillStyle = '#cbd5e1';
        ctx.fill();

        // Lunar Gateway beacon marker
        ctx.beginPath();
        ctx.arc(mx + 2, my - 2, 0.8 * zoomLevel, 0, Math.PI * 2);
        ctx.fillStyle = '#68e5ff';
        ctx.fill();
      }

      // Planet Label
      ctx.fillStyle = '#94a3b8';
      ctx.font = `${Math.max(9, Math.round(10 * zoomLevel))}px ui-monospace, monospace`;
      ctx.fillText(body.name, px + (body.radius_px + 4) * zoomLevel, py + 3);
    });

    // Draw active transfer trajectory arc if requested
    if (transferArc && earthPos && marsPos) {
      ctx.beginPath();
      ctx.moveTo(earthPos.x, earthPos.y);
      const midX = (earthPos.x + marsPos.x) / 2 + 30;
      const midY = (earthPos.y + marsPos.y) / 2 - 40;
      ctx.quadraticCurveTo(midX, midY, marsPos.x, marsPos.y);
      ctx.strokeStyle = '#68e5ff';
      ctx.setLineDash([4, 4]);
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#68e5ff';
      ctx.font = '10px ui-monospace, monospace';
      ctx.fillText('Hohmann Transfer Arc (Δv = 5.59 km/s)', midX - 40, midY - 8);
    }

    if (speedMultiplier > 0) {
      timeEpoch += 0.005 * speedMultiplier;
    }

    animId = requestAnimationFrame(render);
  }

  // Public control API
  window.SolarSimulation = {
    init: function (canvasId) {
      canvas = document.getElementById(canvasId);
      if (!canvas) return;
      ctx = canvas.getContext('2d');
      setupHighDPI();
      window.addEventListener('resize', setupHighDPI);
      if (!animId) render();
    },

    setSpeed: function (mult) {
      speedMultiplier = mult;
      const lbl = document.getElementById('speed-display');
      if (lbl) lbl.innerText = mult === 0 ? 'PAUSED' : mult + 'x';
    },

    setZoom: function (delta) {
      zoomLevel = Math.max(0.4, Math.min(2.5, zoomLevel + delta));
      const lbl = document.getElementById('zoom-display');
      if (lbl) lbl.innerText = Math.round(zoomLevel * 100) + '%';
    },

    resetView: function () {
      zoomLevel = 1.0;
      activeFocus = 'Sun';
      transferArc = null;
      const lbl = document.getElementById('zoom-display');
      if (lbl) lbl.innerText = '100%';
    },

    toggleTransferArc: function (enabled) {
      transferArc = enabled;
    },

    focusBody: function (name) {
      activeFocus = name;
    },
  };
})();
