"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Project } from "@lvpp/shared";
import { Badge, Button, Card, EmptyState, Input, Spinner, Textarea } from "@lvpp/ui";
import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { PipelineRail } from "@/components/PipelineRail";
import { useStudio } from "@/lib/store";

function NewProjectForm({ onDone }: { onDone: () => void }) {
  const [name, setName] = useState("");
  const [idea, setIdea] = useState("");
  const queryClient = useQueryClient();
  const create = useMutation({
    mutationFn: () => api.createProject({ name, idea }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      onDone();
    },
  });
  return (
    <Card className="p-4">
      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim()) create.mutate();
        }}
      >
        <Input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Video title or working name"
          aria-label="Project name"
        />
        <Textarea
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          rows={3}
          placeholder="The idea — one messy paragraph is enough. Agents take it from here."
          aria-label="Idea"
        />
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onDone}>
            Cancel
          </Button>
          <Button type="submit" disabled={create.isPending || !name.trim()}>
            Create project
          </Button>
        </div>
        {create.isError && (
          <p className="text-xs text-danger">{(create.error as Error).message}</p>
        )}
      </form>
    </Card>
  );
}

function ProjectCard({ project, index }: { project: Project; index: number }) {
  const setActiveProject = useStudio((s) => s.setActiveProject);
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.25 }}
    >
      <Link href={`/project?id=${project.id}`} onClick={() => setActiveProject(project.id)}>
        <Card className="group p-4 transition-colors hover:border-accent/40">
          <div className="mb-1 flex items-center justify-between gap-2">
            <h2 className="truncate font-display text-[15px] font-semibold">{project.name}</h2>
            <Badge tone="accent">{project.status}</Badge>
          </div>
          <p className="mb-4 line-clamp-2 min-h-8 text-xs text-muted">
            {project.idea || project.description || "No idea captured yet."}
          </p>
          <PipelineRail status={project.status} compact />
        </Card>
      </Link>
    </motion.div>
  );
}

export default function ProjectsPage() {
  const [creating, setCreating] = useState(false);
  const projects = useQuery({ queryKey: ["projects"], queryFn: api.listProjects });

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold tracking-tight">Projects</h1>
          <p className="mt-1 text-xs text-muted">
            Idea to published video — every stage lives on this rail.
          </p>
        </div>
        <Button onClick={() => setCreating(true)}>
          <Plus className="size-4" /> New project
        </Button>
      </header>

      {creating && (
        <div className="mb-6">
          <NewProjectForm onDone={() => setCreating(false)} />
        </div>
      )}

      {projects.isLoading && <Spinner />}
      {projects.isError && (
        <EmptyState
          title="Backend not reachable"
          hint="Start it with: cd backend && uvicorn app.main:app --reload"
        />
      )}
      {projects.data?.length === 0 && !creating && (
        <EmptyState
          title="No projects yet"
          hint="Create one and the studio scaffolds its folder tree — research, scripts, storyboard, assets, exports."
          action={<Button onClick={() => setCreating(true)}>Create the first project</Button>}
        />
      )}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {projects.data?.map((p, i) => <ProjectCard key={p.id} project={p} index={i} />)}
      </div>
    </div>
  );
}
