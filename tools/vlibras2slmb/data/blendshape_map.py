"""VLibras 22 blendshape to ABNT 68 blendshape mapping for face retargeting.

The ABNT NBR 25606 avatar uses 68 blendshapes on the head_GEO mesh (IDs 0-67).
VLibras animations contain 22 blendshape curves that must be retargeted to the
ABNT targets.  Some VLibras shapes map 1:1, others split across two ABNT
targets, and some are skipped (correction/test shapes).

Multiple ABNT meshes share blendshape deformations.  The MULTI_MESH_IDS table
maps a head_GEO blendshape index to all mesh-specific IDs that must receive
the same weight value in the FaceMotionBlock.
"""

from __future__ import annotations

from typing import Final


# ---------------------------------------------------------------------------
# ABNT blendshape names in head_GEO index order (0-67)
# ---------------------------------------------------------------------------

ABNT_BLENDSHAPE_NAMES: Final[list[str]] = [
    "EyeBlink_Left",       # 0
    "EyeBlink_Right",      # 1
    "EyeSquint_Left",      # 2
    "EyeSquint_Right",     # 3
    "EyeDown_Left",        # 4
    "EyeDown_Right",       # 5
    "EyeIn_Left",          # 6
    "EyeIn_Right",         # 7
    "EyeOpen_Left",        # 8
    "EyeOpen_Right",       # 9
    "EyeOut_Left",         # 10
    "EyeOut_Right",        # 11
    "EyeUp_Left",          # 12
    "EyeUp_Right",         # 13
    "BrowsDown_Left",      # 14
    "BrowsDown_Right",     # 15
    "BrowsUp_Center",      # 16
    "BrowsUp_Left",        # 17
    "BrowsUp_Right",       # 18
    "JawFwd",              # 19
    "JawLeft",             # 20
    "JawOpen",             # 21
    "JawChew",             # 22
    "JawRight",            # 23
    "MouthLeft",           # 24
    "MouthRight",          # 25
    "MouthFrown_Left",     # 26
    "MouthFrown_Right",    # 27
    "MouthSmile_Left",     # 28
    "MouthSmile_Right",    # 29
    "MouthDimple_Left",    # 30
    "MouthDimple_Right",   # 31
    "LipsStretch_Left",    # 32
    "LipsStretch_Right",   # 33
    "LipsUpperClose",      # 34
    "LipsLowerClose",      # 35
    "LipsUpperUp",         # 36
    "LipsLowerDown",       # 37
    "LipsUpperOpen",       # 38
    "LipsLowerOpen",       # 39
    "LipsFunnel",          # 40
    "LipsPucker",          # 41
    "ChinLowerRaise",      # 42
    "ChinUpperRaise",      # 43
    "Sneer",               # 44
    "Puff",                # 45
    "CheekSquint_Left",    # 46
    "CheekSquint_Right",   # 47
    # Emotion shapes (48-60)
    "Emotion_01",          # 48
    "Emotion_02",          # 49
    "Emotion_03",          # 50
    "Emotion_04",          # 51
    "Emotion_05",          # 52
    "Emotion_06",          # 53
    "Emotion_07",          # 54
    "Emotion_08",          # 55
    "Emotion_09",          # 56
    "Emotion_10",          # 57
    "Emotion_11",          # 58
    "Emotion_12",          # 59
    "Emotion_13",          # 60
    # Asymmetric puff and tongue
    "Puff_Left",           # 61
    "Puff_Right",          # 62
    "Tongue_Out",          # 63
    "Tongue_Up",           # 64
    "Tongue_Down",         # 65
    "Tongue_Left",         # 66
    "Tongue_Right",        # 67
]

NUM_BLENDSHAPES: Final[int] = 68


# ---------------------------------------------------------------------------
# VLibras -> ABNT blendshape mapping
# ---------------------------------------------------------------------------
# Each entry: (vlibras_name, list_of_(abnt_head_geo_id, scale_factor))
#
# Multiple VLibras shapes may target the same ABNT ID.  When that happens
# the retargeting pipeline must *accumulate* (add) the weighted values,
# clamping the result to [0, 1].
#
# A negative scale_factor means the VLibras weight should be inverted
# (1.0 - weight) or negated before applying, depending on the shape semantics.

