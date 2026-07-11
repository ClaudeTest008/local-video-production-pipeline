"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@lvpp/shared";
import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import { NAV } from "@/lib/nav";
import { useStudio } from "@/lib/store";

/** Ctrl+K — navigation, project jump, and global search in one surface. */
export function CommandPalette() {
  const { paletteOpen, setPaletteOpen, setActiveProject } = useStudio();
  const router = useRouter();
  const projects = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
    enabled: paletteOpen,
  });

  const go = (href: string) => {
    router.push(href);
    setPaletteOpen(false);
  };

  return (
    <Command.Dialog
      open={paletteOpen}
      onOpenChange={setPaletteOpen}
      label="Command palette"
      className="fixed left-1/2 top-24 z-50 w-[560px] max-w-[calc(100vw-2rem)] -translate-x-1/2 overflow-hidden rounded-xl border border-edge bg-surface shadow-2xl shadow-black/50"
    >
      <Command.Input
        placeholder="Go to module, open project, search…"
        className="h-12 w-full border-b border-edge bg-transparent px-4 text-sm text-fg outline-none placeholder:text-muted/60"
      />
      <Command.List className="max-h-80 overflow-y-auto p-2">
        <Command.Empty className="py-8 text-center text-xs text-muted">
          Nothing matches. Try a module name or project title.
        </Command.Empty>
        <Command.Group
          heading="Modules"
          className="text-[10px] uppercase tracking-wider text-muted [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
        >
          {NAV.map(({ href, label, icon: Icon }) => (
            <Command.Item
              key={href}
              value={`module ${label}`}
              onSelect={() => go(href)}
              className="flex cursor-pointer items-center gap-2.5 rounded-md px-2 py-2 text-sm text-fg data-[selected=true]:bg-surface-2"
            >
              <Icon className="size-4 text-muted" aria-hidden />
              {label}
            </Command.Item>
          ))}
        </Command.Group>
        {(projects.data?.length ?? 0) > 0 && (
          <Command.Group
            heading="Projects"
            className="text-[10px] uppercase tracking-wider text-muted [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
          >
            {projects.data!.map((p) => (
              <Command.Item
                key={p.id}
                value={`project ${p.name}`}
                onSelect={() => {
                  setActiveProject(p.id);
                  go(`/project?id=${p.id}`);
                }}
                className="flex cursor-pointer items-center justify-between rounded-md px-2 py-2 text-sm text-fg data-[selected=true]:bg-surface-2"
              >
                {p.name}
                <span className="font-mono text-[10px] text-accent">{p.status}</span>
              </Command.Item>
            ))}
          </Command.Group>
        )}
      </Command.List>
    </Command.Dialog>
  );
}
