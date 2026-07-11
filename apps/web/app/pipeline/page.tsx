"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type PipelineRun } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Spinner } from "@lvpp/ui";
import { FastForward, Play } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

function StageRow({ stage, entry }: { stage: string; entry?: PipelineRun["log"][number] }) {
  const tone =
    entry?.status === "done"
      ? "success"
      : entry?.status === "skipped"
        ? "neutral"
        : entry?.status === "error"
          ? "danger"
          : "info";
  return (
    <li className="flex items-start gap-3 border-b border-edge py-2 last:border-0">
      <span className="w-24 shrink-0 font-mono text-xs text-fg">{stage}</span>
      <Badge tone={tone}>{entry?.status ?? "pending"}</Badge>
      <span className="min-w-0 flex-1 truncate text-xs text-muted" title={entry?.detail}>
        {entry?.detail ?? ""}
      </span>
    </li>
  );
}

function RunPanel({ run }: { run: PipelineRun }) {
  const queryClient = useQueryClient();
  const stages = useQuery({ queryKey: ["stages"], queryFn: api.pipelineStages });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["runs"] });
  const step = useMutation({ mutationFn: () => api.stepRun(run.id), onSuccess: invalidate });
  const runAll = useMutation({ mutationFn: () => api.runAll(run.id), onSuccess: invalidate });
  const byStage = Object.fromEntries(run.log.map((e) => [e.stage, e]));
  const busy = step.isPending || runAll.isPending;

  return (
    <Card className="p-4">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge tone={run.status === "done" ? "success" : run.status === "error" ? "danger" : "info"}>
            {run.status}
          </Badge>
          <span className="font-mono text-xs text-muted">mode: {run.mode}</span>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => step.mutate()} disabled={busy || run.status === "done"}>
            <Play className="size-3.5" /> Next stage
          </Button>
          <Button size="sm" onClick={() => runAll.mutate()} disabled={busy || run.status === "done"}>
            <FastForward className="size-3.5" /> Run all
          </Button>
        </div>
      </div>
      {busy && (
        <p className="mb-2 flex items-center gap-2 text-xs text-muted">
          <Spinner /> agents working — local model latency applies
        </p>
      )}
      {(step.isError || runAll.isError) && (
        <p className="mb-2 text-xs text-danger">
          {((step.error || runAll.error) as Error).message} — check the provider in Settings.
        </p>
      )}
      <ol>
        {stages.data?.map((s) => <StageRow key={s} stage={s} entry={byStage[s]} />)}
      </ol>
    </Card>
  );
}

export default function PipelinePage() {
  const queryClient = useQueryClient();
  const [projectId, setProjectId] = useState<number | "">("");
  const projects = useQuery({ queryKey: ["projects"], queryFn: api.listProjects });
  const runs = useQuery({
    queryKey: ["runs", projectId],
    queryFn: () => api.listRuns(projectId === "" ? undefined : projectId),
  });
  const createRun = useMutation({
    mutationFn: (mode: PipelineRun["mode"]) => api.createRun(projectId as number, mode),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["runs"] }),
  });

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">Pipeline</h1>
        <p className="mt-1 text-xs text-muted">
          The autonomous production line. Assisted = review between stages; producer = the crew
          runs everything runnable. You direct, agents work.
        </p>
      </header>

      <Card className="mb-6 flex flex-wrap items-center gap-2 p-3">
        <select
          value={projectId}
          onChange={(e) => setProjectId(e.target.value === "" ? "" : Number(e.target.value))}
          className="h-9 rounded-md border border-edge bg-surface px-2 text-sm text-fg"
          aria-label="Project"
        >
          <option value="">Select a project…</option>
          {projects.data?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} ({p.status})
            </option>
          ))}
        </select>
        <Button
          onClick={() => createRun.mutate("assisted")}
          disabled={projectId === "" || createRun.isPending}
          variant="outline"
        >
          New assisted run
        </Button>
        <Button
          onClick={() => createRun.mutate("producer")}
          disabled={projectId === "" || createRun.isPending}
        >
          New producer run
        </Button>
        {projects.data?.length === 0 && (
          <Link href="/" className="text-xs text-info hover:underline">
            Create a project first
          </Link>
        )}
      </Card>

      {runs.isLoading && <Spinner />}
      {runs.data?.length === 0 && (
        <EmptyState
          title="No runs yet"
          hint="Pick a project and start a run. Media stages (images, voice) engage automatically when ComfyUI or a TTS engine is running."
        />
      )}
      <div className="space-y-4">
        {runs.data
          ?.slice()
          .reverse()
          .map((r) => <RunPanel key={r.id} run={r} />)}
      </div>
    </div>
  );
}
