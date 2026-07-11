"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Opportunity } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Input, Spinner } from "@lvpp/ui";
import { Check, Lightbulb, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

const SCORE_KEYS = [
  "growth",
  "competition",
  "virality",
  "evergreen",
  "shortform",
  "longform",
  "audience_fit",
  "urgency",
] as const;

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-20 shrink-0 font-mono text-[10px] text-muted">{label}</span>
      <div className="h-1.5 flex-1 rounded-full bg-surface-2">
        <div
          className="h-1.5 rounded-full bg-accent/70"
          style={{ width: `${Math.min(value * 10, 100)}%` }}
        />
      </div>
      <span className="w-6 text-right font-mono text-[10px] text-fg">{value}</span>
    </div>
  );
}

function OpportunityCard({ opportunity }: { opportunity: Opportunity }) {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["opportunities"] });
  const approve = useMutation({ mutationFn: () => api.approveOpportunity(opportunity.id), onSuccess: invalidate });
  const reject = useMutation({ mutationFn: () => api.rejectOpportunity(opportunity.id), onSuccess: invalidate });
  const projectId = (opportunity.meta as { project_id?: number }).project_id;

  return (
    <Card className="p-4">
      <div className="mb-1 flex items-start justify-between gap-2">
        <h2 className="font-display text-[15px] font-semibold">{opportunity.topic}</h2>
        <Badge
          tone={
            opportunity.status === "approved"
              ? "success"
              : opportunity.status === "rejected"
                ? "danger"
                : "accent"
          }
        >
          {opportunity.status}
        </Badge>
      </div>
      {opportunity.angle && <p className="text-xs text-fg">Angle: {opportunity.angle}</p>}
      {opportunity.rationale && (
        <p className="mt-1 text-xs text-muted">Why: {opportunity.rationale}</p>
      )}
      <div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1">
        {SCORE_KEYS.filter((k) => opportunity.scores[k] !== undefined).map((k) => (
          <ScoreBar key={k} label={k} value={opportunity.scores[k]} />
        ))}
      </div>
      <div className="mt-3 flex items-center gap-2">
        {opportunity.status === "suggested" && (
          <>
            <Button size="sm" onClick={() => approve.mutate()} disabled={approve.isPending}>
              <Check className="size-3.5" /> Approve → project
            </Button>
            <Button size="sm" variant="ghost" onClick={() => reject.mutate()}>
              <X className="size-3.5" /> Reject
            </Button>
          </>
        )}
        {opportunity.status === "approved" && projectId && (
          <Link href={`/projects/${projectId}`} className="text-xs text-info hover:underline">
            Open project #{projectId}
          </Link>
        )}
      </div>
    </Card>
  );
}

export default function StrategyPage() {
  const queryClient = useQueryClient();
  const [brandId, setBrandId] = useState<number | "">("");
  const [seedTopic, setSeedTopic] = useState("");
  const brands = useQuery({ queryKey: ["brands"], queryFn: api.listBrands });
  const opportunities = useQuery({
    queryKey: ["opportunities", brandId],
    queryFn: () => api.listOpportunities(brandId === "" ? undefined : brandId),
  });
  const generate = useMutation({
    mutationFn: () =>
      api.generateOpportunities({
        brand_id: brandId === "" ? null : brandId,
        seed_topic: seedTopic,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["opportunities"] }),
  });

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">Strategy</h1>
        <p className="mt-1 text-xs text-muted">
          {'"What should I create next?" — scored opportunities from the Strategy Director. '}
          Live web evidence when a Brave key is set; model knowledge otherwise.
        </p>
      </header>

      <Card className="mb-6 flex flex-wrap items-center gap-2 p-3">
        <select
          value={brandId}
          onChange={(e) => setBrandId(e.target.value === "" ? "" : Number(e.target.value))}
          className="h-9 rounded-md border border-edge bg-surface px-2 text-sm text-fg"
          aria-label="Brand"
        >
          <option value="">All brands</option>
          {brands.data?.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
        <Input
          className="max-w-xs"
          value={seedTopic}
          onChange={(e) => setSeedTopic(e.target.value)}
          placeholder="Focus area (optional), e.g. roman history"
        />
        <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
          <Lightbulb className="size-4" />
          {generate.isPending ? "Thinking…" : "Generate opportunities"}
        </Button>
        {generate.isError && (
          <span className="text-xs text-danger">
            {(generate.error as Error).message} — check the provider in Settings.
          </span>
        )}
      </Card>

      {opportunities.isLoading && <Spinner />}
      {opportunities.data?.length === 0 && (
        <EmptyState
          title="No opportunities yet"
          hint="Pick a brand, optionally a focus area, and let the Strategy Director propose scored ideas."
        />
      )}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {opportunities.data?.map((o) => <OpportunityCard key={o.id} opportunity={o} />)}
      </div>
    </div>
  );
}
