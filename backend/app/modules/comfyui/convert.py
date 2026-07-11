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

# UI node types that never reach the API graph: annotations + rgthree helper
# widgets that only drive the editor (bypass/mute groups, buttons, labels).
SKIP_TYPES = {
    "Note",
    "MarkdownNote",
    "Fast Groups Bypasser (rgthree)",
    "Fast Groups Muter (rgthree)",
    "Fast Actions Button (rgthree)",
    "Label (rgthree)",
}
# widget appended automatically after seed-like inputs in the UI
SEED_INPUTS = {"seed", "noise_seed"}
PRIMITIVE_TYPES = {"INT", "FLOAT", "STRING", "BOOLEAN"}
# litegraph virtual boundary nodes inside every subgraph definition
SUBGRAPH_INPUT_ID = -10
SUBGRAPH_OUTPUT_ID = -20


def _link_id(link) -> int | None:
    """Top-level graphs serialize links as [id, origin_id, origin_slot,
    target_id, target_slot, type]; subgraph definitions serialize them as
    {"id", "origin_id", "origin_slot", "target_id", "target_slot", "type"}
    dicts. Both shapes occur in the same file — normalize both."""
    if isinstance(link, list) and link:
        return link[0]
    if isinstance(link, dict):
        return link.get("id")
    return None


def _link_fields(link) -> tuple[int, int, int, int] | None:
    """(origin_id, origin_slot, target_id, target_slot), either link shape."""
    if isinstance(link, list) and len(link) >= 5:
        return link[1], link[2], link[3], link[4]
    if isinstance(link, dict):
        try:
            return link["origin_id"], link["origin_slot"], link["target_id"], link["target_slot"]
        except KeyError:
            return None
    return None


