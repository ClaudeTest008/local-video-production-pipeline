"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Timeline, type TimelineTrack } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Input, Spinner } from "@lvpp/ui";
import { Film, Music, Plus, Type } from "lucide-react";
import { useState } from "react";
import { useStudio } from "@/lib/store";

type ExportResult =
  | { status: "dry_run" | "ffmpeg_missing"; command: string[] }
  | { status: "done"; output: string };

const TRACK_ICONS = { video: Film, audio: Music, caption: Type } as const;

function fileName(path: string) {
  return path.split(/[\\/]/).pop() || path;
}

function TrackRow({
  track,
  onAddClip,
  onMoveClip,
  onRemoveClip,
  saving,
}: {
  track: TimelineTrack;
  onAddClip: (clip: { path: string; duration?: number }) => void;
  onMoveClip: (index: number, direction: -1 | 1) => void;
  onRemoveClip: (index: number) => void;
  saving: boolean;
}) {
  const [adding, setAdding] = useState(false);
  const [path, setPath] = useState("");
  const [duration, setDuration] = useState("");
  const Icon = TRACK_ICONS[track.kind];

  const submit = () => {
    if (!path.trim()) return;
    const dur = Number(duration);
    onAddClip({
      path: path.trim(),
      ...(Number.isFinite(dur) && dur > 0 ? { duration: dur } : {}),
    });
    setPath("");
    setDuration("");
    setAdding(false);
  };

  return (
    <div className="border-b border-edge py-2 last:border-b-0">
      <div className="flex items-center gap-3">
        <span className="flex w-24 shrink-0 items-center gap-1.5 font-mono text-xs text-muted">
          <Icon className="size-3.5" /> {track.kind}
        </span>
        <div className="flex min-w-0 flex-1 items-center gap-2 overflow-x-auto py-1">
          {track.clips.length === 0 && (
            <span className="text-xs text-muted/60">Empty track</span>
          )}
          {track.clips.map((clip, i) => (
            <span
              key={`${clip.path}-${i}`}
              className="group inline-flex shrink-0 items-center gap-1 rounded border border-edge bg-surface-2 px-2 py-1 font-mono text-[11px]"
              title={clip.path}
            >
              <button
                aria-label="Move clip left"
                className="text-muted opacity-40 hover:text-fg group-hover:opacity-100 disabled:invisible"
                disabled={i === 0 || saving}
                onClick={() => onMoveClip(i, -1)}
              >
                ‹
              </button>
              {fileName(clip.path)}
              {clip.duration != null && (
                <span className="text-muted">{clip.duration}s</span>
              )}
              <button
                aria-label="Move clip right"
                className="text-muted opacity-40 hover:text-fg group-hover:opacity-100 disabled:invisible"
                disabled={i === track.clips.length - 1 || saving}
                onClick={() => onMoveClip(i, 1)}
              >
                ›
              </button>
              <button
                aria-label="Remove clip"
                className="ml-0.5 text-muted opacity-40 hover:text-danger group-hover:opacity-100"
                disabled={saving}
                onClick={() => onRemoveClip(i)}
              >
                ×
              </button>
            </span>
          ))}
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setAdding((v) => !v)}
          disabled={saving}
        >
          <Plus className="size-3.5" /> Add clip
        </Button>
      </div>
      {adding && (
        <form
          className="mt-2 flex items-center gap-2 pl-24"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <Input
            autoFocus
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="Clip file path (e.g. assets/scene-01.mp4)"
            aria-label="Clip path"
            className="h-7 text-xs"
          />
          <Input
            type="number"
            min={0}
            step="0.1"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            placeholder="Duration s"
            aria-label="Clip duration in seconds"
            className="h-7 w-28 text-xs"
          />
          <Button type="submit" size="sm" disabled={!path.trim() || saving}>
            Add
          </Button>
        </form>
      )}
    </div>
  );
}

