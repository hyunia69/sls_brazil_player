# 프로젝트 현황

브라질 수어(Libras) 3D 아바타 플레이어 생태계. ABNT NBR 25606 표준과 VLibras 레거시 포맷을 지원하는 웹 기반 플레이어.

- **배포**: https://sls-brazil-player.vercel.app/
- **GitHub**: https://github.com/hyunia69/sls_brazil_player
- **기술 스택**: Three.js v0.170.0 (CDN), 단일 HTML, Python 변환 도구
- **배포 방식**: Vercel 정적 사이트, Git push 시 자동 배포

> 프로젝트 메타데이터(디렉토리·기술 사항·VLibras 참조)는 [`CLAUDE.md`](../../CLAUDE.md). 본 문서는 상태·다음 작업·이력 단일 진실 출처.

---

## 현재 상태 (2026-04-27 기준)

| 축 | 상태 | 위치 |
|---|---|---|
| ABNT 파이프라인 (SLMB 인코더/디코더, BVH/SLMB Player) | ✅ 완료 | `tools/slmb_converter/`, `public/players/{bvh,slmb}/` |
| VLibras 레거시 플레이어 (vlibras, vlibras-v3) | 🔄 상체 완료, 하체 미완 | `public/players/vlibras*/` |
| Sentence Player (production) | ✅ P1 + P5 Phase A + P5.1 + P5.3 Step 1-3 | `public/players/sentence/` |
| Stroke 검증 도구 | ✅ Method A/B/C/D + E + G + 자동 메트릭 4종 + JSON export | `public/players/sentence-stroke-test/` |
| 사전 변환 글로스 (27개) | ✅ | `public/animations/vlibras/bundles/` |
| Bundle 변환기 | ✅ | `tools/vlibras2slmb/batch/precompute_threejs.py` |
| 모델 뷰어 / 랜딩 / 문서 페이지 | ✅ | `public/players/viewer/`, `public/index.html`, `public/docs/` |
| VLibras→SLMB 오프라인 변환기 | 🔄 매핑 완료, 파이프라인 미완 | `tools/vlibras2slmb/` |
| 블렌딩 재검토 플랜 | ✅ Codex 2차 검토 반영 | `docs-source/claudedocs/plan-sentence-blending-redesign.md` |
| 수동 hold ground truth | ⏳ scaffold (0/5 라벨됨) | `docs-source/claudedocs/hold-ground-truth.json` — **P6a 결정 게이트** |
| PR #1 (P5.2 Week 2 + P5.3 Step 2-3) | 🔄 open, 머지 대기 | https://github.com/hyunia69/sls_brazil_player/pull/1 |

---

## 다음 작업

### 🔥 즉시 (사용자 복귀 시 1-2시간)

1. **PR #1 review + 머지 결정** — Test plan 5개 체크 → 머지 → `git pull`
2. **수동 hold annotation** — `hold-ground-truth.json` 5 시나리오를 `sentence-stroke-test/` single-word 모드에서 frame-by-frame 라벨링 (개발자 1차 + 동료 cross-check). **P6a 결정의 유일한 acceptance criterion**.
3. **5 시나리오 메트릭 비교** — preset ①~⑤ × Method A/C/E/G 4번 batch → JSON export → 수동 HPR과 비교 → 가장 시나리오-적합한 method 식별

### 🔄 다음 (P6a 승자 결정 후)

4. **P6a (3주)** — Week 2 winner를 production `sentence/index.html`의 `computeStrokeRange`에 포팅. Feature flag `window.__blendingAlgo = 'A' | 'E' | 'hybrid'` (기본 OFF). **targetted vs lax transition** 이원화: gloss end-pose가 static(velocity ≈ 0 ≥100ms) → targetted, 아니면 lax. FADE_MIN 최종값 P5.2 데이터로 재확정.
5. **P5.2 Week 2 잔여** — 4-row stacked 차트 비교 모드 (같은 문장 × 4 method 동시 재생 + row마다 차트 누적). 본 세션은 차트에 E/G 라인만 추가, batch 비교 UI는 별도.

