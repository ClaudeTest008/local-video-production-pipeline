"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@lvpp/shared";
import { Badge, Button, Card, Input, Spinner } from "@lvpp/ui";
import { useState } from "react";

function ProviderList() {
  const providers = useQuery({ queryKey: ["providers"], queryFn: api.providers });
  if (providers.isLoading) return <Spinner />;
  return (
    <ul className="divide-y divide-edge">
      {providers.data?.map((p) => (
        <li key={p.name} className="flex items-center justify-between py-2.5">
          <span className="font-mono text-sm">{p.name}</span>
          <Badge tone={p.available ? "success" : "neutral"}>
            {p.available ? "available" : "not configured"}
          </Badge>
        </li>
      ))}
    </ul>
  );
}

function DefaultsForm() {
  const queryClient = useQueryClient();
  const settings = useQuery({ queryKey: ["settings"], queryFn: api.allSettings });
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const save = useMutation({
    mutationFn: async () => {
      if (provider) await api.putSetting("default_chat_provider", provider);
      if (model) await api.putSetting("default_chat_model", model);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["settings"] }),
  });
  const current = settings.data ?? {};
  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      <div className="grid grid-cols-2 gap-3">
        <label className="space-y-1 text-xs text-muted">
          Default provider
          <Input
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            placeholder={String(current["default_chat_provider"] ?? "ollama")}
          />
        </label>
        <label className="space-y-1 text-xs text-muted">
          Default model
          <Input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={String(current["default_chat_model"] ?? "llama3.1")}
          />
        </label>
      </div>
      <Button type="submit" disabled={save.isPending}>
        Save defaults
      </Button>
      {save.isSuccess && <span className="ml-3 text-xs text-success">Saved</span>}
    </form>
  );
}

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 px-6 py-8">
      <header>
        <h1 className="font-display text-xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-xs text-muted">
          Providers are configured via environment (backend/.env). Keys never leave this machine.
        </p>
      </header>
      <Card className="p-4">
        <h2 className="mb-2 text-sm font-medium">AI providers</h2>
        <ProviderList />
      </Card>
      <Card className="p-4">
        <h2 className="mb-3 text-sm font-medium">Chat defaults</h2>
        <DefaultsForm />
      </Card>
    </div>
  );
}
