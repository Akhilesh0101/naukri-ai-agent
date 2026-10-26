export interface MatchResult {
  score: number;
  skills_score: number;
  role_score: number;
  experience_score: number;
  location_score: number;
  semantic_score: number | null;
  matched_skills: string[];
  missing_skills: string[];
  evidence: string[];
  mandatory_failures: string[];
  eligible: boolean;
  explanation: string | null;
}

export interface Job {
  id: number;
  source_key: string;
  source_job_id: string;
  title: string;
  company: string | null;
  location: string | null;
  description: string | null;
  url: string | null;
  posted_at: string | null;
  posted_text: string | null;
  discovered_at: string | null;
  experience_min: number | null;
  experience_max: number | null;
  required_skills: string[];
  preferred_skills: string[];
  match_score: number | null;
  status: string;
  match_result: MatchResult | null;
  created_at: string;
}

export interface Page<T> { items: T[]; total: number; page: number; page_size: number; }

export interface Profile {
  id: number;
  full_name: string | null;
  email: string | null;
  skills: string[];
  experience_years: number | null;
  target_titles: string[];
  preferred_locations: string[];
  min_experience_years: number;
  min_match_score: number;
  weight_skills: number;
  weight_role: number;
  weight_experience: number;
  weight_location: number;
  poll_interval_minutes: number;
  monitoring_enabled: boolean;
  auto_submit_enabled: boolean;
  notify_email: string | null;
}

export interface Overview {
  total_jobs: number;
  matching_jobs: number;
  applications_submitted_confirmed: number;
  applications_prepared: number;
  applications_failed: number;
  needs_attention: number;
  sources_healthy: number;
  sources_total: number;
  auto_submit_enabled: boolean;
  monitoring_enabled: boolean;
}

export interface Source {
  id: number;
  key: string;
  name: string;
  enabled: boolean;
  health: string;
  last_sync_at: string | null;
  last_error: string | null;
}

export interface Application {
  id: number;
  job_id: number;
  status: string;
  provider_key: string | null;
  provider_status: string | null;
  submitted_at: string | null;
  confirmed: boolean;
  failure_reason: string | null;
  manual_action_required: boolean;
  manual_url: string | null;
  created_at: string;
  attempts: { id: number; attempt_number: number; outcome: string; message: string | null }[];
}

export interface ActivityLog {
  id: number; level: string; category: string; message: string; created_at: string;
}
