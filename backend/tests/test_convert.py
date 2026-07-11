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


def test_subgraph_dict_shaped_links_resolve():
    # Some ComfyUI versions serialize subgraph-definition links as dicts
    # ({"id","origin_id","origin_slot","target_id","target_slot","type"})
    # instead of the legacy [id, origin_id, origin_slot, target_id,
    # target_slot, type] list the top-level graph and older exports use.
    ui = {
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
                "type": "ec0a4d64-82cd-432f-ae9e-4bfac0337f07",
                "inputs": [{"name": "latent", "type": "LATENT", "link": 100}],
                "outputs": [{"name": "out", "type": "LATENT", "links": [101]}],
            },
            {
                "id": 3,
                "type": "VAEDecode",
                "inputs": [{"name": "samples", "type": "LATENT", "link": 101}],
                "outputs": [],
            },
        ],
        "links": [
            [100, 1, 0, 2, 0, "LATENT"],
            [101, 2, 0, 3, 0, "LATENT"],
        ],
        "definitions": {
            "subgraphs": [
                {
                    "id": "ec0a4d64-82cd-432f-ae9e-4bfac0337f07",
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
                        {
                            "id": 200,
                            "origin_id": -10,
                            "origin_slot": 0,
                            "target_id": 10,
                            "target_slot": 0,
                            "type": "LATENT",
                        },
                        {
                            "id": 201,
                            "origin_id": 10,
                            "origin_slot": 0,
                            "target_id": -20,
                            "target_slot": 0,
                            "type": "LATENT",
                        },
                    ],
                }
            ]
        },
    }
    graph = ui_to_api(ui, object_info={})["graph"]
    by_type = {n["class_type"]: (nid, n) for nid, n in graph.items()}
    latent_id, _ = by_type["EmptyLatentImage"]
    ksampler_id, ksampler = by_type["KSampler"]
    _, vaedecode = by_type["VAEDecode"]
    assert ksampler["inputs"]["latent_image"] == [latent_id, 0]
    assert vaedecode["inputs"]["samples"] == [ksampler_id, 0]


def test_setnode_getnode_resolve_to_real_producer():
    # CheckpointLoader --Set("model")--> ... --Get("model")--> KSampler
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "inputs": [],
                "outputs": [{"name": "MODEL", "type": "MODEL", "links": [10]}],
                "widgets_values": ["ckpt.safetensors"],
            },
            {
                "id": 2,
                "type": "SetNode",
                "title": "Set_model",
                "inputs": [{"name": "MODEL", "type": "MODEL", "link": 10}],
                "outputs": [{"name": "MODEL", "type": "MODEL", "links": []}],
                "widgets_values": ["model"],
            },
            {
                "id": 3,
                "type": "GetNode",
                "title": "Get_model",
                "inputs": [],
                "outputs": [{"name": "MODEL", "type": "MODEL", "links": [20]}],
                "widgets_values": ["model"],
            },
            {
                "id": 4,
                "type": "KSampler",
                "inputs": [{"name": "model", "type": "MODEL", "link": 20}],
                "outputs": [],
                "widgets_values": [123, 20, 8.0],
            },
        ],
        "links": [
            [10, 1, 0, 2, 0, "MODEL"],
            [20, 3, 0, 4, 0, "MODEL"],
        ],
    }
    graph = ui_to_api(ui, object_info={})["graph"]
    class_types = {n["class_type"] for n in graph.values()}
    assert "SetNode" not in class_types
    assert "GetNode" not in class_types
    assert graph["4"]["inputs"]["model"] == ["1", 0]  # Get resolved straight to the Checkpoint


