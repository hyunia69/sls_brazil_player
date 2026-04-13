# 프로젝트 현황

브라질 수어(Libras) 3D 아바타 플레이어 생태계. ABNT NBR 25606 표준과 VLibras 레거시 포맷을 지원하는 웹 기반 플레이어.

- **배포**: https://sls-brazil-player.vercel.app/
- **GitHub**: https://github.com/hyunia69/sls_brazil_player
- **기술 스택**: Three.js v0.170.0 (CDN), 단일 HTML, Python 변환 도구
- **배포 방식**: Vercel 정적 사이트, Git push 시 자동 배포

---

## 현재 상태

| 컴포넌트 | 상태 | 위치 |
|---|---|---|
| SLMB 인코더/디코더 | ✅ 완료 | `tools/slmb_converter/` |
| BVH Player (ABNT) | ✅ 완료 | `public/players/bvh/` |
| SLMB Pipeline Player (ABNT) | ✅ 완료 | `public/players/slmb/` |
| VLibras Player | 🔄 상체 완료, 하체 미완 | `public/players/vlibras/` |
| VLibras Player v3 | 🔄 상체 완료, 하체 미완 | `public/players/vlibras-v3/` |
| **Sentence Player (P1)** | ✅ 완료 | `public/players/sentence/` |
| **Bundle 사전 변환기** | ✅ 완료 (21 글로스) | `tools/vlibras2slmb/batch/precompute_threejs.py` |
| Model Viewer | ✅ 완료 | `public/players/viewer/` |
| VLibras→SLMB 변환기 | 🔄 매핑 완료, 파이프라인 미완 | `tools/vlibras2slmb/` |
| 랜딩 페이지 | ✅ 완료 | `public/index.html` |
| 문서 페이지 | ✅ 완료 | `public/docs/` |
| Vercel 배포 | ✅ 완료 | Git push 자동 배포 |

---

## 다음 세션 작업

### P1: 어휘 확장 (완료된 파이프라인 위에)
- 현재 스파이크 세트 21개 → 자주 쓰이는 명사·동사·대명사 100개 수준으로 확장
- `tools/vlibras2slmb/data/spike_glosses.txt` 편집 + `precompute_threejs.py` 재실행
- 확장 후 대표 문장 10개로 회귀 테스트
- `precompute_threejs.py`에 `sys.stdout.reconfigure(encoding='utf-8')` 추가 (Windows cp949 대응)

### P2: SLMB 아바타에 VLibras 애니메이션 적용
- VLibras 84본 → ABNT 46조인트 리타겟팅
- 변환 흐름: CASA (VLibras) → vlibras2slmb → .slmb.xz → decode → JSON → SLMB Pipeline Player
- 선행 차단: `tools/vlibras2slmb/parsing/asset_bundle.py`가 UnityPy ≥ 1.25에서 깨짐 (lowercase API drift). `precompute_threejs.py`의 인라인 리더를 정규화해 공용 모듈로 올릴 필요

### P3: VLibras 하체 좌표계 보정
- Unity LH → glTF RH 변환을 하체 관절(hip, leg, foot)에 정확히 적용
- 대상: `public/players/vlibras/`, `public/players/vlibras-v3/` (Sentence Player는 사전 변환으로 이미 해결됨)

### P4: Sentence Player 타임라인 seek 활성화
- M4 MVP에서 timeline slider 비활성화됨
- 글로벌 시간 → 로컬 클립 시간 역산 + 이전 클립 stop/uncache 로직 구현 필요

---

## 주간보고

### 2026-04-13 (월)
- [완료] **P1 end-to-end 파이프라인 구축 완료** (M0~M5)
  - VLibras 번역 API 스펙 실측 확정 (POST JSON, plain text 응답, CORS 직접 허용)
  - Unity AssetBundle → Three.js JSON 배치 변환기 구현 (12 글로스)
  - 레거시 변환 파이프라인 역공학 성공 (yz sign flip + Icaro-bind override + Playwright 픽셀 검증)
  - `public/players/sentence/` 신규 플레이어 구현 (번역 + 큐잉 + crossfade)
  - Playwright E2E 검증: `Olá casa`(4.833s), `Sim bom dia`(7.1s), `Casa escola não`(8.367s) 모두 성공
  - 융합 토큰 폴백 로직 (`BOM_DIA` → `BOM`+`DIA` 자동 분해)
