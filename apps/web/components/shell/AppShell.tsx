"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@lvpp/shared";
import { Kbd } from "@lvpp/ui";
import { MessageSquare, Plus } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { NAV, NAV_ADVANCED } from "@/lib/nav";
import { useStudio } from "@/lib/store";
import { ChatDock } from "./ChatDock";
import { CommandPalette } from "./CommandPalette";

function NavRail() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Modules"
      className="flex w-56 shrink-0 flex-col border-r border-edge bg-surface"
    >
      <div className="flex h-12 items-center gap-2 border-b border-edge px-4">
        <span className="size-2.5 rounded-full bg-accent shadow-[0_0_8px_var(--color-accent)]" />
        <span className="font-display text-sm font-semibold tracking-wide">LVPP Studio</span>
      </div>
      <div className="flex-1 overflow-y-auto py-2">
        <Link
          href="/create"
          className={`mx-2 mb-2 flex items-center justify-center gap-2 rounded-md py-2 text-[13px] font-medium transition-colors ${
            pathname === "/create"
              ? "bg-accent text-accent-fg"
              : "bg-accent/90 text-accent-fg hover:bg-accent"
          }`}
        >
          <Plus className="size-4" aria-hidden /> Create
        </Link>
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`mx-2 mb-0.5 flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] transition-colors ${
                active
                  ? "bg-surface-2 text-fg shadow-[inset_2px_0_0_var(--color-accent)]"
                  : "text-muted hover:bg-surface-2/60 hover:text-fg"
              }`}
            >
              <Icon className="size-4" aria-hidden />
              {label}
            </Link>
          );
        })}
        <p className="mx-4 mb-1 mt-4 text-[10px] uppercase tracking-wider text-muted/60">
          Advanced
        </p>
        {NAV_ADVANCED.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`mx-2 mb-0.5 flex items-center gap-2.5 rounded-md px-2.5 py-1 text-xs transition-colors ${
                active
                  ? "bg-surface-2 text-fg shadow-[inset_2px_0_0_var(--color-accent)]"
                  : "text-muted/80 hover:bg-surface-2/60 hover:text-fg"
              }`}
            >
              <Icon className="size-3.5" aria-hidden />
              {label}
            </Link>
          );
        })}
      </div>
      <div className="border-t border-edge p-3 text-[11px] text-muted">
        Command palette <Kbd>Ctrl K</Kbd>
      </div>
    </nav>
  );
}

function StatusBar() {
  const health = useQuery({ queryKey: ["health"], queryFn: api.health, refetchInterval: 15_000 });
  const comfy = useQuery({
    queryKey: ["comfy-status"],
    queryFn: api.comfyStatus,
    refetchInterval: 15_000,
  });
  const toggleChatPanel = useStudio((s) => s.toggleChatPanel);
  return (
    <footer className="flex h-6 shrink-0 items-center gap-4 border-t border-edge bg-surface px-3 font-mono text-[11px] text-muted">
      <span className="flex items-center gap-1.5">
        <span
          className={`size-1.5 rounded-full ${health.data ? "bg-success" : "bg-danger"}`}
          aria-hidden
        />
        backend {health.data ? "connected" : "offline"}
      </span>
      <span className="flex items-center gap-1.5">
        <span
          className={`size-1.5 rounded-full ${comfy.data?.available ? "bg-success" : "bg-edge"}`}
          aria-hidden
        />
        comfyui {comfy.data?.available ? "ready" : "off"}
      </span>
      <button
        onClick={toggleChatPanel}
        className="ml-auto flex items-center gap-1 hover:text-fg"
        aria-label="Toggle chat panel"
      >
        <MessageSquare className="size-3" /> chat
      </button>
    </footer>
  );
}

function useFirstRunRedirect() {
  const pathname = usePathname();
  const router = useRouter();
  const setup = useQuery({ queryKey: ["setup"], queryFn: api.setupStatus, staleTime: 60_000 });
  useEffect(() => {
    if (setup.data && !setup.data.complete && pathname !== "/setup") {
      router.replace("/setup");
    }
  }, [setup.data, pathname, router]);
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { paletteOpen, setPaletteOpen, chatPanelOpen } = useStudio();
  useFirstRunRedirect();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen(!paletteOpen);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [paletteOpen, setPaletteOpen]);

  return (
    <div className="flex h-dvh flex-col">
      <div className="flex min-h-0 flex-1">
        <NavRail />
        <PanelGroup direction="horizontal" className="min-w-0 flex-1">
          <Panel defaultSize={chatPanelOpen ? 72 : 100} minSize={40}>
            <main className="h-full overflow-y-auto">{children}</main>
          </Panel>
          {chatPanelOpen && (
            <>
              <PanelResizeHandle className="w-px bg-edge transition-colors hover:bg-accent" />
              <Panel defaultSize={28} minSize={18}>
                <ChatDock />
              </Panel>
            </>
          )}
        </PanelGroup>
      </div>
      <StatusBar />
      <CommandPalette />
    </div>
  );
}
