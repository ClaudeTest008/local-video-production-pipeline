"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type WorkflowDef } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Input, Spinner } from "@lvpp/ui";
import { RefreshCw, Star, Upload } from "lucide-react";
import { useRef, useState } from "react";

const TYPE_TONE: Record<string, "success" | "info" | "accent" | "neutral"> = {
  video_lipsync: "success",
  avatar: "success",
  video: "info",
  image: "accent",
};

const TYPE_LABEL: Record<string, string> = {
  video_lipsync: "Video + Lip-Sync",
  avatar: "Avatar",
  video: "Cinematic Video",
  image: "Image",
  audio: "Audio",
  other: "Other",
};

function Row({ wf }: { wf: WorkflowDef }) {
  const queryClient = useQueryClient();
  const update = useMutation({
    mutationFn: (body: Partial<WorkflowDef>) => api.updateWorkflow(wf.id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      queryClient.invalidateQueries({ queryKey: ["wf-selection"] });
    },
  });
  const issues = (wf.meta as { conversion_issues?: string[] }).conversion_issues ?? [];
  return (
    <li className="flex flex-wrap items-center gap-3 border-b border-edge py-3 last:border-0">
      <button
        aria-label={wf.favorite ? "Unfavorite" : "Favorite"}
        onClick={() => update.mutate({ favorite: !wf.favorite })}
        className="rounded focus-visible:outline-2 focus-visible:outline-accent"
      >
        <Star
          className={`size-4 ${wf.favorite ? "fill-accent text-accent" : "text-muted"}`}
        />
      </button>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm text-fg" title={wf.name}>
            {wf.name}
          </span>
          <Badge tone={TYPE_TONE[wf.wf_type] ?? "neutral"}>
            {TYPE_LABEL[wf.wf_type] ?? wf.wf_type}
          </Badge>
          <Badge tone="neutral">{wf.source}</Badge>
          {issues.length > 0 && (
            <Badge tone="danger">check ({issues.length})</Badge>
          )}
        </div>
        <p className="mt-0.5 truncate font-mono text-[11px] text-muted">
          {wf.models.length ? wf.models.join(", ") : "no model files referenced"}
          {wf.vram_estimate_mb ? ` · ~${Math.round(wf.vram_estimate_mb / 1000)} GB VRAM` : ""}
        </p>
      </div>
      <label className="flex items-center gap-1.5 text-xs text-muted">
        <input
          type="checkbox"
          checked={wf.enabled}
          onChange={(e) => update.mutate({ enabled: e.target.checked })}
          className="accent-[var(--color-accent)]"
        />
        enabled
      </label>
    </li>
  );
}

export default function WorkflowsPage() {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploadName, setUploadName] = useState("");
  const [message, setMessage] = useState("");

  const workflows = useQuery({ queryKey: ["workflows"], queryFn: api.listWorkflows });
  const selection = useQuery({ queryKey: ["wf-selection"], queryFn: api.workflowSelection });

  const discover = useMutation({
    mutationFn: api.discoverWorkflows,
    onSuccess: (r) => {
      setMessage(
        r.error
          ? r.error
          : `Imported ${r.imported.length} workflows${r.failed.length ? `, ${r.failed.length} failed` : ""}.`,
      );
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      queryClient.invalidateQueries({ queryKey: ["wf-selection"] });
    },
  });

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const parsed = JSON.parse(await file.text());
      const name = uploadName.trim() || file.name.replace(/\.json$/i, "");
      return api.uploadWorkflow(name, parsed);
    },
    onSuccess: (wf) => {
      setMessage(`Uploaded '${wf.name}' (${TYPE_LABEL[wf.wf_type] ?? wf.wf_type}).`);
      setUploadName("");
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      queryClient.invalidateQueries({ queryKey: ["wf-selection"] });
    },
    onError: (e) => setMessage(`Upload failed: ${(e as Error).message}`),
  });

  const comfy = (workflows.data ?? []).filter((w) => w.kind === "comfyui");

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">ComfyUI workflows</h1>
        <p className="mt-1 text-xs text-muted">
          The studio consumes workflows that already exist in your ComfyUI — you never edit
          nodes here. Enable what production may use; star favorites to prefer them.
        </p>
      </header>

      <Card className="mb-4 p-3">
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={() => discover.mutate()} disabled={discover.isPending}>
            <RefreshCw className="size-4" />
            {discover.isPending ? "Scanning…" : "Discover from ComfyUI"}
          </Button>
          <Input
            className="max-w-48"
            value={uploadName}
            onChange={(e) => setUploadName(e.target.value)}
            placeholder="Name (optional)"
            aria-label="Upload name"
          />
          <Button variant="outline" onClick={() => fileRef.current?.click()}>
            <Upload className="size-4" /> Upload .json
          </Button>
          <input
            ref={fileRef}
            type="file"
            accept=".json,application/json"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) upload.mutate(f);
              e.target.value = "";
            }}
          />
          {message && <span className="text-xs text-muted">{message}</span>}
        </div>
        {selection.data && (
          <p className="mt-2 text-xs">
            <span className="text-muted">Automatic mode would pick: </span>
            <span className="text-accent">{selection.data.note}</span>
          </p>
        )}
      </Card>

      {workflows.isLoading && <Spinner />}
      {comfy.length === 0 && !workflows.isLoading && (
        <EmptyState
          title="No workflows yet"
          hint="Click Discover to import everything saved in your ComfyUI library, or upload a workflow .json. Templates from ComfyUI's Browse Templates become discoverable once you save them to your library."
        />
      )}
      <Card className="px-4">
        <ul>{comfy.map((wf) => <Row key={wf.id} wf={wf} />)}</ul>
      </Card>
    </div>
  );
}
