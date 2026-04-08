# Brazil Sign Language Player Project

브라질 수어(Libras) 3D 아바타 플레이어 생태계. **ABNT** (표준 기반)과 **VLibras** (레거시 호환) 두 축으로 구성.

## 현재 상태 (2026-04-08)

| 축 | 상태 | 설명 |
|---|---|---|
| **ABNT** | ✅ 완료 | SLMB 인코딩/디코딩/재생 파이프라인 전체 검증 완료 |
| **VLibras** | 🔄 진행중 | 스켈레톤+상체 재생 성공, 하체 좌표계 보정 미완 |

## 디렉토리 구조

```
sls_brazil_player/
├── public/                           # Vercel 정적 배포 루트
│   ├── index.html                    # 메인 랜딩 페이지
│   ├── players/                      # 플레이어 HTML (6개)
│   │   ├── bvh/                      # [완료] BVH 전용 플레이어 (ABNT)
│   │   ├── slmb/                     # [완료] SLMB 파이프라인 검증 (ABNT)
│   │   ├── vlibras-slmb/            # [진행중] VLibras AssetBundle 재생
│   │   ├── vlibras/                  # VLibras 레거시 플레이어
│   │   ├── vlibras-v3/              # VLibras 플레이어 v3
│   │   └── viewer/                   # 3D 모델 뷰어
│   ├── avatars/                      # 공유 아바타 모델
│   │   ├── abnt/                     # ABNT 46조인트 (avatarModel, pcmodel)
│   │   └── vlibras/                  # VLibras 84본 (casa, icaro, padrao, Guga, Hozana)
│   ├── animations/                   # 공유 애니메이션 데이터
│   │   ├── abnt/                     # BVH, SLMB, roundtrip 파일
│   │   └── vlibras/                  # CASA 글로스 데이터
│   └── docs/                         # 배포 문서 페이지
├── tools/                            # Python 변환 도구 (미배포)
│   ├── slmb_converter/               # SLMB 인코더/디코더
│   └── vlibras2slmb/                 # VLibras→SLMB 변환기
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
- **배포**: Vercel 정적 사이트 (`public/` 디렉토리)
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

- **번역 API**: `traducao2.vlibras.gov.br/translate`
- **사전 CDN**: `dicionario2.vlibras.gov.br/bundles`
- **아바타**: Icaro, Guga, Hosana (T-pose, 84본)

## 다음 작업

1. VLibras 하체 좌표계 보정 (Unity LH ↔ Blender GLB)
2. 다양한 수어 단어 테스트 (CASA 외 추가 번들)
3. VLibras→SLMB 변환 파이프라인 완성
4. Vercel 배포 및 Git 연동