- [예정] 어휘 확장 (100개 수준), `asset_bundle.py` UnityPy 드리프트 수정

### 2026-04-08 (화)
- [완료] `slmb/`, `vlibras/` 두 프로젝트를 단일 저장소로 통합
- [완료] 공유 아바타/애니메이션 폴더 구성, 메인 랜딩 페이지 생성
- [완료] Git 저장소 생성, Vercel 배포 완료
- [완료] 프로젝트 현황 문서 작성
- [완료] P1 번역 파이프라인 구축 (2026-04-13로 이관)

---

## 작업 이력

### 2026-04-13
- **P1 파이프라인 M0~M5 완료** (에이전트 병렬 실행)
  - **M0**: VLibras 번역 API 스펙 실측 (`POST https://traducao2.vlibras.gov.br/translate`, JSON body `{"text":"..."}`, plain text 응답, `\s+` split 파싱, CORS 직접 허용). 상세: `docs-source/claudedocs/vlibras-translation-api.md`
  - **M1**: `tools/vlibras2slmb/batch/precompute_threejs.py` 신설 — VLibras Unity AssetBundle → Three.js tracks JSON 배치 변환. UnityPy 1.25 lowercase API 대응 인라인 리더 내장. 레거시 파이프라인 변환(yz sign flip `(x,y,z,w)→(x,-y,-z,w)` + 7개 헬퍼 본 Icaro-bind override + static position tracks) 역공학 후 `--legacy` 기본 적용. 스파이크 12 글로스 `public/animations/vlibras/bundles/*.threejs.json` 생성, Icaro bind pose `tools/vlibras2slmb/data/icaro_bind_pose.json`에 베이크.
  - **M2**: 스킵 — M0에서 CORS 직접 허용 확인, Vercel rewrites 불필요
  - **M3**: `public/players/sentence/index.html` 신설. 문장 입력 → POST 번역 → ASCII 키 정규화(`NFKD`) → 사전 변환 번들 fetch → 첫 글로스 재생. 글로스 칩 UI(미싱 `⚠️` 표시). `buildClipFromJson`, `loadGlossClip`, `asciiKey`, `translateSentence` 순수 함수화
  - **M4**: 큐잉 + crossfade 연속 재생. `CROSSFADE_SEC=0.2s`, `mixer.addEventListener('finished')` + 렌더 루프 timeLeft 체크로 다음 액션 `crossFadeTo`. `stopAndDisposeQueue()` 메모리 정리, 재번역 5연속 누수 없음 확인. 전체 duration 기반 타임라인 갱신
  - **M5**: 융합 토큰 폴백 (`BOM_DIA` → `BOM`+`DIA` split 재조회), 에러 배너 폴리싱, 어휘 확장
  - **Playwright 픽셀/E2E 검증**: M1에서 `CASA`·`ESCOLA` 레퍼런스 대비 bone delta ≤ 6mm, M3~M5에서 5~10개 문장 시나리오 실측 (총 duration 수치 검증 포함)
  - **배포 영향 없음**: 순수 정적 사이트 제약 그대로 유지 (`vercel.json` 무수정)
- 프로젝트 운영 규칙 정립: project-status.md 통합 관리 체계 구축
  - 작업 이력, 주간보고, 다음 세션 작업을 단일 문서로 관리
  - 성공 경로만 기록, 코드 변경 시 문서 동기화

### 2026-04-08
- 프로젝트 통합 완료: slmb + vlibras → sls_brazil_player 단일 구조
- 공유 리소스 구성: `public/avatars/`, `public/animations/`
- 메인 랜딩 페이지 + 문서 페이지 생성
- Vercel 배포 완료 (Git push 자동 배포)
- CLAUDE.md 프로젝트 설정 문서 작성

### 2026-04-08 이전 (요약)
- ABNT NBR 25606 표준 전체 분석 완료
- SLMB 인코더/디코더 구현 및 roundtrip 검증 완료
- BVH Player, SLMB Pipeline Player 구현 완료
- VLibras 플레이어 상체 재생 성공 (하체 미완)
- VLibras→SLMB 스켈레톤 매핑 정의 완료

