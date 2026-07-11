# Vision: an AI Creator Operating System

LVPP is not a video editor, not a ComfyUI frontend, and not another chat app. It is a **local-first Creator OS**: the user is the Creative Director; a crew of specialized AI agents does the work — from "what should I create next?" through research, script, visuals, voice, SEO, and (eventually) publishing and performance review.

## The loop

```
        ┌────────────────────────────────────────────────────┐
        │                     KNOWLEDGE                      │
        │   render stats · pipeline failures · analytics    │
        └───────▲───────────────────────────────────┬───────┘
                │ learns from                        │ feeds context to
┌───────────────┴──────┐   approve   ┌───────────────▼───────────────┐
│       STRATEGY       │────────────▶│           PIPELINE            │
│ scored opportunities │  = project  │ research → script → storyboard│
│ "what to create?"    │             │ → prompts → images → voice    │
└───────────▲──────────┘             │ → seo → thumbnail             │
            │                        └───────────────┬───────────────┘
            │ voice · style · goals                   │ assets, exports
        ┌───┴────────────────────────────────────────▼───────┐
        │                       BRAND                        │
        │  every agent call runs inside a brand's identity   │
        └────────────────────────────────────────────────────┘
```

## Operating modes (autopilot ladder)

| Mode | Who does what | Status |
|---|---|---|
| **Manual** | User drives every module by hand | shipped |
| **Assisted** | AI runs one pipeline stage per click; user reviews between stages | shipped (`POST /pipeline/runs/{id}/step`) |
| **Producer** | AI runs every runnable stage back-to-back for one project | shipped (`/run-all`) |
| **Studio** | AI drafts the calendar from strategy; user approves batches | roadmap |
| **Agency** | User sets business goals ("100k subs"); AI plans, produces, publishes, reviews | roadmap |

The ladder is deliberate: each rung ships only when the rung below is trustworthy. Autonomy is earned by evidence (the knowledge engine), not promised.

## Principles

1. **Local-first** — SQLite + local file tree; Ollama and ComfyUI are the default engines; cloud providers are optional plugins.
2. **Everything replaceable** — providers, workflows, MCP servers, and feature modules are all registry-driven; nothing in core names a vendor.
3. **The AI decides render details** — users state intent; workflow selection uses measured stats (`/comfyui/workflow-stats`), prompt injection adapts saved graphs. Users never have to know what a sampler is.
4. **Honest autonomy** — media stages skip cleanly when local engines are absent; strategy says when it reasons without live data; every stage logs what it actually did.
5. **Learning over time** — operational events become Learnings; the strongest feed back into every agent's context. Analytics close the loop.

## Where this goes next

Multi-format output (Shorts/TikTok cutdowns, blog/newsletter from the same research), WebSocket progress streaming, YouTube publishing, trend ingestion (RSS/Reddit/Google Trends), retention-aware creative review, embedding-based knowledge retrieval. See [roadmap.md](roadmap.md).
