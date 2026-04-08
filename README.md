# Brazil Sign Language (Libras) 3D Avatar Player

브라질 수어(Libras) 3D 아바타 플레이어 생태계. ABNT NBR 25606 표준과 VLibras 레거시 포맷을 지원합니다.

## Players

| Player | Type | Status | Description |
|--------|------|--------|-------------|
| [BVH Player](/players/bvh/) | ABNT | ✅ | BVH 파일 파싱 및 재생 |
| [SLMB Pipeline](/players/slmb/) | ABNT | ✅ | SLMB 인코딩/디코딩 검증 |
| [VLibras Player](/players/vlibras/) | VLibras | 🔄 | VLibras 아바타 애니메이션 |
| [VLibras v3](/players/vlibras-v3/) | VLibras | 🔄 | VLibras 플레이어 v3 |
| [VLibras SLMB](/players/vlibras-slmb/) | VLibras | 🔄 | VLibras AssetBundle 재생 |
| [Model Viewer](/players/viewer/) | Viewer | ✅ | 3D 모델 뷰어 |

## Quick Start

```bash
# 로컬 실행
cd public
python -m http.server 8080
# http://localhost:8080/ 에서 확인
```

## Project Structure

```
public/          → Vercel 배포 루트 (플레이어, 아바타, 애니메이션, 문서)
tools/           → Python 변환 도구 (SLMB 인코더/디코더, VLibras→SLMB)
blender/         → Blender 소스 파일
docs-source/     → 문서 소스 (markdown, PDF)
```

## Tech Stack

- **Rendering**: Three.js v0.170.0 (CDN import map)
- **Avatars**: glTF/GLB format
- **Standards**: ABNT NBR 25606 (46-joint skeleton, 30fps)
- **Deployment**: Vercel (static site)
- **Tools**: Python 3 (conversion utilities)

## Documentation

- [Annex D Progress Report](/docs/annex_d_progress_report_v2.html)
- [Documentation Index](/docs/)

## License

Internal project — not for public distribution.