---

## 알려진 이슈

### 1. VLibras 하체 좌표계 보정
- **문제**: Unity 좌표계(LH)와 glTF/Blender 좌표계(RH) 차이로 하체 애니메이션 부정확
- **원인**: position `[x,y,z]→[x,y,-z]`, quaternion `[x,y,z,w]→[-x,-y,z,w]` 변환이 하체에 완전히 적용되지 않음
- **영향**: `public/players/vlibras/`, `public/players/vlibras-v3/` (Sentence Player는 사전 변환 단계에서 해결됨)
- **참고**: `docs-source/claudedocs/technical-findings.md`

### 2. VLibras→SLMB 파이프라인 미완성
- 스켈레톤 매핑(84→46) 정의됨 (`tools/vlibras2slmb/data/skeleton_map.py`)
- end-to-end 검증 안됨, CASA 단어만 테스트됨

### 3. `asset_bundle.py` UnityPy API 드리프트
- **문제**: `tools/vlibras2slmb/parsing/asset_bundle.py`가 uppercase `kf.value.X/Y/Z/W` 속성을 사용하지만 UnityPy ≥ 1.25는 lowercase(`x/y/z/w`)로 변경됨
- **영향**: `batch/converter.py::convert_one()`이 `.bundle` 경로로 호출되면 실패. JSON 경로는 영향 없음
- **우회**: `tools/vlibras2slmb/batch/precompute_threejs.py`는 자체 lowercase 리더 `_read_unity_clip()`을 포함하므로 정상 동작
- **수정 필요**: `asset_bundle.py`를 lowercase로 마이그레이션하고 공용 리더로 통합 (P2 선행 작업)

### 4. Sentence Player 타임라인 seek 비활성화 (MVP)
- **문제**: M4 MVP 범위에서 timeline slider를 `disabled=true`로 고정
- **원인**: 글로벌 큐 시간 → 로컬 클립 시간 역산 + 이전 클립 stop/uncache 조합이 복잡
- **영향**: 재생 중 임의 지점 이동 불가 (Play/Pause/Stop/Loop는 정상)
- **우회**: P4에서 구현 예정

### 5. 스파이크 어휘 한정 (27 글로스)
- **문제**: VLibras 번역 결과 중 사전 변환된 27개만 재생 가능, 나머지는 `⚠️` 미싱 표시
- **현재 세트**: CASA, ESCOLA, AGUA, OLA, EU, VOCE, OBRIGADO, BOM, DIA, SIM, NAO, POR_FAVOR, AMIGO, AMIGA, TRABALHO, COMER, BEBER, NOME, GOSTAR, MUITO, FAMILIA, MORAR, QUERER, ESTUDAR, IR, TER, FALAR
- **우회**: P1 후속 작업에서 100개 수준으로 확장 예정
- **융합 토큰 폴백 적용됨**: VLibras가 `BOM_DIA` 같은 융합 토큰 반환 시 `_`로 split하여 개별 글로스로 재조회

### 6. Windows Python cp949 인코딩 (precompute 스크립트)
- **문제**: `precompute_threejs.py` 실행 시 비ASCII 글로스(`ÁGUA` 등) print에서 `UnicodeEncodeError`
- **우회**: `PYTHONIOENCODING=utf-8` 환경 변수 또는 스크립트 상단 `sys.stdout.reconfigure(encoding='utf-8')` 보강
- **수정 필요**: P1 후속 작업에서 스크립트에 reconfigure 추가

---

## 핵심 파일 참조

