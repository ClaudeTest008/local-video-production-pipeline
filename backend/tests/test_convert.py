"""ui_to_api conversion: subgraph flattening + UI-only node stripping."""

from app.modules.comfyui.convert import ui_to_api

# Top graph: EmptyLatentImage(1) -> subgraph instance(2) -> VAEDecode(3),
# plus a UI-only Fast Groups Bypasser(4). The subgraph wraps a single KSampler,
# fed by the subgraph's input slot and feeding its output slot.
SUBGRAPH_UI = {
    "nodes": [
        {
            "id": 1,
            "type": "EmptyLatentImage",
            "inputs": [],
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [100]}],
            "widgets_values": [512, 512, 1],
        },
        {
            "id": 2,
            "type": "ec0a4d64-82cd-432f-ae9e-4bfac0337f07",  # subgraph instance
            "inputs": [{"name": "latent", "type": "LATENT", "link": 100}],
            "outputs": [{"name": "out", "type": "LATENT", "links": [101]}],
        },
        {
            "id": 3,
            "type": "VAEDecode",
            "inputs": [{"name": "samples", "type": "LATENT", "link": 101}],
            "outputs": [],
        },
        {"id": 4, "type": "Fast Groups Bypasser (rgthree)", "inputs": [], "outputs": []},
    ],
    "links": [
        [100, 1, 0, 2, 0, "LATENT"],
        [101, 2, 0, 3, 0, "LATENT"],
    ],
    "definitions": {
        "subgraphs": [
            {
                "id": "ec0a4d64-82cd-432f-ae9e-4bfac0337f07",
                "name": "Sampler",
                "inputs": [{"name": "latent", "type": "LATENT"}],
                "outputs": [{"name": "out", "type": "LATENT"}],
                "nodes": [
                    {
                        "id": 10,
                        "type": "KSampler",
                        "inputs": [{"name": "latent_image", "type": "LATENT", "link": 200}],
                        "outputs": [{"name": "LATENT", "type": "LATENT", "links": [201]}],
                        "widgets_values": [123, 20, 8.0],
                    }
                ],
                "links": [
                    [200, -10, 0, 10, 0, "LATENT"],  # subgraph input -> KSampler
                    [201, 10, 0, -20, 0, "LATENT"],  # KSampler -> subgraph output
                ],
            }
        ]
    },
}


def test_flatten_subgraph_and_strip_ui_nodes():
    graph = ui_to_api(SUBGRAPH_UI, object_info={})["graph"]
    by_type = {n["class_type"]: (nid, n) for nid, n in graph.items()}

    # subgraph UUID and UI-only helper never reach the API graph
    class_types = {n["class_type"] for n in graph.values()}
    assert "ec0a4d64-82cd-432f-ae9e-4bfac0337f07" not in class_types
    assert "Fast Groups Bypasser (rgthree)" not in class_types

    # interior node surfaced, boundary links rewired to the real producers
    assert set(class_types) == {"EmptyLatentImage", "KSampler", "VAEDecode"}
    latent_id, _ = by_type["EmptyLatentImage"]
    ksampler_id, ksampler = by_type["KSampler"]
    _, vaedecode = by_type["VAEDecode"]
    assert ksampler["inputs"]["latent_image"] == [latent_id, 0]  # input boundary
    assert vaedecode["inputs"]["samples"] == [ksampler_id, 0]  # output boundary


def test_plain_graph_unchanged():
    ui = {
        "nodes": [
            {"id": 1, "type": "EmptyLatentImage", "inputs": [], "widgets_values": [8, 8, 1]}
        ],
        "links": [],
    }
    graph = ui_to_api(ui, object_info={})["graph"]
    assert graph == {"1": {"class_type": "EmptyLatentImage", "inputs": {}}}