function ExportCard({ timelineId }: { timelineId: number }) {
  const [format, setFormat] = useState<"mp4" | "mov">("mp4");
  const [burn, setBurn] = useState(false);
  const exp = useMutation({
    mutationFn: (run: boolean) =>
      api.post<ExportResult>(`/timelines/${timelineId}/export`, {
        format,
        run,
        burn_subtitles: burn,
      }),
  });
  const result = exp.data;

  return (
    <Card className="p-4">
      <h2 className="mb-3 text-sm font-medium">Export</h2>
      <div className="flex items-center gap-2">
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value as "mp4" | "mov")}
          aria-label="Export format"
          className="h-9 rounded-md border border-edge bg-surface px-3 text-sm text-fg focus-visible:outline-2 focus-visible:outline-accent"
        >
          <option value="mp4">mp4</option>
          <option value="mov">mov</option>
        </select>
        <label className="flex items-center gap-1.5 text-xs text-muted">
          <input
            type="checkbox"
            checked={burn}
            onChange={(e) => setBurn(e.target.checked)}
            className="accent-[var(--color-accent)]"
          />
          burn captions
        </label>
        <Button variant="outline" onClick={() => exp.mutate(false)} disabled={exp.isPending}>
          Dry run
        </Button>
        <Button onClick={() => exp.mutate(true)} disabled={exp.isPending}>
          Export
        </Button>
        {exp.isPending && <Spinner />}
      </div>
      {exp.isError && (
        <p className="mt-3 text-xs text-danger">
          {(exp.error as Error).message} — add at least one clip to a video track, then retry.
        </p>
      )}
      {result?.status === "done" && (
        <p className="mt-3 text-xs text-success">
          Export finished: <span className="font-mono">{result.output}</span>
        </p>
      )}
      {result?.status === "ffmpeg_missing" && (
        <div className="mt-3 space-y-2">
          <p className="text-xs text-danger">
            FFmpeg is not on PATH. Install it (winget install Gyan.FFmpeg) and run this command:
          </p>
          <pre className="overflow-x-auto rounded-md border border-edge bg-surface-2 p-3 font-mono text-[11px] text-muted">
            {result.command.join(" ")}
          </pre>
        </div>
      )}
      {result?.status === "dry_run" && (
        <pre className="mt-3 overflow-x-auto rounded-md border border-edge bg-surface-2 p-3 font-mono text-[11px] text-muted">
          {result.command.join(" ")}
        </pre>
      )}
    </Card>
  );
}

function TimelineEditor({ timeline, projectId }: { timeline: Timeline; projectId: number }) {
  const queryClient = useQueryClient();
  const patch = useMutation({
    mutationFn: (body: Partial<Pick<Timeline, "fps" | "resolution" | "tracks">>) =>
      api.patch<Timeline>(`/timelines/${timeline.id}`, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["timelines", projectId] }),
  });
  const [fps, setFps] = useState(String(timeline.fps));
  const [resolution, setResolution] = useState(timeline.resolution);

  const commitFps = () => {
    const value = Number(fps);
    if (Number.isFinite(value) && value > 0 && value !== timeline.fps) {
      patch.mutate({ fps: value });
    } else {
      setFps(String(timeline.fps));
    }
  };
  const commitResolution = () => {
    const value = resolution.trim();
    if (/^\d+x\d+$/.test(value) && value !== timeline.resolution) {
      patch.mutate({ resolution: value });
    } else {
      setResolution(timeline.resolution);
    }
  };

  const addTrack = (kind: "video" | "audio") =>
    patch.mutate({ tracks: [...timeline.tracks, { kind, clips: [] }] });
  const addClip = (index: number, clip: { path: string; duration?: number }) =>
    patch.mutate({
      tracks: timeline.tracks.map((t, i) =>
        i === index ? { ...t, clips: [...t.clips, clip] } : t,
      ),
    });
  const moveClip = (trackIndex: number, clipIndex: number, direction: -1 | 1) =>
    patch.mutate({
      tracks: timeline.tracks.map((t, i) => {
        if (i !== trackIndex) return t;
        const clips = [...t.clips];
        const [clip] = clips.splice(clipIndex, 1);
        clips.splice(clipIndex + direction, 0, clip);
        return { ...t, clips };
      }),
    });
  const removeClip = (trackIndex: number, clipIndex: number) =>
    patch.mutate({
      tracks: timeline.tracks.map((t, i) =>
        i === trackIndex ? { ...t, clips: t.clips.filter((_, ci) => ci !== clipIndex) } : t,
      ),
    });

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="mb-3 flex items-end justify-between gap-4">
          <div className="flex items-end gap-3">
            <label className="space-y-1 text-xs text-muted">
              FPS
              <Input
                type="number"
                min={1}
                step="0.01"
                value={fps}
                onChange={(e) => setFps(e.target.value)}
                onBlur={commitFps}
                onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
                aria-label="Frames per second"
                className="w-24"
              />
            </label>
            <label className="space-y-1 text-xs text-muted">
              Resolution
              <Input
                value={resolution}
                onChange={(e) => setResolution(e.target.value)}
                onBlur={commitResolution}
                onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
                placeholder="1920x1080"
                aria-label="Resolution"
                className="w-32 font-mono"
              />
            </label>
            {patch.isPending && <Spinner className="mb-2.5" />}
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => addTrack("video")} disabled={patch.isPending}>
              <Film className="size-3.5" /> Video track
            </Button>
            <Button size="sm" variant="outline" onClick={() => addTrack("audio")} disabled={patch.isPending}>
              <Music className="size-3.5" /> Audio track
            </Button>
          </div>
        </div>
        {patch.isError && (
          <p className="mb-2 text-xs text-danger">
            {(patch.error as Error).message} — the change was not saved, retry.
          </p>
        )}
        {timeline.tracks.length === 0 ? (
          <EmptyState
            title="No tracks"
            hint="Add a video track, then drop clip paths onto it. The export concatenates video tracks top to bottom."
          />
        ) : (
          <div>
            {timeline.tracks.map((track, i) => (
              <TrackRow
                key={i}
                track={track}
                saving={patch.isPending}
                onAddClip={(clip) => addClip(i, clip)}
                onMoveClip={(ci, dir) => moveClip(i, ci, dir)}
                onRemoveClip={(ci) => removeClip(i, ci)}
              />
            ))}
          </div>
        )}
      </Card>
      <AiEditCard timeline={timeline} projectId={projectId} />
      <ExportCard timelineId={timeline.id} />
    </div>
  );
}