def _flatten_subgraphs(ui: dict, issues: list[str]) -> dict:
    """Inline ComfyUI subgraph instances into their constituent nodes.

    A subgraph instance node carries the subgraph definition's UUID as its
    ``type``; the interior lives in ``definitions.subgraphs``. ComfyUI's
    /prompt has no concept of subgraphs, so we splice the interior into the
    top level and rewire boundary links: interior links from the virtual input
    node (-10) resolve to whatever fed the instance's matching input slot, and
    the instance's output slots resolve to the interior producer feeding the
    virtual output node (-20). Handles nesting via recursion. All inlined ids
    are renumbered above every existing id so they never collide.
    """
    subdefs = {
        sd["id"]: sd
        for sd in (ui.get("definitions") or {}).get("subgraphs") or []
        if isinstance(sd, dict) and "id" in sd
    }
    if not subdefs:
        return ui

    max_node = max_link = 0
    node_lists = [ui.get("nodes")] + [sd.get("nodes") for sd in subdefs.values()]
    link_lists = [ui.get("links")] + [sd.get("links") for sd in subdefs.values()]
    for ns in node_lists:
        for n in ns or []:
            try:
                max_node = max(max_node, int(n.get("id", 0)))
            except (TypeError, ValueError):
                pass
    for ls in link_lists:
        for link in ls or []:
            lid = _link_id(link)
            if lid is not None:
                try:
                    max_link = max(max_link, int(lid))
                except (TypeError, ValueError):
                    pass
    counter = {"node": max_node + 1, "link": max_link + 1}

    def fresh(key: str) -> int:
        counter[key] += 1
        return counter[key] - 1

    out_nodes: list[dict] = []
    out_links: list[list] = []

    def flatten_level(nodes: list, links: list, input_binding: dict) -> dict:
        """Emit this level's real nodes; return {output_slot: producer} so a
        parent can resolve links to this subgraph's outputs."""
        link_by_id: dict[int, tuple[int, int, int, int]] = {}
        for link in links or []:
            lid, fields = _link_id(link), _link_fields(link)
            if lid is not None and fields is not None:
                link_by_id[lid] = fields
        real_final: dict = {}
        real_node: dict = {}
        instances: dict = {}
        for n in nodes or []:
            if n.get("type") in subdefs:
                instances[n["id"]] = n
            else:
                real_final[n["id"]] = fresh("node")
                real_node[n["id"]] = n

        inlined: dict = {}
        in_progress: set = set()

        def resolve(origin_id, origin_slot):
            """(final_node_id, slot) that produces this pin, or None."""
            if origin_id == SUBGRAPH_INPUT_ID:
                return input_binding.get(origin_slot)
            if origin_id in instances:
                return inline(origin_id).get(origin_slot)
            if origin_id in real_final:
                return (real_final[origin_id], origin_slot)
            return None

        def resolve_link(link_id):
            fields = link_by_id.get(link_id)
            return resolve(fields[0], fields[1]) if fields else None

        def inline(inst_id: int) -> dict:
            if inst_id in inlined:
                return inlined[inst_id]
            if inst_id in in_progress:  # cycle guard (graphs are DAGs)
                return {}
            in_progress.add(inst_id)
            inst = instances[inst_id]
            if inst.get("mode") == 2:
                issues.append(f"subgraph instance {inst_id} is muted; dropped")
                inlined[inst_id] = {}
                in_progress.discard(inst_id)
                return {}
            if inst.get("mode") == 4:
                issues.append(f"subgraph instance {inst_id} is bypassed; inlined as-is")
            if inst.get("widgets_values"):
                # ponytail: promoted widgets stay at subgraph defaults; overrides on
                # the instance aren't reapplied. Surface it, upgrade if it bites.
                issues.append(
                    f"subgraph instance {inst_id}: promoted widget values not applied "
                    "(using subgraph defaults)"
                )
            binding = {
                idx: (resolve_link(inp["link"]) if inp.get("link") is not None else None)
                for idx, inp in enumerate(inst.get("inputs") or [])
            }
            sd = subdefs[inst["type"]]
            capture = flatten_level(sd.get("nodes"), sd.get("links"), binding)
            inlined[inst_id] = capture
            in_progress.discard(inst_id)
            return capture

        for old_id, n in real_node.items():
            fid = real_final[old_id]
            new_inputs = []
            for slot, inp in enumerate(n.get("inputs") or []):
                producer = resolve_link(inp["link"]) if inp.get("link") is not None else None
                link_id = None
                if producer is not None:
                    link_id = fresh("link")
                    out_links.append(
                        [link_id, producer[0], producer[1], fid, slot, inp.get("type")]
                    )
                new_inputs.append(
                    {"name": inp.get("name"), "type": inp.get("type"), "link": link_id}
                )
            node_copy = {
                "id": fid,
                "type": n.get("type"),
                "inputs": new_inputs,
                "widgets_values": n.get("widgets_values"),
            }
            if "mode" in n:
                node_copy["mode"] = n["mode"]
            out_nodes.append(node_copy)

        boundary: dict = {}
        for link in links or []:
            fields = _link_fields(link)
            if fields is not None and fields[2] == SUBGRAPH_OUTPUT_ID:
                boundary[fields[3]] = resolve(fields[0], fields[1])
        return boundary

    flatten_level(ui.get("nodes"), ui.get("links"), {})
    flat = dict(ui)
    flat["nodes"] = out_nodes
    flat["links"] = out_links
    flat.pop("definitions", None)
    return flat


class ConversionResult(dict):
    """api graph in ["graph"], issues in ["issues"] (empty = clean)."""


def _link_map(ui: dict) -> dict[int, tuple[int, int]]:
    """link_id -> (source_node_id, source_slot)."""
    return {
        link[0]: (link[1], link[2])
        for link in ui.get("links", [])
        if isinstance(link, list) and len(link) >= 5
    }


def _set_node_map(nodes: list) -> dict[str, dict]:
    """SetNode (KJNodes) variable name -> the node itself, for GetNode resolution."""
    return {
        (n.get("widgets_values") or [None])[0]: n
        for n in nodes
        if n.get("type") == "SetNode" and n.get("widgets_values")
    }


