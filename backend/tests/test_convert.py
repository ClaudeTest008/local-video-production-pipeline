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


# VHS_VideoCombine serializes widgets_values as a name-keyed DICT and interleaves
# format-dependent (pix_fmt/crf/...) and a non-serialized videopreview widget
# among the declared inputs. Its declared widget inputs, in order.
VHS_OBJECT_INFO = {
    "VHS_VideoCombine": {
        "input": {
            "required": {
                "images": ["IMAGE"],
                "frame_rate": ["FLOAT", {"default": 8}],
                "loop_count": ["INT", {"default": 0}],
                "filename_prefix": ["STRING", {"default": "AnimateDiff"}],
                "format": [["image/gif", "video/h264-mp4", "video/webm"]],
                "pingpong": ["BOOLEAN", {"default": False}],
                "save_output": ["BOOLEAN", {"default": True}],
            },
            "optional": {"audio": ["AUDIO"], "vae": ["VAE"]},
        }
    }
}


def test_vhs_videocombine_dict_widgets_values_map_by_name():
    """Regression: dict-shaped widgets_values must be assigned by widget name.
    list(dict) yields the KEYS, which positionally shifted every widget by one
    (loop_count<-'frame_rate', format<-'filename_prefix', ...) and silently
    corrupted VHS_VideoCombine params."""
    ui = {
        "nodes": [
            {
                "id": 5905,
                "type": "VHS_VideoCombine",
                "inputs": [
                    {"name": "images", "type": "IMAGE", "link": 1},
                    {"name": "audio", "type": "AUDIO", "link": None},
                    {"name": "vae", "type": "VAE", "link": None},
                    {"name": "frame_rate", "type": "FLOAT", "link": 2},  # driven by a link
                ],
                "widgets_values": {
                    "frame_rate": 25,
                    "loop_count": 0,
                    "filename_prefix": "ltx2.3\\i2v",
                    "format": "video/h264-mp4",
                    "pix_fmt": "yuv420p",
                    "crf": 19,
                    "save_metadata": True,
                    "trim_to_audio": False,
                    "pingpong": False,
                    "save_output": True,
                    "videopreview": {"hidden": False, "params": {}},
                },
            },
            {
                "id": 1,
                "type": "EmptyLatentImage",
                "inputs": [],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [1]},
                    {"name": "FLOAT", "type": "FLOAT", "links": [2]},
                ],
                "widgets_values": [8, 8, 1],
            },
        ],
        "links": [[1, 1, 0, 5905, 0, "IMAGE"], [2, 1, 1, 5905, 3, "FLOAT"]],
    }
    inputs = ui_to_api(ui, VHS_OBJECT_INFO)["graph"]["5905"]["inputs"]
    assert inputs["loop_count"] == 0
    assert inputs["filename_prefix"] == "ltx2.3\\i2v"
    assert inputs["format"] == "video/h264-mp4"
    assert inputs["pingpong"] is False
    assert inputs["save_output"] is True
    # connected widget stays a link, never a positional value
    assert inputs["frame_rate"] == ["1", 1]
    # non-declared / preview keys never leak in as widget inputs
    assert "videopreview" not in inputs
    assert "pix_fmt" not in inputs


def test_legacy_primitivenode_inlined_as_widget_value():
    """Generic PrimitiveNode is frontend-only (no execution class): its literal
    must be inlined into each consumer's widget input and the node dropped, else
    /prompt rejects the graph with "Node 'PrimitiveNode' not found". Fans out to
    two consumers here."""
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "PrimitiveNode",
                "inputs": [],
                "outputs": [{"name": "INT", "type": "INT", "links": [10, 11]}],
                "widgets_values": [42, "fixed"],
            },
            {
                "id": 2,
                "type": "EmptyLatentImage",
                "inputs": [{"name": "width", "type": "INT", "link": 10}],
                "outputs": [],
                "widgets_values": [512, 1],  # height, batch (width driven by primitive)
            },
            {
                "id": 3,
                "type": "EmptyLatentImage",
                "inputs": [{"name": "width", "type": "INT", "link": 11}],
                "outputs": [],
                "widgets_values": [768, 1],
            },
        ],
        "links": [
            [10, 1, 0, 2, 0, "INT"],
            [11, 1, 0, 3, 0, "INT"],
        ],
    }
    result = ui_to_api(ui, object_info={})
    graph = result["graph"]
    assert "PrimitiveNode" not in {n["class_type"] for n in graph.values()}
    assert "1" not in graph  # the primitive node itself is dropped
    # literal inlined as a value (not a [node, slot] link) on both consumers
    assert graph["2"]["inputs"]["width"] == 42
    assert graph["3"]["inputs"]["width"] == 42
    assert not any("dangling link" in i for i in result["issues"])


