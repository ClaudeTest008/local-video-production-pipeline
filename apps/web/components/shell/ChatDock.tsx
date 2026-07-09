"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@lvpp/shared";
import { Button, Input, Spinner } from "@lvpp/ui";
import { useState } from "react";
import { useStudio } from "@/lib/store";

/** Always-available side chat, pinned to the active project when one is set. */
export function ChatDock() {
  const activeProjectId = useStudio((s) => s.activeProjectId);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const queryClient = useQueryClient();

  const messages = useQuery({
    queryKey: ["chat", conversationId],
    queryFn: () => api.chatMessages(conversationId!),
    enabled: conversationId !== null,
  });

  const send = useMutation({
    mutationFn: async (content: string) => {
      let cid = conversationId;
      if (cid === null) {
        const conversation = await api.createConversation({
          project_id: activeProjectId,
        });
        cid = conversation.id;
        setConversationId(cid);
      }
      return api.sendMessage(cid, content);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["chat", conversationId] }),
  });

  const submit = () => {
    if (!draft.trim() || send.isPending) return;
    send.mutate(draft.trim());
    setDraft("");
  };

  return (
    <aside className="flex h-full flex-col bg-surface" aria-label="Chat panel">
      <div className="flex h-9 items-center border-b border-edge px-3 text-xs font-medium text-muted">
        Chat {activeProjectId ? `· project #${activeProjectId}` : "· no project pinned"}
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        {(messages.data ?? []).map((m) => (
          <div key={m.id} className={m.role === "user" ? "text-right" : ""}>
            <div
              className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-left text-[13px] leading-relaxed ${
                m.role === "user" ? "bg-accent/15 text-fg" : "bg-surface-2 text-fg"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {send.isPending && <Spinner />}
        {send.isError && (
          <p className="text-xs text-danger">
            {(send.error as Error).message}. Check the provider in Settings.
          </p>
        )}
      </div>
      <form
        className="flex gap-2 border-t border-edge p-2"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask the studio…"
          aria-label="Chat message"
        />
        <Button type="submit" size="md" disabled={send.isPending}>
          Send
        </Button>
      </form>
    </aside>
  );
}
