"""UI-format → API-format workflow conversion.

ComfyUI's web UI saves graphs with layout + numbered links; the /prompt API
wants {node_id: {class_type, inputs}}. Widget values are positional in the UI
format, so the live server's object_info supplies the input-name order.

Best effort by design: nodes we cannot map are reported, never guessed —
the workflow is stored with a "check_required" conversion status and verified
by its first successful render.
"""

import logging

logger = logging.getLogger(__name__)

# UI node types that never reach the API graph
SKIP_TYPES = {"Note", "MarkdownNote"}
# widget appended automatically after seed-like inputs in the UI
SEED_INPUTS = {"seed", "noise_seed"}
PRIMITIVE_TYPES = {"INT", "FLOAT", "STRING", "BOOLEAN"}


class ConversionResult(dict):
    """api graph in ["graph"], issues in ["issues"] (empty = clean)."""


def _link_map(ui: dict) -> dict[int, tuple[int, int]]:
    """link_id -> (source_node_id, source_slot)."""
    return {
        link[0]: (link[1], link[2])
        for link in ui.get("links", [])
        if isinstance(link, list) and len(link) >= 5
    }


def _resolve_reroutes(node_by_id: dict, links: dict, src: tuple[int, int]) -> tuple[int, int]:
    """Follow Reroute chains to the real producer."""
    for _ in range(50):
        node = node_by_id.get(src[0])
        if node is None or node.get("type") not in ("Reroute", "RerouteNode"):
            return src
        in_links = [i.get("link") for i in node.get("inputs", []) if i.get("link") is not None]
        if not in_links:
            return src
        src = links.get(in_links[0], src)
    return src


def _widget_input_names(class_type: str, object_info: dict) -> list[str]:
    """Input names that are widgets (primitives/combos), in declaration order."""
    spec = object_info.get(class_type, {}).get("input", {})
    names = []
    for section in ("required", "optional"):
        for name, definition in spec.get(section, {}).items():
            if not isinstance(definition, (list, tuple)) or not definition:
                continue
            kind = definition[0]
            if isinstance(kind, list) or kind in PRIMITIVE_TYPES:  # combo list or primitive
                names.append(name)
    return names


def ui_to_api(ui: dict, object_info: dict) -> ConversionResult:
    issues: list[str] = []
    nodes = ui.get("nodes", [])
    node_by_id = {n["id"]: n for n in nodes}
    links = _link_map(ui)
    graph: dict[str, dict] = {}

    for node in nodes:
        node_type = node.get("type", "")
        if node_type in SKIP_TYPES or node_type.startswith("Reroute"):
            continue
        if node.get("mode") == 2:  # muted — drop; consumers will report missing input
            issues.append(f"node {node['id']} ({node_type}) is muted; dropped")
            continue
        if node.get("mode") == 4:
            issues.append(f"node {node['id']} ({node_type}) is bypassed; kept as-is")

        inputs: dict = {}
        connected = set()
        for inp in node.get("inputs", []) or []:
            if inp.get("link") is not None:
                src = _resolve_reroutes(node_by_id, links, links.get(inp["link"], (None, 0)))
                if src[0] is None:
                    issues.append(f"node {node['id']}: dangling link on '{inp.get('name')}'")
                    continue
                inputs[inp["name"]] = [str(src[0]), src[1]]
                connected.add(inp["name"])

        if class_missing := node_type not in object_info:
            issues.append(f"node {node['id']}: unknown class '{node_type}' on this server")
        widget_names = [] if class_missing else _widget_input_names(node_type, object_info)
        values = list(node.get("widgets_values") or [])
        vi = 0
        for name in widget_names:
            if name in connected:
                continue
            if vi >= len(values):
                break
            inputs[name] = values[vi]
            vi += 1
            if (
                name in SEED_INPUTS
                and vi < len(values)
                and values[vi] in ("fixed", "increment", "decrement", "randomize")
            ):
                vi += 1  # control_after_generate ghost widget

        graph[str(node["id"])] = {"class_type": node_type, "inputs": inputs}

    result = ConversionResult()
    result["graph"] = graph
    result["issues"] = issues
    return result
