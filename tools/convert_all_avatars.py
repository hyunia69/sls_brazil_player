"""Blender script: Convert all VLibras avatar FBX files to GLB with textures.

Usage:
    blender --background --python convert_all_avatars.py
"""
import bpy
import os

work_dir = os.path.dirname(os.path.abspath(__file__))

AVATARS = {
    "Guga": {
        "fbx": "Guga/GuGa.fbx",
        "glb": "Guga/Guga.glb",
        "tex_dir": "Guga",
        "tex_map": {
            "guga_pele_m":           "peleTex.png",
            "Guga_Cabelo_m":         "cabeloTex.png",
            "Guga_calca":            "calcaTex.png",
            "GugaCamisa_m":          "camisaTex.png",
            "GugaCamisaDetalhes_m":  "camisaTex.png",
            "GugaEstampa":           "camisaestampa.png",
            "GugaIris_m":            "olhoTex.png",
            "gugaOlhoBranco_m":      "olhoTex.png",
        },
    },
    "Hozana": {
        "fbx": "Hozana/Hozana2.0.fbx",
        "glb": "Hozana/Hozana.glb",
        "tex_dir": "Hozana",
        "tex_map": {
            "HozPele_m":               "H_PeleTex.png",
            "HozCabelo_m":             "HozcabeloTex.png",
            "calca_m":                 "CalcaTex.png",
            "HozCamisa_m":             "camisaTex.png",
            "HozEstampacentral_m":     "camisaestampa.png",
            "HozEstampapeito_m":       "camisaestampa.png",
            "HozIris_m":               "olhoTex.png",
            "HozOlhoB_m":             "olhoTex.png",
            "hoZacessorios_m":         "camisaTex.png",
            "HozAcessorios_detalhe":   "camisaTex.png",
        },
    },
    "Icaro": {
        "fbx": "Icaro_NovoEstilo.fbx",
        "glb": "Icaro/Icaro.glb",
        "tex_dir": "Icaro",
        "tex_map": {
            "IcaroPele_m":       "PeleTex.png",
            "IcaroCabelo_m":     "cabelo.png",
            "IcaroCalca_m":      "calca.png",
            "IcaroCamisa_m":     "Camisa.png",
            "IcaroEstampa_m":    "camisaestampa.png",
            "IcaroOlhos_m":      "olhoTex.png",
            "OlhosBranco_m":     "olhoTex.png",
        },
    },
}


def assign_texture(mat, tex_path):
    """Assign a texture image to material's Base Color input."""
    if not mat or not mat.use_nodes:
        return False

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = None
    for node in nodes:
        if node.type == "BSDF_PRINCIPLED":
            bsdf = node
            break
    if not bsdf:
        return False

    tex_node = nodes.new("ShaderNodeTexImage")
    tex_node.image = bpy.data.images.load(tex_path)
    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    return True


for avatar_name, config in AVATARS.items():
    print(f"\n{'='*60}")
    print(f"Converting: {avatar_name}")
    print(f"{'='*60}")

    bpy.ops.wm.read_factory_settings(use_empty=True)

    fbx_path = os.path.join(work_dir, config["fbx"])
    if not os.path.exists(fbx_path):
        print(f"ERROR: FBX not found: {fbx_path}")
        continue

    bpy.ops.import_scene.fbx(
        filepath=fbx_path,
        use_manual_orientation=True,
        axis_forward='-Z',
        axis_up='Y',
        use_anim=False,
        ignore_leaf_bones=False,
        force_connect_children=False,
        automatic_bone_orientation=False,
    )
    print(f"Imported: {fbx_path}")

    # Assign textures
    tex_dir = os.path.join(work_dir, config["tex_dir"])
    for mat_name, tex_file in config["tex_map"].items():
        mat = bpy.data.materials.get(mat_name)
        tex_path = os.path.join(tex_dir, tex_file)

        if not mat:
            print(f"  WARN: Material '{mat_name}' not found")
            continue
        if not os.path.exists(tex_path):
            print(f"  WARN: Texture '{tex_path}' not found")
            continue

        if assign_texture(mat, tex_path):
            print(f"  OK: {tex_file} -> {mat_name}")
        else:
            print(f"  FAIL: No BSDF node in {mat_name}")

    # Report unassigned materials
    assigned = set(config["tex_map"].keys())
    for mat in bpy.data.materials:
        if mat.name not in assigned:
            has_tex = False
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        has_tex = True
            status = "(has embedded tex)" if has_tex else "(no texture)"
            print(f"  INFO: Unassigned material '{mat.name}' {status}")

    # Export GLB
    glb_path = os.path.join(work_dir, config["glb"])
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        export_image_format="AUTO",
        export_yup=True,
    )
    file_size = os.path.getsize(glb_path) / (1024 * 1024)
    print(f"DONE: {glb_path} ({file_size:.1f} MB)")

print(f"\n{'='*60}")
print("All avatars converted!")
print(f"{'='*60}")
