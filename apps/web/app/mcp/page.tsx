"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type McpServer } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Spinner } from "@lvpp/ui";
import { Check, Copy, RadioTower } from "lucide-react";
import { useState } from "react";

function ToggleSwitch({ server }: { server: McpServer }) {
  const queryClient = useQueryClient();
  const toggle = useMutation({
    mutationFn: () => api.mcpToggle(server.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
      queryClient.invalidateQueries({ queryKey: ["mcp-export"] });
    },
  });
  return (
    <button
      type="button"
      role="switch"
      aria-checked={server.enabled}
      aria-label={`${server.enabled ? "Disable" : "Enable"} ${server.name}`}
      disabled={toggle.isPending}
      onClick={() => toggle.mutate()}
      className={`relative h-5 w-9 shrink-0 rounded-full transition-colors disabled:opacity-50 ${
        server.enabled ? "bg-accent" : "bg-surface-2 border border-edge"
      }`}
    >
      <span
        className={`absolute top-0.5 size-4 rounded-full bg-bg transition-transform ${
          server.enabled ? "translate-x-4" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

function ServerRow({ server }: { server: McpServer }) {
  return (
    <li className="flex items-center gap-4 py-3">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-fg">{server.name}</span>
          <Badge tone={server.source === "catalog" ? "neutral" : "info"}>{server.source}</Badge>
        </div>
        {server.description && (
          <p className="mt-0.5 line-clamp-1 text-xs text-muted">{server.description}</p>
        )}
        <p className="mt-0.5 truncate font-mono text-[11px] text-muted/70">
          {[server.command, ...server.args].join(" ")}
        </p>
      </div>
      <ToggleSwitch server={server} />
    </li>
  );
}

function ExportConfig() {
  const [copied, setCopied] = useState(false);
  const exported = useQuery({
    queryKey: ["mcp-export"],
    queryFn: () => api.get<Record<string, unknown>>("/mcp/export"),
  });
  const json = exported.data ? JSON.stringify(exported.data, null, 2) : "";
  return (
    <Card className="p-4">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-medium">Export config</h2>
        <Button
          size="sm"
          variant="outline"
          disabled={!json}
          onClick={() => {
            navigator.clipboard.writeText(json);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          }}
        >
          {copied ? <Check className="size-3.5 text-success" /> : <Copy className="size-3.5" />}
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      <p className="mb-3 text-xs text-muted">
        Paste this into any MCP client config (Claude Desktop, editors) to reuse the enabled
        servers.
      </p>
      {exported.isLoading && <Spinner />}
      {exported.isError && (
        <p className="text-xs text-danger">
          Export unavailable — check that the backend is running on port 8321.
        </p>
      )}
      {json && (
        <pre className="overflow-x-auto rounded-md border border-edge bg-bg p-3 font-mono text-xs text-muted">
          {json}
        </pre>
      )}
    </Card>
  );
}

export default function McpPage() {
  const queryClient = useQueryClient();
  const servers = useQuery({ queryKey: ["mcp-servers"], queryFn: api.mcpServers });
  const discover = useMutation({
    mutationFn: api.mcpDiscover,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
      queryClient.invalidateQueries({ queryKey: ["mcp-export"] });
    },
  });

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight">MCP servers</h1>
          <p className="mt-1 text-xs text-muted">
            Tool servers the studio&apos;s agents can call — filesystem, git, media, and more.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {discover.isSuccess && (
            <span className="text-xs text-success">{discover.data.added.length} added</span>
          )}
          {discover.isError && (
            <span className="text-xs text-danger">Discovery failed — is the backend up?</span>
          )}
          <Button onClick={() => discover.mutate()} disabled={discover.isPending}>
            <RadioTower className="size-4" /> Discover servers
          </Button>
        </div>
      </header>

      <div className="space-y-6">
        {servers.isLoading && <Spinner />}
        {servers.isError && (
          <EmptyState
            title="Backend not reachable"
            hint="Start it with: cd backend && uvicorn app.main:app --reload"
          />
        )}
        {servers.data?.length === 0 && (
          <EmptyState
            title="No servers registered"
            hint="The built-in catalog ships filesystem, git, github, comfyui, whisper, ffmpeg and more — one click on Discover servers registers them all."
            action={
              <Button onClick={() => discover.mutate()} disabled={discover.isPending}>
                <RadioTower className="size-4" /> Discover servers
              </Button>
            }
          />
        )}
        {servers.data && servers.data.length > 0 && (
          <Card className="px-4">
            <ul className="divide-y divide-edge">
              {servers.data.map((s) => (
                <ServerRow key={s.id} server={s} />
              ))}
            </ul>
          </Card>
        )}
        <ExportConfig />
      </div>
    </div>
  );
}
