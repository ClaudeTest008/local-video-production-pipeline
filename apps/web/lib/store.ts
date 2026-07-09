"use client";

import { create } from "zustand";

interface StudioState {
  activeProjectId: number | null;
  setActiveProject: (id: number | null) => void;
  paletteOpen: boolean;
  setPaletteOpen: (open: boolean) => void;
  chatPanelOpen: boolean;
  toggleChatPanel: () => void;
}

export const useStudio = create<StudioState>((set) => ({
  activeProjectId: null,
  setActiveProject: (id) => set({ activeProjectId: id }),
  paletteOpen: false,
  setPaletteOpen: (open) => set({ paletteOpen: open }),
  chatPanelOpen: false,
  toggleChatPanel: () => set((s) => ({ chatPanelOpen: !s.chatPanelOpen })),
}));
