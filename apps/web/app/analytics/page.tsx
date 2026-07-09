"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Input, Spinner } from "@lvpp/ui";
import { BarChart3, Plus } from "lucide-react";
import { useState } from "react";
import { useStudio } from "@/lib/store";

interface MetricSnapshot {
  id: number;
  project_id: number;
  platform: string;
  views: number;
  likes: number;
  comments: number;
  watch_time_h: number;
  captured_at: string;
}

const num = (n: number) => n.toLocaleString("en-US");

function SummaryTiles({ snapshots }: { snapshots: MetricSnapshot[] }) {
  const sum = (f: (s: MetricSnapshot) => number) =>
    snapshots.reduce((acc, s) => acc + (f(s) || 0), 0);
  const tiles = [
    { label: "Total views", value: num(sum((s) => s.views)) },
    { label: "Likes", value: num(sum((s) => s.likes)) },
    { label: "Comments", value: num(sum((s) => s.comments)) },
    { label: "Watch hours", value: sum((s) => s.watch_time_h).toFixed(1) },
  ];
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {tiles.map((t) => (
        <Card key={t.label} className="p-4">
          <p className="font-mono text-2xl font-semibold tabular-nums text-fg">{t.value}</p>
          <p className="mt-1 text-xs text-muted">{t.label}</p>
        </Card>
      ))}
    </div>
  );
}

function SnapshotForm({
  projectId,
  onDone,
}: {
  projectId: number;
  onDone: () => void;
}) {
  const [platform, setPlatform] = useState("youtube");
  const [views, setViews] = useState("0");
  const [likes, setLikes] = useState("0");
  const [comments, setComments] = useState("0");
  const [watchTimeH, setWatchTimeH] = useState("0");
  const [capturedAt, setCapturedAt] = useState(() => new Date().toISOString().slice(0, 10));
  const queryClient = useQueryClient();
  const create = useMutation({
    mutationFn: () =>
      api.post<MetricSnapshot>("/analytics", {
        project_id: projectId,
        platform,
        views: Number(views) || 0,
        likes: Number(likes) || 0,
        comments: Number(comments) || 0,
        watch_time_h: Number(watchTimeH) || 0,
        captured_at: capturedAt,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      onDone();
    },
  });
  const field = (
    label: string,
    value: string,
    set: (v: string) => void,
    type: string = "number",
  ) => (
    <label className="space-y-1 text-xs text-muted">
      {label}
      <Input
        type={type}
        min={type === "number" ? 0 : undefined}
        step={label === "Watch hours" ? "0.1" : undefined}
        value={value}
        onChange={(e) => set(e.target.value)}
      />
    </label>
  );
  return (
    <Card className="p-4">
      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          if (platform.trim()) create.mutate();
        }}
      >
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          <label className="space-y-1 text-xs text-muted">
            Platform
            <Input
              autoFocus
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              placeholder="youtube"
            />
          </label>
          {field("Views", views, setViews)}
          {field("Likes", likes, setLikes)}
          {field("Comments", comments, setComments)}
          {field("Watch hours", watchTimeH, setWatchTimeH)}
          {field("Captured at", capturedAt, setCapturedAt, "date")}
        </div>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onDone}>
            Cancel
          </Button>
          <Button type="submit" disabled={create.isPending || !platform.trim()}>
            Save snapshot
          </Button>
        </div>
        {create.isError && (
          <p className="text-xs text-danger">{(create.error as Error).message}</p>
        )}
      </form>
    </Card>
  );
}

function SnapshotTable({ snapshots }: { snapshots: MetricSnapshot[] }) {
  const sorted = [...snapshots].sort((a, b) => b.captured_at.localeCompare(a.captured_at));
  return (
    <Card className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-edge text-left text-xs text-muted">
            <th className="px-4 py-2.5 font-medium">Captured</th>
            <th className="px-4 py-2.5 font-medium">Platform</th>
            <th className="px-4 py-2.5 text-right font-medium">Views</th>
            <th className="px-4 py-2.5 text-right font-medium">Likes</th>
            <th className="px-4 py-2.5 text-right font-medium">Comments</th>
            <th className="px-4 py-2.5 text-right font-medium">Watch h</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-edge">
          {sorted.map((s) => (
            <tr key={s.id}>
              <td className="px-4 py-2.5 font-mono text-xs text-muted">
                {s.captured_at.slice(0, 10)}
              </td>
              <td className="px-4 py-2.5">
                <Badge tone="accent">{s.platform}</Badge>
              </td>
              <td className="px-4 py-2.5 text-right font-mono tabular-nums">{num(s.views)}</td>
              <td className="px-4 py-2.5 text-right font-mono tabular-nums">{num(s.likes)}</td>
              <td className="px-4 py-2.5 text-right font-mono tabular-nums">{num(s.comments)}</td>
              <td className="px-4 py-2.5 text-right font-mono tabular-nums">
                {s.watch_time_h.toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

export default function AnalyticsPage() {
  const activeProjectId = useStudio((s) => s.activeProjectId);
  const [recording, setRecording] = useState(false);
  const snapshots = useQuery({
    queryKey: ["analytics", activeProjectId],
    queryFn: () =>
      api.get<MetricSnapshot[]>(
        `/analytics${activeProjectId ? `?project_id=${activeProjectId}` : ""}`,
      ),
  });

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight">Analytics</h1>
          <p className="mt-1 text-xs text-muted">
            Publishing and analytics APIs are local records for now — platform sync is on the
            roadmap.
          </p>
        </div>
        <Button
          onClick={() => setRecording((v) => !v)}
          disabled={!activeProjectId}
          title={activeProjectId ? undefined : "Open a project first — snapshots need one"}
        >
          <Plus className="size-4" /> Record snapshot
        </Button>
      </header>

      {recording && activeProjectId && (
        <div className="mb-6">
          <SnapshotForm projectId={activeProjectId} onDone={() => setRecording(false)} />
        </div>
      )}

      {snapshots.isLoading && <Spinner />}
      {snapshots.isError && (
        <EmptyState
          title="Backend not reachable"
          hint="Start it with: cd backend && uvicorn app.main:app --reload"
        />
      )}
      {snapshots.data?.length === 0 && (
        <EmptyState
          title="No snapshots yet"
          hint={
            activeProjectId
              ? "Record the first snapshot — paste the numbers from your platform dashboard."
              : "Open a project from the Projects page, then record snapshots here."
          }
          action={
            activeProjectId ? (
              <Button onClick={() => setRecording(true)}>
                <BarChart3 className="size-4" /> Record first snapshot
              </Button>
            ) : undefined
          }
        />
      )}
      {snapshots.data && snapshots.data.length > 0 && (
        <div className="space-y-6">
          <SummaryTiles snapshots={snapshots.data} />
          <SnapshotTable snapshots={snapshots.data} />
        </div>
      )}
    </div>
  );
}
