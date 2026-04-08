# Python Tools

SLMB/VLibras 변환 및 유틸리티 도구. Vercel에는 배포되지 않으며 로컬에서 실행합니다.

## SLMB Converter

BVH/SLMB 인코딩 및 디코딩 도구 (ABNT NBR 25606 표준).

```bash
cd tools
python -m slmb_converter --help
```

## VLibras to SLMB Converter

VLibras AssetBundle을 SLMB 포맷으로 변환하는 파이프라인.

```bash
cd tools
python -m vlibras2slmb --help
```

## Individual Scripts

| 스크립트 | 설명 |
|---|---|
| `convert_anim.py` | VLibras 애니메이션 포맷 변환 |
| `vlibras_to_gltf.py` | VLibras AssetBundle → glTF 변환 |
| `extract_casa.py` | CASA AssetBundle 데이터 추출 |
| `convert_fbx.py` | FBX → GLB 변환 (Blender 필요) |
| `convert_all_avatars.py` | 전체 아바타 일괄 변환 |
