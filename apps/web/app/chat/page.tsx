"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ChatMessage, type Conversation } from "@lvpp/shared";
import { Button, Card, EmptyState, Input, Spinner } from "@lvpp/ui";
import { MessageSquare, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useStudio } from "@/lib/store";

function ConversationRow({
  conversation,
  selected,
  onSelect,
  onDeleted,
}: {
  conversation: Conversation;
  selected: boolean;
  onSelect: () => void;
  onDeleted: () => void;
}) {
  const queryClient = useQueryClient();
  const remove = useMutation({
    mutationFn: () => api.delete(`/chat/conversations/${conversation.id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      onDeleted();
    },
  });
  return (
    <li
      className={`group flex cursor-pointer items-center justify-between gap-2 rounded-md px-2.5 py-2 transition-colors ${
        selected ? "bg-surface-2" : "hover:bg-surface-2"
      }`}
      onClick={onSelect}
    >
      <div className="min-w-0">
        <p className={`truncate text-sm ${selected ? "text-fg" : "text-muted"}`}>
          {conversation.title || "Untitled"}
        </p>
        <p className="font-mono text-[10px] text-muted/70">
          {new Date(conversation.created_at).toLocaleDateString()}
        </p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        aria-label="Delete conversation"
        className="opacity-0 group-hover:opacity-100"
        disabled={remove.isPending}
        onClick={(e) => {
          e.stopPropagation();
          remove.mutate();
        }}
      >
        <Trash2 className="size-3.5 text-danger" />
      </Button>
    </li>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
          isUser ? "bg-accent/15 text-fg" : "bg-surface-2 text-fg"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}

function MessagePane({ conversationId }: { conversationId: number }) {
  const [draft, setDraft] = useState("");
  const queryClient = useQueryClient();
  const messages = useQuery({
    queryKey: ["chat-messages", conversationId],
    queryFn: () => api.chatMessages(conversationId),
  });
  const send = useMutation({
    mutationFn: (content: string) => api.sendMessage(conversationId, content),
    onSuccess: () => {
      setDraft("");
      queryClient.invalidateQueries({ queryKey: ["chat-messages", conversationId] });
    },
  });

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.isLoading && <Spinner />}
        {messages.isError && (
          <EmptyState
            title="Could not load messages"
            hint="Check that the backend is running on port 8321, then reselect the conversation."
          />
        )}
        {messages.data?.length === 0 && (
          <p className="text-xs text-muted">No messages yet. Say something below.</p>
        )}
        {messages.data?.map((m) => <MessageBubble key={m.id} message={m} />)}
      </div>
      <form
        className="border-t border-edge p-3"
        onSubmit={(e) => {
          e.preventDefault();
          if (draft.trim() && !send.isPending) send.mutate(draft.trim());
        }}
      >
        <div className="flex gap-2">
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Message the assistant…"
            aria-label="Message"
            disabled={send.isPending}
          />
          <Button type="submit" disabled={send.isPending || !draft.trim()}>
            {send.isPending ? <Spinner className="size-3.5" /> : "Send"}
          </Button>
        </div>
        {send.isError && (
          <p className="mt-2 text-xs text-danger">
            Provider failed: {(send.error as Error).message}. Configure providers in Settings or
            make sure ollama is running.
          </p>
        )}
      </form>
    </div>
  );
}

export default function ChatPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const activeProjectId = useStudio((s) => s.activeProjectId);
  const queryClient = useQueryClient();

  const conversations = useQuery({
    queryKey: ["conversations"],
    queryFn: () => api.listConversations(),
  });
  const create = useMutation({
    mutationFn: () => api.createConversation({ project_id: activeProjectId }),
    onSuccess: (c) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      setSelectedId(c.id);
    },
  });

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-display text-xl font-semibold tracking-tight">Chat</h1>
        <p className="mt-1 text-xs text-muted">
          Full-width AI workspace — conversations persist per project.
        </p>
      </header>

      <Card className="flex h-[calc(100vh-14rem)] min-h-96 overflow-hidden">
        <aside className="flex w-64 shrink-0 flex-col border-r border-edge">
          <div className="border-b border-edge p-3">
            <Button
              size="sm"
              className="w-full"
              disabled={create.isPending}
              onClick={() => create.mutate()}
            >
              <Plus className="size-3.5" /> New conversation
            </Button>
            {create.isError && (
              <p className="mt-2 text-xs text-danger">{(create.error as Error).message}</p>
            )}
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {conversations.isLoading && <Spinner className="m-2" />}
            {conversations.isError && (
              <p className="p-2 text-xs text-danger">
                Backend not reachable. Start it with: cd backend &amp;&amp; uvicorn app.main:app
                --reload
              </p>
            )}
            {conversations.data?.length === 0 && (
              <p className="p-2 text-xs text-muted">No conversations yet.</p>
            )}
            <ul className="space-y-1">
              {conversations.data?.map((c) => (
                <ConversationRow
                  key={c.id}
                  conversation={c}
                  selected={c.id === selectedId}
                  onSelect={() => setSelectedId(c.id)}
                  onDeleted={() => {
                    if (selectedId === c.id) setSelectedId(null);
                  }}
                />
              ))}
            </ul>
          </div>
        </aside>

        {selectedId === null ? (
          <div className="flex flex-1 items-center justify-center p-6">
            <EmptyState
              title="No conversation selected"
              hint={
                "Pick one on the left or start a new conversation. Replies use the default provider (ollama) unless you change it — providers and defaults live in Settings."
              }
              action={
                <Button size="sm" onClick={() => create.mutate()}>
                  <MessageSquare className="size-3.5" /> Start a conversation
                </Button>
              }
            />
          </div>
        ) : (
          <MessagePane conversationId={selectedId} />
        )}
      </Card>
    </div>
  );
}
