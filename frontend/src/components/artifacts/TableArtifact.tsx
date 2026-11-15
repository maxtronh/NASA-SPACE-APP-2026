"use client";

import React, { useState, useMemo } from "react";
import { Table as TableIcon, Maximize2, Download, Search } from "lucide-react";
import { TableArtifact as TableArtifactType } from "@/types/artifacts";

interface Props {
  artifact: TableArtifactType;
  onExpand?: () => void;
}

export default function TableArtifact({ artifact, onExpand }: Props) {
  const [filterText, setFilterText] = useState("");

  const filteredRows = useMemo(() => {
    if (!filterText.trim()) return artifact.rows;
    const lower = filterText.toLowerCase();
    return artifact.rows.filter((row) =>
      Object.values(row).some((val) =>
        String(val ?? "").toLowerCase().includes(lower)
      )
    );
  }, [artifact.rows, filterText]);

  const handleExportCSV = () => {
    if (!artifact.rows.length) return;
    const headers = artifact.columns.map((c) => `"${c.label}"`).join(",");
    const rows = artifact.rows.map((row) =>
      artifact.columns
        .map((c) => {
          const val = row[c.key];
          return val === null || val === undefined ? '""' : `"${val}"`;
        })
        .join(",")
    );
    const csvContent = [headers, ...rows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${artifact.title.replace(/\s+/g, "_")}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-space-950/90 border border-nasa-cyan/40 rounded-xl p-4 shadow-xl space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-space-800">
        <div className="flex items-center space-x-2">
          <TableIcon className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-semibold text-white tracking-wide">{artifact.title}</h3>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleExportCSV}
            className="p-1 rounded bg-space-900 hover:bg-space-800 text-slate-300 hover:text-white transition-colors flex items-center space-x-1 text-[11px] font-mono px-2"
            title="Download CSV"
          >
            <Download className="w-3 h-3 text-cyan-400" />
            <span>CSV</span>
          </button>
          {onExpand && (
            <button
              onClick={onExpand}
              className="p-1 rounded bg-space-900 hover:bg-space-800 text-slate-300 hover:text-white transition-colors"
              title="Expand to Canvas"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {artifact.description && (
        <p className="text-xs text-slate-400">{artifact.description}</p>
      )}

      {/* Filter / Search input */}
      <div className="relative">
        <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
        <input
          type="text"
          aria-label="Filter table rows"
          placeholder="Filter rows..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          className="w-full pl-8 pr-3 py-1.5 bg-space-900/80 border border-space-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-nasa-cyan"
        />
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-lg border border-space-800 max-h-64">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-space-900/90 text-slate-400 font-mono text-[11px] uppercase tracking-wider sticky top-0 border-b border-space-800">
            <tr>
              {artifact.columns.map((col) => (
                <th key={col.key} className="px-3 py-2">
                  {col.label}
                  {col.unit && <span className="text-slate-500 lowercase ml-1">({col.unit})</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-space-800/60 font-mono text-xs">
            {filteredRows.length > 0 ? (
              filteredRows.map((row, idx) => (
                <tr key={idx} className="hover:bg-space-900/40 transition-colors">
                  {artifact.columns.map((col) => {
                    const rawVal = row[col.key];
                    let displayVal: string;
                    if (rawVal === null || rawVal === undefined) {
                      displayVal = "--"; // Preserving NULL
                    } else if (typeof rawVal === "number" && col.format) {
                      displayVal = rawVal.toFixed(2);
                    } else {
                      displayVal = String(rawVal);
                    }
                    return (
                      <td
                        key={col.key}
                        className={`px-3 py-2 whitespace-nowrap ${
                          rawVal === null || rawVal === undefined
                            ? "text-slate-600 italic"
                            : "text-slate-200"
                        }`}
                      >
                        {displayVal}
                      </td>
                    );
                  })}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={artifact.columns.length} className="px-3 py-4 text-center text-slate-500">
                  No matching evidence rows found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {artifact.source_investigation && (
        <div className="text-[11px] font-mono text-slate-500">
          Source Investigation: <span className="text-slate-300">{artifact.source_investigation}</span>
        </div>
      )}
    </div>
  );
}
