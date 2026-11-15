"use client";

import { useState } from "react";
import {
  Sparkles,
  Send,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  Tag,
  Gauge,
  Bot,
  User,
  HelpCircle,
  Flame,
  FileText,
  CornerDownLeft,
} from "lucide-react";
import GenerativeUIArtifact from "@/components/GenerativeUIArtifact";
import ArtifactRenderer from "@/components/artifacts/ArtifactRenderer";
import ArtifactCanvasDrawer from "@/components/artifacts/ArtifactCanvasDrawer";
import { queryScientificIntelligence } from "@/lib/api";
import { SIQueryResponse, ScientificArtifact } from "@/types";

interface ChatMessage {
  id: string;
  sender: "user" | "si";
  text: string;
  response?: SIQueryResponse;
  timestamp: string;
}

const PRESET_QUERIES = [
  "What are the droplet extinction dynamics of n-heptane in microgravity?",
  "How does low-speed concurrent airflow affect PMMA solid slab flame spread in BASS-II?",
  "Explain soot inception and flame structure in ACME methane diffusion flames.",
  "What is the capital of Mars and weather on Jupiter?", // Demonstrates explicit abstention
];

export default function IntelligenceChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "si",
      text: "Welcome to the Flame in Freefall Scientific Intelligence Assistant. I provide evidence-grounded answers derived strictly from authentic NASA microgravity combustion archives (FLEX, BASS-II, ACME). If evidence is lacking or questions fall outside the domain, I explicitly abstain rather than fabricate assertions.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeCanvasArtifact, setActiveCanvasArtifact] = useState<ScientificArtifact | null>(null);

  const handleSubmit = async (queryText: string) => {
    const q = queryText.trim();
    if (!q || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setLoading(true);

    try {
      const res = await queryScientificIntelligence(q);
      const siMsg: ChatMessage = {
        id: `si-${Date.now()}`,
        sender: "si",
        text: res.answer,
        response: res,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, siMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: `si-err-${Date.now()}`,
        sender: "si",
        text: "An error occurred while executing hybrid scientific intelligence retrieval.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-space-800">
        <div>
          <div className="flex items-center space-x-2 text-nasa-cyan text-xs font-mono mb-1">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Hybrid RAG + Evidence Verification Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-wide">
            Scientific Intelligence Assistant
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Natural language interrogation of NASA microgravity combustion flight archives with verifiable citations
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-500/40 px-3 py-1.5 rounded-lg">
          <ShieldCheck className="w-4 h-4" />
          <span>Zero Hallucination • Anti-Fabrication Safeguard</span>
        </div>
      </div>

      {/* Preset Queries Toolbar */}
      <div className="bg-space-900 border border-space-700/80 rounded-xl p-4 shadow-lg space-y-2">
        <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
          Recommended Scientific Queries:
        </span>
        <div className="flex flex-wrap gap-2">
          {PRESET_QUERIES.map((pq, idx) => (
            <button
              key={idx}
              onClick={() => handleSubmit(pq)}
              disabled={loading}
              className="text-xs bg-space-950 hover:bg-space-800 text-slate-300 hover:text-nasa-cyan border border-space-700 hover:border-nasa-cyan px-3 py-1.5 rounded-lg transition-colors text-left font-sans flex items-center space-x-1.5"
            >
              <Flame className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
              <span>{pq}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 bg-space-900 border border-space-700 rounded-2xl p-4 sm:p-6 shadow-xl overflow-y-auto space-y-6 min-h-[420px]">
        {messages.map((msg) => {
          const isUser = msg.sender === "user";

          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${
                isUser ? "flex-row-reverse space-x-reverse" : "flex-row"
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md ${
                  isUser
                    ? "bg-gradient-to-br from-cyan-600 to-blue-700 text-white"
                    : "bg-gradient-to-br from-amber-500 to-orange-600 text-white"
                }`}
              >
                {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-3xl rounded-2xl p-4 space-y-3 ${
                  isUser
                    ? "bg-space-800 border border-space-600 text-white rounded-tr-none"
                    : "bg-space-950 border border-space-700 text-slate-100 rounded-tl-none"
                }`}
              >
                {/* Header */}
                <div className="flex items-center justify-between text-xs font-mono text-slate-400 pb-1 border-b border-space-800">
                  <span className="font-semibold text-slate-300">
                    {isUser ? "Research Investigator" : "Flame in Freefall SI Engine"}
                  </span>
                  <span>{msg.timestamp}</span>
                </div>

                {/* Body Text */}
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>

                {/* SI Evidence Card (if response available) */}
                {msg.response && (
                  <div className="pt-3 border-t border-space-800 space-y-3">
                    {/* Abstention Warning Banner */}
                    {msg.response.abstention_flag && (
                      <div className="bg-amber-950/60 border border-amber-500/70 rounded-xl p-3 text-amber-200 text-xs flex items-start space-x-2.5">
                        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <div className="font-bold uppercase tracking-wider text-[11px]">
                            Explicit SI Abstention Triggered
                          </div>
                          <p className="text-amber-300 text-xs mt-0.5">
                            {msg.response.explainability.abstention_reason ||
                              "Confidence below scientific verification threshold. No verified NASA microgravity evidence exists for this query."}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Confidence Meter & Entity Tags */}
                    <div className="flex flex-wrap items-center justify-between gap-3 bg-space-900/80 p-3 rounded-lg border border-space-800 text-xs">
                      {/* Confidence Score Gauge */}
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-slate-400 uppercase text-[11px]">
                          Grounding Confidence:
                        </span>
                        <div className="flex items-center space-x-1.5">
                          <div className="w-24 bg-space-800 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-2 rounded-full ${
                                msg.response.confidence_score > 0.7
                                  ? "bg-emerald-400"
                                  : msg.response.confidence_score > 0.4
                                  ? "bg-amber-400"
                                  : "bg-rose-400"
                              }`}
                              style={{ width: `${msg.response.confidence_score * 100}%` }}
                            />
                          </div>
                          <span
                            className={`font-mono font-bold ${
                              msg.response.confidence_score > 0.7
                                ? "text-emerald-400"
                                : msg.response.confidence_score > 0.4
                                ? "text-amber-400"
                                : "text-rose-400"
                            }`}
                          >
                            {(msg.response.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      {/* Method */}
                      <div className="font-mono text-[11px] text-slate-400">
                        Method: <span className="text-nasa-cyan">{msg.response.explainability.retrieval_method}</span>
                      </div>
                    </div>

                    {/* Extracted Scientific Entities */}
                    {msg.response.explainability.matched_entities &&
                      msg.response.explainability.matched_entities.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[11px] font-mono text-slate-400 uppercase flex items-center space-x-1">
                            <Tag className="w-3.5 h-3.5 text-nasa-cyan" />
                            <span>Extracted Scientific Entities:</span>
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.response.explainability.matched_entities.map((tag, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 rounded bg-space-900 border border-space-700 text-slate-300 text-xs font-mono"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                    {/* Cited NASA Sources */}
                    {msg.response.citations && msg.response.citations.length > 0 && (
                      <div className="space-y-2 pt-1">
                        <span className="text-[11px] font-mono text-slate-400 uppercase flex items-center space-x-1">
                          <FileText className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Verifiable NASA Source Citations:</span>
                        </span>
                        <div className="grid grid-cols-1 gap-2">
                          {msg.response.citations.map((cite, idx) => (
                            <div
                              key={idx}
                              className="bg-space-900 border border-space-800 rounded-lg p-3 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                            >
                              <div>
                                <div className="font-bold text-white text-xs">{cite.title}</div>
                                <div className="text-slate-400 font-mono text-[11px]">
                                  Investigation: {cite.investigation_id}
                                </div>
                              </div>
                              <div className="flex items-center space-x-3">
                                <span className="text-emerald-400 font-mono text-[11px]">
                                  Relevance: {(cite.relevance_score * 100).toFixed(0)}%
                                </span>
                                <a
                                  href={cite.nasa_source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="px-2.5 py-1 rounded bg-nasa-cyan hover:bg-cyan-400 text-space-950 font-semibold text-[11px] inline-flex items-center space-x-1 transition-colors"
                                >
                                  <span>NTRS Link</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Discriminated Generative UI Scientific Artifacts (Upgrade 17) */}
                    {!msg.response.abstention_flag && msg.response.artifacts && msg.response.artifacts.length > 0 && (
                      <div className="space-y-3 pt-2">
                        <div className="flex items-center space-x-1.5 text-[11px] font-mono text-nasa-cyan uppercase tracking-wider">
                          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                          <span>Grounded Scientific Artifacts ({msg.response.artifacts.length}):</span>
                        </div>
                        <div className="grid grid-cols-1 gap-3">
                          {msg.response.artifacts.map((art, artIdx) => (
                            <ArtifactRenderer
                              key={artIdx}
                              artifact={art}
                              onExpand={(artifact) => setActiveCanvasArtifact(artifact)}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Interactive Generative UI Artifact Widget Fallback / Companion */}
                    {!msg.response.abstention_flag && (!msg.response.artifacts || msg.response.artifacts.length === 0) && (
                      <GenerativeUIArtifact
                        query={msg.response.query}
                        matchedEntities={msg.response.explainability.matched_entities}
                        investigationSlug={msg.response.citations?.[0]?.investigation_id || "flex-droplet-burning"}
                      />
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center space-x-3 text-slate-400 text-xs font-mono animate-pulse">
            <div className="w-8 h-8 rounded-xl bg-space-800 flex items-center justify-center text-nasa-cyan">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <span>Querying pgvector + BM25 hybrid indices & ranking evidence...</span>
          </div>
        )}
      </div>

      {/* Query Input Box */}
      <div className="bg-space-900 border border-space-700 rounded-xl p-3 shadow-lg">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit(inputQuery);
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            aria-label="Ask the scientific intelligence assistant"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask a scientific combustion query (e.g., 'What causes cool flames in heptane droplets?')..."
            disabled={loading}
            className="flex-1 bg-space-950 border border-space-700 text-white placeholder-slate-500 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-nasa-cyan transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !inputQuery.trim()}
            className="px-5 py-3 rounded-lg bg-nasa-cyan hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed text-space-950 font-bold text-sm transition-all flex items-center space-x-2 shadow-md shadow-cyan-500/20"
          >
            <span>Ask SI</span>
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Split Canvas Side Drawer (Upgrade 17) */}
      <ArtifactCanvasDrawer
        artifact={activeCanvasArtifact}
        onClose={() => setActiveCanvasArtifact(null)}
      />
    </div>
  );
}
