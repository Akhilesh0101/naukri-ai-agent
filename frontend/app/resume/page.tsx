"use client";
import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Profile } from "@/lib/types";
import { Banner } from "@/components/ui";

export default function ResumePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [resume, setResume] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [skillsText, setSkillsText] = useState("");

  async function load() {
    const p = await api.get<Profile>("/api/profile");
    setProfile(p);
    setSkillsText((p.skills || []).join(", "));
    try { setResume(await api.get<any>("/api/resume")); } catch {}
  }
  useEffect(() => { load(); }, []);

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true); setMsg(null);
    try {
      const form = new FormData();
      form.append("file", file);
      await api.upload("/api/resume", form);
      setMsg("Resume uploaded and parsed. Profile updated.");
      await load();
    } catch (err) {
      setMsg((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function saveSkills() {
    const skills = skillsText.split(",").map((s) => s.trim()).filter(Boolean);
    setProfile(await api.put<Profile>("/api/profile", { skills }));
    setMsg("Skills saved. Jobs rescored.");
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Resume &amp; Profile</h1>
      {msg && <Banner kind="info">{msg}</Banner>}

      <div className="card space-y-3">
        <h2 className="font-semibold">Active resume (PDF)</h2>
        {resume ? (
          <div className="text-sm text-slate-600">
            <div><b>{resume.filename}</b> · {(resume.size_bytes / 1024).toFixed(0)} KB · {new Date(resume.created_at).toLocaleString()}</div>
            <div className="text-slate-400 mt-1">Parsed skills: {(resume.parsed?.skills || []).length} · Experience: {resume.parsed?.experience_years ?? "unknown"}</div>
          </div>
        ) : <div className="text-sm text-slate-400">No resume uploaded yet.</div>}
        <label className="btn btn-primary cursor-pointer w-fit">
          {busy ? "Uploading…" : resume ? "Replace resume" : "Upload resume"}
          <input type="file" accept="application/pdf" className="hidden" onChange={upload} disabled={busy} />
        </label>
        <p className="text-xs text-slate-400">PDF only, max 10 MB. Parsing happens locally. Real content only — unknown fields are left blank, never invented.</p>
      </div>

      {profile && (
        <div className="card space-y-4">
          <h2 className="font-semibold">Parsed profile (editable)</h2>
          <div>
            <label className="label">Skills (comma-separated)</label>
            <textarea className="input h-24" value={skillsText} onChange={(e) => setSkillsText(e.target.value)} />
            <button className="btn btn-primary mt-2" onClick={saveSkills}>Save skills</button>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="label">Experience (years)</label>
              <input className="input" type="number" step="0.5" defaultValue={profile.experience_years ?? ""}
                onBlur={async (e) => setProfile(await api.put<Profile>("/api/profile", { experience_years: e.target.value ? Number(e.target.value) : null }))} />
            </div>
            <div>
              <label className="label">Preferred locations (comma-separated)</label>
              <input className="input" defaultValue={(profile.preferred_locations || []).join(", ")}
                onBlur={async (e) => setProfile(await api.put<Profile>("/api/profile", { preferred_locations: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) }))} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