def test_getnode_without_matching_setnode_reports_dangling():
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "GetNode",
                "title": "Get_missing",
                "inputs": [],
                "outputs": [{"name": "MODEL", "type": "MODEL", "links": [10]}],
                "widgets_values": ["missing"],
            },
            {
                "id": 2,
                "type": "KSampler",
                "inputs": [{"name": "model", "type": "MODEL", "link": 10}],
                "outputs": [],
                "widgets_values": [123, 20, 8.0],
            },
        ],
        "links": [[10, 1, 0, 2, 0, "MODEL"]],
    }
    result = ui_to_api(ui, object_info={})
    assert "model" not in result["graph"]["2"]["inputs"]
    assert any("dangling link" in issue for issue in result["issues"])


def test_bypassed_node_rewires_matching_type_passthrough():
    # LoadImage --IMAGE--> [bypassed ImageScale: IMAGE in/out, MASK in/out] --IMAGE--> PreviewImage
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "LoadImage",
                "inputs": [],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [10]}],
                "widgets_values": ["photo.png"],
            },
            {
                "id": 2,
                "type": "ImageScale",
                "mode": 4,
                "inputs": [
                    {"name": "image", "type": "IMAGE", "link": 10},
                    {"name": "mask", "type": "MASK", "link": None},
                ],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [11]},
                    {"name": "MASK", "type": "MASK", "links": []},
                ],
                "widgets_values": ["nearest", 512, 512],
            },
            {
                "id": 3,
                "type": "PreviewImage",
                "inputs": [{"name": "images", "type": "IMAGE", "link": 11}],
                "outputs": [],
            },
        ],
        "links": [
            [10, 1, 0, 2, 0, "IMAGE"],
            [11, 2, 0, 3, 0, "IMAGE"],
        ],
    }
    graph = ui_to_api(ui, object_info={})["graph"]
    class_types = {n["class_type"] for n in graph.values()}
    assert "ImageScale" not in class_types  # bypassed node never executes
    assert graph["3"]["inputs"]["images"] == ["1", 0]  # rewired straight to LoadImage


def test_bypassed_node_no_matching_type_reports_dangling():
    # bypassed node's only input is IMAGE but the consumed output is MASK — no passthrough
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "LoadImage",
                "inputs": [],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [10]}],
                "widgets_values": ["photo.png"],
            },
            {
                "id": 2,
                "type": "SomeMaskGenerator",
                "mode": 4,
                "inputs": [{"name": "image", "type": "IMAGE", "link": 10}],
                "outputs": [{"name": "MASK", "type": "MASK", "links": [11]}],
            },
            {
                "id": 3,
                "type": "PreviewMask",
                "inputs": [{"name": "mask", "type": "MASK", "link": 11}],
                "outputs": [],
            },
        ],
        "links": [
            [10, 1, 0, 2, 0, "IMAGE"],
            [11, 2, 0, 3, 0, "MASK"],
        ],
    }
    result = ui_to_api(ui, object_info={})
    assert "mask" not in result["graph"]["3"]["inputs"]
    assert any("dangling link" in issue for issue in result["issues"])


def test_muted_node_output_reports_dangling():
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "LoadImage",
                "mode": 2,
                "inputs": [],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [10]}],
                "widgets_values": ["photo.png"],
            },
            {
                "id": 2,
                "type": "PreviewImage",
                "inputs": [{"name": "images", "type": "IMAGE", "link": 10}],
                "outputs": [],
            },
        ],
        "links": [[10, 1, 0, 2, 0, "IMAGE"]],
    }
    result = ui_to_api(ui, object_info={})
    assert "1" not in result["graph"]
    assert "images" not in result["graph"]["2"]["inputs"]
    assert any("dangling link" in issue for issue in result["issues"])


