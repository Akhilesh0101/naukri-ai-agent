"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Application, Page } from "@/lib/types";
import { StatusBadge, Empty } from "@/components/ui";

export default function ApplicationsPage() {
  const [data, setData] = useState<Page<Application> | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  async function load() { setData(await api.get<Page<Application>>("/api/applications?page_size=100")); }
  useEffect(() => { load(); }, []);

  async function retry(id: number) {
    setBusy(id);
    try { await api.post(`/api/applications/${id}/retry`); await load(); }
    catch (e) { alert((e as Error).message); } finally { setBusy(null); }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Applications</h1>
      <div className="card">
        {!data || data.items.length === 0 ? (
          <Empty title="No applications yet" hint="Process eligible jobs from the Jobs page." />
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-slate-400 text-xs uppercase">
              <tr><th className="py-2">Job</th><th>Status</th><th>Provider</th><th>Submitted</th><th>Reason / action</th><th></th></tr>
            </thead>
            <tbody>
              {data.items.map((a) => (
                <tr key={a.id} className="border-t border-slate-100 align-top">
                  <td className="py-2">#{a.job_id}</td>
                  <td><StatusBadge status={a.status} /></td>
                  <td className="text-slate-500">{a.provider_key || "—"}</td>
                  <td className="text-slate-500">{a.submitted_at ? new Date(a.submitted_at).toLocaleString() : "—"}</td>
                  <td className="text-slate-600 max-w-sm">
                    {a.failure_reason || (a.confirmed ? "Confirmed" : "")}
                    {a.manual_url && (
                      <div><a className="text-brand underline" href={a.manual_url} target="_blank" rel="noreferrer">Open job to apply manually →</a></div>
                    )}
                  </td>
                  <td className="text-right">
                    {["failed", "needs_attention"].includes(a.status) && (
                      <button className="btn btn-secondary py-1" disabled={busy === a.id} onClick={() => retry(a.id)}>
                        {busy === a.id ? "…" : "Retry"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
