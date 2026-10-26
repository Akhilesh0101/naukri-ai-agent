"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Profile } from "@/lib/types";
import { Banner } from "@/components/ui";

interface SemanticStatus {
  enable_semantic: boolean; provider: string; model?: string;
  available: boolean; blend_weight: number; detail: string;
}

export default function SettingsPage() {
  const [p, setP] = useState<Profile | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [sem, setSem] = useState<SemanticStatus | null>(null);

  async function load() {
    setP(await api.get<Profile>("/api/profile"));
    try { setSem(await api.get<SemanticStatus>("/api/semantic")); } catch {}
  }
  useEffect(() => { load(); }, []);

  async function save(patch: Partial<Profile>) {
    setP(await api.put<Profile>("/api/profile", patch));
    setMsg("Saved.");
    setTimeout(() => setMsg(null), 1500);
  }

  if (!p) return <div className="text-slate-400">Loading…</div>;
  const wsum = p.weight_skills + p.weight_role + p.weight_experience + p.weight_location;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      {msg && <Banner kind="info">{msg}</Banner>}

      <div className="card space-y-3">
        <h2 className="font-semibold">Target roles</h2>
        <textarea className="input h-24" defaultValue={(p.target_titles || []).join("\n")}
          onBlur={(e) => save({ target_titles: e.target.value.split("\n").map((s) => s.trim()).filter(Boolean) })} />
        <p className="text-xs text-slate-400">One title per line.</p>
      </div>

      <div className="card grid md:grid-cols-2 gap-4">
        <div>
          <label className="label">Minimum match score</label>
          <input className="input" type="number" defaultValue={p.min_match_score} onBlur={(e) => save({ min_match_score: Number(e.target.value) })} />
        </div>
        <div>
          <label className="label">Minimum experience (years)</label>
          <input className="input" type="number" step="0.5" defaultValue={p.min_experience_years} onBlur={(e) => save({ min_experience_years: Number(e.target.value) })} />
        </div>
        <div>
          <label className="label">Polling interval (minutes)</label>
          <input className="input" type="number" defaultValue={p.poll_interval_minutes} onBlur={(e) => save({ poll_interval_minutes: Number(e.target.value) })} />
        </div>
        <div>
          <label className="label">Notification email</label>
          <input className="input" defaultValue={p.notify_email ?? ""} onBlur={(e) => save({ notify_email: e.target.value || null })} />
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="font-semibold">Matching weights</h2>
        <p className="text-xs text-slate-400">Current sum: {wsum.toFixed(2)} (auto-normalized at scoring time).</p>
        <div className="grid md:grid-cols-4 gap-4">
          {([["weight_skills", "Skills"], ["weight_role", "Role"], ["weight_experience", "Experience"], ["weight_location", "Location"]] as const).map(([k, label]) => (
            <div key={k}>
              <label className="label">{label}</label>
              <input className="input" type="number" step="0.05" defaultValue={(p as any)[k]}
                onBlur={(e) => save({ [k]: Number(e.target.value) } as any)} />
            </div>
          ))}
        </div>
      </div>

      <div className="card space-y-2">
        <h2 className="font-semibold">Semantic matching (optional, local)</h2>
        {sem ? (
          <div className="text-sm text-slate-600 space-y-1">
            <div>
              Status:{" "}
              <span className={`badge ${sem.enable_semantic && sem.available ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                {sem.enable_semantic ? (sem.available ? "active" : "enabled but unavailable") : "disabled"}
              </span>
            </div>
            <div>Provider: <b>{sem.provider}</b>{sem.model ? ` · ${sem.model}` : ""}</div>
            <div>Blend weight: {(sem.blend_weight * 100).toFixed(0)}%</div>
            <div className="text-xs text-slate-400">{sem.detail}</div>
          </div>
        ) : <div className="text-sm text-slate-400">Status unavailable.</div>}
        <p className="text-xs text-slate-400">
          Toggle with <code>ENABLE_SEMANTIC</code> and <code>EMBEDDING_PROVIDER</code> in <code>backend/.env</code>,
          then restart the backend. Uses your local Ollama embedding model by default.
        </p>
      </div>

      <div className="card space-y-2">
        <h2 className="font-semibold">Authorized provider configuration</h2>
        <Banner kind="warn">
          Automatic submission stays disabled until an authorized application provider is implemented and verified.
          The system-level lock is <b>AUTO_SUBMIT_ENABLED</b> in <code>backend/.env</code>. Until then, eligible jobs
          are prepared and routed to manual action.
        </Banner>
      </div>
    </div>
  );
}