VLIBRAS_TO_ABNT_BLENDSHAPE: Final[list[tuple[str, list[tuple[int, float]]]]] = [
    # ---- Eyebrow shapes ----
    # "Raiva" = anger eyebrow (lowered)
    ("SobrancelhaDirRaiva", [(15, 1.0)]),       # -> BrowsDown_Right
    ("SobrancelhaEsqRaiva", [(14, 1.0)]),       # -> BrowsDown_Left
    # "Aberta" = open/raised eyebrow
    ("SobrancelhaDirAberta", [(18, 1.0)]),      # -> BrowsUp_Right
    ("SobrancelhaEsqAberta", [(17, 1.0)]),      # -> BrowsUp_Left
    # Raise/lower eyebrow (accumulates with Raiva/Aberta on same targets)
    ("LevantaSobrancelhaDir", [(18, 1.0)]),     # -> BrowsUp_Right (accumulate)
    ("LevantaSobrancelhaEsq", [(17, 1.0)]),     # -> BrowsUp_Left (accumulate)
    ("BaixaSobrancelhaDir", [(15, 1.0)]),       # -> BrowsDown_Right (accumulate)
    ("BaixaSobrancelhaEsq", [(14, 1.0)]),       # -> BrowsDown_Left (accumulate)
    # Furrow center brow -- inverted mapping to BrowsUp_Center
    ("FranzirSobrancelha", [(16, -1.0)]),       # -> BrowsUp_Center (inverted)
    # ---- Lip / mouth shapes ----
    ("Bico", [(41, 1.0)]),                      # -> LipsPucker
    ("LabioContraido", [(34, 1.0)]),            # -> LipsUpperClose
    ("Sorriso", [(28, 1.0), (29, 1.0)]),        # -> MouthSmile_Left + Right
    ("LabioSuperior", [(36, 1.0)]),             # -> LipsUpperUp
    ("BaixaCantoBoca", [(26, 1.0), (27, 1.0)]), # -> MouthFrown_Left + Right
    ("baixaBocaCanto_esq", [(26, 1.0)]),        # -> MouthFrown_Left
    ("baixaBocaCanto_dir", [(27, 1.0)]),        # -> MouthFrown_Right
    # ---- Cheek shapes ----
    ("InflaBochecha", [(45, 1.0)]),             # -> Puff (symmetric)
    ("BochechaContraida", [(46, 1.0), (47, 1.0)]),  # -> CheekSquint_Left + Right
    ("BochechaInfladaEsq", [(61, 1.0)]),        # -> Puff_Left
    ("BochechaInfladaDir", [(62, 1.0)]),        # -> Puff_Right
    # ---- Skipped shapes ----
    # correcaoAbreBoca: correction shape, not a semantic expression
    # TESTE: test/debug shape
]

# Names of VLibras blendshapes that should be skipped during retargeting
VLIBRAS_SKIP_BLENDSHAPES: Final[frozenset[str]] = frozenset({
    "correcaoAbreBoca",
    "TESTE",
})


# ---------------------------------------------------------------------------
# Multi-mesh blendshape ID mapping
# ---------------------------------------------------------------------------
# The ABNT avatar has 7 meshes.  A single semantic blendshape (e.g.
# EyeBlink_Left, head_GEO ID 0) may need to be applied to multiple meshes.
# Each mesh uses its own ID range:
#
#   head_GEO:     0 - 67       (base range, 68 shapes)
#   mouth_GEO:    1020 - 1067  (offset = 1020, covers IDs 20-67 of head_GEO)
#   eyelash_GEO:  2000 - 2059  (offset = 2000, covers IDs 0-59 of head_GEO)
#   eyebrow_l_GEO: 3014 - 3058 (offset = 3000+14, covers IDs 14-58)
#   eyebrow_r_GEO: 4014 - 4058 (offset = 4000+14, covers IDs 14-58)
#   iris_l_GEO:   5059         (single shape)
#   iris_r_GEO:   6059         (single shape)
#
# MULTI_MESH_IDS maps head_GEO blendshape index -> list of all mesh IDs
# (including the head_GEO ID itself) that must receive the same weight.


def _build_multi_mesh_ids() -> dict[int, list[int]]:
    """Build the complete multi-mesh blendshape ID lookup table.

    Returns:
        Dictionary mapping head_GEO blendshape index (0-67) to a list of
        all mesh-specific IDs that share that blendshape deformation.
    """
    result: dict[int, list[int]] = {}

    for head_id in range(68):
        ids: list[int] = [head_id]  # Always include head_GEO

        # mouth_GEO: covers head_GEO IDs 20-67 with offset 1000
        if 20 <= head_id <= 67:
            ids.append(1000 + head_id)

        # eyelash_GEO: covers head_GEO IDs 0-59 with offset 2000
        if 0 <= head_id <= 59:
            ids.append(2000 + head_id)

        # eyebrow_l_GEO: covers head_GEO IDs 14-58 with offset 3000
        if 14 <= head_id <= 58:
            ids.append(3000 + head_id)

        # eyebrow_r_GEO: covers head_GEO IDs 14-58 with offset 4000
        if 14 <= head_id <= 58:
            ids.append(4000 + head_id)

        # iris_l_GEO: only head_GEO ID 59
        if head_id == 59:
            ids.append(5059)

        # iris_r_GEO: only head_GEO ID 59
        # Note: iris_r uses 6059, same head_GEO source shape
        if head_id == 59:
            ids.append(6059)

        result[head_id] = ids

    return result


MULTI_MESH_IDS: Final[dict[int, list[int]]] = _build_multi_mesh_ids()
