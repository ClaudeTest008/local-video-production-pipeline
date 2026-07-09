import {
  BarChart3,
  Bot,
  Clapperboard,
  FileText,
  FolderOpen,
  Image,
  LayoutDashboard,
  MessageSquare,
  Network,
  Plug,
  Settings,
  SlidersHorizontal,
  Wand2,
} from "lucide-react";

export const NAV = [
  { href: "/", label: "Projects", icon: LayoutDashboard },
  { href: "/chat", label: "AI Chat", icon: MessageSquare },
  { href: "/studio", label: "Prompt Studio", icon: Wand2 },
  { href: "/scripts", label: "Scripts", icon: FileText },
  { href: "/canvas", label: "Workflow Canvas", icon: Network },
  { href: "/comfyui", label: "ComfyUI", icon: Image },
  { href: "/assets", label: "Assets", icon: FolderOpen },
  { href: "/timeline", label: "Timeline", icon: Clapperboard },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/mcp", label: "MCP Servers", icon: Plug },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

export const MISC_ICON = SlidersHorizontal;