| 목적 | 파일 |
|---|---|
| 프로젝트 설정 | `CLAUDE.md` |
| ABNT 아바타 모델 | `public/avatars/abnt/avatarModel/model_external.gltf` |
| VLibras 아바타 | `public/avatars/vlibras/{padrao,casa,icaro}/export/*.glb` |
| CASA 애니메이션 | `public/animations/vlibras/CASA_full.json` |
| 사전 변환 번들 | `public/animations/vlibras/bundles/*.threejs.json` + `index.json` |
| ABNT 레퍼런스 BVH | `public/animations/abnt/avatarModel.bvh` |
| 스켈레톤 매핑 | `tools/vlibras2slmb/data/skeleton_map.py` |
| 좌표 변환 유틸 | `tools/vlibras2slmb/math_utils/coordinate.py` |
| **사전 변환기 (P1)** | `tools/vlibras2slmb/batch/precompute_threejs.py` |
| **Icaro bind pose** | `tools/vlibras2slmb/data/icaro_bind_pose.json` |
| **스파이크 어휘 목록** | `tools/vlibras2slmb/data/spike_glosses.txt` |
| **번역 API 스펙** | `docs-source/claudedocs/vlibras-translation-api.md` |
| **Sentence Player** | `public/players/sentence/index.html` |
| 기술 검증 결과 | `docs-source/claudedocs/technical-findings.md` |

---

## VLibras 참조 정보

- **번역 API**: `traducao2.vlibras.gov.br/translate`
- **사전 CDN**: `dicionario2.vlibras.gov.br/bundles`
- **아바타**: Icaro, Guga, Hosana (T-pose, 84본)

---

## Sentence Player 테스트 가이드

### 모션 파일 저장 위치

| 항목 | 경로 |
|---|---|
| **사전 변환 번들 디렉토리** | `public/animations/vlibras/bundles/` |
| 개별 글로스 파일 | `{GLOSS}.threejs.json` (Three.js KeyframeTrack JSON) |
| 인덱스 메타데이터 | `public/animations/vlibras/bundles/index.json` — `{raw, key, file, duration}` |
| 원본 (Unity AssetBundle) | `https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/<GLOSS>` |
| 배치 변환기 | `tools/vlibras2slmb/batch/precompute_threejs.py` |
| 어휘 목록 (재생성 입력) | `tools/vlibras2slmb/data/spike_glosses.txt` |
| Icaro bind pose (좌표 보정) | `tools/vlibras2slmb/data/icaro_bind_pose.json` |

- **로컬 실행**: `cd public && python -m http.server 8080` → `http://localhost:8080/players/sentence/`
- **배포 URL**: `https://sls-brazil-player.vercel.app/players/sentence/`
- **어휘 재생성**: `PYTHONIOENCODING=utf-8 python -m tools.vlibras2slmb.batch.precompute_threejs --gloss-list tools/vlibras2slmb/data/spike_glosses.txt --output-dir public/animations/vlibras/bundles`

### 사용 가능한 어휘 (27개)

- **명사**: CASA, ESCOLA, ÁGUA, OLÁ, AMIGO, AMIGA, TRABALHO, NOME, FAMÍLIA, DIA
- **대명사**: EU, VOCÊ
- **동사**: MORAR, QUERER, COMER, BEBER, ESTUDAR, IR, TER, FALAR, GOSTAR
- **형용사·부사·감탄사**: BOM, MUITO, SIM, NÃO, OBRIGADO, POR_FAVOR

### 테스트 문장 (VLibras API 실측)

아래 표의 "번역 결과"는 `POST https://traducao2.vlibras.gov.br/translate` 실측값입니다. VLibras 번역 엔진은 동일 표현도 맥락에 따라 다르게 글로스화하므로, 재실측 시 소폭 차이 가능.

#### 1) 기초 (1~2어)

| 입력 | 번역 결과 | 큐 | 설명 |
|---|---|---|---|
| `Casa` | `CASA` | 1/1 ✅ | 단일 글로스 기본 |
| `Olá` | `OLA` | 1/1 ✅ | 인사 |
| `Por favor` | `POR_FAVOR` | 1/1 ✅ | VLibras가 `_` 붙여 단일 글로스로 반환, 사전에 동일 키로 존재 |
| `Bom dia` | `BOM DIA` | 2/2 ✅ | 공백 분리로 2글로스 |
| `Olá casa` | `OLA CASA` | 2/2 ✅ | 2연속 재생 |
| `Bom amigo` | `BOM AMIGO` | 2/2 ✅ | 형용사+명사 |
| `Você amigo` | `VOCE AMIGO` | 2/2 ✅ | 대명사+명사 |
| `Trabalho bom` | `TRABALHO BOM` | 2/2 ✅ | 명사+형용사 |
| `Nome amigo` | `NOME AMIGO` | 2/2 ✅ | 명사 결합 |
| `Eu comer` | `EU COMER` | 2/2 ✅ | 대명사+동사 |

