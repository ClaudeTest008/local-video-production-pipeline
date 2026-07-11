"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@lvpp/shared";
import { Badge, Card, Spinner } from "@lvpp/ui";
import Link from "next/link";

function Dot({ ok }: { ok: boolean }) {
  return <span className={`size-1.5 rounded-full ${ok ? "bg-success" : "bg-edge"}`} aria-hidden />;
}

function HealthCard() {
  const health = useQuery({
    queryKey: ["system-health"],
    queryFn: api.systemHealth,
    refetchInterval: 10_000,
  });
  if (health.isLoading) return <Card className="p-4"><Spinner /></Card>;
  if (!health.data)
    return (
      <Card className="p-4 text-xs text-danger">
        Backend offline — start it: cd backend && uvicorn app.main:app --port 8321
      </Card>
    );
  const h = health.data;
  const providersUp = h.providers.filter((p) => p.available);
  return (
    <Card className="p-4">
      <h2 className="mb-3 text-sm font-medium">System</h2>
      <ul className="space-y-2 text-xs">
        <li className="flex items-center gap-2">
          <Dot ok /> backend · {h.database}
        </li>
        <li className="flex items-center gap-2">
          <Dot ok={h.comfyui.available} /> ComfyUI
          {h.comfyui.queue &&
            ` · ${h.comfyui.queue.running} running, ${h.comfyui.queue.pending} pending`}
        </li>
        {h.comfyui.devices?.map((d) => (
          <li key={d.name} className="ml-3.5 font-mono text-[11px] text-muted">
            {d.name}: {(d.vram_free_mb / 1024).toFixed(1)} / {(d.vram_total_mb / 1024).toFixed(1)} GB VRAM free
          </li>
        ))}
        <li className="flex items-center gap-2">
          <Dot ok={providersUp.length > 0} /> AI providers:{" "}
          {providersUp.length > 0 ? providersUp.map((p) => p.name).join(", ") : "none reachable"}
        </li>
        <li className="flex items-center gap-2">
          <Dot ok={h.engines.ffmpeg} /> FFmpeg
          <Dot ok={h.engines.whisper} /> Whisper
          <Dot ok={h.engines.tts.some((t) => t.available)} /> TTS
        </li>
        <li className="flex items-center gap-2">
          <Dot ok={h.pipeline.errored === 0} /> pipeline: {h.pipeline.running} running,{" "}
          {h.pipeline.errored} errored · render queue: {h.render_queue.queued_jobs}
        </li>
      </ul>
    </Card>
  );
}

function RunsCard() {
  const runs = useQuery({ queryKey: ["runs"], queryFn: () => api.listRuns(), refetchInterval: 10_000 });
  const projects = useQuery({ queryKey: ["projects"], queryFn: api.listProjects });
  const names = new Map(projects.data?.map((p) => [p.id, p.name]));
  const active = (runs.data ?? []).filter((r) => r.status !== "done").slice(-5).reverse();
  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium">Production</h2>
        <Link href="/pipeline" className="text-xs text-info hover:underline">
          Pipeline →
        </Link>
      </div>
      {active.length === 0 && (
        <p className="text-xs text-muted">No active runs. Approve an opportunity or start a run.</p>
      )}
      <ul className="space-y-2">
        {active.map((r) => (
          <li key={r.id} className="flex items-center gap-2 text-xs">
            <Badge tone={r.status === "error" ? "danger" : r.status === "running" ? "info" : "neutral"}>
              {r.status}
            </Badge>
            <span className="truncate">{names.get(r.project_id) ?? `project #${r.project_id}`}</span>
            <span className="ml-auto font-mono text-[10px] text-muted">
              {r.log.filter((e) => e.status === "done").length}/8 stages
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function OpportunitiesCard() {
  const opportunities = useQuery({
    queryKey: ["opportunities", ""],
    queryFn: () => api.listOpportunities(),
  });
  const suggested = (opportunities.data ?? [])
    .filter((o) => o.status === "suggested")
    .sort((a, b) => (b.scores.growth ?? 0) - (a.scores.growth ?? 0))
    .slice(0, 4);
  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium">What to create next</h2>
        <Link href="/strategy" className="text-xs text-info hover:underline">
          Strategy →
        </Link>
      </div>
      {suggested.length === 0 && (
        <p className="text-xs text-muted">
          No open opportunities. Generate some in Strategy — the studio starts with “what”, not
          “how”.
        </p>
      )}
      <ul className="space-y-2">
        {suggested.map((o) => (
          <li key={o.id} className="text-xs">
            <span className="text-fg">{o.topic}</span>
            <span className="ml-2 font-mono text-[10px] text-accent">
              growth {o.scores.growth ?? "?"}/10
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function KnowledgeCard() {
  const learnings = useQuery({ queryKey: ["learnings"], queryFn: () => api.listLearnings() });
  const latest = (learnings.data ?? []).slice(-5).reverse();
  return (
    <Card className="p-4">
      <h2 className="mb-3 text-sm font-medium">Latest learnings</h2>
      {latest.length === 0 && (
        <p className="text-xs text-muted">
          The studio learns from renders, failures, and analytics as you work.
        </p>
      )}
      <ul className="space-y-1.5">
        {latest.map((l) => (
          <li key={l.id} className="truncate text-xs text-muted" title={l.insight}>
            <span className="font-mono text-[10px] text-info">[{l.kind}]</span> {l.insight}
          </li>
        ))}
      </ul>
    </Card>
  );
}

function BrandsCard() {
  const brands = useQuery({ queryKey: ["brands"], queryFn: api.listBrands });
  const projects = useQuery({ queryKey: ["projects"], queryFn: api.listProjects });
  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium">Brands</h2>
        <Link href="/brands" className="text-xs text-info hover:underline">
          Manage →
        </Link>
      </div>
      {brands.data?.length === 0 && (
        <p className="text-xs text-muted">No brands yet — every agent works inside one.</p>
      )}
      <ul className="space-y-2">
        {brands.data?.slice(0, 5).map((b) => (
          <li key={b.id} className="flex items-center justify-between text-xs">
            <span className="text-fg">{b.name}</span>
            <span className="font-mono text-[10px] text-muted">
              {projects.data?.filter((p) => p.brand_id === b.id).length ?? 0} projects
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export default function StudioDashboard() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">Studio</h1>
        <p className="mt-1 text-xs text-muted">
          You direct, the crew works. Health, production, and the next best move — at a glance.
        </p>
      </header>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <HealthCard />
        <RunsCard />
        <OpportunitiesCard />
        <BrandsCard />
        <div className="md:col-span-2">
          <KnowledgeCard />
        </div>
      </div>
    </div>
  );
}
