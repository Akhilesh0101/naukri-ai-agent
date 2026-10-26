"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Overview, ActivityLog } from "@/lib/types";
import { Banner } from "@/components/ui";

function Stat({ label, value, accent }: { label: string; value: number | string; accent?: string }) {
  return (
    <div className="card">
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className={`text-3xl font-bold mt-1 ${accent || "text-slate-800"}`}>{value}</div>
    </div>
  );
}

export default function OverviewPage() {
  const [ov, setOv] = useState<Overview | null>(null);
  const [acts, setActs] = useState<ActivityLog[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      setOv(await api.get<Overview>("/api/overview"));
      setActs(await api.get<ActivityLog[]>("/api/activity?limit=10"));
    } catch (e) { setErr((e as Error).message); }
  }
  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Overview</h1>
      {err && <Banner kind="error">Cannot reach backend API: {err}. Is the backend running on port 8000?</Banner>}
      {!ov?.auto_submit_enabled && (
        <Banner kind="warn">
          Automatic submission is <b>disabled</b>. Eligible jobs are prepared and routed to manual action until an
          authorized application provider is verified. This is the safe default.
        </Banner>
      )}
      {ov && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <Stat label="Jobs discovered" value={ov.total_jobs} />
          <Stat label="Matching threshold" value={ov.matching_jobs} accent="text-brand" />
          <Stat label="Submitted (confirmed)" value={ov.applications_submitted_confirmed} accent="text-green-600" />
          <Stat label="Prepared" value={ov.applications_prepared} accent="text-indigo-600" />
          <Stat label="Needs attention" value={ov.needs_attention} accent="text-amber-600" />
          <Stat label="Failed" value={ov.applications_failed} accent="text-red-600" />
          <Stat label="Sources healthy" value={`${ov.sources_healthy}/${ov.sources_total}`} />
          <Stat label="Monitoring" value={ov.monitoring_enabled ? "On" : "Off"} />
        </div>
      )}
      <div className="card">
        <h2 className="font-semibold mb-3">Recent activity</h2>
        {acts.length === 0 ? (
          <div className="text-sm text-slate-400">No activity yet. Sync a source or upload a resume to begin.</div>
        ) : (
          <ul className="space-y-2">
            {acts.map((a) => (
              <li key={a.id} className="text-sm flex gap-3">
                <span className={`badge ${a.level === "error" ? "bg-red-100 text-red-700" : a.level === "warning" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600"}`}>{a.category}</span>
                <span className="text-slate-600">{a.message}</span>
                <span className="ml-auto text-xs text-slate-400">{new Date(a.created_at).toLocaleString()}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
