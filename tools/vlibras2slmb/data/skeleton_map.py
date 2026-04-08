"""VLibras 84-bone to ABNT 46-joint skeleton mapping.

Maps the VLibras avatar skeleton (Portuguese bone names from Unity/Blender
export) to the ABNT NBR 25606 Annex D standard skeleton (English joint names).

Key design decisions:
- Intermediate bones (BnAntBraco.L.001 / .R.001) have no direct ABNT mapping;
  their rotation must be composited into the child hand joint.
- Auxiliary controller bones (orientation helpers, IK/FK switches, pole vectors)
  are skipped entirely.
- Face bones are separated for the face-motion pipeline (blendshape-based).
- Leg and sub-pelvis bones have no ABNT equivalent because the ABNT skeleton
  covers upper body only.
"""

from __future__ import annotations


def get_leaf_name(bone_path: str) -> str:
    """Extract the leaf bone name from a full hierarchical path.

    VLibras animation data stores bone paths as slash-separated hierarchies,
    e.g. ``"Armature.001/BnBacia.001/BnCol-01/BnCol-02"``.  This function
    returns the rightmost component (``"BnCol-02"``).

    Args:
        bone_path: Full slash-separated bone path string.

    Returns:
        The leaf (last) component of the path.

    Raises:
        ValueError: If *bone_path* is empty.
    """
    if not bone_path:
        raise ValueError("bone_path must be a non-empty string")
    return bone_path.rsplit("/", maxsplit=1)[-1]


# ---------------------------------------------------------------------------
# VLibras leaf bone name -> ABNT joint name
# ---------------------------------------------------------------------------
# Only bones that have a direct 1:1 correspondence are listed here.
# Intermediate bones, auxiliary controllers, face bones, and unmapped bones
# are tracked in separate collections below.

VLIBRAS_TO_ABNT: dict[str, str] = {
    # Pelvis / root
    "BnBacia.001": "hips_JNT",
    # Spine chain
    "BnCol-01": "spine_JNT",
    "BnCol-02": "spine1_JNT",
    "BnCol-03": "spine2_JNT",
    # Neck / head
    "BnPescoco": "neck_JNT",
    "BnCabeca": "head_JNT",
    # ---- Left arm ----
    "BnOmbro.L": "l_shoulder_JNT",
    "BnBraco.L": "l_arm_JNT",
    "BnAntBraco.L": "l_forearm_JNT",
    "BnMao.L": "l_hand_JNT",
    # Left thumb
    "BnDedo.1.L": "l_handThumb1_JNT",
    "BnDedo.1.L.006": "l_handThumb2_JNT",
    "BnDedo.1.L.005": "l_handThumb3_JNT",
    # Left index
    "BnDedo.1.L.001": "l_handIndex1_JNT",
    "BnDedo.1.L.008": "l_handIndex2_JNT",
    "BnDedo.1.L.007": "l_handIndex3_JNT",
    # Left middle
    "BnDedo.1.L.002": "l_handMiddle1_JNT",
    "BnDedo.1.L.010": "l_handMiddle2_JNT",
    "BnDedo.1.L.009": "l_handMiddle3_JNT",
    # Left ring
    "BnDedo.1.L.003": "l_handRing1_JNT",
    "BnDedo.1.L.012": "l_handRing2_JNT",
    "BnDedo.1.L.011": "l_handRing3_JNT",
    # Left pinky
    "BnDedo.1.L.004": "l_handPinky1_JNT",
    "BnDedo.1.L.014": "l_handPinky2_JNT",
    "BnDedo.1.L.013": "l_handPinky3_JNT",
    # ---- Right arm ----
    "BnOmbro.R": "r_shoulder_JNT",
    "BnBraco.R": "r_arm_JNT",
    "BnAntBraco.R": "r_forearm_JNT",
    "BnMao.R": "r_hand_JNT",
    # Right thumb
    "BnDedo.1.R": "r_handThumb1_JNT",
    "BnDedo.1.R.006": "r_handThumb2_JNT",
    "BnDedo.1.R.005": "r_handThumb3_JNT",
    # Right index
    "BnDedo.1.R.001": "r_handIndex1_JNT",
    "BnDedo.1.R.008": "r_handIndex2_JNT",
    "BnDedo.1.R.007": "r_handIndex3_JNT",
    # Right middle
    "BnDedo.1.R.002": "r_handMiddle1_JNT",
    "BnDedo.1.R.010": "r_handMiddle2_JNT",
    "BnDedo.1.R.009": "r_handMiddle3_JNT",
    # Right ring
    "BnDedo.1.R.003": "r_handRing1_JNT",
    "BnDedo.1.R.012": "r_handRing2_JNT",
    "BnDedo.1.R.011": "r_handRing3_JNT",
    # Right pinky
    "BnDedo.1.R.004": "r_handPinky1_JNT",
    "BnDedo.1.R.014": "r_handPinky2_JNT",
    "BnDedo.1.R.013": "r_handPinky3_JNT",
}