def test_combo_widget_populated_from_widgets_values():
    """Regression: a V3 "COMBO" input (definition ["COMBO", {options:[...]}]) is a
    single-value selector widget. It was not recognized as a widget kind, so
    SaveVideo's required format/codec never got populated and ComfyUI silently
    pruned the whole video output branch as an invalid output node."""
    oi = {
        "SaveVideo": {
            "input": {
                "required": {
                    "video": ["VIDEO"],
                    "filename_prefix": ["STRING", {"default": "video/ComfyUI"}],
                    "format": ["COMBO", {"options": ["auto", "mp4"]}],
                    "codec": ["COMBO", {"options": ["auto", "h264"]}],
                }
            }
        }
    }
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "SaveVideo",
                "inputs": [{"name": "video", "type": "VIDEO", "link": 5}],
                "widgets_values": ["video/ComfyUI", "auto", "auto"],
            },
            {
                "id": 2,
                "type": "CreateVideo",
                "inputs": [],
                "outputs": [{"name": "VIDEO", "type": "VIDEO", "links": [5]}],
            },
        ],
        "links": [[5, 2, 0, 1, 4, "VIDEO"]],
    }
    inputs = ui_to_api(ui, oi)["graph"]["1"]["inputs"]
    assert inputs["filename_prefix"] == "video/ComfyUI"
    assert inputs["format"] == "auto"
    assert inputs["codec"] == "auto"


def test_linked_widget_slot_retained_keeps_later_widgets_aligned():
    """Regression: modern ComfyUI keeps a value slot in widgets_values even for a
    widget whose input is driven by a link. Skipping that slot instead of
    consuming it desynced every later widget — e.g. PromptRelayEncode read its
    FLOAT 'epsilon' from a neighbour's empty string and ComfyUI rejected the node
    ('could not convert string to float: ''), pruning the video branch."""
    oi = {
        "PromptRelayEncode": {
            "input": {
                "required": {
                    "clip": ["CLIP"],
                    "global_prompt": ["STRING", {"multiline": True}],
                    "local_prompts": ["STRING", {"multiline": True}],
                    "epsilon": ["FLOAT", {"default": 0.001}],
                }
            }
        }
    }
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "PromptRelayEncode",
                # global_prompt is linked, yet its slot ('' placeholder) is still
                # present in widgets_values ahead of local_prompts and epsilon.
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 7},
                    {"name": "global_prompt", "type": "STRING", "link": 8},
                ],
                "widgets_values": ["", "two chefs talking", 0.001],
            },
            {
                "id": 2,
                "type": "CLIPLoader",
                "inputs": [],
                "outputs": [
                    {"name": "CLIP", "type": "CLIP", "links": [7]},
                    {"name": "STRING", "type": "STRING", "links": [8]},
                ],
            },
        ],
        "links": [[7, 2, 0, 1, 0, "CLIP"], [8, 2, 1, 1, 1, "STRING"]],
    }
    inputs = ui_to_api(ui, oi)["graph"]["1"]["inputs"]
    assert inputs["global_prompt"] == ["2", 1]  # link wins, not the '' slot
    assert inputs["local_prompts"] == "two chefs talking"
    assert inputs["epsilon"] == 0.001  # not '' — slot stayed aligned