#### 2) 주어+동사+목적어 (2~3어)

| 입력 | 번역 결과 | 큐 | 비고 |
|---|---|---|---|
| `Eu morar casa` | `MORAR CASA` | 2/2 ✅ | VLibras가 `Eu` 드롭 |
| `Eu querer água` | `QUERER AGUA` | 2/2 ✅ | `Eu` 드롭 |
| `Eu estudar escola` | `ESTUDAR ESCOLA` | 2/2 ✅ | `Eu` 드롭 |
| `Eu ter amigo` | `TER AMIGO` | 2/2 ✅ | `Eu` 드롭 |
| `Eu beber água` | `EU BEBER AGUA` | 3/3 ✅ | `Eu` 유지, 3연속 재생 |
| `Eu ir escola` | `EU IR ESCOLA` | 3/3 ✅ | `Eu` 유지 |
| `Eu ter família` | `EU TER FAMILIA` | 3/3 ✅ | `Eu` 유지 |
| `Eu falar você` | `EU FALAR VOCE` | 3/3 ✅ | 3연속 재생 |

#### 3) 3~4어 (큐잉 + crossfade 확인)

| 입력 | 번역 결과 | 큐 | 총 duration (초) |
|---|---|---|---|
| `Sim bom dia` | `SIM BOM DIA` | 3/3 ✅ | ≈ 7.10 |
| `Casa escola não` | `CASA ESCOLA NAO` | 3/3 ✅ | ≈ 8.37 |

#### 4) 융합 토큰 폴백 검증 (`_` split)

| 입력 | 번역 결과 | 큐 처리 |
|---|---|---|
| `Obrigado bom dia` | `OBRIGADO&AGRADECIMENTO BOM_DIA` | `OBRIGADO&AGRADECIMENTO` ⚠️ 미싱 칩 + `BOM_DIA` 폴백 분해 → `BOM`+`DIA` 2연속 재생 (≈ 3.90s) |

#### 5) 알려진 특이 동작·엣지케이스 (참고)

| 입력 | 번역 결과 | 설명 |
|---|---|---|
| `Obrigado` (단독) | `OBRIGAR` | 단독일 때 동사 원형으로 변환. bundle에 `OBRIGAR`가 없어 미싱 처리 — `OBRIGADO`는 문장 속일 때 `OBRIGADO&AGRADECIMENTO` 형태로 반환 |
| `Eu gostar muito` | `GOSTAR` | VLibras가 전체 문장을 단일 글로스로 축약 (의미 압축) |
| `Família muito bom` | `FAMILIA BOM(+)` | `BOM(+)`은 VLibras 강도 수식자(`매우 좋은`). bundle에 해당 변형이 없어 `BOM(+)` 미싱 처리 |
| `Casa bonita` | `CASA BONITA` | `BONITA`가 어휘에 없음 — 어휘 확장 대상 |

### 회귀 테스트 권장 시퀀스

다음 5개 문장을 순서대로 입력하면 주요 기능을 빠르게 검증할 수 있습니다:

1. `Casa` — 단일 글로스 기본 재생 (M3 동작)
2. `Sim bom dia` — 3연속 재생 + 큐잉 + 전체 타임라인 progress (M4 동작)
3. `Obrigado bom dia` — 융합 토큰 `BOM_DIA` → `BOM`+`DIA` 폴백 + `OBRIGADO&AGRADECIMENTO` 미싱 칩 (M5-A 동작)
4. `Eu morar casa` — `Eu` 드롭 + 2연속 재생 (어휘 확장 커밋 검증)
5. `Casa bonita` — 미싱 글로스 경고 UI + 재번역 후 mixer 정리 확인 (M5-C 동작)

모델 전환(Padrao/CASA/Icaro)도 위 문장마다 테스트하면 아바타 스켈레톤 호환성이 확인됩니다.
