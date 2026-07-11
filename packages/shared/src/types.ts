/** Mirrors backend Pydantic schemas (backend/app/modules/*). */

export interface Timestamped {
  id: number;
  created_at: string;
  updated_at: string;
}

export const PIPELINE_STAGES = [
  "idea",
  "research",
  "script",
  "storyboard",
  "prompts",
  "images",
  "video",
  "voice",
  "music",
  "captions",
  "editing",
  "thumbnail",
  "seo",
  "publishing",
  "done",
] as const;

export type PipelineStage = (typeof PIPELINE_STAGES)[number];

export interface Brand extends Timestamped {
  name: string;
  description: string;
  voice: string;
  style: string;
  audience: string;
  guidelines: string;
  platforms: string[];
  schedule: Record<string, unknown>;
  goals: string;
  memory: Record<string, unknown>;
  meta: Record<string, unknown>;
}

export interface Opportunity extends Timestamped {
  brand_id: number | null;
  topic: string;
  angle: string;
  rationale: string;
  scores: Record<string, number>;
  status: "suggested" | "approved" | "rejected" | "produced";
  sources: string[];
  meta: Record<string, unknown>;
}

export interface PipelineRun extends Timestamped {
  project_id: number;
  mode: "manual" | "assisted" | "producer";
  status: "idle" | "running" | "done" | "error";
  current_stage: string;
  log: { stage: string; status: string; detail: string }[];
  meta: Record<string, unknown>;
}

export interface Learning extends Timestamped {
  brand_id: number | null;
  project_id: number | null;
  kind: string;
  key: string;
  insight: string;
  data: Record<string, unknown>;
  score: number;
}

export interface SystemHealth {
  backend: string;
  database: string;
  comfyui: {
    available: boolean;
    url: string;
    queue?: { running: number; pending: number };
    devices?: { name: string; vram_total_mb: number; vram_free_mb: number }[];
  };
  providers: { name: string; available: boolean }[];
  engines: { ffmpeg: boolean };
  pipeline: { running: number; errored: number };
  render_queue: { queued_jobs: number };
}

export interface Project extends Timestamped {
  name: string;
  brand_id: number | null;
  description: string;
  status: PipelineStage;
  idea: string;
  tags: string[];
  meta: Record<string, unknown>;
}

export interface Script extends Timestamped {
  project_id: number;
  title: string;
  content: string;
  version: number;
  meta: Record<string, unknown>;
}

export interface Scene extends Timestamped {
  project_id: number;
  order_index: number;
  title: string;
  description: string;
  prompt: string;
  duration_s: number;
  image_asset_id: number | null;
  meta: Record<string, unknown>;
}

export interface Prompt extends Timestamped {
  project_id: number;
  name: string;
  text: string;
  kind: string;
  version: number;
  parent_id: number | null;
  meta: Record<string, unknown>;
}

export interface Asset extends Timestamped {
  project_id: number;
  kind: "image" | "video" | "audio" | "music" | "thumbnail" | "other";
  path: string;
  source: string;
  tags: string[];
  meta: Record<string, unknown>;
}

export interface AgentProfile extends Timestamped {
  role: string;
  name: string;
  system_prompt: string;
  provider: string;
  model: string;
  temperature: number;
  settings: Record<string, unknown>;
  memory: Record<string, unknown>;
}

export interface AgentPreset {
  role: string;
  name: string;
  system_prompt: string;
}

export interface RunResponse {
  conversation_id: number;
  content: string;
  provider: string;
  model: string;
}

export interface Conversation extends Timestamped {
  project_id: number | null;
  title: string;
  provider: string;
  model: string;
}

export interface ChatMessage extends Timestamped {
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  meta: Record<string, unknown>;
}

export interface McpServer extends Timestamped {
  name: string;
  description: string;
  command: string;
  args: string[];
  env: Record<string, string>;
  enabled: boolean;
  source: string;
  meta: Record<string, unknown>;
}

export interface ComfyStatus {
  available: boolean;
  url: string;
  queue?: { running: number; pending: number };
}

export interface ComfyJob {
  id: number;
  project_id: number | null;
  prompt_id: string;
  status: "queued" | "done" | "error";
  outputs: { filename: string; subfolder: string; type: string; kind: string }[];
  created_at: string;
}

export interface Timeline extends Timestamped {
  project_id: number;
  name: string;
  tracks: TimelineTrack[];
  fps: number;
  resolution: string;
  meta: Record<string, unknown>;
}

export interface TimelineTrack {
  kind: "video" | "audio" | "caption";
  clips: { path: string; start?: number; duration?: number }[];
}

export interface SubtitleTrack extends Timestamped {
  project_id: number;
  language: string;
  segments: { start: number; end: number; text: string }[];
  meta: Record<string, unknown>;
}

export interface WorkflowDef extends Timestamped {
  name: string;
  kind: string;
  graph: Record<string, unknown>;
  version: number;
  parent_id: number | null;
  meta: Record<string, unknown>;
}

export interface ProviderStatus {
  name: string;
  available: boolean;
}

export interface SeoPack extends Timestamped {
  project_id: number;
  title: string;
  description: string;
  tags: string[];
  keywords: string[];
  meta: Record<string, unknown>;
}