function AiEditCard({ timeline, projectId }: { timeline: Timeline; projectId: number }) {
  const [instruction, setInstruction] = useState("");
  const agents = useQuery({ queryKey: ["agents"], queryFn: api.listAgents });
  const editor = agents.data?.find((a) => a.role === "editor");
  const ask = useMutation({
    mutationFn: () =>
      api.runAgent(editor!.id, `Timeline (JSON): ${JSON.stringify(timeline.tracks).slice(0, 3000)}\n\nInstruction: ${instruction}\n\nPropose a concrete edit plan: exact clip order changes, trims (seconds), which scenes to regenerate and with what kind of workflow (video/lip-sync). Numbered steps.`, { project_id: projectId }),
  });
  return (
    <Card className="p-4">
      <h2 className="mb-1 text-sm font-medium">AI editing</h2>
      <p className="mb-3 text-xs text-muted">
        Tell the Editor what to change — {"“"}tighten the middle{"”"},
        {" “"}regenerate scene 3 with a lip-sync workflow{"”"}. It proposes a plan; you
        apply it with the controls above.
      </p>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (instruction.trim() && editor) ask.mutate();
        }}
      >
        <Input
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder={editor ? "Describe the edit…" : "Seed the agent crew first (Agents page)"}
          disabled={!editor}
          aria-label="Edit instruction"
        />
        <Button type="submit" disabled={!editor || !instruction.trim() || ask.isPending}>
          {ask.isPending ? "Thinking…" : "Ask"}
        </Button>
      </form>
      {ask.data && (
        <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-md bg-surface-2 p-3 text-xs text-fg">
          {ask.data.content}
        </pre>
      )}
      {ask.isError && (
        <p className="mt-2 text-xs text-danger">{(ask.error as Error).message}</p>
      )}
    </Card>
  );
}

export default function TimelinePage() {
  const projectId = useStudio((s) => s.activeProjectId);
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [name, setName] = useState("");

  const timelines = useQuery({
    queryKey: ["timelines", projectId],
    queryFn: () => api.timelines(projectId!),
    enabled: projectId != null,
  });

  const create = useMutation({
    mutationFn: () =>
      api.post<Timeline>("/timelines", { project_id: projectId, name: name.trim() }),
    onSuccess: (created) => {
      setName("");
      setSelectedId(created.id);
      queryClient.invalidateQueries({ queryKey: ["timelines", projectId] });
    },
  });

  if (projectId == null) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-8">
        <EmptyState
          title="No active project"
          hint="Open a project from the Projects page first — the timeline editor cuts the active project."
        />
      </div>
    );
  }

  const selected =
    timelines.data?.find((t) => t.id === selectedId) ?? timelines.data?.[0];

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight">Timeline</h1>
          <p className="mt-1 text-xs text-muted">
            Structured cut — tracks and clips in, one ffmpeg command out.
          </p>
        </div>
        <form
          className="flex items-center gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (name.trim()) create.mutate();
          }}
        >
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New timeline name"
            aria-label="New timeline name"
            className="w-48"
          />
          <Button type="submit" disabled={create.isPending || !name.trim()}>
            <Plus className="size-4" /> Create
          </Button>
        </form>
      </header>
      {create.isError && (
        <p className="mb-4 text-xs text-danger">{(create.error as Error).message}</p>
      )}

      {timelines.isLoading && <Spinner />}
      {timelines.isError && (
        <EmptyState
          title="Backend not reachable"
          hint="Start it with: cd backend && uvicorn app.main:app --reload"
        />
      )}
      {timelines.data?.length === 0 && (
        <EmptyState
          title="No timelines yet"
          hint="Name one above and hit Create — it starts at 30 fps, 1920x1080, no tracks."
        />
      )}

      {timelines.data && timelines.data.length > 0 && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            {timelines.data.map((t) => (
              <button
                key={t.id}
                onClick={() => setSelectedId(t.id)}
                className={`rounded-md border px-3 py-1.5 text-sm transition-colors ${
                  selected?.id === t.id
                    ? "border-accent/50 bg-accent/10 text-accent"
                    : "border-edge bg-surface text-muted hover:text-fg"
                }`}
              >
                {t.name}
                <Badge tone="neutral" className="ml-2">
                  {t.fps}fps · {t.resolution}
                </Badge>
              </button>
            ))}
          </div>
          {selected && (
            <TimelineEditor key={selected.id} timeline={selected} projectId={projectId} />
          )}
        </div>
      )}
    </div>
  );
}