def _bypass_passthrough(node: dict, slot: int) -> int | None:
    """ComfyUI's own bypass rewiring: a mode=4 node never executes — each
    output is instead whatever same-typed input feeds it (same-slot preferred,
    else the first input of matching type). Returns the link id to continue
    resolving from, or None if the output has no matching passthrough (the
    link is dropped, same as a real ComfyUI bypass with no compatible input)."""
    outputs = node.get("outputs") or []
    if slot >= len(outputs):
        return None
    out_type = outputs[slot].get("type")
    inputs = node.get("inputs") or []
    match = None
    if slot < len(inputs) and inputs[slot].get("type") == out_type:
        match = inputs[slot]
    if match is None:
        match = next((i for i in inputs if i.get("type") == out_type), None)
    return match.get("link") if match else None


def _resolve_reroutes(
    node_by_id: dict, links: dict, src: tuple[int, int], set_by_name: dict | None = None
) -> tuple[int | None, int]:
    """Follow Reroute chains, KJNodes Set/Get variable passthroughs, and
    bypassed (mode=4) nodes to the real producer. Get<name> resolves to
    whatever feeds the matching Set<name>; a muted (mode=2) node or a bypassed
    node with no type-matched input passthrough resolves to (None, 0) —
    nothing feeds the consumer, same as ComfyUI's own bypass/mute semantics."""
    set_by_name = set_by_name or {}
    for _ in range(50):
        node = node_by_id.get(src[0])
        if node is None:
            return src
        node_type = node.get("type")
        mode = node.get("mode")
        if node_type in ("Reroute", "RerouteNode", "SetNode"):
            in_links = [
                i.get("link") for i in node.get("inputs", []) if i.get("link") is not None
            ]
            if not in_links:
                return src
            src = links.get(in_links[0], src)
        elif node_type == "GetNode":
            name = (node.get("widgets_values") or [None])[0]
            setter = set_by_name.get(name)
            if setter is None:
                return src
            in_links = [
                i.get("link") for i in setter.get("inputs", []) if i.get("link") is not None
            ]
            if not in_links:
                return src
            src = links.get(in_links[0], src)
        elif mode == 2:
            return (None, 0)
        elif mode == 4:
            link_id = _bypass_passthrough(node, src[1])
            if link_id is None:
                return (None, 0)
            src = links.get(link_id, (None, 0))
        else:
            return src
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
    ui = _flatten_subgraphs(ui, issues)
    nodes = ui.get("nodes", [])
    node_by_id = {n["id"]: n for n in nodes}
    links = _link_map(ui)
    set_by_name = _set_node_map(nodes)
    graph: dict[str, dict] = {}

    for node in nodes:
        node_type = node.get("type", "")
        if node_type in SKIP_TYPES or node_type.startswith("Reroute"):
            continue
        if node_type in ("SetNode", "GetNode"):
            continue
        if node.get("mode") == 2:  # muted — drop; consumers will report missing input
            issues.append(f"node {node['id']} ({node_type}) is muted; dropped")
            continue
        if node.get("mode") == 4:  # bypassed — never executes; consumers rewire around it
            issues.append(f"node {node['id']} ({node_type}) is bypassed; rewired around")
            continue

        inputs: dict = {}
        connected = set()
        for inp in node.get("inputs", []) or []:
            if inp.get("link") is not None:
                src = _resolve_reroutes(
                    node_by_id, links, links.get(inp["link"], (None, 0)), set_by_name
                )
                src_node = node_by_id.get(src[0]) if src[0] is not None else None
                unresolved = src_node is not None and (
                    src_node.get("type") in ("Reroute", "RerouteNode", "SetNode", "GetNode")
                    or src_node.get("mode") in (2, 4)
                )
                if src[0] is None or unresolved:
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
