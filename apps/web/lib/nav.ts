import {
  BarChart3,
  Bot,
  Clapperboard,
  Compass,
  FileText,
  FolderKanban,
  FolderOpen,
  Image,
  LayoutDashboard,
  Lightbulb,
  MessageSquare,
  Network,
  Play,
  Plug,
  Settings,
  Wand2,
  Workflow,
} from "lucide-react";

/** Focused core — the creator's daily loop. */
export const NAV = [
  { href: "/", label: "Studio", icon: LayoutDashboard },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/brands", label: "Brands", icon: Compass },
  { href: "/strategy", label: "Strategy", icon: Lightbulb },
  { href: "/pipeline", label: "Pipeline", icon: Play },
  { href: "/timeline", label: "Editor", icon: Clapperboard },
  { href: "/assets", label: "Assets", icon: FolderOpen },
  { href: "/workflows", label: "ComfyUI Workflows", icon: Workflow },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

/** Advanced tools — collapsed under their own sidebar group. */
export const NAV_ADVANCED = [
  { href: "/chat", label: "AI Chat", icon: MessageSquare },
  { href: "/studio", label: "Prompt Studio", icon: Wand2 },
  { href: "/scripts", label: "Scripts", icon: FileText },
  { href: "/canvas", label: "Workflow Canvas", icon: Network },
  { href: "/comfyui", label: "ComfyUI Console", icon: Image },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/mcp", label: "MCP Servers", icon: Plug },
] as const;