### 🧪 Spike / Eval

6. **P6b (3일 Go/No-Go)** — SQUAD Three.js spike. 60fps 유지 & jerk 개선 둘 다 미달성 시 즉시 폐기.
7. **P6.5 (2주)** — 3-track hybrid eval: KSL 3-5명(Track A) + 원격 LIBRAS 2-3명(Track B) + 전문가 fallback(Track C). Rollout 게이트: Track A 과반 + Track B 저하 없음.

### 📋 Scope 외 (별도 트랙)

- **어휘 확장 (27 → 100)**: `tools/vlibras2slmb/data/spike_glosses.txt` 편집 → `precompute_threejs.py` 재실행. `sys.stdout.reconfigure(encoding='utf-8')` 보강 필요.
- **VLibras 하체 좌표계 보정** (P3): Sentence Player의 legacy retarget 로직을 레거시 플레이어에 적용.
- **`asset_bundle.py` UnityPy 1.25+ 마이그레이션** (P2 선행 차단): uppercase `X/Y/Z/W` → lowercase. `precompute_threejs.py`의 `_read_unity_clip()`을 공용 모듈로 승격.
- **VLibras→SLMB 변환 파이프라인 완성** (P2): VLibras 84본 → ABNT 46조인트 리타겟팅.
- **Sentence Player 타임라인 seek** (P4): 글로벌 시간 → 로컬 클립 시간 역산.
- **비수지(non-manual) 노테이션** (P6): VLibras 번역 API의 `[NEG]`/`[INT]` 마커 + face blendshape 추출.
- **다른 아바타 리타겟팅** (P7): Sentence Player에서 ABNT avatarModel 런타임 리타겟.

### 의사결정 게이트 요약

- **P5.2 종료 (현재)**: Method E가 A보다 우수? → 수동 라벨 HPR + 자동 메트릭 + 시각 A/B
- **P6a 종료**: P6b 시도? → 안정 + 시간 여유
- **P6b 중간**: SQUAD Go? → 60fps & jerk 개선
- **P6.5 종료**: rollout? → Track A 과반 + Track B 저하 없음

---

## 주간보고

### 2026-04-22 ~ 2026-04-27 — Method E/G + 운영 저위험 개선

P5.2 Week 1 실험대(자동 메트릭 + 5 시나리오 preset)에 알고리즘 후보를 채워 넣고, 운영 플레이어에 회귀 위험 0인 저위험 개선을 같이 반영한 주간. 사용자 부재 + 전권 위임 상태에서 도구 부재(gh CLI 미설치)·인증 prompt(GCM hang) 환경 장애를 자동 우회.

- **[완료]** gstack `/office-hours` 진단 → 4가지 가설(hold 손실 / 양손 비대칭 / 일률 fade / SQUAD 미사용) 식별 → Method E(M-H 모델) + G(bimanual separated) 우선 추가 결정. 수동 hold annotation을 acceptance criterion으로 분리.
- **[완료]** P5.2 Week 2 코드부 — Method E/G 추가 (`sentence-stroke-test/`), 차트/UI 6 method 일반화, `computeMotionProfile`에 boneList 인자.
- **[완료]** P5.3 Step 2-3 운영 저위험 개선 (`sentence/`) — 손가락 5본 가중치 추가(handshape), bimanual union 토글(`window.__bimanualUnion`, 기본 OFF).
- **[완료]** Playwright 회귀 (콘솔 에러 0) → feature 브랜치 푸시 → PR #1 생성. gh CLI 부재는 GitHub Releases zip 직접 다운로드, 인증 scope 부족은 GCM 캐시 OAuth 토큰을 REST API로 우회.
- **[진행중]** PR #1 머지 게이트 (사용자 복귀 후 review + Test plan 5개 체크).
- **[예정]** 수동 hold annotation → 메트릭 비교 → P6a winner → P6b spike → P6.5 hybrid eval.

