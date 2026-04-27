# Brazil Sign Language Player Project

브라질 수어(Libras) 3D 아바타 플레이어 생태계. **ABNT** (표준 기반)와 **VLibras** (레거시 호환) 두 축으로 구성.

- **배포**: https://sls-brazil-player.vercel.app/
- **GitHub**: https://github.com/hyunia69/sls_brazil_player

> **현재 상태·다음 작업·작업 이력**은 [`docs-source/claudedocs/project-status.md`](docs-source/claudedocs/project-status.md)가 단일 진실 출처입니다. 본 문서는 변하지 않는 프로젝트 메타데이터만 담습니다.

## 디렉토리 구조

```
sls_brazil_player/
├── public/                          # Vercel 정적 배포 루트
│   ├── index.html                   # 메인 랜딩
│   ├── players/                     # 플레이어 HTML
│   │   ├── bvh/                     # BVH 전용 (ABNT)
│   │   ├── slmb/                    # SLMB 파이프라인 검증 (ABNT)
│   │   ├── vlibras/                 # VLibras 레거시
│   │   ├── vlibras-v3/              # VLibras 단일 글로스 검증
│   │   ├── sentence/                # Sentence Player (production)
│   │   ├── sentence-stroke-test/    # Stroke 검출 검증 도구
│   │   └── viewer/                  # 3D 모델 뷰어
│   ├── avatars/                     # 공유 아바타 모델
│   │   ├── abnt/                    # ABNT 46조인트 (avatarModel, pcmodel)
│   │   └── vlibras/                 # VLibras 84본 (casa, icaro, padrao, Guga, Hozana)
│   ├── animations/                  # 공유 애니메이션 데이터
│   │   ├── abnt/                    # BVH, SLMB, roundtrip
│   │   └── vlibras/                 # CASA + bundles/*.threejs.json
│   └── docs/                        # 배포 문서 페이지
├── tools/                           # Python 변환 도구 (미배포)
│   ├── slmb_converter/              # SLMB 인코더/디코더
│   └── vlibras2slmb/                # VLibras→SLMB 변환기 + batch/precompute_threejs.py
├── blender/                         # Blender 소스 (Git LFS)
├── docs-source/                     # 문서 소스 (markdown + PDF)
│   ├── claudedocs/                  # 구현 분석
│   ├── standards/                   # 표준 분석
│   └── pdfs/                        # PDF 보고서
└── _validation/                     # 테스트 데이터
```

## 핵심 기술 사항

- **렌더링**: Three.js v0.170.0 (CDN import map), 단일 HTML 파일 구조
- **ABNT 스켈레톤**: 46 조인트, 30fps, cm 단위 (ABNT NBR 25606)
- **VLibras 스켈레톤**: 84 본, Bn 접두사 포르투갈어 명명
- **glTF scale 이슈**: `model_external.gltf`의 RootNode scale=[100,100,100] → Three.js에서 `×0.01` 필수
- **좌표 변환**: Unity LH → glTF RH: position `[x,y,z]→[x,y,-z]`, quaternion `[x,y,z,w]→[-x,-y,z,w]`
- **배포**: Vercel 정적 사이트(`public/`), Git push 자동 배포
- **에셋 경로**: 모든 플레이어는 절대 경로 (`/avatars/...`, `/animations/...`)

## 로컬 실행

```bash
cd public
python -m http.server 8080
# http://localhost:8080/
```

## VLibras 참조 정보

- **번역 API**: `POST https://traducao2.vlibras.gov.br/translate`, JSON body `{"text":"..."}`, plain text 응답 (CORS 직접 허용). 상세: `docs-source/claudedocs/vlibras-translation-api.md`
- **사전 CDN**: `https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/<GLOSS>` (Unity AssetBundle, UnityPy 파싱 필요)
- **사용 가능 아바타**: Padrao, CASA, Icaro (90본 공통 스켈레톤)
- **사용 금지 아바타**: Guga(244본), Hozana(136본) — 스켈레톤 불일치
- **사전 변환 도구**: `tools/vlibras2slmb/batch/precompute_threejs.py` (Icaro bind pose 기반 레거시 변환)

## 문서 인덱스

### 표준 분석

| 파일 | 내용 |
|---|---|
| `docs-source/standards/ABNT_NBR25606_core_analysis.md` | ABNT NBR 25606 핵심 분석 |
| `docs-source/standards/ABNT_NBR25606_annex_AB.md` | Annex A(영상), B(글로스) 전송 |
| `docs-source/standards/ABNT_NBR25606_annex_CD.md` | Annex C(자막), D(모션/SLMB) 전송 |
| `docs-source/standards/SBTVD_OG06_analysis.md` | SBTVD OG-06 운영 가이드라인 |
| `docs-source/standards/SLMB_Converter_구현문서.md` | SLMB 인코더/디코더 구현 |

### 구현 분석

| 파일 | 내용 |
|---|---|
| `docs-source/claudedocs/project-status.md` | **현재 상태·다음 작업·작업 이력 통합 관리** |
| `docs-source/claudedocs/project-analysis.md` | 프로젝트 종합 분석 |
| `docs-source/claudedocs/technical-findings.md` | 기술 검증 결과 |
| `docs-source/claudedocs/implement-player-bvh-slmb.md` | player_bvh_slmb 구현 상세 |
| `docs-source/claudedocs/design-player-vlibras.md` | VLibras 플레이어 설계 |
| `docs-source/claudedocs/plan-sentence-blending-redesign.md` | Sentence Player 블렌딩 재검토 플랜 (P5.2 → P6.5) |
| `docs-source/claudedocs/vlibras-translation-api.md` | VLibras 번역 API 스펙 |
| `docs-source/claudedocs/avatar-handedness-analysis.md` | 메인 vs. 위젯 손잡이(chirality) 차이 분석 |
| `docs-source/claudedocs/hold-ground-truth.json` | 수동 hold annotation scaffold (P6a 결정 게이트) |
