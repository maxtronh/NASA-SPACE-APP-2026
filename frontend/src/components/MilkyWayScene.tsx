"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

interface MilkyWaySceneProps {
  autoRotate: boolean;
}

function seededRandom(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function disposeScene(scene: THREE.Scene) {
  scene.traverse((object) => {
    if (object instanceof THREE.Mesh || object instanceof THREE.Points) {
      object.geometry.dispose();
      const materials = Array.isArray(object.material)
        ? object.material
        : [object.material];
      materials.forEach((material) => material.dispose());
    }
  });
}

export default function MilkyWayScene({ autoRotate }: MilkyWaySceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#020611");

    const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 2000);
    camera.position.set(0, 150, 360);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    } catch {
      setError("WebGL is unavailable in this browser. Try a browser with WebGL enabled.");
      return () => disposeScene(scene);
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor("#020611", 1);
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 90;
    controls.maxDistance = 720;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 0.45;
    controlsRef.current = controls;

    const random = seededRandom(2026);
    const backgroundCount = 4500;
    const backgroundPositions = new Float32Array(backgroundCount * 3);
    const backgroundColors = new Float32Array(backgroundCount * 3);
    for (let index = 0; index < backgroundCount; index += 1) {
      const offset = index * 3;
      backgroundPositions[offset] = (random() - 0.5) * 1800;
      backgroundPositions[offset + 1] = (random() - 0.5) * 1000;
      backgroundPositions[offset + 2] = (random() - 0.5) * 1800;
      const shade = 0.55 + random() * 0.45;
      backgroundColors[offset] = shade * 0.72;
      backgroundColors[offset + 1] = shade * 0.83;
      backgroundColors[offset + 2] = shade;
    }
    const backgroundGeometry = new THREE.BufferGeometry();
    backgroundGeometry.setAttribute(
      "position",
      new THREE.BufferAttribute(backgroundPositions, 3),
    );
    backgroundGeometry.setAttribute(
      "color",
      new THREE.BufferAttribute(backgroundColors, 3),
    );
    scene.add(
      new THREE.Points(
        backgroundGeometry,
        new THREE.PointsMaterial({
          size: 1.15,
          vertexColors: true,
          transparent: true,
          opacity: 0.85,
          sizeAttenuation: true,
        }),
      ),
    );

    const galaxy = new THREE.Group();
    scene.add(galaxy);

    const bulge = new THREE.Mesh(
      new THREE.SphereGeometry(23, 48, 48),
      new THREE.MeshBasicMaterial({ color: "#ffc46b" }),
    );
    galaxy.add(bulge);

    const glow = new THREE.Mesh(
      new THREE.SphereGeometry(42, 48, 48),
      new THREE.MeshBasicMaterial({
        color: "#ff9d42",
        transparent: true,
        opacity: 0.2,
        blending: THREE.AdditiveBlending,
        side: THREE.BackSide,
        depthWrite: false,
      }),
    );
    galaxy.add(glow);

    const armCount = 4;
    const starsPerArm = 2600;
    const armPositions = new Float32Array(armCount * starsPerArm * 3);
    const armColors = new Float32Array(armCount * starsPerArm * 3);
    for (let arm = 0; arm < armCount; arm += 1) {
      const armAngle = (arm / armCount) * Math.PI * 2;
      for (let star = 0; star < starsPerArm; star += 1) {
        const offset = (arm * starsPerArm + star) * 3;
        const radius = 30 + random() * 185;
        const spiral = (star / starsPerArm) * Math.PI * 4;
        const angle = armAngle + spiral * 0.52 + (random() - 0.5) * 0.34;
        armPositions[offset] = Math.cos(angle) * radius;
        armPositions[offset + 1] = (random() - 0.5) * 11;
        armPositions[offset + 2] = Math.sin(angle) * radius;

        const color = new THREE.Color().setHSL(
          0.09 + random() * 0.08,
          0.72,
          0.55 + (radius / 215) * 0.26,
        );
        armColors[offset] = color.r;
        armColors[offset + 1] = color.g;
        armColors[offset + 2] = color.b;
      }
    }
    const armGeometry = new THREE.BufferGeometry();
    armGeometry.setAttribute("position", new THREE.BufferAttribute(armPositions, 3));
    armGeometry.setAttribute("color", new THREE.BufferAttribute(armColors, 3));
    galaxy.add(
      new THREE.Points(
        armGeometry,
        new THREE.PointsMaterial({
          size: 1.2,
          vertexColors: true,
          transparent: true,
          opacity: 0.9,
          blending: THREE.AdditiveBlending,
          sizeAttenuation: true,
        }),
      ),
    );

    const solarMarker = new THREE.Mesh(
      new THREE.SphereGeometry(2.2, 16, 16),
      new THREE.MeshBasicMaterial({ color: "#68e5ff" }),
    );
    solarMarker.position.set(-78, 3, 92);
    galaxy.add(solarMarker);

    const resize = () => {
      const width = Math.max(container.clientWidth, 1);
      const height = Math.max(container.clientHeight, 1);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
    resize();

    let frame = 0;
    const clock = new THREE.Clock();
    const animate = () => {
      frame = window.requestAnimationFrame(animate);
      glow.material.opacity = 0.18 + Math.sin(clock.getElapsedTime() * 1.2) * 0.035;
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      window.cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      controls.dispose();
      controlsRef.current = null;
      disposeScene(scene);
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  useEffect(() => {
    if (controlsRef.current) controlsRef.current.autoRotate = autoRotate;
  }, [autoRotate]);

  return (
    <div
      ref={containerRef}
      role="img"
      aria-label="Interactive procedural visualization of a spiral galaxy. Drag to rotate and scroll to zoom."
      className="relative h-[55vh] min-h-[360px] w-full overflow-hidden rounded-xl border border-space-700 bg-[#020611]"
    >
      {error && (
        <div
          role="status"
          className="absolute inset-0 z-10 flex items-center justify-center bg-space-950/90 p-6 text-center text-sm text-amber-200"
        >
          {error}
        </div>
      )}
      <span className="sr-only">
        The Sun marker is illustrative. Galaxy stars and distances are generated for visualization.
      </span>
    </div>
  );
}
