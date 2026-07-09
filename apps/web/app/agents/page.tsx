"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type AgentProfile } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Input, Spinner, Textarea } from "@lvpp/ui";
import { Bot, Play } from "lucide-react";
import { useState } from "react";
import { useStudio } from "@/lib/store";

function AgentCard({
  agent,
  selected,
  onSelect,
}: {
  agent: AgentProfile;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button type="button" onClick={onSelect} className="w-full text-left">
      <Card
        className={`p-4 transition-colors hover:border-accent/40 ${selected ? "border-accent/60" : ""}`}
      >
        <div className="mb-1 flex items-center justify-between gap-2">
          <h2 className="truncate font-display text-[15px] font-semibold">{agent.name}</h2>
          <span className="font-mono text-[11px] text-muted">t={agent.temperature}</span>
        </div>
        <p className="mb-3 font-mono text-xs text-muted">{agent.role}</p>
        <div className="flex flex-wrap gap-1.5">
          {agent.provider || agent.model ? (
            <>
              {agent.provider && <Badge tone="accent">{agent.provider}</Badge>}
              {agent.model && <Badge tone="info">{agent.model}</Badge>}
            </>
          ) : (
            <Badge>app default</Badge>
          )}
        </div>
      </Card>
    </button>
  );
}

function AgentEditor({ agent }: { agent: AgentProfile }) {
  const queryClient = useQueryClient();
  const [systemPrompt, setSystemPrompt] = useState(agent.system_prompt);
  const [provider, setProvider] = useState(agent.provider);
  const [model, setModel] = useState(agent.model);
  const [temperature, setTemperature] = useState(String(agent.temperature));

  const save = useMutation({
    mutationFn: () =>
      api.patch<AgentProfile>(`/agents/${agent.id}`, {
        system_prompt: systemPrompt,
        provider,
        model,
        temperature: Number(temperature) || 0,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["agents"] }),
  });

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      <label className="block space-y-1 text-xs text-muted">
        System prompt
        <Textarea
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          rows={8}
          className="font-mono text-xs"
        />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="space-y-1 text-xs text-muted">
          Provider
          <Input
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            placeholder="app default"
          />
        </label>
        <label className="space-y-1 text-xs text-muted">
          Model
          <Input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="app default"
          />
        </label>
      </div>
      <label className="block space-y-1 text-xs text-muted">
        Temperature
        <Input
          type="number"
          step="0.1"
          min="0"
          max="2"
          value={temperature}
          onChange={(e) => setTemperature(e.target.value)}
        />
      </label>
      <div className="flex items-center gap-3">
        <Button type="submit" disabled={save.isPending}>
          Save
        </Button>
        {save.isSuccess && <span className="text-xs text-success">Saved</span>}
        {save.isError && (
          <span className="text-xs text-danger">{(save.error as Error).message}</span>
        )}
      </div>
    </form>
  );
}

function RunBox({ agent }: { agent: AgentProfile }) {
  const activeProjectId = useStudio((s) => s.activeProjectId);
  const [input, setInput] = useState("");
  const run = useMutation({
    mutationFn: () =>
      api.runAgent(agent.id, input, { project_id: activeProjectId ?? undefined }),
  });

  const runError =
    run.error instanceof ApiError && run.error.status === 502
      ? "Provider not reachable. Start Ollama (or configure a provider in Settings) and retry."
      : run.error instanceof Error
        ? run.error.message
        : null;

  return (
    <div className="space-y-3">
      <Textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        rows={3}
        placeholder={`Give ${agent.name} something to work on…`}
        aria-label="Agent input"
      />
      <Button
        onClick={() => {
          if (input.trim()) run.mutate();
        }}
        disabled={run.isPending || !input.trim()}
      >
        {run.isPending ? <Spinner className="size-3.5" /> : <Play className="size-4" />} Run
      </Button>
      {run.isError && runError && <p className="text-xs text-danger">{runError}</p>}
      {run.data && (
        <div className="rounded-md border border-edge bg-surface-2 p-3">
          <div className="mb-2 flex gap-1.5">
            <Badge tone="accent">{run.data.provider}</Badge>
            <Badge tone="info">{run.data.model}</Badge>
          </div>
          <p className="whitespace-pre-wrap text-sm">{run.data.content}</p>
        </div>
      )}
    </div>
  );
}

export default function AgentsPage() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const agents = useQuery({ queryKey: ["agents"], queryFn: api.listAgents });
  const seed = useMutation({
    mutationFn: api.seedAgents,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["agents"] }),
  });

  const selected = agents.data?.find((a) => a.id === selectedId) ?? null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">Agents</h1>
        <p className="mt-1 text-xs text-muted">
          The crew — each role carries its own system prompt, provider, and model.
        </p>
      </header>

      {agents.isLoading && <Spinner />}
      {agents.isError && (
        <EmptyState
          title="Backend not reachable"
          hint="Start it with: cd backend && uvicorn app.main:app --reload"
        />
      )}
      {agents.data?.length === 0 && (
        <EmptyState
          title="No agents yet"
          hint="Seed the default crew — writer, director, editor, and eleven more — then tune each one."
          action={
            <Button onClick={() => seed.mutate()} disabled={seed.isPending}>
              <Bot className="size-4" /> Seed the 14 default roles
            </Button>
          }
        />
      )}

      {agents.data && agents.data.length > 0 && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
          <div className="grid grid-cols-1 content-start gap-3 md:grid-cols-2 lg:col-span-3">
            {agents.data.map((a) => (
              <AgentCard
                key={a.id}
                agent={a}
                selected={a.id === selectedId}
                onSelect={() => setSelectedId(a.id)}
              />
            ))}
          </div>
          <div className="lg:col-span-2">
            {selected ? (
              <div className="space-y-4">
                <Card className="p-4">
                  <h2 className="mb-3 text-sm font-medium">{selected.name}</h2>
                  {/* key resets form state when selection changes */}
                  <AgentEditor key={selected.id} agent={selected} />
                </Card>
                <Card className="p-4">
                  <h2 className="mb-3 text-sm font-medium">Run</h2>
                  <RunBox key={selected.id} agent={selected} />
                </Card>
              </div>
            ) : (
              <EmptyState
                title="No agent selected"
                hint="Pick an agent to edit its prompt or give it a task."
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
