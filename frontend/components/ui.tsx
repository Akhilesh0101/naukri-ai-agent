"use client";
import React from "react";

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    submitted: "bg-green-100 text-green-700",
    eligible: "bg-blue-100 text-blue-700",
    prepared: "bg-indigo-100 text-indigo-700",
    needs_attention: "bg-amber-100 text-amber-700",
    failed: "bg-red-100 text-red-700",
    skipped: "bg-slate-100 text-slate-500",
    scored: "bg-slate-100 text-slate-600",
    discovered: "bg-slate-100 text-slate-600",
    submitting: "bg-purple-100 text-purple-700",
  };
  return <span className={`badge ${map[status] || "bg-slate-100 text-slate-600"}`}>{status.replace(/_/g, " ")}</span>;
}

export function ScorePill({ score }: { score: number | null }) {
  if (score == null) return <span className="badge bg-slate-100 text-slate-500">—</span>;
  const cls = score >= 75 ? "bg-green-100 text-green-700" : score >= 50 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700";
  return <span className={`badge ${cls}`}>{score.toFixed(0)}</span>;
}

export function Empty({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="text-center py-12 text-slate-400">
      <div className="text-sm font-medium">{title}</div>
      {hint && <div className="text-xs mt-1">{hint}</div>}
    </div>
  );
}

export function Banner({ kind = "info", children }: { kind?: "info" | "warn" | "error"; children: React.ReactNode }) {
  const cls = kind === "warn" ? "bg-amber-50 border-amber-200 text-amber-800"
    : kind === "error" ? "bg-red-50 border-red-200 text-red-800"
    : "bg-blue-50 border-blue-200 text-blue-800";
  return <div className={`rounded-lg border px-4 py-3 text-sm ${cls}`}>{children}</div>;
}