LTXV_OBJECT_INFO = {
    "LTXVImgToVideoInplaceKJ": {
        "input": {
            "required": {
                "num_images": [
                    "COMFY_DYNAMICCOMBO_V3",
                    {
                        "options": [
                            {
                                "key": "1",
                                "inputs": {
                                    "required": {"strength_1": ["FLOAT", {"default": 1.0}]},
                                    "optional": {
                                        "image_1": ["IMAGE", {}],
                                        "index_1": ["INT", {"default": 0}],
                                    },
                                },
                            },
                            {
                                "key": "2",
                                "inputs": {
                                    "required": {
                                        "strength_1": ["FLOAT", {"default": 1.0}],
                                        "strength_2": ["FLOAT", {"default": 1.0}],
                                    },
                                    "optional": {
                                        "image_1": ["IMAGE", {}],
                                        "index_1": ["INT", {"default": 0}],
                                        "image_2": ["IMAGE", {}],
                                        "index_2": ["INT", {"default": 0}],
                                    },
                                },
                            },
                        ]
                    },
                ]
            },
            "optional": {},
        }
    }
}


def test_dynamic_combo_expands_selected_option_num_images_1():
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "LTXVImgToVideoInplaceKJ",
                "inputs": [],
                "outputs": [],
                # num_images=1, strength_1, index_1 (image_1 left unconnected)
                "widgets_values": ["1", 0.75, 3],
            }
        ],
        "links": [],
    }
    graph = ui_to_api(ui, object_info=LTXV_OBJECT_INFO)["graph"]
    assert graph["1"]["inputs"] == {
        "num_images": "1",
        "num_images.strength_1": 0.75,
        "num_images.index_1": 3,
    }


def test_dynamic_combo_expands_selected_option_num_images_2():
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "LTXVImgToVideoInplaceKJ",
                "inputs": [],
                "outputs": [],
                # num_images=2, strength_1, strength_2, index_1, index_2
                "widgets_values": ["2", 0.5, 0.9, 1, 2],
            }
        ],
        "links": [],
    }
    graph = ui_to_api(ui, object_info=LTXV_OBJECT_INFO)["graph"]
    assert graph["1"]["inputs"] == {
        "num_images": "2",
        "num_images.strength_1": 0.5,
        "num_images.strength_2": 0.9,
        "num_images.index_1": 1,
        "num_images.index_2": 2,
    }


def test_dynamic_combo_sub_input_connected_via_link_not_consumed_positionally():
    # image_1 is wired to a real link (a socket, not a widget) — its value
    # slot never appears in widgets_values at all, matching ComfyUI's own
    # "converted to input" behavior. index_1 still consumes positionally.
    # ComfyUI's V3 UI names the socket "num_images.image_1" (combo-scoped),
    # and execution expects that qualified name verbatim as the kwarg key.
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "LoadImage",
                "inputs": [],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [50]}],
                "widgets_values": ["photo.png"],
            },
            {
                "id": 2,
                "type": "LTXVImgToVideoInplaceKJ",
                "inputs": [{"name": "num_images.image_1", "type": "IMAGE", "link": 50}],
                "outputs": [],
                "widgets_values": ["1", 0.75, 3],
            },
        ],
        "links": [[50, 1, 0, 2, 0, "IMAGE"]],
    }
    graph = ui_to_api(ui, object_info=LTXV_OBJECT_INFO)["graph"]
    assert graph["2"]["inputs"] == {
        "num_images": "1",
        "num_images.image_1": ["1", 0],
        "num_images.strength_1": 0.75,
        "num_images.index_1": 3,
    }


def test_dynamic_combo_unknown_option_reports_issue():
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "LTXVImgToVideoInplaceKJ",
                "inputs": [],
                "outputs": [],
                "widgets_values": ["3"],
            }
        ],
        "links": [],
    }
    result = ui_to_api(ui, object_info=LTXV_OBJECT_INFO)
    assert result["graph"]["1"]["inputs"] == {"num_images": "3"}
    assert any("unknown option" in issue for issue in result["issues"])


def test_plain_graph_unchanged():
    ui = {
        "nodes": [
            {"id": 1, "type": "EmptyLatentImage", "inputs": [], "widgets_values": [8, 8, 1]}
        ],
        "links": [],
    }
    graph = ui_to_api(ui, object_info={})["graph"]
    assert graph == {"1": {"class_type": "EmptyLatentImage", "inputs": {}}}
