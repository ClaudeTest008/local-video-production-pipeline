"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Brand } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Input, Spinner, Textarea } from "@lvpp/ui";
import { Plus } from "lucide-react";
import { useState } from "react";

const FIELDS: { key: keyof Brand & string; label: string; hint: string }[] = [
  { key: "voice", label: "Voice", hint: "tone of voice — how this brand talks" },
  { key: "style", label: "Visual style", hint: "look every generated frame should share" },
  { key: "audience", label: "Audience", hint: "who this is for" },
  { key: "guidelines", label: "Guidelines", hint: "dos and don'ts" },
  { key: "goals", label: "Goals", hint: 'business goal, e.g. "100k subscribers in 12 months"' },
];

function BrandEditor({ brand, onClose }: { brand: Brand; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<Record<string, string>>(
    Object.fromEntries(FIELDS.map((f) => [f.key, String(brand[f.key] ?? "")])),
  );
  const save = useMutation({
    mutationFn: () => api.updateBrand(brand.id, draft),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["brands"] }),
  });
  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-display text-sm font-semibold">{brand.name}</h2>
        <Button variant="ghost" size="sm" onClick={onClose}>
          Close
        </Button>
      </div>
      <div className="space-y-3">
        {FIELDS.map((f) => (
          <label key={f.key} className="block space-y-1 text-xs text-muted">
            {f.label}
            <Textarea
              rows={2}
              value={draft[f.key]}
              placeholder={f.hint}
              onChange={(e) => setDraft({ ...draft, [f.key]: e.target.value })}
            />
          </label>
        ))}
        <div className="flex items-center gap-3">
          <Button onClick={() => save.mutate()} disabled={save.isPending}>
            Save brand
          </Button>
          {save.isSuccess && <span className="text-xs text-success">Saved</span>}
        </div>
      </div>
    </Card>
  );
}

export default function BrandsPage() {
  const queryClient = useQueryClient();
  const brands = useQuery({ queryKey: ["brands"], queryFn: api.listBrands });
  const [name, setName] = useState("");
  const [selected, setSelected] = useState<number | null>(null);
  const create = useMutation({
    mutationFn: () => api.createBrand({ name }),
    onSuccess: () => {
      setName("");
      queryClient.invalidateQueries({ queryKey: ["brands"] });
    },
  });

  const selectedBrand = brands.data?.find((b) => b.id === selected);

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">Brands</h1>
        <p className="mt-1 text-xs text-muted">
          Every agent works inside a brand: its voice, style, audience, and goals shape research,
          scripts, prompts, and strategy.
        </p>
      </header>

      <form
        className="mb-6 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim()) create.mutate();
        }}
      >
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New brand or channel name"
          aria-label="Brand name"
        />
        <Button type="submit" disabled={!name.trim() || create.isPending}>
          <Plus className="size-4" /> Create
        </Button>
      </form>

      {brands.isLoading && <Spinner />}
      {brands.data?.length === 0 && (
        <EmptyState
          title="No brands yet"
          hint="Create one, define its voice and goals, then generate strategy and projects under it."
        />
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="space-y-3">
          {brands.data?.map((b) => (
            <Card
              key={b.id}
              className={`cursor-pointer p-4 transition-colors hover:border-accent/40 ${
                selected === b.id ? "border-accent/60" : ""
              }`}
              onClick={() => setSelected(b.id)}
            >
              <div className="flex items-center justify-between">
                <h2 className="font-display text-[15px] font-semibold">{b.name}</h2>
                <div className="flex gap-1">
                  {b.platforms.map((p) => (
                    <Badge key={p} tone="info">
                      {p}
                    </Badge>
                  ))}
                </div>
              </div>
              <p className="mt-1 line-clamp-2 text-xs text-muted">
                {b.goals || b.description || "No goals set — click to define."}
              </p>
            </Card>
          ))}
        </div>
        {selectedBrand && (
          <BrandEditor
            key={selectedBrand.id}
            brand={selectedBrand}
            onClose={() => setSelected(null)}
          />
        )}
      </div>
    </div>
  );
}
