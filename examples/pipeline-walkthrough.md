# Idea → video: an API walkthrough

Everything below is plain REST against `http://127.0.0.1:8321/api` (interactive docs at `/docs`). The UI drives these same endpoints.

```bash
# 1. Idea → project (folder tree is created automatically)
curl -X POST localhost:8321/api/projects -H "Content-Type: application/json" \
  -d '{"name": "My Video", "idea": "Why do CRTs still beat modern displays for retro games?"}'

# 2. Research — notes + optional web search (Brave/Tavily key required for search)
curl -X POST localhost:8321/api/research/search -H "Content-Type: application/json" \
  -d '{"query": "CRT latency vs OLED retro gaming", "provider": "brave"}'
curl -X POST localhost:8321/api/research -H "Content-Type: application/json" \
  -d '{"project_id": 1, "query": "latency", "content": "CRT ~0ms scanout…", "sources": []}'

# 3. Script — via the Script Writer agent (seed agents first: POST /agents/seed-defaults)
curl -X POST localhost:8321/api/agents/4/run -H "Content-Type: application/json" \
  -d '{"input": "Write a 3-minute script from my research notes: …", "project_id": 1}'

# 4. Storyboard scenes
curl -X POST localhost:8321/api/storyboard -H "Content-Type: application/json" \
  -d '{"project_id": 1, "order_index": 0, "title": "CRT glow", "prompt": "macro shot of CRT phosphor glow", "duration_s": 5}'

# 5. Images — queue a ComfyUI workflow (see comfyui-txt2img.json)
curl -X POST localhost:8321/api/comfyui/queue -H "Content-Type: application/json" \
  -d "{\"workflow\": $(cat examples/comfyui-txt2img.json), \"project_id\": 1}"

# 6. Voice-over (needs piper on PATH, or an XTTS/Kokoro server)
curl -X POST localhost:8321/api/voice/synthesize -H "Content-Type: application/json" \
  -d '{"project_id": 1, "text": "CRTs draw the frame as it arrives…", "engine": "piper"}'

# 7. Captions (needs: pip install -e ".[transcribe]")
curl -X POST localhost:8321/api/subtitles/transcribe -H "Content-Type: application/json" \
  -d '{"project_id": 1, "audio_path": "data/projects/project-1/assets/audio/voice-1.wav"}'
curl "localhost:8321/api/subtitles/1/export?fmt=srt"

# 8. Timeline → MP4 (needs FFmpeg on PATH; run:false returns the command without executing)
curl -X POST localhost:8321/api/timelines -H "Content-Type: application/json" \
  -d '{"project_id": 1, "tracks": [{"kind": "video", "clips": [{"path": "scene1.mp4"}, {"path": "scene2.mp4"}]}]}'
curl -X POST localhost:8321/api/timelines/1/export -H "Content-Type: application/json" \
  -d '{"format": "mp4", "run": true}'

# 9. SEO + publishing record + archive
curl -X POST localhost:8321/api/seo -H "Content-Type: application/json" \
  -d '{"project_id": 1, "title": "CRTs Never Died", "tags": ["retro", "crt"]}'
curl -X POST localhost:8321/api/projects/1/archive
```
