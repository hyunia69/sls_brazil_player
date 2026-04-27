# Brazil Sign Language Player Project

브라질 수어(Libras) 3D 아바타 플레이어 생태계. **ABNT** (표준 기반)과 **VLibras** (레거시 호환) 두 축으로 구성.

- **배포**: https://sls-brazil-player.vercel.app/
- **GitHub**: https://github.com/hyunia69/sls_brazil_player

## 프로젝트 현황

**상세 현황 문서**: [`docs-source/claudedocs/project-status.md`](docs-source/claudedocs/project-status.md)
(현재 상태, 다음 작업, 주간보고, 작업 이력, 알려진 이슈 통합 관리)

## 현재 상태 (2026-04-27)

| 축 | 상태 | 설명 |
|---|---|---|
| **ABNT** | ✅ 완료 | SLMB 인코딩/디코딩/재생 파이프라인 전체 검증 완료 |
| **VLibras (레거시 플레이어)** | 🔄 진행중 | 스켈레톤+상체 재생 성공, 하체 좌표계 보정 미완 |
| **VLibras (Sentence Player)** | ✅ P1 + P5 Phase A + P5.1 + **P5.3 Step 1-3 완료 (2026-04-27)** | 문장 → 번역 → 글로스 큐 + 동적 crossfade + stroke trim 재생 (27 글로스) + **손가락 8본 가중치(handshape) + bimanual union 토글** |
| **Stroke 검증 도구** | ✅ **P5.2 Week 1 + Week 2 코드부 완료 (2026-04-27)** | Method A/B/C/D + **E (M-H 인식) + G (bimanual separated)** 비교 + motion profile + 5 시나리오 preset + 자동 메트릭 4종(Jerk RMS/Boundary/Velocity/Quaternion Plateau) + JSON export |
| **블렌딩 재검토 플랜** | ✅ Codex 2차 검토 반영 완료 | `docs-source/claudedocs/plan-sentence-blending-redesign.md` (P5.2→P5.3→P6a→P6b spike→P6.5 hybrid eval) |
| **수동 hold ground truth** | ⏳ scaffold (0/5 라벨됨) | `docs-source/claudedocs/hold-ground-truth.json` — **사용자 frame-by-frame annotation 필요 (P6a 결정 게이트)** |
| **PR #1** | 🔄 open | https://github.com/hyunia69/sls_brazil_player/pull/1 (P5.2 Week 2 + P5.3 Step 2-3, 머지 게이트 대기) |

**오늘 중점 (2026-04-27)**: 사용자 부재 + 전권 위임 상태에서 gstack `/office-hours` → P5.2 Week 2 코드부 (Method E/G) → P5.3 Step 2-3 (손가락 본 + bimanual 토글) → Playwright 회귀 → PR #1 생성까지 자동 풀 사이클. 상세: [`docs-source/claudedocs/project-status.md`](docs-source/claudedocs/project-status.md) 상단 "오늘의 작업 중점" 섹션.

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
│   │   ├── sentence/                 # [완료] Sentence Player (P1/P5 Phase A/P5.1/P5.3 Step 1-3) - stroke trim + 동적 crossfade + handshape + bimanual 토글
│   │   ├── sentence-stroke-test/     # [완료] Stroke 검출 검증 도구 (Method A/B/C/D/E/G + motion profile + 5 시나리오 preset + 메트릭 export)
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

### 🔥 즉시 (사용자 복귀 시 1-2시간)
1. **PR #1 review + merge 결정** — https://github.com/hyunia69/sls_brazil_player/pull/1 diff 확인 → 로컬 Test plan 5개 체크 → 머지
2. **수동 hold annotation** — `docs-source/claudedocs/hold-ground-truth.json` 5 시나리오 × frame-by-frame 채우기 (개발자 1차 + 동료 cross-check). **P6a 결정의 유일한 acceptance criterion**.
3. **5 시나리오 메트릭 비교** — `sentence-stroke-test/`에서 ①~⑤ × Method A/C/E/G batch JSON export → 수동 HPR과 비교 → P6a 승자 후보 식별

### 🔄 다음 (P6a 승자 결정 후)
4. **P6a (3주)**: Week 2 결과 승자를 production `sentence/index.html` `computeStrokeRange`에 포팅 (feature flag `window.__blendingAlgo`) + targetted/lax transition 이원화
5. **P5.2 Week 2 잔여**: 4-row stacked 차트 비교 모드(같은 문장 × 4 method 동시 비교 UI) — 본 세션은 차트에 E/G 라인만 추가, batch 비교 UI는 별도

### 🧪 spike / eval
6. **P6b (3일 Go/No-Go)**: SQUAD Three.js spike — 60fps 유지 & jerk 개선 둘 다 미달성 시 즉시 폐기
7. **P6.5 (2주)**: 3-track hybrid eval — KSL naturalness 3-5명 + 원격 LIBRAS 2-3명 + 전문가 fallback

### 📋 Scope 외 (별도 트랙)
8. Sentence Player 어휘 확장 (27 → 100 글로스) — `tools/vlibras2slmb/data/spike_glosses.txt` 편집 + `precompute_threejs.py` 재실행
9. VLibras 하체 좌표계 보정 (레거시 vlibras/vlibras-v3 플레이어)
10. `tools/vlibras2slmb/parsing/asset_bundle.py` UnityPy 1.25+ 마이그레이션
11. VLibras→SLMB 변환 파이프라인 완성 (P2)
12. Sentence Player 타임라인 seek 활성화 (P4)

### 📂 의사결정 게이트 요약 (`plan-sentence-blending-redesign.md` 발췌)
- **P5.2 종료 (현재 위치)**: Method E가 A보다 우수? → 수동 라벨 HPR + 자동 메트릭 + 시각 A/B
- **P6a 종료**: P6b 시도? → 안정 + 시간 여유
- **P6b 중간**: SQUAD Go? → 60fps & jerk 개선
- **P6.5 종료**: rollout? → Track A 과반 + Track B 저하 없음
