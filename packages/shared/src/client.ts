/** Typed API client for the LVPP backend. Framework-free; works in web and Tauri. */

import type {
  AgentPreset,
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
  VoiceJob,
  WorkflowDef,
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
  voiceJobs = (projectId?: number) => this.listByProject<VoiceJob>("voice/jobs", projectId);

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

  // Settings
  providers = () => this.get<ProviderStatus[]>("/settings/providers");
  allSettings = () => this.get<Record<string, unknown>>("/settings");
  putSetting = (key: string, value: unknown) => this.put(`/settings/${key}`, { value });

  health = () => this.get<{ status: string; app: string }>("/health");
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
