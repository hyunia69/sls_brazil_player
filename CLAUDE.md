# Brazil Sign Language Player Project

브라질 수어(Libras) 3D 아바타 플레이어 생태계. **ABNT** (표준 기반)과 **VLibras** (레거시 호환) 두 축으로 구성.

- **배포**: https://sls-brazil-player.vercel.app/
- **GitHub**: https://github.com/hyunia69/sls_brazil_player

## 프로젝트 현황

**상세 현황 문서**: [`docs-source/claudedocs/project-status.md`](docs-source/claudedocs/project-status.md)
(현재 상태, 다음 작업, 주간보고, 작업 이력, 알려진 이슈 통합 관리)

## 현재 상태 (2026-04-20)

| 축 | 상태 | 설명 |
|---|---|---|
| **ABNT** | ✅ 완료 | SLMB 인코딩/디코딩/재생 파이프라인 전체 검증 완료 |
| **VLibras (레거시 플레이어)** | 🔄 진행중 | 스켈레톤+상체 재생 성공, 하체 좌표계 보정 미완 |
| **VLibras (Sentence Player)** | ✅ P1 + P5 Phase A + P5.1 완료 | 문장 → 번역 → 글로스 큐 + 동적 crossfade + stroke trim 재생 (27 글로스) |
| **Stroke 검증 도구** | ✅ 완료 (2026-04-15) | Method A/B/C/D 비교 + motion profile SVG 차트 + 배치 재생 |

**오늘 중점 (2026-04-20)**: 모션 블렌딩 전략 재검토 — stroke 기반 단어 연결이 적절한지 `sentence-stroke-test/`로 원점 평가. 상세: [`docs-source/claudedocs/project-status.md`](docs-source/claudedocs/project-status.md) 상단 "오늘의 작업 중점" 섹션.

## 디렉토리 구조

```
sls_brazil_player/
├── public/                           # Vercel 정적 배포 루트
│   ├── index.html                    # 메인 랜딩 페이지
│   ├── players/                      # 플레이어 HTML (7개)
│   │   ├── bvh/                      # [완료] BVH 전용 플레이어 (ABNT)
│   │   ├── slmb/                     # [완료] SLMB 파이프라인 검증 (ABNT)
│   │   ├── vlibras/                  # VLibras 레거시 플레이어
│   │   ├── vlibras-v3/              # VLibras 단일 글로스 검증 (Three.js tracks)
│   │   ├── sentence/                 # [완료] Sentence Player (P1/P5 Phase A/P5.1) - stroke trim + 동적 crossfade
│   │   ├── sentence-stroke-test/     # [완료] Stroke 검출 검증 도구 (Method A/B/C/D + motion profile)
│   │   └── viewer/                   # 3D 모델 뷰어
│   ├── avatars/                      # 공유 아바타 모델
│   │   ├── abnt/                     # ABNT 46조인트 (avatarModel, pcmodel)
│   │   └── vlibras/                  # VLibras 84본 (casa, icaro, padrao, Guga, Hozana)
│   ├── animations/                   # 공유 애니메이션 데이터
│   │   ├── abnt/                     # BVH, SLMB, roundtrip 파일
│   │   └── vlibras/                  # CASA + bundles/*.threejs.json (사전 변환 글로스)
│   └── docs/                         # 배포 문서 페이지
├── tools/                            # Python 변환 도구 (미배포)
│   ├── slmb_converter/               # SLMB 인코더/디코더
│   └── vlibras2slmb/                 # VLibras→SLMB 변환기 + batch/precompute_threejs.py
├── blender/                          # Blender 소스 파일 (Git LFS)
├── docs-source/                      # 문서 소스 (markdown + PDF)
│   ├── claudedocs/                   # 구현 분석 문서
│   ├── standards/                    # 표준 분석 문서
│   └── pdfs/                         # PDF 보고서
└── _validation/                      # 테스트 데이터
```

## 핵심 기술 사항

- **렌더링**: Three.js v0.170.0 (CDN import map), 단일 HTML 파일 구조
- **ABNT 스켈레톤**: 46 조인트, 30fps, cm 단위 (ABNT NBR 25606)
- **VLibras 스켈레톤**: 84 본, Bn 접두사 포르투갈어 명명
- **glTF scale 이슈**: `model_external.gltf`의 RootNode scale=[100,100,100] → Three.js에서 `×0.01` 필수
- **좌표 변환**: Unity LH → glTF RH: position `[x,y,z]→[x,y,-z]`, quaternion `[x,y,z,w]→[-x,-y,z,w]`
- **배포**: Vercel 정적 사이트 (`public/` 디렉토리), Git push 시 자동 배포
- **에셋 경로**: 모든 플레이어는 절대 경로 사용 (`/avatars/...`, `/animations/...`)

## 로컬 실행

```bash
cd public
python -m http.server 8080
# http://localhost:8080/
```

## 표준 분석 문서

| 파일 | 내용 |
|---|---|
| `docs-source/standards/ABNT_NBR25606_core_analysis.md` | ABNT NBR 25606 핵심 분석 |
| `docs-source/standards/ABNT_NBR25606_annex_AB.md` | Annex A(영상), B(글로스) 전송 |
| `docs-source/standards/ABNT_NBR25606_annex_CD.md` | Annex C(자막), D(모션/SLMB) 전송 |
| `docs-source/standards/SBTVD_OG06_analysis.md` | SBTVD OG-06 운영 가이드라인 |
| `docs-source/standards/SLMB_Converter_구현문서.md` | SLMB 인코더/디코더 구현 문서 |

## 구현 분석 문서

| 파일 | 내용 |
|---|---|
| `docs-source/claudedocs/project-analysis.md` | 프로젝트 종합 분석 |
| `docs-source/claudedocs/technical-findings.md` | 기술 검증 결과 |
| `docs-source/claudedocs/implement-player-bvh-slmb.md` | player_bvh_slmb 구현 상세 |
| `docs-source/claudedocs/design-player-vlibras.md` | VLibras 플레이어 설계 |

## VLibras 참조 정보

- **번역 API**: `POST https://traducao2.vlibras.gov.br/translate`, JSON body `{"text":"..."}`, plain text 응답 (CORS 직접 허용). 상세: `docs-source/claudedocs/vlibras-translation-api.md`
- **사전 CDN**: `https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/<GLOSS>` (Unity AssetBundle, UnityPy 파싱 필요)
- **아바타 (사용 가능)**: Padrao, CASA, Icaro (90본 공통 스켈레톤)
- **아바타 (사용 금지)**: Guga(244본), Hozana(136본) — 스켈레톤 불일치
- **사전 변환 도구**: `tools/vlibras2slmb/batch/precompute_threejs.py` (Icaro bind pose 기반 레거시 변환 적용)

## 다음 작업

1. **[오늘 중점] 모션 블렌딩 전략 재검토** — stroke 기반 연결이 적절한지 `sentence-stroke-test/`로 다양한 글로스 × Method A/B/C/D 시각 비교. 대안(full clip smart crossfade / hand-trajectory IK / hold plateau) 검토
2. **P5.2**: Method C(asymmetric + plateau 0.90)를 production `sentence/index.html`에 적용 여부 결정 (위 재검토와 연계)
3. Sentence Player 어휘 확장 (현재 27 → 100 글로스)
4. VLibras 하체 좌표계 보정 (레거시 vlibras/vlibras-v3 플레이어)
5. `tools/vlibras2slmb/parsing/asset_bundle.py` UnityPy 1.25+ 마이그레이션
6. VLibras→SLMB 변환 파이프라인 완성 (P2)
7. Sentence Player 타임라인 seek 활성화 (P4)
