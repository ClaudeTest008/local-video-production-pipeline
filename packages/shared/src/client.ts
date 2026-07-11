/** Typed API client for the LVPP backend. Framework-free; works in web and Tauri. */

import type {
  AgentPreset,
  Brand,
  Learning,
  Opportunity,
  PipelineRun,
  SystemHealth,
  AgentProfile,
  Asset,
  ChatMessage,
  ComfyJob,
  ComfyStatus,
  Conversation,
  McpServer,
  Project,
  Prompt,
  ProviderStatus,
  RunResponse,
  Scene,
  Script,
  SubtitleTrack,
  Timeline,
  WorkflowDef,
  WorkflowSelection,
} from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`${status}: ${detail}`);
  }
}

export class ApiClient {
  constructor(private baseUrl: string = "http://127.0.0.1:8321/api") {}

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        detail = (await res.json()).detail ?? detail;
      } catch {
        /* non-JSON error body */
      }
      throw new ApiError(res.status, detail);
    }
    if (res.status === 204) return undefined as T;
    const text = await res.text();
    return (text ? JSON.parse(text) : undefined) as T;
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>(path);
  }
  post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) });
  }
  patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
  }
  put<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, { method: "PUT", body: JSON.stringify(body) });
  }
  delete(path: string): Promise<void> {
    return this.request<void>(path, { method: "DELETE" });
  }

  // Projects
  listProjects = () => this.get<Project[]>("/projects");
  createProject = (body: Partial<Project> & { name: string }) =>
    this.post<Project>("/projects", body);
  getProject = (id: number) => this.get<Project>(`/projects/${id}`);
  updateProject = (id: number, body: Partial<Project>) =>
    this.patch<Project>(`/projects/${id}`, body);
  deleteProject = (id: number) => this.delete(`/projects/${id}`);

  // Feature collections (uniform CRUD)
  listByProject = <T>(resource: string, projectId?: number) =>
    this.get<T[]>(`/${resource}${projectId ? `?project_id=${projectId}` : ""}`);
  scripts = (projectId?: number) => this.listByProject<Script>("scripts", projectId);
  scenes = (projectId?: number) => this.listByProject<Scene>("storyboard", projectId);
  prompts = (projectId?: number) => this.listByProject<Prompt>("prompts", projectId);
  assets = (projectId?: number) => this.listByProject<Asset>("assets", projectId);
  timelines = (projectId?: number) => this.listByProject<Timeline>("timelines", projectId);
  subtitles = (projectId?: number) => this.listByProject<SubtitleTrack>("subtitles", projectId);

  // Agents
  agentPresets = () => this.get<AgentPreset[]>("/agents/presets");
  listAgents = () => this.get<AgentProfile[]>("/agents");
  seedAgents = () => this.post<AgentProfile[]>("/agents/seed-defaults");
  runAgent = (id: number, input: string, opts?: { project_id?: number; conversation_id?: number }) =>
    this.post<RunResponse>(`/agents/${id}/run`, { input, ...opts });

  // Chat
  listConversations = (projectId?: number) =>
    this.get<Conversation[]>(`/chat/conversations${projectId ? `?project_id=${projectId}` : ""}`);
  createConversation = (body?: Partial<Conversation>) =>
    this.post<Conversation>("/chat/conversations", body);
  chatMessages = (conversationId: number) =>
    this.get<ChatMessage[]>(`/chat/conversations/${conversationId}/messages`);
  sendMessage = (conversationId: number, content: string) =>
    this.post<{ content: string; provider: string; model: string }>(
      `/chat/conversations/${conversationId}/messages`,
      { content },
    );

  // ComfyUI
  comfyStatus = () => this.get<ComfyStatus>("/comfyui/status");
  comfyModels = () => this.get<Record<string, string[]>>("/comfyui/models");
  comfyJobs = (projectId?: number) =>
    this.get<ComfyJob[]>(`/comfyui/jobs${projectId ? `?project_id=${projectId}` : ""}`);
  comfyQueue = (workflow: Record<string, unknown>, projectId?: number) =>
    this.post<{ job_id: number; prompt_id: string }>("/comfyui/queue", {
      workflow,
      project_id: projectId,
    });

  // MCP
  mcpCatalog = () => this.get<Omit<McpServer, keyof Timestamped>[]>("/mcp/catalog");
  mcpServers = () => this.get<McpServer[]>("/mcp/servers");
  mcpDiscover = () => this.post<{ added: string[]; total: number }>("/mcp/discover");
  mcpToggle = (id: number) => this.post<McpServer>(`/mcp/servers/${id}/toggle`);

  // Workflows
  listWorkflows = () => this.get<WorkflowDef[]>("/workflows");
  saveWorkflow = (body: { name: string; kind?: string; graph: Record<string, unknown> }) =>
    this.post<WorkflowDef>("/workflows", body);
  discoverWorkflows = () =>
    this.post<{ imported: { name: string }[]; failed: { name: string }[]; error?: string }>(
      "/workflows/discover",
    );
  uploadWorkflow = (name: string, workflow: Record<string, unknown>) =>
    this.post<WorkflowDef>("/workflows/upload", { name, workflow });
  updateWorkflow = (id: number, body: Partial<WorkflowDef>) =>
    this.patch<WorkflowDef>(`/workflows/${id}`, body);
  workflowSelection = () => this.get<WorkflowSelection>("/workflows/selection");
  workflowTemplates = () =>
    this.get<{ available: boolean; templates: Record<string, unknown> }>("/workflows/templates");

  // Settings
  providers = () => this.get<ProviderStatus[]>("/settings/providers");
  allSettings = () => this.get<Record<string, unknown>>("/settings");
  putSetting = (key: string, value: unknown) => this.put(`/settings/${key}`, { value });

  // Brands
  listBrands = () => this.get<Brand[]>("/brands");
  createBrand = (body: Partial<Brand> & { name: string }) => this.post<Brand>("/brands", body);
  updateBrand = (id: number, body: Partial<Brand>) => this.patch<Brand>(`/brands/${id}`, body);
  deleteBrand = (id: number) => this.delete(`/brands/${id}`);

  // Strategy
  listOpportunities = (brandId?: number) =>
    this.get<Opportunity[]>(
      `/strategy/opportunities${brandId ? `?brand_id=${brandId}` : ""}`,
    );
  generateOpportunities = (body: { brand_id?: number | null; seed_topic?: string; count?: number }) =>
    this.post<Opportunity[]>("/strategy/generate", body);
  approveOpportunity = (id: number) =>
    this.post<{ project_id: number }>(`/strategy/opportunities/${id}/approve`);
  rejectOpportunity = (id: number) =>
    this.post<Opportunity>(`/strategy/opportunities/${id}/reject`);

  // Pipeline
  pipelineStages = () => this.get<string[]>("/pipeline/stages");
  listRuns = (projectId?: number) =>
    this.get<PipelineRun[]>(`/pipeline/runs${projectId ? `?project_id=${projectId}` : ""}`);
  createRun = (projectId: number, mode: PipelineRun["mode"] = "assisted") =>
    this.post<PipelineRun>("/pipeline/runs", { project_id: projectId, mode });
  stepRun = (runId: number) =>
    this.post<{ entry: PipelineRun["log"][number]; run: PipelineRun }>(
      `/pipeline/runs/${runId}/step`,
    );
  runAll = (runId: number) =>
    this.post<{ entries: PipelineRun["log"]; run: PipelineRun }>(
      `/pipeline/runs/${runId}/run-all`,
    );

  // Knowledge
  listLearnings = (kind?: string) =>
    this.get<Learning[]>(`/knowledge${kind ? `?kind=${kind}` : ""}`);
  knowledgeDigest = (brandId?: number) =>
    this.get<{ digest: string }>(`/knowledge/digest${brandId ? `?brand_id=${brandId}` : ""}`);

  health = () => this.get<{ status: string; app: string }>("/health");
  systemHealth = () => this.get<SystemHealth>("/system/health");
  systemDetect = () => this.get<Record<string, any>>("/system/detect");
  setupStatus = () => this.get<{ complete: boolean }>("/system/setup/status");
  setupComplete = (body: { default_chat_provider?: string; default_chat_model?: string }) =>
    this.post<{ complete: boolean }>("/system/setup/complete", body);
}

interface Timestamped {
  id: number;
  created_at: string;
  updated_at: string;
}

export const api = new ApiClient(
  typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : "http://127.0.0.1:8321/api",
);
