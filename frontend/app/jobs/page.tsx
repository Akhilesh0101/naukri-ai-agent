"use client";
import React, { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { Job, Page } from "@/lib/types";
import { ScorePill, StatusBadge, Empty } from "@/components/ui";

export default function JobsPage() {
  const [data, setData] = useState<Page<Job> | null>(null);
  const [status, setStatus] = useState("");
  const [minScore, setMinScore] = useState("");
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("score");
  const [open, setOpen] = useState<number | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  const load = useCallback(async () => {
    const params = new URLSearchParams({ page: "1", page_size: "100", sort });
    if (status) params.set("status", status);
    if (minScore) params.set("min_score", minScore);
    if (q) params.set("q", q);
    setData(await api.get<Page<Job>>(`/api/jobs?${params.toString()}`));
  }, [status, minScore, q, sort]);
  useEffect(() => { load(); }, [load]);

  async function apply(id: number) {
    setBusy(id);
    try { await api.post(`/api/applications/job/${id}`); await load(); }
    catch (e) { alert((e as Error).message); } finally { setBusy(null); }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Jobs</h1>
      <div className="card flex flex-wrap gap-3 items-end">
        <div><label className="label">Search title</label><input className="input w-48" value={q} onChange={(e) => setQ(e.target.value)} /></div>
        <div>
          <label className="label">Status</label>
          <select className="input w-40" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All</option>
            {["discovered", "scored", "eligible", "prepared", "needs_attention", "submitted", "failed", "skipped"].map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div><label className="label">Min score</label><input className="input w-24" type="number" value={minScore} onChange={(e) => setMinScore(e.target.value)} /></div>
        <div>
          <label className="label">Sort</label>
          <select className="input w-36" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="score">Match score</option>
            <option value="posted">Posted date</option>
            <option value="discovered">Discovered</option>
          </select>
        </div>
      </div>

      <div className="card">
        {!data || data.items.length === 0 ? (
          <Empty title="No jobs" hint="Sync a source or run a URL search." />
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-slate-400 text-xs uppercase">
              <tr><th className="py-2">Score</th><th>Title</th><th>Company</th><th>Location</th><th>Posted</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {data.items.map((j) => (
                <React.Fragment key={j.id}>
                  <tr className="border-t border-slate-100">
                    <td className="py-2"><ScorePill score={j.match_score} /></td>
                    <td className="font-medium">{j.title}</td>
                    <td className="text-slate-600">{j.company}</td>
                    <td className="text-slate-500">{j.location}</td>
                    <td className="text-slate-400 text-xs">{j.posted_text || (j.posted_at ? new Date(j.posted_at).toLocaleDateString() : "—")}</td>
                    <td><StatusBadge status={j.status} /></td>
                    <td className="text-right whitespace-nowrap">
                      <button className="btn btn-secondary py-1" onClick={() => setOpen(open === j.id ? null : j.id)}>
                        {open === j.id ? "Hide" : "Details"}
                      </button>{" "}
                      {j.match_result?.eligible && !["submitted", "prepared", "needs_attention"].includes(j.status) && (
                        <button className="btn btn-primary py-1" disabled={busy === j.id} onClick={() => apply(j.id)}>
                          {busy === j.id ? "…" : "Process"}
                        </button>
                      )}
                    </td>
                  </tr>
                  {open === j.id && j.match_result && (
                    <tr className="bg-slate-50">
                      <td colSpan={7} className="p-4">
                        <div className="grid md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="font-medium mb-1">Score breakdown</div>
                            <ul className="text-slate-600 space-y-0.5">
                              <li>Skills: {j.match_result.skills_score}</li>
                              <li>Role: {j.match_result.role_score}</li>
                              <li>Experience: {j.match_result.experience_score}</li>
                              <li>Location: {j.match_result.location_score}</li>
                              {j.match_result.semantic_score != null && <li>Semantic: {j.match_result.semantic_score}</li>}
                            </ul>
                            <p className="text-xs text-slate-500 mt-2">{j.match_result.explanation}</p>
                          </div>
                          <div>
                            <div className="font-medium mb-1">Matched skills</div>
                            <div className="flex flex-wrap gap-1 mb-2">
                              {j.match_result.matched_skills.map((s) => <span key={s} className="badge bg-green-100 text-green-700">{s}</span>)}
                            </div>
                            <div className="font-medium mb-1">Missing skills</div>
                            <div className="flex flex-wrap gap-1 mb-2">
                              {j.match_result.missing_skills.length ? j.match_result.missing_skills.map((s) => <span key={s} className="badge bg-red-100 text-red-700">{s}</span>) : <span className="text-slate-400 text-xs">None</span>}
                            </div>
                            {j.match_result.mandatory_failures.length > 0 && (
                              <div className="text-xs text-red-600">Mandatory issues: {j.match_result.mandatory_failures.join("; ")}</div>
                            )}
                            {j.url && <a className="text-brand underline text-sm" href={j.url} target="_blank" rel="noreferrer">Open original listing →</a>}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