# ---------------------------------------------------------------------------
# Intermediate bones whose rotation must be composited into a child joint
# ---------------------------------------------------------------------------
# These bones exist in VLibras but have no direct ABNT joint.  During
# retargeting the rotation of the intermediate bone is multiplied into
# the rotation of the specified child bone.

INTERMEDIATE_BONES: dict[str, str] = {
    "BnAntBraco.L.001": "BnMao.L",
    "BnAntBraco.R.001": "BnMao.R",
}


# ---------------------------------------------------------------------------
# Auxiliary controller bones -- skip entirely
# ---------------------------------------------------------------------------
# These are IK targets, FK switches, pole-vector helpers, and hand-orientation
# controllers used by VLibras' animation rig.  They carry no motion data
# relevant to the ABNT skeleton.

AUXILIARY_BONES: frozenset[str] = frozenset({
    "BnMaoOrient.L",
    "BnMaoOrient.R",
    "BnPolyV.L",
    "BnPolyV.R",
    "ik_FK.L",
    "ik_FK.R",
})


# ---------------------------------------------------------------------------
# Face bones -- handled by the face/blendshape pipeline, not body skeleton
# ---------------------------------------------------------------------------
# These bones drive facial deformation in VLibras and are mapped to ABNT
# blendshape targets rather than skeleton joints.

FACE_BONES: frozenset[str] = frozenset({
    # Eyes
    "BnOlho.L",
    "BnOlho.R",
    "BnOlhosMira",
    "BnOlhoMira.L",
    "BnOlhoMira.R",
    # Eyelids
    "BnPalpebSuper.L",
    "BnPalpebSuper.R",
    "BnPalpebInfe.L",
    "BnPalpebInfe.R",
    # Eyebrows
    "BnSobrancCentro",
    "BnSobrancCentro.L",
    "BnSobrancCentro.R",
    "BnSobrancLateral.L",
    "BnSobrancLateral.R",
    # Mouth / lips
    "BnBocaCanto.L",
    "BnBocaCanto.R",
    "BnLabioCentroInfer",
    "BnLabioCentroSuper",
    # Cheeks
    "BnBochecha.L",
    "BnBochecha.R",
    # Jaw / chin / tongue
    "BnDirigeQueixo",
    "BnMandibula",
    "BnLingua",
    "BnLingua.001",
    "BnLingua.002",
})


# ---------------------------------------------------------------------------
# Unmapped bones -- no ABNT equivalent (legs, sub-pelvis, armature root)
# ---------------------------------------------------------------------------
# The ABNT NBR 25606 skeleton is upper-body only.  Leg bones and the
# intermediate pelvis bone (BnBacia, distinct from BnBacia.001) have no
# target joint.  The armature root carries a -90 degree X rotation from
# the Unity-to-Blender export which must be handled separately.

UNMAPPED_BONES: frozenset[str] = frozenset({
    # Armature root (export rotation only)
    "Armature.001",
    # Intermediate pelvis
    "BnBacia",
    # Left leg chain
    "BnBacia_L",
    "BnPerna.L",
    "BnCanela.L",
    "BnPe.L",
    "BnDedoPe.L",
    # Right leg chain
    "BnBacia_R",
    "BnPerna.R",
    "BnCanela.R",
    "BnPe.R",
    "BnDedoPe.R",
})
