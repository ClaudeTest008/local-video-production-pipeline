"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@lvpp/shared";
import { Badge, Button, Card, Input, Spinner, Textarea } from "@lvpp/ui";
import { ArrowRight, Check } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

/* eslint-disable @typescript-eslint/no-explicit-any */

const STEPS = ["Welcome", "System scan", "AI defaults", "First brand", "Finish"] as const;

function DetectRow({ label, item, extra }: { label: string; item: any; extra?: string }) {
  const found = Array.isArray(item) ? item.some((i) => i.found) : !!item?.found;
  return (
    <li className="flex items-start justify-between gap-3 border-b border-edge py-2 last:border-0">
      <div className="min-w-0">
        <span className="text-sm text-fg">{label}</span>
        {extra && <span className="ml-2 font-mono text-[11px] text-muted">{extra}</span>}
        {!found && item?.fix && <p className="mt-0.5 text-xs text-muted">{item.fix}</p>}
      </div>
      <Badge tone={found ? "success" : "neutral"}>{found ? "detected" : "not found"}</Badge>
    </li>
  );
}

export default function SetupWizard() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [step, setStep] = useState(0);
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [brandName, setBrandName] = useState("");
  const [brandGoals, setBrandGoals] = useState("");
  const [createSample, setCreateSample] = useState(true);

  const detect = useQuery({
    queryKey: ["detect"],
    queryFn: api.systemDetect,
    enabled: step >= 1,
    staleTime: Infinity,
  });
  const d = detect.data;

  const finish = useMutation({
    mutationFn: async () => {
      let brandId: number | undefined;
      if (brandName.trim()) {
        const brand = await api.createBrand({ name: brandName.trim(), goals: brandGoals });
        brandId = brand.id;
      }
      if (createSample) {
        await api.createProject({
          name: "Sample: Why Vertical Farms Fail",
          brand_id: brandId ?? null,
          idea: "Why did vertical farming startups burn $3B? The physics of light.",
          tags: ["sample"],
        } as any);
      }
      return api.setupComplete({
        default_chat_provider: provider || undefined,
        default_chat_model: model || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["setup"] });
      router.replace("/");
    },
  });

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <ol className="mb-8 flex items-center gap-2" aria-label="Setup progress">
        {STEPS.map((s, i) => (
          <li key={s} className="flex items-center gap-2">
            <span
              className={`flex size-6 items-center justify-center rounded-full font-mono text-[11px] ${
                i < step
                  ? "bg-success/20 text-success"
                  : i === step
                    ? "bg-accent text-accent-fg"
                    : "bg-surface-2 text-muted"
              }`}
            >
              {i < step ? <Check className="size-3.5" /> : i + 1}
            </span>
            <span className={`text-xs ${i === step ? "text-fg" : "text-muted"}`}>{s}</span>
            {i < STEPS.length - 1 && <span className="h-px w-4 bg-edge" aria-hidden />}
          </li>
        ))}
      </ol>

      {step === 0 && (
        <Card className="p-6">
          <h1 className="font-display text-xl font-semibold">Welcome to LVPP Studio</h1>
          <p className="mt-2 text-sm text-muted">
            A local-first AI production studio. You direct; a crew of agents researches, writes,
            storyboards, renders, and optimizes. This wizard checks your machine and sets sane
            defaults — nothing leaves your computer.
          </p>
          <Button className="mt-6" onClick={() => setStep(1)}>
            Start <ArrowRight className="size-4" />
          </Button>
        </Card>
      )}

      {step === 1 && (
        <Card className="p-6">
          <h2 className="mb-1 font-display text-lg font-semibold">System scan</h2>
          <p className="mb-4 text-xs text-muted">
            Missing tools are optional — the pipeline skips what it can{"'"}t reach and tells you.
          </p>
          {detect.isLoading && (
            <p className="flex items-center gap-2 text-sm text-muted">
              <Spinner /> probing local tools…
            </p>
          )}
          {d && (
            <ul>
              <DetectRow label="Python (backend)" item={d.python} extra={d.python.version} />
              <DetectRow label="FFmpeg (video export)" item={d.ffmpeg} extra={d.ffmpeg.version} />
              <DetectRow label="Git" item={d.git} />
              <DetectRow label="Whisper (captions)" item={d.whisper} />
              <DetectRow label="TTS engines (voice-over)" item={d.tts} />
              <DetectRow
                label="Ollama (local AI)"
                item={d.ollama}
                extra={d.ollama.models?.length ? `${d.ollama.models.length} models` : undefined}
              />
              <DetectRow
                label="ComfyUI (rendering)"
                item={d.comfyui}
                extra={
                  d.comfyui.models?.checkpoints !== undefined
                    ? `${d.comfyui.models.checkpoints} checkpoints`
                    : undefined
                }
              />
              <li className="flex items-start justify-between gap-3 py-2">
                <span className="text-sm text-fg">GPU</span>
                <span className="text-right font-mono text-[11px] text-muted">
                  {d.gpus.length
                    ? d.gpus
                        .map((g: any) => `${g.name} · ${(g.vram_total_mb / 1024).toFixed(0)} GB`)
                        .join(", ")
                    : "none detected — CPU-only workflows"}
                </span>
              </li>
            </ul>
          )}
          <div className="mt-6 flex justify-between">
            <Button variant="ghost" onClick={() => setStep(0)}>
              Back
            </Button>
            <Button onClick={() => setStep(2)} disabled={!d}>
              Continue <ArrowRight className="size-4" />
            </Button>
          </div>
        </Card>
      )}

      {step === 2 && (
        <Card className="p-6">
          <h2 className="mb-1 font-display text-lg font-semibold">AI defaults</h2>
          <p className="mb-4 text-xs text-muted">
            {d?.ollama.found
              ? "Ollama detected — the studio will use it automatically. Override below if you want."
              : "No local AI detected. Install Ollama (recommended) or set a cloud key in backend/.env, then pick the provider here."}
          </p>
          <div className="grid grid-cols-2 gap-3">
            <label className="space-y-1 text-xs text-muted">
              Default provider
              <Input
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                placeholder={d?.ollama.found ? "ollama (auto)" : "e.g. openai"}
              />
            </label>
            <label className="space-y-1 text-xs text-muted">
              Default model
              <Input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder={d?.ollama.models?.[0] ?? "e.g. gpt-4o-mini"}
              />
            </label>
          </div>
          {d && (
            <p className="mt-3 text-xs text-muted">
              Render sizing: <Badge tone="info">{d.workflow_hint}</Badge>{" "}
              {d.workflow_hint === "heavy"
                ? "— ≥16 GB VRAM, larger workflows enabled."
                : d.workflow_hint === "light"
                  ? "— limited VRAM, lightweight workflows preferred."
                  : "— no GPU seen; rendering will wait for ComfyUI."}
            </p>
          )}
          <div className="mt-6 flex justify-between">
            <Button variant="ghost" onClick={() => setStep(1)}>
              Back
            </Button>
            <Button onClick={() => setStep(3)}>
              Continue <ArrowRight className="size-4" />
            </Button>
          </div>
        </Card>
      )}

      {step === 3 && (
        <Card className="p-6">
          <h2 className="mb-1 font-display text-lg font-semibold">Your first brand</h2>
          <p className="mb-4 text-xs text-muted">
            Every agent works inside a brand — its voice and goals shape everything. Optional; you
            can create brands later.
          </p>
          <div className="space-y-3">
            <Input
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              placeholder="Brand or channel name (optional)"
              aria-label="Brand name"
            />
            <Textarea
              value={brandGoals}
              onChange={(e) => setBrandGoals(e.target.value)}
              rows={2}
              placeholder='Goal, e.g. "Reach 100k subscribers with weekly deep-dives"'
              aria-label="Brand goals"
            />
            <label className="flex items-center gap-2 text-xs text-muted">
              <input
                type="checkbox"
                checked={createSample}
                onChange={(e) => setCreateSample(e.target.checked)}
                className="accent-[var(--color-accent)]"
              />
              Create a sample project so the pipeline has something to chew on
            </label>
          </div>
          <div className="mt-6 flex justify-between">
            <Button variant="ghost" onClick={() => setStep(2)}>
              Back
            </Button>
            <Button onClick={() => setStep(4)}>
              Continue <ArrowRight className="size-4" />
            </Button>
          </div>
        </Card>
      )}

      {step === 4 && (
        <Card className="p-6">
          <h2 className="mb-1 font-display text-lg font-semibold">Ready</h2>
          <ul className="mt-3 space-y-1.5 text-sm text-muted">
            <li>• Provider: {provider || (d?.ollama.found ? "ollama (auto)" : "not set — configure in Settings")}</li>
            <li>• Brand: {brandName.trim() || "skipped"}</li>
            <li>• Sample project: {createSample ? "yes" : "no"}</li>
            <li>• Render sizing: {d?.workflow_hint}</li>
          </ul>
          {finish.isError && (
            <p className="mt-3 text-xs text-danger">{(finish.error as Error).message}</p>
          )}
          <div className="mt-6 flex justify-between">
            <Button variant="ghost" onClick={() => setStep(3)}>
              Back
            </Button>
            <Button onClick={() => finish.mutate()} disabled={finish.isPending}>
              {finish.isPending ? "Finishing…" : "Open the studio"}
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
