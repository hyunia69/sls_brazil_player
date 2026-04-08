"""Blender script: Convert VLibras Icaro FBX to GLB with textures.

The FBX is from Unity (Y-up, left-handed). We need to preserve the
bone orientations exactly as Unity expects them, since the animation
data uses the same coordinate system.
"""
import bpy
import os

work_dir = os.path.dirname(os.path.abspath(__file__))

# Clear default scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import FBX with explicit Unity-compatible axis settings
fbx_path = os.path.join(work_dir, "Icaro_NovoEstilo.fbx")
bpy.ops.import_scene.fbx(
    filepath=fbx_path,
    use_manual_orientation=True,
    axis_forward='-Z',
    axis_up='Y',
    use_anim=False,         # No animation in avatar FBX
    ignore_leaf_bones=False,
    force_connect_children=False,
    automatic_bone_orientation=False,
)
print(f"Imported: {fbx_path}")

# Assign textures to materials
tex_map = {
    "IcaroPele_m": "PeleTex.png",
    "IcaroCabelo_m": "cabelo.png",
    "IcaroCalca_m": "calca.png",
    "IcaroCamisa_m": "Camisa.png",
    "IcaroEstampa_m": "camisaestampa.png",
    "IcaroOlhos_m": "olhoTex.png",
}

for mat_name, tex_file in tex_map.items():
    mat = bpy.data.materials.get(mat_name)
    if not mat or not mat.use_nodes:
        print(f"SKIP: {mat_name}")
        continue

    tex_path = os.path.join(work_dir, tex_file)
    if not os.path.exists(tex_path):
        print(f"MISSING: {tex_path}")
        continue

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = None
    for node in nodes:
        if node.type == "BSDF_PRINCIPLED":
            bsdf = node
            break

    if bsdf:
        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.image = bpy.data.images.load(tex_path)
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
        print(f"OK: {tex_file} -> {mat_name}")
    else:
        print(f"NO_BSDF: {mat_name}")

# Export GLB
glb_path = os.path.join(work_dir, "Icaro.glb")
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format="GLB",
    export_image_format="AUTO",
    export_yup=True,
)
print(f"DONE: {glb_path}")
