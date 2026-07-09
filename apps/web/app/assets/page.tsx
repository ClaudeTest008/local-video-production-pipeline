"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Asset } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Input, Spinner } from "@lvpp/ui";
import { AudioLines, FileQuestion, Film, Image, Music, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useStudio } from "@/lib/store";

const KINDS = ["image", "video", "audio", "music", "thumbnail", "other"] as const;
type Kind = (typeof KINDS)[number];
type Filter = "all" | Kind;

const KIND_ICONS: Record<Kind, typeof Image> = {
  image: Image,
  video: Film,
  audio: AudioLines,
  music: Music,
  thumbnail: Image,
  other: FileQuestion,
};

function fileName(path: string) {
  return path.split(/[\\/]/).filter(Boolean).pop() ?? path;
}

function RegisterAssetForm({ onDone }: { onDone: () => void }) {
  const activeProjectId = useStudio((s) => s.activeProjectId);
  const [path, setPath] = useState("");
  const [kind, setKind] = useState<Kind>("image");
  const queryClient = useQueryClient();
  const create = useMutation({
    mutationFn: () =>
      api.post<Asset>("/assets", { project_id: activeProjectId, path, kind }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      onDone();
    },
  });
  return (
    <Card className="p-4">
      {activeProjectId == null ? (
        <p className="text-xs text-muted">
          Select a project first — assets are registered against the active project. Open a
          project from the Projects page to set it.
        </p>
      ) : (
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (path.trim()) create.mutate();
          }}
        >
          <div className="flex gap-3">
            <Input
              autoFocus
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="Absolute or project-relative file path"
              aria-label="Asset path"
            />
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value as Kind)}
              aria-label="Asset kind"
              className="h-9 rounded-md border border-edge bg-surface px-3 text-sm text-fg focus-visible:outline-2 focus-visible:outline-accent"
            >
              {KINDS.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={onDone}>
              Cancel
            </Button>
            <Button type="submit" disabled={create.isPending || !path.trim()}>
              Register asset
            </Button>
          </div>
          {create.isError && (
            <p className="text-xs text-danger">{(create.error as Error).message}</p>
          )}
        </form>
      )}
    </Card>
  );
}

function AssetCard({ asset }: { asset: Asset }) {
  const queryClient = useQueryClient();
  const remove = useMutation({
    mutationFn: () => api.delete(`/assets/${asset.id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["assets"] }),
  });
  const Icon = KIND_ICONS[asset.kind] ?? FileQuestion;
  return (
    <Card className="group p-4">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <Icon className="size-4 shrink-0 text-accent" />
          <span className="truncate font-mono text-sm" title={fileName(asset.path)}>
            {fileName(asset.path)}
          </span>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => remove.mutate()}
          disabled={remove.isPending}
          aria-label="Delete asset"
          className="opacity-0 transition-opacity group-hover:opacity-100"
        >
          <Trash2 className="size-3.5 text-danger" />
        </Button>
      </div>
      <div className="mb-2 flex flex-wrap items-center gap-1.5">
        <Badge tone="accent">{asset.kind}</Badge>
        {asset.source && <Badge tone="info">{asset.source}</Badge>}
        {asset.tags?.map((t) => <Badge key={t}>{t}</Badge>)}
      </div>
      <p className="truncate text-[11px] text-muted" title={asset.path}>
        {asset.path}
      </p>
      {remove.isError && (
        <p className="mt-2 text-xs text-danger">{(remove.error as Error).message}</p>
      )}
    </Card>
  );
}

export default function AssetsPage() {
  const activeProjectId = useStudio((s) => s.activeProjectId);
  const [filter, setFilter] = useState<Filter>("all");
  const [registering, setRegistering] = useState(false);
  const assets = useQuery({
    queryKey: ["assets", activeProjectId],
    queryFn: () => api.assets(activeProjectId ?? undefined),
  });

  const filtered =
    filter === "all" ? assets.data : assets.data?.filter((a) => a.kind === filter);

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight">Assets</h1>
          <p className="mt-1 text-xs text-muted">
            {activeProjectId != null
              ? "Everything registered for the active project."
              : "All assets across projects — select a project to scope and register."}
          </p>
        </div>
        <Button onClick={() => setRegistering((v) => !v)}>
          <Plus className="size-4" /> Register asset
        </Button>
      </header>

      {registering && (
        <div className="mb-6">
          <RegisterAssetForm onDone={() => setRegistering(false)} />
        </div>
      )}

      <div className="mb-6 flex flex-wrap gap-1.5">
        {(["all", ...KINDS] as Filter[]).map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => setFilter(k)}
            className={`rounded-full border px-3 py-1 font-mono text-xs transition-colors ${
              filter === k
                ? "border-accent/40 bg-accent/15 text-accent"
                : "border-edge bg-surface text-muted hover:bg-surface-2 hover:text-fg"
            }`}
          >
            {k}
          </button>
        ))}
      </div>

      {assets.isLoading && <Spinner />}
      {assets.isError && (
        <EmptyState
          title="Backend not reachable"
          hint="Start it with: cd backend && uvicorn app.main:app --reload"
        />
      )}
      {filtered?.length === 0 && (
        <EmptyState
          title={filter === "all" ? "No assets yet" : `No ${filter} assets`}
          hint="Register a file path to track it here, or let the pipeline agents generate assets into the project tree."
          action={<Button onClick={() => setRegistering(true)}>Register the first asset</Button>}
        />
      )}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {filtered?.map((a) => <AssetCard key={a.id} asset={a} />)}
      </div>
    </div>
  );
}
