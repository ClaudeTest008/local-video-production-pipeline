"""Read-only compatibility/dependency sweep across all discovered ComfyUI
workflows. Converts each via the live object_info, then statically reports
missing custom-node classes and missing model files. Launches NO renders."""
import sys, json
from app.modules.comfyui.client import ComfyUIClient
from app.modules.comfyui.convert import ui_to_api
from app.modules.workflows.classify import classify

c = ComfyUIClient()
if not c.is_available():
    print("ComfyUI not reachable"); sys.exit(1)
oi = c.object_info()

# installed model filenames, harvested from every loader's combo option lists
installed_models = set()
for cls, info in oi.items():
    for sec in ("required", "optional"):
        for k, v in (info.get("input", {}).get(sec, {}) or {}).items():
            if isinstance(v, list) and v and isinstance(v[0], list):
                installed_models |= {
                    x for x in v[0]
                    if isinstance(x, str)
                    and x.lower().endswith((".safetensors", ".gguf", ".ckpt", ".pt", ".sft"))
                }

MODEL_EXTS = (".safetensors", ".gguf", ".ckpt", ".pt", ".sft")
rows = []
for filename in c.list_server_workflows():
    name = filename.rsplit("/", 1)[-1].removesuffix(".json")
    try:
        ui = c.get_server_workflow(filename)
        graph = ui_to_api(ui, oi)["graph"] if "nodes" in ui else ui
        info = classify(name, graph)
        classes = {n.get("class_type") for n in graph.values()}
        missing_nodes = sorted(cl for cl in classes if cl and cl not in oi)
        refs = {
            v for n in graph.values() for v in (n.get("inputs") or {}).values()
            if isinstance(v, str) and v.lower().endswith(MODEL_EXTS)
        }
        missing_models = sorted(m for m in refs if m not in installed_models)
        renderable = not missing_nodes and not missing_models
        rows.append({
            "name": name, "wf_type": info["wf_type"], "nodes": len(graph),
            "missing_nodes": missing_nodes, "missing_models": missing_models,
            "renderable": renderable,
        })
    except Exception as e:
        rows.append({"name": name, "error": str(e)[:160]})

rows.sort(key=lambda r: (not r.get("renderable", False), r.get("wf_type", ""), r["name"]))
ready = [r for r in rows if r.get("renderable")]
print(f"=== {len(rows)} workflows | {len(ready)} render-ready (deps present) ===\n")
for r in rows:
    if "error" in r:
        print(f"[ERR ] {r['name']}: {r['error']}"); continue
    flag = "OK  " if r["renderable"] else "BLOCK"
    print(f"[{flag}] {r['wf_type']:<13} {r['name'][:52]:<52} nodes={r['nodes']}")
    if r["missing_nodes"]:
        print(f"         missing nodes: {r['missing_nodes']}")
    if r["missing_models"]:
        mm = r["missing_models"]
        print(f"         missing models ({len(mm)}): {mm[:4]}{'...' if len(mm) > 4 else ''}")

# aggregate: which custom-node packs block the most workflows
from collections import Counter
blk = Counter()
for r in rows:
    for n in r.get("missing_nodes", []):
        blk[n] += 1
if blk:
    print("\n=== most-blocking missing node classes ===")
    for cls, n in blk.most_common(12):
        print(f"  {n:>2} workflows  <- {cls}")
