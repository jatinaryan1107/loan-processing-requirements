export type Role = "ba" | "compliance" | "pm" | "developer";
export type View =
  "overview" | "gather" | "analyse" | "compliance" | "sdlc" | "export";
export interface Session {
  token: string;
  user: { id: string; name: string; role: Role };
  mode: string;
}
export interface ProjectSummary {
  id: string;
  name: string;
  description: string;
  jurisdiction: string;
  synthetic: boolean;
  created_at: string;
  requirement_count: number;
  approved_count: number;
}
export interface Source {
  id: string;
  source_name: string;
  stakeholder: string;
  text: string;
  created_at: string;
  extracted: boolean;
  synthetic: boolean;
  excluded?: boolean;
}
export interface Requirement {
  id: string;
  source_id: string;
  original_text: string;
  statement: string;
  kind: string;
  categories: string[];
  priority: string;
  acceptance_criteria: string[];
  justification: string;
  dependencies: string[];
  assumptions: string[];
  risk: string;
  confidence: number;
  status: string;
  history: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
}
export interface Flag {
  id: string;
  requirement_ids: string[];
  type: string;
  severity: string;
  message: string;
  question: string;
}
export interface Question {
  id: string;
  requirement_ids: string[];
  text: string;
  status: string;
  answer?: string;
  source_id?: string;
}
export interface PolicySource {
  id: string;
  title: string;
  clause: string;
  text: string;
  jurisdiction: string;
  version: string;
  effective_date: string;
  applicability: string;
  synthetic: boolean;
}
export interface Mapping {
  matches?: {
    requirement_id: string;
    keywords: string[];
    cosine_distance: number | null;
  }[];
  id: string;
  requirement_ids: string[];
  control: string;
  status: string;
  reason: string;
  interpretation: string;
  source: PolicySource | null;
  history: Record<string, unknown>[];
}
export type Factors = Record<
  | "stability"
  | "complexity"
  | "regulatory"
  | "security"
  | "stakeholders"
  | "change"
  | "legacy"
  | "testing"
  | "cadence",
  number
>;
export interface Ranking {
  model: string;
  score: number;
  max_score: number;
  rationale: string[];
}
export interface Phase {
  phase: string;
  activities: string[];
  roles: string[];
  deliverables: string[];
  security_checkpoint: string;
  approval_gate: string;
  entry: string;
  exit: string;
}
export interface Sdlc {
  factors: Factors;
  rankings: Ranking[];
  uncertainty: string;
  selected_model: string;
  status: string;
  workflow: Phase[];
  history: Record<string, unknown>[];
}
export interface Audit {
  id: string;
  at: string;
  actor: string;
  role: string;
  action: string;
  details: unknown;
}
export interface Run {
  id: string;
  at: string;
  agent: string;
  version: string;
  provider: string;
  input_ids: string[];
  outcome: string;
  confidence: number;
  evidence: string[];
}
export interface Project extends Omit<
  ProjectSummary,
  "requirement_count" | "approved_count"
> {
  updated_at: string;
  sources: Source[];
  requirements: Requirement[];
  flags: Flag[];
  questions: Question[];
  mappings: Mapping[];
  sdlc: Sdlc | null;
  audit: Audit[];
  runs: Run[];
  mode: string;
  final_ready: boolean;
  final_blockers: string[];
}

export type Mutate = (
  path: string,
  data?: unknown,
  method?: string,
  message?: string,
) => Promise<boolean>;