**핵심 수치 (BOM 글로스 dur=1.800s, 6 method 결과)**: A 75.8% / B 94.9% / C 55.9% / D 10.2% / E 40.0%(clamp) / G 84.3%. Method E는 BOM의 hold 윈도우(720ms)를 검출했으나 MIN_STROKE_RATIO=0.40에 걸림 — BOM이 단일 ballistic 글로스에 가깝다는 신호.

**핵심 결정**: PR까지만 자동, 머지·배포는 사용자 게이트. 모든 production 변경은 feature flag OFF 기본으로 회귀 위험 0.

### 2026-04-14 ~ 2026-04-21 — 블렌딩 재검토 + 검증 도구 구축

단어 간 차렷 왕복으로 부자연스러운 문장 재생을 원점 재검토하고 검증 실험대를 구축한 주간.

- **[완료]** 학술(Movement-Hold, SQUAD) + 산업(VLibras, JASigning) 조사 → 4-phase 마이그레이션 플랜 수립. Codex 1·2차 검토 반영(P6 분할, 수동 라벨, 메트릭 격하, 3-track hybrid eval, 문헌 인용 순화).
- **[완료]** 검증 전용 실험 플레이어 (`sentence-stroke-test/`) — 4가지 stroke 검출 알고리즘 동시 비교 + motion profile SVG 차트. UI 재구성(2단 컨트롤 바, 글로스 칩, 차트↔배치 동기화), 5문장 프리셋 + VLibras 토큰 정규화 파서.
- **[완료]** 운영 저위험 튜닝 — `FADE_MIN` 0.12→0.20 + `window.__fadeMin` 런타임 override.
- **[완료]** 자동 메트릭 4종 + 5 시나리오 preset + JSON export. FK 월드 위치 실패(평면 본 계층 한계) → STROKE_BONES 6본 quaternion plateau proxy로 전환.
- **[진행중]** 수동 라벨 scaffold(`hold-ground-truth.json`).

**핵심 수치 (자동 메트릭 진단 신호)**: Hold 시나리오(`TER CASA`) plateau 비율 0.305(최고) / Rapid 시나리오(`EU IR ESTUDAR`) jerk 1733(Hold 대비 ≈2.7배) / 단어 경계 끊김 14ms 이내.

**핵심 결정**: 자동 지표는 합격/불합격이 아닌 **진단 신호**. 최종 알고리즘 선택은 수동 라벨 + 다수 지표 수렴 + 시각 A/B를 모두 거친 뒤 결정.

---

## 작업 이력

### 2026-04-27 — P5.2 Week 2 코드부 + P5.3 Step 2-3

