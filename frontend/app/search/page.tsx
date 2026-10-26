"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Banner } from "@/components/ui";

interface SearchResp {
  accessible: boolean; reason: string | null; jobs_retrieved: number;
  ingested: { jobs_found: number; jobs_new: number; jobs_duplicate: number };
  fallbacks: string[];
}

export default function SearchPage() {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [resp, setResp] = useState<SearchResp | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setBusy(true); setErr(null); setResp(null);
    try {
      setResp(await api.post<SearchResp>("/api/search/url", { url }));
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">URL-Based Search</h1>
      <Banner kind="info">
        Paste a Naukri.com job-search URL. The agent validates it, fetches via an authorized method with SSRF
        protection, parses any machine-readable listings, scores them, and ingests them. Login, CAPTCHA, and access
        controls are never bypassed.
      </Banner>

      <div className="card space-y-3">
        <label className="label">Naukri job-search URL</label>
        <div className="flex gap-2">
          <input className="input" placeholder="https://www.naukri.com/generative-ai-engineer-jobs"
            value={url} onChange={(e) => setUrl(e.target.value)} />
          <button className="btn btn-primary" disabled={busy || !url} onClick={run}>
            {busy ? "Searching…" : "Search"}
          </button>
        </div>
        <p className="text-xs text-slate-400">Only naukri.com domains are allowed.</p>
      </div>

      {err && <Banner kind="error">{err}</Banner>}

      {resp && (
        <div className="card space-y-3">
          <div className="flex items-center gap-2">
            <span className={`badge ${resp.accessible ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"}`}>
              {resp.accessible ? "Accessible" : "Not accessible"}
            </span>
            <span className="text-sm text-slate-600">{resp.jobs_retrieved} listing(s) retrieved</span>
          </div>
          {resp.reason && <p className="text-sm text-slate-600">{resp.reason}</p>}
          {resp.accessible && (
            <p className="text-sm text-green-700">
              Ingested: {resp.ingested.jobs_new} new, {resp.ingested.jobs_duplicate} duplicate. See the Jobs page.
            </p>
          )}
          {resp.fallbacks.length > 0 && (
            <div>
              <div className="text-sm font-medium text-slate-700">Alternatives:</div>
              <ul className="list-disc list-inside text-sm text-slate-600">
                {resp.fallbacks.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
