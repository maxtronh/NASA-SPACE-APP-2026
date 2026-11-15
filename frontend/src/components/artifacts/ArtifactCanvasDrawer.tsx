"use client";

import React, { useState, useEffect } from "react";
import { X, Maximize2, Minimize2, Code2, Copy, Check, Sparkles } from "lucide-react";
import { ScientificArtifact } from "@/types/artifacts";
import ArtifactRenderer from "./ArtifactRenderer";

interface Props {
  artifact: ScientificArtifact | null;
  onClose: () => void;
}

export default function ArtifactCanvasDrawer({ artifact, onClose }: Props) {
  const [showJson, setShowJson] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    if (artifact) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [artifact, onClose]);

  if (!artifact) return null;

  const handleCopyJson = () => {
    const text = JSON.stringify(artifact, null, 2);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text);
    } else {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label="Split Canvas Workspace"
        className="fixed inset-y-0 right-0 z-50 w-full md:w-[600px] lg:w-[680px] bg-space-950/95 backdrop-blur-xl border-l border-space-800 shadow-2xl flex flex-col transform transition-transform duration-300 ease-in-out"
      >
      {/* Drawer Header */}
      <div className="px-5 py-4 border-b border-space-800 flex items-center justify-between bg-space-900/50">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-nasa-cyan" />
          <span className="font-mono text-xs uppercase tracking-wider text-nasa-cyan font-bold">
            Split Canvas Workspace
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-800 text-slate-300 border border-space-700 capitalize">
            {artifact.artifact_type}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowJson(!showJson)}
            className={`p-1.5 rounded-lg border transition-colors flex items-center space-x-1 text-xs font-mono ${
              showJson
                ? "bg-nasa-cyan text-space-950 border-nasa-cyan"
                : "bg-space-900 text-slate-300 border-space-800 hover:text-white"
            }`}
            title="Inspect Raw JSON"
          >
            <Code2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">JSON</span>
          </button>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-space-900 text-slate-400 hover:text-white border border-space-800 transition-colors"
            title="Close Canvas"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Drawer Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {/* Render Primary Expanded Artifact */}
        <div className="space-y-4">
          <ArtifactRenderer artifact={artifact} />
        </div>

        {/* JSON Inspector */}
        {showJson && (
          <div className="space-y-2 pt-2 border-t border-space-800">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400">
              <span>Authentic Artifact Payload</span>
              <button
                onClick={handleCopyJson}
                className="flex items-center space-x-1 text-nasa-cyan hover:underline"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? "Copied" : "Copy Payload"}</span>
              </button>
            </div>
            <pre className="text-[11px] font-mono bg-black/80 p-3 rounded-lg border border-space-800 overflow-x-auto text-emerald-400">
              {JSON.stringify(artifact, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Drawer Footer */}
      <div className="px-5 py-3 border-t border-space-800 bg-space-900/30 flex items-center justify-between text-xs font-mono text-slate-400">
        <span>Zero-Fabrication Authenticated Record</span>
        <button
          onClick={onClose}
          className="text-xs text-slate-300 hover:text-white underline"
        >
          Return to Conversation
        </button>
      </div>
    </div>
    </>
  );
}
