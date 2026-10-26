"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Source } from "@/lib/types";
import { Banner } from "@/components/ui";

interface Monitoring {
  monitoring_enabled: boolean; poll_interval_minutes: number; min_match_score: number;
  auto_submit_enabled: boolean; auto_submit_globally_enabled: boolean;
  auto_submit_effective: boolean; warning: string | null;
}

export default function HuntingPage() {
  const [mon, setMon] = useState<Monitoring | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    setMon(await api.get<Monitoring>("/api/monitoring"));
    setSources(await api.get<Source[]>("/api/sources"));
  }
  useEffect(() => { load(); }, []);

  async function save(patch: Partial<Monitoring>) {
    setMon(await api.put<Monitoring>("/api/monitoring", patch));
  }
  async function syncAll() {
    setBusy(true); setMsg(null);
    try {
      const res = await api.post<any[]>("/api/sources/sync-all");
      const total = res.reduce((s, r) => s + (r.jobs_new || 0), 0);
      setMsg(`Sync complete. ${total} new job(s) ingested.`);
      await load();
    } catch (e) { setMsg((e as Error).message); } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Automatic Job Hunting</h1>
      {mon?.warning && <Banner kind="warn">{mon.warning}</Banner>}

      {mon && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Monitoring</div>
              <div className="text-sm text-slate-500">Periodically discover and score new jobs.</div>
            </div>
            <button className={`btn ${mon.monitoring_enabled ? "btn-danger" : "btn-primary"}`}
              onClick={() => save({ monitoring_enabled: !mon.monitoring_enabled })}>
              {mon.monitoring_enabled ? "Disable" : "Enable"}
            </button>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="label">Polling interval (minutes)</label>
              <input className="input" type="number" min={1} defaultValue={mon.poll_interval_minutes}
                onBlur={(e) => save({ poll_interval_minutes: Number(e.target.value) })} />
            </div>
            <div>
              <label className="label">Minimum match score</label>
              <input className="input" type="number" min={0} max={100} defaultValue={mon.min_match_score}
                onBlur={(e) => save({ min_match_score: Number(e.target.value) })} />
            </div>
            <div>
              <label className="label">Auto-submit (your preference)</label>
              <div className="flex items-center gap-2 mt-2">
                <input type="checkbox" checked={mon.auto_submit_enabled}
                  onChange={(e) => save({ auto_submit_enabled: e.target.checked })} />
                <span className="text-sm text-slate-600">
                  Effective: <b>{mon.auto_submit_effective ? "ON" : "OFF"}</b>
                </span>
              </div>
              {!mon.auto_submit_globally_enabled && (
                <div className="text-xs text-amber-600 mt-1">System lock: AUTO_SUBMIT_ENABLED=false in .env</div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Sources</h2>
          <button className="btn btn-primary" disabled={busy} onClick={syncAll}>
            {busy ? "Syncing…" : "Sync all now"}
          </button>
        </div>
        {msg && <div className="text-sm text-slate-600 mb-3">{msg}</div>}
        <table className="w-full text-sm">
          <thead className="text-left text-slate-400 text-xs uppercase">
            <tr><th className="py-2">Source</th><th>Health</th><th>Last sync</th><th></th></tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id} className="border-t border-slate-100">
                <td className="py-2">{s.name} <span className="text-slate-400">({s.key})</span></td>
                <td>
                  <span className={`badge ${s.health === "ok" ? "bg-green-100 text-green-700" : s.health === "down" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-500"}`}>{s.health}</span>
                </td>
                <td className="text-slate-500">{s.last_sync_at ? new Date(s.last_sync_at).toLocaleString() : "—"}</td>
                <td className="text-right">
                  {["sample", "email_alert"].includes(s.key) && (
                    <button className="btn btn-secondary py-1"
                      onClick={async () => { await api.post(`/api/sources/${s.key}/sync`); await load(); }}>
                      Sync
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-xs text-slate-400 mt-3">
          Live Naukri discovery/submission requires an authorized integration (not available by default).
          Use sample data, authorized email alerts, or manual entry meanwhile.
        </p>
      </div>
    </div>
  );
}