def test_flattened_bypassed_node_rewires_via_preserved_outputs():
    """Regression: flattening a subgraph dropped each inlined node's 'outputs',
    so _bypass_passthrough (which reads output slot types) could never rewire a
    bypassed node living inside a subgraph — its link was dropped as dangling,
    breaking the execution path to the output node."""
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "LoadImage",
                "inputs": [],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [100]}],
                "widgets_values": ["photo.png"],
            },
            {
                "id": 2,
                "type": "sub-uuid",
                "inputs": [{"name": "image", "type": "IMAGE", "link": 100}],
                "outputs": [{"name": "out", "type": "IMAGE", "links": [101]}],
            },
            {
                "id": 3,
                "type": "PreviewImage",
                "inputs": [{"name": "images", "type": "IMAGE", "link": 101}],
                "outputs": [],
            },
        ],
        "links": [[100, 1, 0, 2, 0, "IMAGE"], [101, 2, 0, 3, 0, "IMAGE"]],
        "definitions": {
            "subgraphs": [
                {
                    "id": "sub-uuid",
                    "inputs": [{"name": "image", "type": "IMAGE"}],
                    "outputs": [{"name": "out", "type": "IMAGE"}],
                    "nodes": [
                        {
                            "id": 10,
                            "type": "ImageScale",  # bypassed: IMAGE in -> IMAGE out
                            "mode": 4,
                            "inputs": [{"name": "image", "type": "IMAGE", "link": 200}],
                            "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [201]}],
                            "widgets_values": ["nearest", 512, 512],
                        }
                    ],
                    "links": [
                        [200, -10, 0, 10, 0, "IMAGE"],
                        [201, 10, 0, -20, 0, "IMAGE"],
                    ],
                }
            ]
        },
    }
    result = ui_to_api(ui, object_info={})
    graph = result["graph"]
    by_type = {n["class_type"]: (nid, n) for nid, n in graph.items()}
    assert "ImageScale" not in by_type  # bypassed, never executes
    load_id, _ = by_type["LoadImage"]
    _, preview = by_type["PreviewImage"]
    # bypassed ImageScale rewired straight through to LoadImage, not dropped
    assert preview["inputs"]["images"] == [load_id, 0]
    assert not any("dangling link" in i for i in result["issues"])


def test_model_paths_normalized_to_server_options():
    # workflow references models with author-machine subfolders/separators; the
    # server lists them differently — exact-string validation would fail even
    # though the files are installed. Unique-basename match must substitute.
    oi = {
        "UnetLoaderGGUF": {
            "input": {
                "required": {
                    "unet_name": ["COMBO", {"options": ["LTX-2.3-distilled-Q4_K_S.gguf"]}]
                }
            }
        }
    }
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "UnetLoaderGGUF",
                "inputs": [],
                "widgets_values": ["LTXvideo/LTX-2/quantstack/LTX-2.3-distilled-Q4_K_S.gguf"],
            }
        ],
        "links": [],
    }
    result = ui_to_api(ui, oi)
    assert result["graph"]["1"]["inputs"]["unet_name"] == "LTX-2.3-distilled-Q4_K_S.gguf"
    assert any("normalized" in i for i in result["issues"])


def test_model_paths_not_normalized_when_basename_differs():
    # a genuinely different file (x1.5 vs x2 upscaler) must NOT be swapped
    oi = {
        "LatentUpscaleModelLoader": {
            "input": {
                "required": {
                    "model_name": [
                        "COMBO",
                        {"options": ["ltx-2.3-spatial-upscaler-x2-1.1.safetensors"]},
                    ]
                }
            }
        }
    }
    ui = {
        "nodes": [
            {
                "id": 1,
                "type": "LatentUpscaleModelLoader",
                "inputs": [],
                "widgets_values": ["ltx-2.3-spatial-upscaler-x1.5-1.0.safetensors"],
            }
        ],
        "links": [],
    }
    result = ui_to_api(ui, oi)
    # left untouched -> dependency detection reports it missing
    assert (
        result["graph"]["1"]["inputs"]["model_name"]
        == "ltx-2.3-spatial-upscaler-x1.5-1.0.safetensors"
    )
    assert not any("normalized" in i for i in result["issues"])
