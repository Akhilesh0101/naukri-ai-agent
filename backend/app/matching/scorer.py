"""Hybrid deterministic + optional semantic matching engine.

Score composition (weights configurable):
  - skills alignment   (default 45%)
  - role relevance     (default 25%)
  - experience compat  (default 20%)
  - location compat    (default 10%)

Returns a 0..100 score, component breakdown, matched/missing skills, evidence,
mandatory-requirement failures, eligibility flag, and a short explanation.

Mandatory eligibility rules OVERRIDE the score: a job can score high yet be
ineligible (for example seniority far above the candidate experience level).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.matching.skills import extract_skills_from_text, normalize_skills


@dataclass
class CandidateProfile:
    skills: list[str]
    experience_years: float | None
    target_titles: list[str]
    preferred_locations: list[str]
    min_experience_years: float = 2.0
    resume_text: str = ""


@dataclass
class JobPosting:
    title: str
    description: str = ""
    location: str | None = None
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    experience_min: float | None = None
    experience_max: float | None = None


@dataclass
class Weights:
    skills: float = 0.45
    role: float = 0.25
    experience: float = 0.20
    location: float = 0.10

    def normalized(self) -> "Weights":
        total = self.skills + self.role + self.experience + self.location
        if total <= 0:
            return Weights()
        return Weights(
            skills=self.skills / total,
            role=self.role / total,
            experience=self.experience / total,
            location=self.location / total,
        )


@dataclass
class ScoreResult:
    score: float
    skills_score: float
    role_score: float
    experience_score: float
    location_score: float
    semantic_score: float | None
    matched_skills: list[str]
    missing_skills: list[str]
    evidence: list[str]
    mandatory_failures: list[str]
    eligible: bool
    explanation: str
    details: dict


_REMOTE_TOKENS = {"remote", "anywhere", "work from home", "wfh", "hybrid"}


def _job_skill_sets(job: JobPosting) -> tuple[list[str], list[str]]:
    """Return (required, preferred) normalized skills.

    If the job provides no explicit skills, infer them from the description.
    Required and preferred are kept distinct and preferred excludes anything
    already required (avoid double counting).
    """
    required = normalize_skills(job.required_skills)
    preferred = normalize_skills(job.preferred_skills)
    if not required and not preferred:
        inferred = extract_skills_from_text(f"{job.title}. {job.description}")
        required = inferred
    preferred = [s for s in preferred if s not in set(required)]
    return required, preferred


def _score_skills(cand_skills: list[str], required: list[str], preferred: list[str]):
    cand = set(cand_skills)
    matched_req = [s for s in required if s in cand]
    matched_pref = [s for s in preferred if s in cand]
    missing_req = [s for s in required if s not in cand]

    # Required skills weighted 3x vs preferred to reflect importance.
    req_total = len(required)
    pref_total = len(preferred)
    weighted_have = len(matched_req) * 3 + len(matched_pref) * 1
    weighted_total = req_total * 3 + pref_total * 1

    if weighted_total == 0:
        # No skill signal available; neutral-ish score.
        score = 50.0
    else:
        score = 100.0 * weighted_have / weighted_total

    matched = matched_req + [s for s in matched_pref if s not in set(matched_req)]
    return round(score, 2), matched, missing_req


def _score_role(job_title: str, target_titles: list[str]) -> tuple[float, str]:
    if not target_titles:
        return 50.0, "No target titles configured."
    jt = job_title.lower()
    jt_tokens = set(jt.replace("/", " ").replace("-", " ").split())
    best = 0.0
    best_title = ""
    for t in target_titles:
        tl = t.lower()
        if tl and tl in jt:
            return 100.0, f"Job title matches target '{t}'."
        t_tokens = set(tl.replace("/", " ").replace("-", " ").split())
        if not t_tokens:
            continue
        overlap = len(jt_tokens & t_tokens) / len(t_tokens)
        if overlap > best:
            best = overlap
            best_title = t
    score = round(best * 100.0, 2)
    note = (
        f"Partial title overlap with '{best_title}'." if best_title else "No title overlap."
    )
    return score, note


def _score_experience(cand_years, job_min, job_max, cand_min_target):
    """Experience compatibility. Unknown candidate experience -> neutral 60."""
    if cand_years is None:
        return 60.0, "Candidate experience unknown; neutral score.", False
    if job_min is None and job_max is None:
        return 80.0, "Job experience requirement not specified.", False

    lo = job_min if job_min is not None else 0.0
    hi = job_max if job_max is not None else float("inf")

    if lo <= cand_years <= hi:
        return 100.0, f"Experience {cand_years}y fits required {lo}-{hi}y.", False

    if cand_years < lo:
        gap = lo - cand_years
        # Mandatory fail if candidate is more than 2y below minimum.
        mandatory_fail = gap > 2.0
        score = max(0.0, 100.0 - gap * 25.0)
        return round(score, 2), f"Below minimum by {gap:.1f}y (needs {lo}y).", mandatory_fail

    # cand_years > hi (overqualified) - mild penalty, never a mandatory fail.
    over = cand_years - hi
    score = max(40.0, 100.0 - over * 10.0)
    return round(score, 2), f"Above max by {over:.1f}y.", False


def _score_location(job_location, preferred_locations):
    if not job_location:
        return 70.0, "Job location unspecified."
    jl = job_location.lower()
    if any(tok in jl for tok in _REMOTE_TOKENS):
        return 100.0, "Remote/hybrid friendly."
    if not preferred_locations:
        return 70.0, "No preferred locations configured."
    for loc in preferred_locations:
        ll = loc.lower().strip()
        if ll and (ll in jl or jl in ll):
            return 100.0, f"Matches preferred location '{loc}'."
    # India-wide preference fallback.
    if any(p.lower().strip() in {"india", "pan india"} for p in preferred_locations):
        return 80.0, "Within India preference."
    return 30.0, "Outside preferred locations."


def score_job(
    cand: CandidateProfile,
    job: JobPosting,
    weights: Weights,
    min_match_score: float = 75.0,
    semantic_score: float | None = None,
    semantic_blend: float = 0.20,
) -> ScoreResult:
    w = weights.normalized()
    cand_skills = normalize_skills(cand.skills)
    required, preferred = _job_skill_sets(job)

    skills_score, matched, missing = _score_skills(cand_skills, required, preferred)
    role_score, role_note = _score_role(job.title, cand.target_titles)
    exp_score, exp_note, exp_mandatory_fail = _score_experience(
        cand.experience_years, job.experience_min, job.experience_max, cand.min_experience_years
    )
    loc_score, loc_note = _score_location(job.location, cand.preferred_locations)

    base = (
        skills_score * w.skills
        + role_score * w.role
        + exp_score * w.experience
        + loc_score * w.location
    )

    # Optionally blend semantic similarity. blend in [0,1]; 0 => deterministic only.
    blend = max(0.0, min(1.0, semantic_blend))
    if semantic_score is not None:
        final = base * (1.0 - blend) + semantic_score * blend
    else:
        final = base
    final = round(max(0.0, min(100.0, final)), 2)

    # ---- Mandatory eligibility rules (override score) ----
    mandatory_failures: list[str] = []
    if exp_mandatory_fail:
        mandatory_failures.append(exp_note)
    # If more than half of required skills are missing, flag mandatory gap.
    if required and len(missing) > len(required) / 2:
        mandatory_failures.append(
            f"Missing majority of required skills ({len(missing)}/{len(required)})."
        )

    eligible = (final >= min_match_score) and not mandatory_failures

    evidence: list[str] = []
    if matched:
        evidence.append("Matched skills: " + ", ".join(matched[:12]))
    evidence.append(role_note)
    evidence.append(exp_note)
    evidence.append(loc_note)

    explanation = (
        f"Score {final}/100 = skills {skills_score} (w {w.skills:.2f}), "
        f"role {role_score} (w {w.role:.2f}), experience {exp_score} (w {w.experience:.2f}), "
        f"location {loc_score} (w {w.location:.2f})."
    )
    if semantic_score is not None:
        explanation += f" Semantic similarity {semantic_score} blended at {int(blend * 100)}%."
    if mandatory_failures:
        explanation += " INELIGIBLE: " + "; ".join(mandatory_failures)

    return ScoreResult(
        score=final,
        skills_score=skills_score,
        role_score=role_score,
        experience_score=exp_score,
        location_score=loc_score,
        semantic_score=semantic_score,
        matched_skills=matched,
        missing_skills=missing,
        evidence=evidence,
        mandatory_failures=mandatory_failures,
        eligible=eligible,
        explanation=explanation,
        details={
            "required_skills": required,
            "preferred_skills": preferred,
            "weights": {
                "skills": w.skills,
                "role": w.role,
                "experience": w.experience,
                "location": w.location,
            },
        },
    )
