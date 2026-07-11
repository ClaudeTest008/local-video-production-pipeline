# Workflow Compatibility Report

Generated 2026-07-11 by a read-only compatibility sweep: every workflow in the
connected ComfyUI library is converted through `ui_to_api` (subgraph
flattening, Set/Get + bypass resolution, dynamic-combo expansion) and its
dependencies are checked against the live server's `object_info`. **No renders
are launched** — this is static dependency analysis after conversion.

Regenerate: `cd backend && python scripts/wf_sweep.py` against a running
ComfyUI.

## Summary

- **26** workflows discovered
- **8** render-ready (all custom nodes registered *and* all referenced models
  matched on the server)
- Remaining blocks are almost entirely **missing models** (user download) or
  **missing custom-node packs** (user install) — not converter defects.

## Detection confidence

| Signal | Source | Reliability |
| --- | --- | --- |
| Missing custom nodes | class absent from `object_info` | **High** — `object_info` is authoritative for registered node classes |
| Missing models | filename not found in any loader's combo option list | **Approximate** — subfolder/path-separator formats vary; verify before acting |

> The LTX 2.3 Dual Character Lip Sync workflow reports 2 "missing models" here
> yet produced a real 1920×1024, 9.04 s, H.264+AAC video on 2026-07-11
> (`output/video/ComfyUI_00027_.mp4`). Those two are false positives from
> nested-path formatting — treat model-missing flags as hints, not verdicts.

## Render-ready (dependencies present)

| Workflow | Type | Nodes |
| --- | --- | --- |
| LTX Director Example Workflow Subgraphs v2 | video_lipsync | 33 |
| LTX_Director_2_Workflow_Hotfix | video_lipsync | 32 |
| SCAIL 2 Multi-role Reference Action Transfer | video | 42 |
| image_ernie_image_turbo | video | 20 |
| image_flux2_klein_9b_kv_image_edit | image | 23 |
| High_Quality_GGUF | other | 25 |
| llm_gemma4_text_gen | (utility) | 7 |
| 0 Help and Resources | (empty) | 0 |

## Blocked — missing custom nodes (user must install the pack)

| Workflow | Missing node classes |
| --- | --- |
| 260504_BUG-SKY_EXAMPLE-MOVIE_v01 | MickmumpitzLabel, MickmumpitzMultilineLabel, MickmumpitzShotDuplicator, MickmumpitzShotOrder |
| 3D Movie Pipeline Cinematic Video Creator | MickmumpitzLabel |
| LTX 2.3 MSR Multi-Subject Video Generator | LiconMSR |
| LTX-2.3 I2V Short-Story PromptRelay | PrimitiveNode\* |
| LVPP-LTX-T2V-v3 | PrimitiveNode\*, CacheDiT_LTX2_Optimizer, RTXVideoSuperResolution |

\* `PrimitiveNode` is **not** a user-install item — it is ComfyUI's legacy
frontend virtual node and should be stripped/resolved by the converter (like
Reroute). Tracked as a converter fix, not a dependency gap. The typed
primitives (`PrimitiveInt`, `PrimitiveFloat`, `PrimitiveString`,
`PrimitiveStringMultiline`) are real nodes and are kept.

## Blocked — missing models (user must download)

These convert cleanly (all nodes present) but reference model files not found
on the server. Verify against the flagged path before downloading — some are
false positives (see confidence note).

| Workflow | Type | Example missing models |
| --- | --- | --- |
| 1–4 Juggernaut Reborn (txt2img / img2img / +Lora / +ControlNet) | image | `sd15/juggernaut_reborn.safetensors` (+ CakeStyle, canny controlnet) |
| 5a–7 Z-Image Turbo (fp8 / GGUF / +Lora / +ControlNet) | image | `z-image/z-image-turbo-*`, Qwen text encoders, Fun-Controlnet-Union |
| templates-qwen_multiangle | image | Qwen-Image-Edit 2511 checkpoints + LoRAs |
| LTX 2.3 Director Cinematic AI Video Creator | video_lipsync | OmniCine preview, ic-subtitles-remove |
| LTX 2.3 Prompt Relay Scene-Controlled | video_lipsync | ltx-2.3-22b-dev, distilled-lora-384 |
| LTX-2.3 I2V Short-Story PromptRelay | video_lipsync | LTX23 audio/video VAE (KJ), taeltx2_3 |

## Most-blocking missing node classes

| Count | Class | Note |
| --- | --- | --- |
| 2 | MickmumpitzLabel | Mickmumpitz pack (annotation nodes) |
| 2 | PrimitiveNode | converter should strip (virtual node) |
| 1 | MickmumpitzMultilineLabel / ShotDuplicator / ShotOrder | Mickmumpitz pack |
| 1 | LiconMSR | LTX MSR pack |
| 1 | CacheDiT_LTX2_Optimizer / RTXVideoSuperResolution | LTX optimizer nodes |

## Follow-ups

- Converter: strip/resolve legacy `PrimitiveNode` (unblocks 2 workflows).
- Converter: `VHS_VideoCombine` widget off-by-one (does not block rendering via
  `SaveVideo`, but corrupts video-combine params).
- Model/custom-node acquisition is a user action; the app should surface these
  per-workflow lists in the UI (workflow-intelligence milestone).
