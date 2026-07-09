"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ComfyJob } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Spinner, Textarea } from "@lvpp/ui";
import { useState } from "react";
import { useStudio } from "@/lib/store";

const MODEL_KINDS = ["checkpoints", "loras", "vae", "controlnet", "upscale_models"] as const;

const STATUS_TONE: Record<ComfyJob["status"], "success" | "danger" | "info"> = {
  done: "success",
  error: "danger",
  queued: "info",
};

function StatusCard({ available, url, queue, isLoading }: {
  available: boolean;
  url?: string;
  queue?: { running: number; pending: number };
  isLoading: boolean;
}) {
  return (
    <Card className="p-4">
      <h2 className="mb-3 text-sm font-medium">Server</h2>
      {isLoading ? (
        <Spinner />
      ) : (
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
          <span className="inline-flex items-center gap-2">
            <span
              className={`size-2 rounded-full ${available ? "bg-success" : "bg-danger"}`}
              aria-hidden
            />
            {available ? "available" : "unreachable"}
          </span>
          {url && <span className="font-mono text-xs text-muted">{url}</span>}
          {queue && (
            <span className="text-xs text-muted">
              queue: <span className="text-fg">{queue.running}</span> running,{" "}
              <span className="text-fg">{queue.pending}</span> pending
            </span>
          )}
        </div>
      )}
    </Card>
  );
}

function ModelsCard({ available }: { available: boolean }) {
  const models = useQuery({
    queryKey: ["comfy-models"],
    queryFn: api.comfyModels,
    enabled: available,
  });
  return (
    <Card className="p-4">
      <h2 className="mb-3 text-sm font-medium">Models</h2>
      {!available && (
        <EmptyState
          title="ComfyUI is not running"
          hint="Start ComfyUI at http://127.0.0.1:8188"
        />
      )}
      {available && models.isLoading && <Spinner />}
      {available && models.isError && (
        <EmptyState
          title="Model list failed to load"
          hint="Check that ComfyUI is reachable, then reload this page."
        />
      )}
      {available && models.data && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {MODEL_KINDS.map((kind) => {
            const list = models.data[kind] ?? [];
            return (
              <div key={kind}>
                <h3 className="mb-1 text-xs font-medium text-muted">{kind}</h3>
                {list.length === 0 ? (
                  <p className="text-xs text-muted/60">none installed</p>
                ) : (
                  <ul className="space-y-0.5">
                    {list.map((m) => (
                      <li key={m} className="truncate font-mono text-xs">
                        {m}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

function QueueCard() {
  const activeProjectId = useStudio((s) => s.activeProjectId);
  const queryClient = useQueryClient();
  const [raw, setRaw] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);
  const queue = useMutation({
    mutationFn: (workflow: Record<string, unknown>) =>
      api.comfyQueue(workflow, activeProjectId ?? undefined),
    onSuccess: () => {
      setRaw("");
      queryClient.invalidateQueries({ queryKey: ["comfy-jobs"] });
    },
  });
  return (
    <Card className="p-4">
      <h2 className="mb-3 text-sm font-medium">Queue a workflow</h2>
      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          setParseError(null);
          let parsed: unknown;
          try {
            parsed = JSON.parse(raw);
          } catch (err) {
            setParseError(`Invalid JSON: ${(err as Error).message}`);
            return;
          }
          if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
            setParseError("Workflow must be a JSON object (ComfyUI API format).");
            return;
          }
          queue.mutate(parsed as Record<string, unknown>);
        }}
      >
        <Textarea
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
          rows={8}
          className="font-mono text-xs"
          placeholder={'Paste a workflow in API format, e.g. {"3": {"class_type": "KSampler", ...}}'}
          aria-label="Workflow JSON"
        />
        <div className="flex items-center gap-3">
          <Button type="submit" disabled={queue.isPending || !raw.trim()}>
            Queue job
          </Button>
          {queue.isSuccess && (
            <span className="font-mono text-xs text-success">
              queued as {queue.data.prompt_id}
            </span>
          )}
        </div>
        {parseError && <p className="text-xs text-danger">{parseError}</p>}
        {queue.isError && (
          <p className="text-xs text-danger">
            {(queue.error as Error).message} — check the workflow and that ComfyUI is running.
          </p>
        )}
      </form>
    </Card>
  );
}

function JobsCard() {
  const queryClient = useQueryClient();
  const jobs = useQuery({
    queryKey: ["comfy-jobs"],
    queryFn: () => api.comfyJobs(),
    refetchInterval: (query) =>
      query.state.data?.some((j) => j.status === "queued") ? 5000 : false,
  });
  const refresh = useMutation({
    mutationFn: (id: number) => api.get<ComfyJob>(`/comfyui/jobs/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["comfy-jobs"] }),
  });
  return (
    <Card className="p-4">
      <h2 className="mb-3 text-sm font-medium">Jobs</h2>
      {jobs.isLoading && <Spinner />}
      {jobs.isError && (
        <EmptyState
          title="Jobs failed to load"
          hint="Start the backend: cd backend && uvicorn app.main:app --reload"
        />
      )}
      {jobs.data?.length === 0 && (
        <EmptyState
          title="No jobs yet"
          hint="Queue a workflow above — jobs and their outputs land here."
        />
      )}
      {jobs.data && jobs.data.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-edge text-left text-xs text-muted">
              <th className="py-2 pr-3 font-medium">id</th>
              <th className="py-2 pr-3 font-medium">prompt</th>
              <th className="py-2 pr-3 font-medium">status</th>
              <th className="py-2 font-medium">outputs</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-edge">
            {jobs.data.map((job) => (
              <tr
                key={job.id}
                className="cursor-pointer transition-colors hover:bg-surface-2"
                title="Click to refresh this job"
                onClick={() => refresh.mutate(job.id)}
              >
                <td className="py-2 pr-3 font-mono text-xs">{job.id}</td>
                <td className="max-w-40 truncate py-2 pr-3 font-mono text-xs text-muted">
                  {job.prompt_id}
                </td>
                <td className="py-2 pr-3">
                  <Badge tone={STATUS_TONE[job.status]}>{job.status}</Badge>
                </td>
                <td className="py-2 text-xs">{job.outputs.length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}

export default function ComfyUiPage() {
  const status = useQuery({
    queryKey: ["comfy-status"],
    queryFn: api.comfyStatus,
    refetchInterval: 5000,
  });
  const available = status.data?.available === true;

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-6 py-8">
      <header>
        <h1 className="font-display text-xl font-semibold tracking-tight">ComfyUI</h1>
        <p className="mt-1 text-xs text-muted">
          Local render engine — server status, installed models, and the job queue.
        </p>
      </header>
      <StatusCard
        available={available}
        url={status.data?.url}
        queue={status.data?.queue}
        isLoading={status.isLoading}
      />
      <ModelsCard available={available} />
      <QueueCard />
      <JobsCard />
    </div>
  );
}
