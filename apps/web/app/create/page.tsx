"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@lvpp/shared";
import { Button, Card, Input, Textarea } from "@lvpp/ui";
import { Clapperboard } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useStudio } from "@/lib/store";

/** The one-button flow: idea in, autonomous production out. */
export default function CreatePage() {
  const router = useRouter();
  const setActiveProject = useStudio((s) => s.setActiveProject);
  const [name, setName] = useState("");
  const [idea, setIdea] = useState("");
  const [brandId, setBrandId] = useState<number | "">("");

  const brands = useQuery({ queryKey: ["brands"], queryFn: api.listBrands });
  const selection = useQuery({ queryKey: ["wf-selection"], queryFn: api.workflowSelection });

  const produce = useMutation({
    mutationFn: async () => {
      const project = await api.createProject({
        name: name.trim() || idea.trim().slice(0, 80),
        brand_id: brandId === "" ? null : brandId,
        idea: idea.trim(),
      });
      setActiveProject(project.id);
      const run = await api.createRun(project.id, "producer");
      await api.post(`/pipeline/runs/${run.id}/run-all?background=true`);
      return project;
    },
    onSuccess: () => router.push("/pipeline"),
  });

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">Create</h1>
        <p className="mt-1 text-xs text-muted">
          Describe the video. The crew researches, writes, reviews, renders through your ComfyUI
          workflows (voice and lip-sync included when a capable workflow is enabled), captions,
          and assembles the timeline — in the background.
        </p>
      </header>
      <Card className="p-5">
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (idea.trim()) produce.mutate();
          }}
        >
          <Textarea
            autoFocus
            rows={4}
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder='e.g. "A 60-second explainer on why local AI beats cloud AI for creators"'
            aria-label="Video idea"
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Title (optional — the idea works)"
              aria-label="Project title"
            />
            <select
              value={brandId}
              onChange={(e) => setBrandId(e.target.value === "" ? "" : Number(e.target.value))}
              className="h-9 rounded-md border border-edge bg-surface px-2 text-sm text-fg"
              aria-label="Brand"
            >
              <option value="">No brand</option>
              {brands.data?.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
          {selection.data && (
            <p className="text-xs text-muted">
              Render plan: <span className="text-accent">{selection.data.note}</span>{" "}
              <Link href="/workflows" className="text-info hover:underline">
                (manage workflows)
              </Link>
            </p>
          )}
          <Button type="submit" disabled={produce.isPending || !idea.trim()} className="w-full">
            <Clapperboard className="size-4" />
            {produce.isPending ? "Starting the crew…" : "Produce video"}
          </Button>
          {produce.isError && (
            <p className="text-xs text-danger">{(produce.error as Error).message}</p>
          )}
        </form>
      </Card>
    </div>
  );
}
