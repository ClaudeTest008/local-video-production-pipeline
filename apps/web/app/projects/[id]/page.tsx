"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type PipelineStage } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Spinner } from "@lvpp/ui";
import { motion } from "framer-motion";
import {
  Archive,
  Camera,
  Clapperboard,
  FileText,
  FolderOpen,
  LayoutGrid,
  Subtitles,
  Wand2,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { use, useEffect, useState } from "react";
import { PipelineRail } from "@/components/PipelineRail";
import { useStudio } from "@/lib/store";

function StageCard<T>({
  title,
  href,
  icon: Icon,
  queryKey,
  queryFn,
  latest,
}: {
  title: string;
  href: string;
  icon: LucideIcon;
  queryKey: (string | number)[];
  queryFn: () => Promise<T[]>;
  latest: (item: T) => string;
}) {
  const q = useQuery({ queryKey, queryFn });
  const last = q.data && q.data.length > 0 ? q.data[q.data.length - 1] : undefined;
  return (
    <Link href={href}>
      <Card className="h-full p-4 transition-colors hover:border-accent/40">
        <div className="mb-2 flex items-center justify-between gap-2">
          <span className="flex items-center gap-2 text-sm font-medium">
            <Icon className="size-4 text-muted" aria-hidden /> {title}
          </span>
          {q.isLoading ? (
            <Spinner className="size-3" />
          ) : (
            <Badge tone={q.data && q.data.length > 0 ? "accent" : "neutral"}>
              {q.data?.length ?? 0}
            </Badge>
          )}
        </div>
        <p className="truncate text-xs text-muted">
          {q.isError
            ? "Failed to load — check the backend."
            : last
              ? `Latest: ${latest(last)}`
              : "Nothing here yet."}
        </p>
      </Card>
    </Link>
  );
}

export default function ProjectOverviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const projectId = Number(id);
  const queryClient = useQueryClient();
  const setActiveProject = useStudio((s) => s.setActiveProject);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isNaN(projectId)) setActiveProject(projectId);
  }, [projectId, setActiveProject]);

  const project = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
    enabled: !Number.isNaN(projectId),
  });

  const setStatus = useMutation({
    mutationFn: (status: PipelineStage) => api.updateProject(projectId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const snapshot = useMutation({
    mutationFn: () => api.post<{ id: number }>(`/projects/${projectId}/snapshots`),
    onSuccess: (snap) => setNotice(`Snapshot #${snap.id} saved.`),
  });

  const archive = useMutation({
    mutationFn: () => api.post<{ archive: string }>(`/projects/${projectId}/archive`),
    onSuccess: (res) => setNotice(`Archive written: ${res.archive}`),
  });

  if (Number.isNaN(projectId)) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-8">
        <EmptyState
          title="Invalid project id"
          hint="Head back to the projects list and pick a project."
          action={
            <Link href="/">
              <Button variant="outline">All projects</Button>
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      {project.isLoading && <Spinner />}
      {project.isError && (
        <EmptyState
          title="Project failed to load"
          hint={`${(project.error as Error).message} — start the backend (cd backend && uvicorn app.main:app --reload) or pick another project from the list.`}
          action={
            <Link href="/">
              <Button variant="outline">All projects</Button>
            </Link>
          }
        />
      )}
      {project.data && (
        <>
          <header className="mb-6">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="truncate font-display text-xl font-semibold tracking-tight">
                    {project.data.name}
                  </h1>
                  <Badge tone="accent">{project.data.status}</Badge>
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-muted">
                  {project.data.idea || project.data.description || "No idea captured yet."}
                </p>
              </div>
              <div className="flex shrink-0 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => snapshot.mutate()}
                  disabled={snapshot.isPending}
                >
                  <Camera className="size-4" /> Snapshot
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => archive.mutate()}
                  disabled={archive.isPending}
                >
                  <Archive className="size-4" /> Export archive
                </Button>
              </div>
            </div>
            {notice && (
              <div className="mt-3 rounded-md border border-edge bg-surface-2 px-3 py-2 font-mono text-xs text-success">
                {notice}
              </div>
            )}
            {(snapshot.isError || archive.isError) && (
              <p className="mt-3 text-xs text-danger">
                {((snapshot.error ?? archive.error) as Error).message} — check the backend and
                retry.
              </p>
            )}
          </header>

          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
          >
            <Card className="mb-6 p-5">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-medium">Pipeline</h2>
                <span className="font-mono text-[11px] text-muted">
                  {setStatus.isPending ? "saving…" : "click a frame to set the stage"}
                </span>
              </div>
              <PipelineRail
                status={project.data.status}
                onSelect={(stage) => setStatus.mutate(stage)}
              />
              {setStatus.isError && (
                <p className="mt-2 text-xs text-danger">
                  {(setStatus.error as Error).message} — stage not saved, click the frame again.
                </p>
              )}
            </Card>
          </motion.div>

          {/* ponytail: storyboard + subtitles have no dedicated module page yet; both land on /timeline where they are consumed. Point them at their own routes when those pages exist. */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StageCard
              title="Scripts"
              href="/scripts"
              icon={FileText}
              queryKey={["scripts", projectId]}
              queryFn={() => api.scripts(projectId)}
              latest={(s) => s.title}
            />
            <StageCard
              title="Storyboard scenes"
              href="/timeline"
              icon={LayoutGrid}
              queryKey={["storyboard", projectId]}
              queryFn={() => api.scenes(projectId)}
              latest={(s) => s.title || `Scene ${s.order_index + 1}`}
            />
            <StageCard
              title="Prompts"
              href="/studio"
              icon={Wand2}
              queryKey={["prompts", projectId]}
              queryFn={() => api.prompts(projectId)}
              latest={(p) => p.name}
            />
            <StageCard
              title="Assets"
              href="/assets"
              icon={FolderOpen}
              queryKey={["assets", projectId]}
              queryFn={() => api.assets(projectId)}
              latest={(a) => a.path.split(/[\\/]/).pop() ?? a.path}
            />
            <StageCard
              title="Subtitle tracks"
              href="/timeline"
              icon={Subtitles}
              queryKey={["subtitles", projectId]}
              queryFn={() => api.subtitles(projectId)}
              latest={(t) => `${t.language} · ${t.segments.length} segments`}
            />
            <StageCard
              title="Timelines"
              href="/timeline"
              icon={Clapperboard}
              queryKey={["timelines", projectId]}
              queryFn={() => api.timelines(projectId)}
              latest={(t) => t.name}
            />
          </div>
        </>
      )}
    </div>
  );
}
