"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, PIPELINE_STAGES, type WorkflowDef } from "@lvpp/shared";
import { Button, Card, Input, Spinner } from "@lvpp/ui";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Save } from "lucide-react";
import { useCallback, useState } from "react";

const initialNodes: Node[] = PIPELINE_STAGES.map((stage, i) => ({
  id: stage,
  position: { x: i * 180, y: i % 2 === 0 ? 0 : 120 },
  data: { label: stage },
}));

const initialEdges: Edge[] = PIPELINE_STAGES.slice(0, -1).map((stage, i) => ({
  id: `e-${stage}-${PIPELINE_STAGES[i + 1]}`,
  source: stage,
  target: PIPELINE_STAGES[i + 1],
  animated: true,
}));

export default function CanvasPage() {
  const [name, setName] = useState("Default pipeline");
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(initialEdges);
  const queryClient = useQueryClient();

  const workflows = useQuery({ queryKey: ["workflows"], queryFn: api.listWorkflows });

  const save = useMutation({
    mutationFn: () =>
      api.saveWorkflow({
        name: name.trim(),
        kind: "pipeline",
        // ponytail: JSON round-trip strips React Flow's internal fields to plain data
        graph: JSON.parse(JSON.stringify({ nodes, edges })) as Record<string, unknown>,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workflows"] }),
  });

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [setEdges],
  );

  const loadWorkflow = (wf: WorkflowDef) => {
    const graph = wf.graph as { nodes?: Node[]; edges?: Edge[] };
    setNodes(graph.nodes?.length ? graph.nodes : initialNodes);
    setEdges(Array.isArray(graph.edges) ? graph.edges : initialEdges);
    setName(wf.name);
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">Workflow canvas</h1>
        <p className="mt-1 text-xs text-muted">
          The pipeline as a graph — rewire stages, then save it as a reusable workflow.
        </p>
      </header>

      <Card className="mb-4 flex flex-wrap items-center gap-2 p-3">
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Workflow name"
          aria-label="Workflow name"
          className="max-w-60"
        />
        <Button onClick={() => save.mutate()} disabled={save.isPending || !name.trim()}>
          <Save className="size-4" /> Save
        </Button>
        {workflows.isLoading && <Spinner />}
        {workflows.data && workflows.data.length > 0 && (
          <select
            aria-label="Load workflow"
            defaultValue=""
            onChange={(e) => {
              const wf = workflows.data.find((w) => w.id === Number(e.target.value));
              if (wf) loadWorkflow(wf);
            }}
            className="h-9 rounded-md border border-edge bg-surface px-2 text-sm text-fg focus-visible:outline-2 focus-visible:outline-accent"
          >
            <option value="" disabled>
              Load saved workflow…
            </option>
            {workflows.data.map((wf) => (
              <option key={wf.id} value={wf.id}>
                {wf.name} (v{wf.version})
              </option>
            ))}
          </select>
        )}
        {save.isSuccess && <span className="text-xs text-success">Saved</span>}
        {save.isError && (
          <span className="text-xs text-danger">
            Save failed: {(save.error as Error).message} — check the backend is running.
          </span>
        )}
        {workflows.isError && (
          <span className="text-xs text-danger">
            Backend not reachable — saved workflows unavailable. Start it with: cd backend &&
            uvicorn app.main:app --reload
          </span>
        )}
      </Card>

      <Card className="overflow-hidden" style={{ height: "calc(100dvh - 16rem)" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          colorMode="dark"
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </Card>
    </div>
  );
}