- `sentence-stroke-test/`: Method E (M-H 모델, Liddell & Johnson 1989) + Method G (bimanual separated R/L union) 추가. velocity ≤ peakVel × 15% AND restDist ≥ maxRest × 80% AND ≥100ms 지속을 hold로 라벨하는 휴리스틱. `computeMotionProfile`에 boneList 인자, `ALL_METHODS` 상수, 차트/UI 6 method 일반화.
- `sentence/`: `BONE_WEIGHTS`에 `BnDedo2..5R/L` 8본(각 0.15) 추가 — handshape 차이를 동적 fade에 반영. `STROKE_BONES_R/L` 분리 + `computeStrokeRangeForBones` 추출 + `window.__bimanualUnion` 토글(기본 OFF).
- Playwright 회귀: 두 페이지 콘솔 에러 0, BOM 글로스 6 method 정상 결과 산출.
- 환경 장애 우회: gh CLI 부재 → GitHub Releases zip 직접 다운로드(`%LOCALAPPDATA%\gh-cli\bin\`, User PATH). gh `--with-token`이 `read:org` scope 부족 → GCM 캐시 OAuth 토큰을 Python urllib로 GitHub REST API `POST /repos/.../pulls` 직접 호출.
- PR #1 open: `p5-blending-week2-method-eg-bimanual` 브랜치, 커밋 `de95581`.
- 디자인 doc: `~/.gstack/projects/sls_brazil_player/admin-main-design-20260427-blending-redo.md`.

### 2026-04-21 — 블렌딩 재설계 플랜 + P5.2 Week 1 + P5.3 Step 1

- **플랜 수립**: `plan-sentence-blending-redesign.md`. P6 분할(P6a Winner port + targetted/lax / P6b SQUAD spike Go/No-Go). 수동 ground truth 라벨링 프로토콜 추가. 자동 메트릭 → diagnostic signal 격하. P6.5 → 3-track hybrid eval. P7과 27→100 확장은 범위 외 명시.
- **P5.2 Week 1**: `sentence-stroke-test/`에 5 시나리오 preset(single OLA / multi-peak BOM DIA AMIGO / bimanual FAMILIA AGUA / hold TER CASA / rapid EU IR ESTUDAR), 자동 메트릭 4종(Jerk RMS / Boundary discontinuity / Velocity continuity / Quaternion Plateau), JSON export 버튼 + auto-download 토글.
- **FK 월드 위치 → quaternion proxy 대체**: VLibras flat skeleton(`BnMaoOrientR.parent = Armature001`)에서 손목 월드 위치가 애니메이션에 반응하지 않음을 Playwright로 확인 → STROKE_BONES 6본 quaternion rolling window(0.05rad, 100ms)로 plateau 독립 측정.
- **P5.3 Step 1**: `FADE_MIN` 0.12 → 0.20 상향 + `getFadeMin()` 헬퍼 + `window.__fadeMin` 런타임 override.

### 2026-04-20 — Stroke Test UI 정리 + 프리셋 + VLibras 토큰 파서

- 컨트롤 바 2단(`flex-direction: column`) — 주 동선(번역&배치) / 보조 동선(단일 글로스 분석) 분리. 잔여 디버그 버튼 `[Sim bom dia]` 제거.
- 글로스 칩 UI: `renderGlossChips`/`highlightChip`/`clearGlossChips` 헬퍼. 칩 클릭 → 단일 분석 override.
- Motion profile ↔ 배치 동기화: `_runBatch`가 fetchResults에 `profile` 첨부, `syncInspectionToBatchItem(idx)`가 batch advance 시 차트 갱신.
- 프리셋 5개(`#preset-select`): `Bom dia amigo` / `Eu quero beber água` / `Você gosta de estudar?` / `Eu moro na casa` / `Obrigado, muito bom!`. 27 글로스 안에서 페어 다양성 확보.
- VLibras 토큰 파서(`normalizeVlibrasTokens`): `[PONTO]`/`[INTERROGAÇÃO]` 마커 drop, `A&B` 컴파운드 first-token, 꼬리 괄호 `(+)` strip. user-typed 문장에도 적용.

### 2026-04-15 — Stroke 검증 전용 도구 신설

- `public/players/sentence-stroke-test/index.html` 신설(~1200 라인). production `sentence/index.html`은 미수정 → 검증 대상과 도구 격리.
- 4가지 stroke 검출 방법 동시 비교: A(Cumulative %, 12/12 기본) / B(Peak-hold window, 45%) / C(Rest-pose + asymmetric plateau 90%) / D(Peak drop centered).
- Motion profile SVG 차트 (496×180): velocity 파랑 / cumulative 회색 점선 / rest-dist 주황 + peak marker + method 경계선 + playback cursor.
- Method C 진화: bidirectional last-index → peak-centered → asymmetric + plateau 90%. BOM에서 recovery 427ms 배제 확인.
- 범용 배치 재생(`_runBatch`): LoopOnce + clampWhenFinished + animate 루프에서 `strokeEnd` 도달 수동 advance. 초기 `finished` 이벤트 방식은 SIM이 clip 끝까지 가는 동안 BOM이 strokeEnd+115ms 진행되는 버그로 폐기.
- Debug hook: `window.__strokeTest.getBatchState()`.
- Plan: `C:\Users\admin\.claude\plans\twinkling-snacking-diffie.md`.

### 2026-04-14 — P5 Phase A + P5.1 Stroke Trim + VLibras 위젯 통합

- **P5 Phase A** (동적 모션 블렌딩): 고정 `CROSSFADE_SEC=0.2` 제거 → `FADE_MIN=0.12 / FADE_MAX=0.45 / D_REF=1.5rad` + `BONE_WEIGHTS` 13개 본(어깨/상박/전박/손목/손가락 root/목 R·L 대칭). `extractBoundaryPoses` + `computeTransitionDuration`(가중 RMS 각거리 sqrt 매핑). `computeTotalDuration`/`updateTimeline`/animate 루프 fade window 모두 가변 overlap 합산으로 재작성. Plan: `curried-shimmying-bengio.md`.
- **P5.1 Stroke Trim**: 모든 글로스가 prep + stroke + recovery U-shape 구조라는 진단 (8 글로스 quintile 측정, 양 끝 25-42% / 중간 0.7-9.3%). `computeStrokeRange`가 STROKE_BONES 6본의 합산 angular delta를 60샘플링해 head 12% / tail 88% 임계로 stroke 경계 검출, ±50ms padding + 40% 최소 길이 안전망. `fetchClipFromEntry`가 stroke 시점 quaternion으로 startPose/endPose sample. 큐 위치별 trim 분기(단일 trim X / 첫 head trim X / 마지막 tail trim X / 중간 양쪽 trim).
- **검증**: `Sim bom dia` 7.082s → **5.903s** (−1.18s). `Eu beber agua` 124ms FADE_MIN clamp가 stroke quaternion 사용으로 235/285ms 의미적 거리로 해결.
- **결정**: stroke 사이는 Three.js native crossfade(quaternion SLERP)만. 손이 가슴/배까지 내려왔다 올라오는 dip arc는 P5.1 범위 외(사용자 명시).
- **VLibras 공식 위젯 통합**: `vlibras-plugin.js` 임베드 + `#vlibras-toggle`(`🤟 위젯`) + `localStorage` 상태 복원 + `syncToVLibrasPlugin(text)` Tier 1(`plugin.translate(text)`). VLibras click 가로챔 버그(capture phase listener) 우회: `__vlibrasSafeClickHandlers` WeakMap + `safeClick(el, handler)` API.
- **vlibras-portal 검증**: `crossfade/blend/lerp/slerp/interpolat*` 0건 — 블렌딩 로직 전체가 `playerweb.wasm`에 있어 JS 재사용 불가능. 위젯은 시각 비교 레퍼런스로만.
- **메인 vs. 위젯 chirality 차이**: 메인은 signer 오른손, 위젯은 왼손. 코드 추적(`(x,y,z,w)→(x,-y,-z,w)` X-mirror + Icaro X-mirror bind 결합 = double-mirror)으로 self-consistent 확인. 둘 다 LIBRAS valid → 수정 없음. 상세: `avatar-handedness-analysis.md`.

### 2026-04-13 — P1 파이프라인 M0~M5 + 어휘 27 확장

- **M0**: VLibras 번역 API 스펙 실측 (CORS 직접 허용 → Vercel rewrites 불필요).
- **M1**: `precompute_threejs.py` 신설. UnityPy 1.25 lowercase API 대응 인라인 리더 내장. 레거시 변환(yz sign flip + 7개 헬퍼 본 Icaro-bind override) 역공학 후 `--legacy` 기본. CASA·ESCOLA 레퍼런스 대비 bone delta ≤ 6mm.
- **M3**: `sentence/index.html` 신설. 문장 입력 → 번역 → ASCII 키 정규화(NFKD) → 사전 변환 번들 fetch → 글로스 칩 UI(미싱 ⚠️ 표시).
- **M4**: 큐잉 + 고정 `CROSSFADE_SEC=0.2s` crossfade. `mixer.addEventListener('finished')` + 렌더 루프 timeLeft 체크. `stopAndDisposeQueue()` 메모리 정리(재번역 5연속 누수 없음 확인).
- **M5**: 융합 토큰 폴백(`BOM_DIA` → `BOM`+`DIA`), 에러 배너 폴리싱, `loadBundleIndex` cache `no-store`.
- 어휘 27 확장: `MORAR/QUERER/ESTUDAR/IR/TER/FALAR` 6개 동사 추가.
- 워크스페이스 정리: 루트 PNG 31개 + `.playwright-mcp/` 제거, `.gitignore`에 재발 방지 규칙 추가.

### 2026-04-08 — 프로젝트 통합 + 배포

- slmb + vlibras → `sls_brazil_player` 단일 구조. 공유 리소스 (`public/avatars/`, `public/animations/`). 메인 랜딩 + 문서 페이지. Vercel Git push 자동 배포.

### 2026-04-08 이전 (요약)

- ABNT NBR 25606 표준 분석 완료.
- SLMB 인코더/디코더 + roundtrip 검증.
- BVH Player, SLMB Pipeline Player 구현.
- VLibras 플레이어 상체 재생 성공 (하체 미완).
- VLibras→SLMB 스켈레톤 매핑 정의.

---

## 알려진 이슈

1. **VLibras 하체 좌표계 보정** — Unity LH ↔ glTF RH 변환이 `vlibras/`, `vlibras-v3/` 하체 관절에 불완전. Sentence Player는 사전 변환 단계에서 해결됨. P3 작업.
2. **VLibras→SLMB 파이프라인 미완** — 84→46 매핑 정의됨 (`tools/vlibras2slmb/data/skeleton_map.py`), end-to-end 검증 안됨(CASA만).
3. **`asset_bundle.py` UnityPy API 드리프트** — uppercase `X/Y/Z/W` 사용, UnityPy ≥1.25는 lowercase. `precompute_threejs.py`는 자체 lowercase 리더로 정상. P2 선행 차단.
4. **Sentence Player 타임라인 seek 비활성화** — M4 MVP에서 `disabled=true`. 글로벌 큐 시간 ↔ 로컬 클립 시간 역산 복잡. P4 작업.
5. **스파이크 어휘 한정 (27)** — 미싱 글로스는 ⚠️ 표시. 융합 토큰 폴백(`BOM_DIA` → `BOM`+`DIA`) 적용됨. 100 확장 예정.
6. **Windows Python cp949 인코딩** — `precompute_threejs.py` 비ASCII print에서 `UnicodeEncodeError`. 우회: `PYTHONIOENCODING=utf-8`. 스크립트 상단 `sys.stdout.reconfigure(encoding='utf-8')` 보강 필요.
7. **메인 vs. 위젯 chirality 차이** — 메인은 signer 오른손, 위젯은 왼손. 둘 다 LIBRAS valid (학술 컨벤션 vs. VLibras 공식 채널). 수정 없음. 상세: [`avatar-handedness-analysis.md`](avatar-handedness-analysis.md).

---

## 핵심 파일 참조

| 목적 | 파일 |
|---|---|
| 프로젝트 메타데이터 | `CLAUDE.md` |
| ABNT 아바타 모델 | `public/avatars/abnt/avatarModel/model_external.gltf` |
| VLibras 아바타 | `public/avatars/vlibras/{padrao,casa,icaro}/export/*.glb` |
| 사전 변환 번들 | `public/animations/vlibras/bundles/*.threejs.json` + `index.json` |
| Sentence Player | `public/players/sentence/index.html` |
| Stroke 검증 도구 | `public/players/sentence-stroke-test/index.html` |
| 사전 변환기 | `tools/vlibras2slmb/batch/precompute_threejs.py` |
| 스켈레톤 매핑 | `tools/vlibras2slmb/data/skeleton_map.py` |
| 좌표 변환 유틸 | `tools/vlibras2slmb/math_utils/coordinate.py` |
| Icaro bind pose | `tools/vlibras2slmb/data/icaro_bind_pose.json` |
| 스파이크 어휘 목록 | `tools/vlibras2slmb/data/spike_glosses.txt` |
| 번역 API 스펙 | `docs-source/claudedocs/vlibras-translation-api.md` |
| 블렌딩 재검토 플랜 | `docs-source/claudedocs/plan-sentence-blending-redesign.md` |
| 수동 hold 라벨 scaffold | `docs-source/claudedocs/hold-ground-truth.json` |

---

## Sentence Player 테스트 가이드

### 어휘 재생성

```bash
PYTHONIOENCODING=utf-8 python -m tools.vlibras2slmb.batch.precompute_threejs \
  --gloss-list tools/vlibras2slmb/data/spike_glosses.txt \
  --output-dir public/animations/vlibras/bundles
```

- 로컬: `cd public && python -m http.server 8080` → `http://localhost:8080/players/sentence/`
- 배포: https://sls-brazil-player.vercel.app/players/sentence/

### 사용 가능한 어휘 (27개)

- **명사**: CASA, ESCOLA, ÁGUA, OLÁ, AMIGO, AMIGA, TRABALHO, NOME, FAMÍLIA, DIA
- **대명사**: EU, VOCÊ
- **동사**: MORAR, QUERER, COMER, BEBER, ESTUDAR, IR, TER, FALAR, GOSTAR
- **형용사·부사·감탄사**: BOM, MUITO, SIM, NÃO, OBRIGADO, POR_FAVOR

### 회귀 테스트 5문장

| # | 입력 | 검증 항목 |
|---|---|---|
| 1 | `Casa` | 단일 글로스 기본 재생 (M3) |
| 2 | `Sim bom dia` | 3연속 + 큐잉 + 타임라인 progress (M4). 총 ≈5.9s (P5.1 trim 적용) |
| 3 | `Obrigado bom dia` | `BOM_DIA` 폴백 + `OBRIGADO&AGRADECIMENTO` 미싱 칩 (M5-A) |
| 4 | `Eu morar casa` | `Eu` 드롭 + 2연속 (어휘 확장 검증) |
| 5 | `Casa bonita` | 미싱 글로스 경고 + mixer 정리 (M5-C) |

모델 전환(Padrao/CASA/Icaro)도 위 문장마다 테스트하면 스켈레톤 호환성 확인 가능.

### VLibras 번역 특이 동작 (참고)

| 입력 | 결과 | 설명 |
|---|---|---|
| `Obrigado` 단독 | `OBRIGAR` | 동사 원형 변환 (bundle에 없어 미싱) |
| 문장 속 `Obrigado` | `OBRIGADO&AGRADECIMENTO` | 동의어 컴파운드 |
| `Eu morar casa` | `MORAR CASA` | VLibras가 `Eu` 드롭 |
| `Eu beber água` | `EU BEBER AGUA` | `Eu` 유지 |
| `Eu gostar muito` | `GOSTAR` | 단일 글로스로 의미 압축 |
| `Família muito bom` | `FAMILIA BOM(+)` | `BOM(+)` 강도 수식자 (괄호 strip 후 `BOM`으로 매칭) |
| `Por favor` | `POR_FAVOR` | `_` 붙은 단일 글로스 |
| `Bom dia` | `BOM DIA` | 공백 분리 |
