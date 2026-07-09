"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Script } from "@lvpp/shared";
import { Button, Card, EmptyState, Input, Spinner, Textarea } from "@lvpp/ui";
import { Download, FileText, Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useStudio } from "@/lib/store";

const WORDS_PER_MINUTE = 150;

function wordCount(text: string): number {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

function runtime(words: number): string {
  const totalSeconds = Math.round((words / WORDS_PER_MINUTE) * 60);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function exportMarkdown(title: string, content: string) {
  const blob = new Blob([content], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${title.trim() || "script"}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

function NewScriptForm({
  projectId,
  onCreated,
}: {
  projectId: number;
  onCreated: (id: number) => void;
}) {
  const [title, setTitle] = useState("");
  const queryClient = useQueryClient();
  const create = useMutation({
    mutationFn: () =>
      api.post<Script>("/scripts", { project_id: projectId, title, content: "" }),
    onSuccess: (script) => {
      queryClient.invalidateQueries({ queryKey: ["scripts", projectId] });
      setTitle("");
      onCreated(script.id);
    },
  });
  return (
    <form
      className="flex gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (title.trim()) create.mutate();
      }}
    >
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="New script title"
        aria-label="Script title"
      />
      <Button type="submit" size="sm" className="h-9" disabled={create.isPending || !title.trim()}>
        <Plus className="size-4" />
      </Button>
    </form>
  );
}

function Editor({ script, projectId }: { script: Script; projectId: number }) {
  const [content, setContent] = useState(script.content);
  const queryClient = useQueryClient();
  const save = useMutation({
    mutationFn: () => api.patch<Script>(`/scripts/${script.id}`, { content }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scripts", projectId] }),
  });
  const words = wordCount(content);
  return (
    <Card className="flex flex-col p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="truncate font-display text-sm font-semibold">{script.title}</h2>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => exportMarkdown(script.title, content)}
          >
            <Download className="size-3.5" /> Export .md
          </Button>
          <Button type="button" size="sm" onClick={() => save.mutate()} disabled={save.isPending}>
            Save
          </Button>
        </div>
      </div>
      <Textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="min-h-[60vh] flex-1 font-mono"
        placeholder="# Cold open&#10;&#10;Write the script in markdown. Narration, cues, everything."
        aria-label="Script content"
      />
      <div className="mt-3 flex items-center justify-between font-mono text-xs text-muted">
        <span>
          {words} words · ~{runtime(words)} runtime
        </span>
        <span>
          {save.isError && (
            <span className="text-danger">
              Save failed — check the backend and try again.
            </span>
          )}
          {save.isSuccess && !save.isPending && <span className="text-success">Saved</span>}
        </span>
      </div>
    </Card>
  );
}

function ScriptsWorkspace({ projectId }: { projectId: number }) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const scripts = useQuery({
    queryKey: ["scripts", projectId],
    queryFn: () => api.scripts(projectId),
  });

  if (scripts.isLoading) return <Spinner />;
  if (scripts.isError) {
    return (
      <EmptyState
        title="Backend not reachable"
        hint="Start it with: cd backend && uvicorn app.main:app --reload"
      />
    );
  }

  const list = scripts.data ?? [];
  const selected = list.find((s) => s.id === selectedId) ?? null;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-[16rem_1fr]">
      <div className="space-y-3">
        <NewScriptForm projectId={projectId} onCreated={setSelectedId} />
        {list.length === 0 ? (
          <p className="px-1 text-xs text-muted">
            No scripts yet — create one above to start writing.
          </p>
        ) : (
          <ul className="space-y-1">
            {list.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(s.id)}
                  className={`flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors ${
                    s.id === selectedId
                      ? "bg-surface-2 text-fg"
                      : "text-muted hover:bg-surface-2 hover:text-fg"
                  }`}
                >
                  <FileText className="size-3.5 shrink-0" />
                  <span className="truncate">{s.title}</span>
                  <span className="ml-auto font-mono text-[10px] text-muted">v{s.version}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      {selected ? (
        // ponytail: key remount seeds editor state per script, no sync effect needed
        <Editor key={selected.id} script={selected} projectId={projectId} />
      ) : (
        <EmptyState
          title="No script selected"
          hint="Pick a script from the list, or create one to start writing."
        />
      )}
    </div>
  );
}

export default function ScriptsPage() {
  const activeProjectId = useStudio((s) => s.activeProjectId);

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">Scripts</h1>
        <p className="mt-1 text-xs text-muted">
          Draft in markdown. Word count maps to runtime at {WORDS_PER_MINUTE} words per minute.
        </p>
      </header>
      {activeProjectId === null ? (
        <EmptyState
          title="No active project"
          hint="Scripts belong to a project. Open one from the projects page first."
          action={
            <Link href="/">
              <Button>Go to projects</Button>
            </Link>
          }
        />
      ) : (
        <ScriptsWorkspace projectId={activeProjectId} />
      )}
    </div>
  );
}
