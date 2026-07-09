"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Prompt } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Input, Spinner } from "@lvpp/ui";
import { GitBranch, Plus, Save } from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useState } from "react";
import { useStudio } from "@/lib/store";

const Editor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center">
      <Spinner />
    </div>
  ),
});

function NewPromptForm({ projectId, onDone }: { projectId: number; onDone: () => void }) {
  const [name, setName] = useState("");
  const queryClient = useQueryClient();
  const create = useMutation({
    mutationFn: () => api.post<Prompt>("/prompts", { project_id: projectId, name, text: "" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts", projectId] });
      onDone();
    },
  });
  return (
    <form
      className="flex gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (name.trim()) create.mutate();
      }}
    >
      <Input
        autoFocus
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Prompt name"
        aria-label="Prompt name"
        className="h-7 text-xs"
      />
      <Button type="submit" size="sm" disabled={create.isPending || !name.trim()}>
        Add
      </Button>
    </form>
  );
}

export default function PromptStudioPage() {
  const activeProjectId = useStudio((s) => s.activeProjectId);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const [creating, setCreating] = useState(false);
  const queryClient = useQueryClient();

  const prompts = useQuery({
    queryKey: ["prompts", activeProjectId],
    queryFn: () => api.prompts(activeProjectId ?? undefined),
    enabled: activeProjectId !== null,
  });

  const selected = prompts.data?.find((p) => p.id === selectedId) ?? null;
  const chain = selected
    ? (prompts.data ?? [])
        .filter((p) => p.name === selected.name)
        .sort((a, b) => a.version - b.version)
    : [];

  const select = (p: Prompt) => {
    setSelectedId(p.id);
    setDraft(p.text);
  };

  const save = useMutation({
    mutationFn: () => api.patch<Prompt>(`/prompts/${selected!.id}`, { text: draft }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["prompts", activeProjectId] }),
  });

  const saveAsNewVersion = useMutation({
    mutationFn: () =>
      api.post<Prompt>("/prompts", {
        project_id: activeProjectId,
        name: selected!.name,
        text: draft,
        kind: selected!.kind,
        version: selected!.version + 1,
        parent_id: selected!.id,
      }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["prompts", activeProjectId] });
      select(created);
    },
  });

  if (activeProjectId === null) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-8">
        <EmptyState
          title="No active project"
          hint="Prompts belong to a project. Open one first, then come back here."
          action={
            <Link href="/">
              <Button>Open a project</Button>
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">Prompt Studio</h1>
        <p className="mt-1 text-xs text-muted">
          Versioned prompts for every agent — edit, save, branch a new version when it drifts.
        </p>
      </header>

      {prompts.isLoading && <Spinner />}
      {prompts.isError && (
        <EmptyState
          title="Backend not reachable"
          hint="Start it with: cd backend && uvicorn app.main:app --reload"
        />
      )}

      {prompts.data && (
        <div className="grid grid-cols-[220px_1fr_170px] gap-4">
          {/* Prompt list */}
          <Card className="flex flex-col p-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-medium text-muted">Prompts</h2>
              <Button size="sm" variant="ghost" onClick={() => setCreating((c) => !c)}>
                <Plus className="size-3.5" />
              </Button>
            </div>
            {creating && (
              <div className="mb-2">
                <NewPromptForm projectId={activeProjectId} onDone={() => setCreating(false)} />
              </div>
            )}
            {prompts.data.length === 0 && !creating && (
              <p className="py-6 text-center text-xs text-muted">
                No prompts yet. Add the first one.
              </p>
            )}
            <ul className="space-y-1 overflow-y-auto">
              {prompts.data.map((p) => (
                <li key={p.id}>
                  <button
                    onClick={() => select(p)}
                    className={`w-full rounded-md px-2 py-1.5 text-left text-xs transition-colors ${
                      p.id === selectedId
                        ? "bg-surface-2 text-fg"
                        : "text-muted hover:bg-surface-2 hover:text-fg"
                    }`}
                  >
                    <span className="block truncate font-medium">{p.name}</span>
                    <span className="mt-0.5 flex items-center gap-1.5">
                      <Badge tone="accent">{p.kind}</Badge>
                      <span className="font-mono text-[10px]">v{p.version}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </Card>

          {/* Editor */}
          <Card className="flex min-h-[480px] flex-col overflow-hidden">
            {selected ? (
              <>
                <div className="flex items-center justify-between border-b border-edge px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{selected.name}</span>
                    <Badge>v{selected.version}</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    {save.isError && (
                      <span className="text-xs text-danger">
                        Save failed — check the backend and retry.
                      </span>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={saveAsNewVersion.isPending}
                      onClick={() => saveAsNewVersion.mutate()}
                    >
                      <GitBranch className="size-3.5" /> Save as v{selected.version + 1}
                    </Button>
                    <Button size="sm" disabled={save.isPending} onClick={() => save.mutate()}>
                      <Save className="size-3.5" /> Save
                    </Button>
                  </div>
                </div>
                <div className="flex-1">
                  <Editor
                    language="markdown"
                    theme="vs-dark"
                    value={draft}
                    onChange={(v) => setDraft(v ?? "")}
                    options={{ automaticLayout: true, minimap: { enabled: false }, wordWrap: "on" }}
                  />
                </div>
              </>
            ) : (
              <div className="flex flex-1 items-center justify-center">
                <p className="text-xs text-muted">Select a prompt to edit its text.</p>
              </div>
            )}
          </Card>

          {/* Version chain */}
          <Card className="p-3">
            <h2 className="mb-2 text-xs font-medium text-muted">Version chain</h2>
            {chain.length === 0 && (
              <p className="text-xs text-muted">
                Versions of the selected prompt appear here.
              </p>
            )}
            <ul className="space-y-1">
              {chain.map((p) => (
                <li key={p.id}>
                  <button
                    onClick={() => select(p)}
                    className={`flex w-full items-center justify-between rounded-md px-2 py-1.5 font-mono text-xs transition-colors ${
                      p.id === selectedId
                        ? "bg-accent/15 text-accent"
                        : "text-muted hover:bg-surface-2 hover:text-fg"
                    }`}
                  >
                    <span>v{p.version}</span>
                    <span className="text-[10px]">
                      {new Date(p.updated_at).toLocaleDateString()}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </div>
  );
}
