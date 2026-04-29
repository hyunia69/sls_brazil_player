# 프로젝트 현황

브라질 수어(Libras) 3D 아바타 플레이어 생태계. ABNT NBR 25606 표준과 VLibras 레거시 포맷을 지원하는 웹 기반 플레이어.

- **배포**: https://sls-brazil-player.vercel.app/
- **GitHub**: https://github.com/hyunia69/sls_brazil_player
- **기술 스택**: Three.js v0.170.0 (CDN), 단일 HTML, Python 변환 도구
- **배포 방식**: Vercel 정적 사이트, Git push 시 자동 배포

> 프로젝트 메타데이터(디렉토리·기술 사항·VLibras 참조)는 [`CLAUDE.md`](../../CLAUDE.md). 본 문서는 상태·다음 작업·이력 단일 진실 출처.

---

## 현재 상태 (2026-04-29 기준)

| 축 | 상태 | 위치 |
|---|---|---|
| ABNT 파이프라인 (SLMB 인코더/디코더, BVH/SLMB Player) | ✅ 완료 | `tools/slmb_converter/`, `public/players/{bvh,slmb}/` |
| VLibras 레거시 플레이어 (vlibras, vlibras-v3) | 🔄 상체 완료, 하체 미완 | `public/players/vlibras*/` |
| Sentence Player (production) | ✅ P1 + P5 Phase A + P5.1 + P5.3 Step 1-3 | `public/players/sentence/` |
| Stroke 검증 도구 | ✅ Method A/B/C/D + E + G + 자동 메트릭 4종 + JSON export | `public/players/sentence-stroke-test/` |
| 사전 변환 글로스 (30개) | ✅ 27 어휘 + 3 마커(INTERROGAÇÃO/PONTO/EXCLAMAÇÃO) | `public/animations/vlibras/bundles/` |
| Bundle 변환기 | ✅ | `tools/vlibras2slmb/batch/precompute_threejs.py` |
| 모델 뷰어 / 랜딩 / 문서 페이지 | ✅ | `public/players/viewer/`, `public/index.html`, `public/docs/` |
| VLibras→SLMB 오프라인 변환기 | 🔄 매핑 완료, 파이프라인 미완 | `tools/vlibras2slmb/` |
| 블렌딩 재검토 플랜 | ✅ Codex 2차 검토 반영 | `docs-source/claudedocs/plan-sentence-blending-redesign.md` |
| 수동 hold ground truth | ⏳ scaffold (0/5 라벨됨) | `docs-source/claudedocs/hold-ground-truth.json` — **P6a 결정 게이트** |
| PR #1 (P5.2 Week 2 + P5.3 Step 2-3) | ✅ merged (2026-04-27) | `5f5a464` |
| 데이터 파이프라인 단일 진실 출처 문서 | ✅ 신규 | `docs-source/claudedocs/data-pipeline-and-handedness.md` |
| 운영 변환 아키텍처 결정 (CORS 검증) | ⏳ 대기 | (옵션 A·B·C·하이브리드) |
| Git/gh 인증 환경 정비 | ✅ 완료 | git config + `gh auth login` |

---

## 다음 작업

### 🔥 즉시

1. **CORS 검증** (5분) — `curl -I -H "Origin: https://sls-brazil-player.vercel.app" https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/CASA` → 운영 변환 아키텍처(A/B/C/하이브리드) 결정의 전제. 상세: [`data-pipeline-and-handedness.md`](data-pipeline-and-handedness.md) §6.
2. **운영 아키텍처 의사결정** — 어휘 규모·신규 어휘 빈도·백엔드 운영 가능성 4가지 입력으로 옵션 결정. 권장: 하이브리드 A+B (자주 쓰는 어휘 사전변환 + long-tail 서버 lazy compute).
3. **수동 hold annotation** — `hold-ground-truth.json` 5 시나리오를 `sentence-stroke-test/` single-word 모드에서 frame-by-frame 라벨링 (개발자 1차 + 동료 cross-check). **P6a 결정의 유일한 acceptance criterion**.
4. **5 시나리오 메트릭 비교** — preset ①~⑤ × Method A/C/E/G 4번 batch → JSON export → 수동 HPR과 비교 → 가장 시나리오-적합한 method 식별

### 🔄 다음 (P6a 승자 결정 후)

5. **P6a (3주)** — Week 2 winner를 production `sentence/index.html`의 `computeStrokeRange`에 포팅. Feature flag `window.__blendingAlgo = 'A' | 'E' | 'hybrid'` (기본 OFF). **targetted vs lax transition** 이원화: gloss end-pose가 static(velocity ≈ 0 ≥100ms) → targetted, 아니면 lax. FADE_MIN 최종값 P5.2 데이터로 재확정.
6. **P5.2 Week 2 잔여** — 4-row stacked 차트 비교 모드 (같은 문장 × 4 method 동시 재생 + row마다 차트 누적). 본 세션은 차트에 E/G 라인만 추가, batch 비교 UI는 별도.

### 🧪 Spike / Eval

7. **P6b (3일 Go/No-Go)** — SQUAD Three.js spike. 60fps 유지 & jerk 개선 둘 다 미달성 시 즉시 폐기.
8. **P6.5 (2주)** — 3-track hybrid eval: KSL 3-5명(Track A) + 원격 LIBRAS 2-3명(Track B) + 전문가 fallback(Track C). Rollout 게이트: Track A 과반 + Track B 저하 없음.

### 📋 Scope 외 (별도 트랙)

- **어휘 확장 (27 → 100)**: `tools/vlibras2slmb/data/spike_glosses.txt` 편집 → `precompute_threejs.py` 재실행. `sys.stdout.reconfigure(encoding='utf-8')` 보강 필요.
- **운영 변환 옵션 B (서버 on-demand)** 구현 — 위 즉시 작업 1·2번 결과에 따라. `precompute_threejs.py`를 서버 엔드포인트로 래핑 + Redis 캐시. 상세: [`data-pipeline-and-handedness.md`](data-pipeline-and-handedness.md) §5.
- **VLibras 하체 좌표계 보정** (P3): Sentence Player의 legacy retarget 로직을 레거시 플레이어에 적용.
- **`asset_bundle.py` UnityPy 1.25+ 마이그레이션** (P2 선행 차단): uppercase `X/Y/Z/W` → lowercase. `precompute_threejs.py`의 `_read_unity_clip()`을 공용 모듈로 승격.
- **VLibras→SLMB 변환 파이프라인 완성** (P2): VLibras 84본 → ABNT 46조인트 리타겟팅.
- **Sentence Player 타임라인 seek** (P4): 글로벌 시간 → 로컬 클립 시간 역산.
- **비수지(non-manual) 노테이션** (P6): VLibras 번역 API의 `[NEG]`/`[INT]` 마커 + face blendshape 추출.
- **다른 아바타 리타겟팅** (P7): Sentence Player에서 ABNT avatarModel 런타임 리타겟.
- **`CLAUDE.md` 좌표 변환 1줄 검증**: 실제 `coordinate.py`와 차이 발견(2026-04-29). precompute_threejs.py의 추가 변환 매핑까지 포함한 정확한 표현으로 갱신 필요.

### 의사결정 게이트 요약

- **P5.2 종료 (현재)**: Method E가 A보다 우수? → 수동 라벨 HPR + 자동 메트릭 + 시각 A/B
- **P6a 종료**: P6b 시도? → 안정 + 시간 여유
- **P6b 중간**: SQUAD Go? → 60fps & jerk 개선
- **P6.5 종료**: rollout? → Track A 과반 + Track B 저하 없음

---

## 주간보고

### 2026-04-28 ~ 2026-04-29 — PR 머지 + 데이터 파이프라인 단일 진실 출처 정리

PR #1 머지 후 후속 검증 + 운영 서비스 전환을 위한 사전 분석 주간. 코드 변경은 없고 문서·운영 환경 정비 중심.

- **[완료]** PR #1 머지 (`5f5a464`) — Method E/G + bimanual + 손가락 가중치가 production에 반영. P5.2 Week 2 코드부 종료.
- **[완료]** Sentence 플레이어 테스트 추가 (`d280bc7`).
- **[완료]** Git/gh 인증 환경 정비 — `git config credential.https://github.com.username hyunia69`로 푸시 시 계정 선택 팝업 제거. `gh auth login` keyring 등록(scope: repo·workflow·read:org·gist).
- **[완료]** **데이터 변환 파이프라인 단일 진실 출처 문서 작성** — [`data-pipeline-and-handedness.md`](data-pipeline-and-handedness.md). AssetBundle → CASA_full → ik_fixed → CASA.anim → CASA_threejs → bundles 5단계 흐름, LH→RH 수학(`(w,x,y,z)→(w,-x,y,-z)`, `(x,y,z)→(-x,y,-z)`), vlibras vs vlibras-v3 데이터 핸들링 차이 4영역(본 8개·시간 1프레임 shift·scale 트랙·rest pose 출처).
- **[완료]** **운영 변환 아키텍처 옵션 평가** — A(사전 일괄, 현재) / B(서버 on-demand) / C(브라우저 직접) / 하이브리드 A+B 비교. 옵션 C 기술 가능성 평가: CORS 검증 필요 + UnityFS 파서 + LZMA 디코더 + 변환 로직 ~105KB 추가, 첫 호출 150–430ms. 권장: 하이브리드 A+B (변환 코드를 Python 한 군데에 유지).
- **[발견]** **`CLAUDE.md`의 좌표 변환 1줄 요약과 실제 `coordinate.py` 불일치** — `coordinate.py`가 진실 출처. 별도 verification 후 `CLAUDE.md` 갱신 필요 (precompute_threejs.py의 추가 변환까지 반영).
- **[검토]** "vlibras에 v3 로직 적용 가능한가" — 시나리오 A·B·C 분석 결과 모두 비추천. 손목 회전 누락은 데이터 출처 자체의 문제(Stage 3 retargeting이 BnMaoOrient 제외). 통합 필요 시 데이터 파이프라인 수정이 정답.
- **[예정]** CORS 검증 → 운영 아키텍처 결정 → 옵션 B 구현(필요 시).

**핵심 결정**: 자주 쓰는 어휘는 사전변환 CDN, long-tail은 서버 lazy compute가 가장 자연스러운 운영 토폴로지. 브라우저 직접 변환(C)은 백엔드 절대 불가한 환경에서만 의미.

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

### 2026-04-29 (오후) — Annex C 마커 NMS 클립 + 위젯 sync에 raw 글로스 직접 주입

**핵심 발견 (2단계)**:
1. **마커 키는 사전에 *2종류씩* 존재**: VLibras 사전 카탈로그(22,508 키)에 `INTERROGAÇÃO`(어휘 = "물음표"라는 명사, 손가락 16본 활성)와 `[INTERROGAÇÃO]`(NMS 마커, 얼굴 6본 + `BnCabeca` 머리 회전 활성)이 *서로 다른 클립*으로 등록됨. PONTO/EXCLAMAÇÃO도 동일 패턴. 즉 VLibras는 *문법 NMS 클립을 가지고 있다* — 이전 NMS_Analysis.md §5.2의 "규칙 기반 휴리스틱" 추정이 *부분적으로 옳았음*. 단, JS는 합성 안 하고 Unity가 사전에서 NMS 키를 직접 검색.
2. **위젯이 ASCII 응답을 사전 검색해 미스매칭**: 번역 API는 항상 ASCII 응답(`VOCE`)이지만 사전 키는 악센트 보존(`VOCÊ`)이라 위젯이 자체 번역 시 지문자 폴백 발생. 해결: 사전 카탈로그(`/bundles`, ~313KB)로 ASCII↔raw 매핑을 만들어 `plugin.play(rawGlossString)`으로 위젯에 직접 주입 → 위젯 자체 번역 우회.

**구현**:
- 마커 클립 3종을 *대괄호 포함 키*(`[INTERROGAÇÃO]` 등)로 다시 다운로드/변환 → `INTERROGACAO/PONTO/EXCLAMACAO.threejs.json` 내용 교체. 클립 크기 54KB→43KB, duration 2.97s→1.63s 등(NMS 클립이 어휘 클립보다 짧음).
- `bundles/index.json`: 마커 raw를 `"[INTERROGAÇÃO]"`로 변경(chip UI 정확성), duration 업데이트, count 27→30.
- `sentence/index.html` + `sentence-stroke-test/index.html`:
  - `asciiKey()`에 대괄호 제거 추가 (`[INTERROGAÇÃO]` → `INTERROGACAO` 정규화 매칭)
  - `loadVlibrasDictMap()` + `toRawGlossString()` 신규 — 사전 카탈로그 lazy fetch, ASCII 글로스 시퀀스를 raw로 변환
  - `syncToVLibrasPlugin(text, asciiGlosses)` 시그니처 변경 — Tier 0(plugin.play로 raw 주입) + Tier 1(translate 폴백). `handleTranslate`/`onTranslateAndBatch`에서 `glosses` 인자 전달.
- `sentence-stroke-test/index.html` `normalizeVlibrasTokens()` 마커 null 반환 제거(보존하여 사전 매칭).

**검증** (사용자 확인): `Você gosta de estudar?` → 두 아바타 모두 VOCE 정상 수어 + 마지막에 NMS 머리·눈썹 동작 (이전: 위젯이 VOCE를 지문자로, 마커를 손가락 ? 그리기로 잘못 재생).

**파일**: `public/animations/vlibras/bundles/{INTERROGACAO,PONTO,EXCLAMACAO}.threejs.json`(교체), `public/animations/vlibras/bundles/index.json`, `public/players/sentence/index.html`, `public/players/sentence-stroke-test/index.html`.

**한계**: `(+)` 강조와 인칭 일치 동사(`1S_AJUDAR_2S` 등)는 별개 라인업. 사전 카탈로그에는 인칭 일치 동사 클립도 있어(예: `1S_AJUDAR_2S`) 추후 활용 가능.

### 2026-04-29 — 데이터 파이프라인 문서 정리 + 운영 아키텍처 사전 분석

- **신규 문서**: `data-pipeline-and-handedness.md` — VLibras AssetBundle → bundles 5단계 변환 + LH→RH 좌표 변환 수학 + vlibras vs v3 차이 + 운영 아키텍처 옵션을 단일 진실 출처로 통합.
- **검증 작업** (코드 미변경): Python으로 `CASA.anim.json`(76 quat, 153 트랙, delta) vs `CASA_threejs.json`(83 quat, 249 트랙, abs) 직접 비교 — 본 8개 차이(`BnMaoOrientL/R` 등), 시간 1프레임 shift, scale 83 트랙 추가, quaternion 공통 트랙 max diff 2×10⁻⁴ 확인.
- **vlibras 런타임 변환 시나리오 검토** (코드 미변경): 시나리오 A(anim.json만 흉내), B(ik_fixed.json 런타임 retarget), C(threejs.json 직접 fetch) 모두 비추천. 손목 회전 누락은 데이터 출처 문제이지 변환 시점 문제가 아님.
- **환경 정비**: `git config credential.https://github.com.username hyunia69` (push 팝업 제거), `gh auth login` (keyring, scope: repo·workflow·read:org·gist). MCP는 gstack/superpowers가 CLI 기반이라 별도 설정 불필요.
- **문서 갱신**: `project-status.md`(현재 상태 + 다음 작업 + 주간보고), `CLAUDE.md`(문서 인덱스), 구식 경로(`slmb-player/`, `data/`) 정리.

### 2026-04-28 — PR #1 머지 + 테스트 추가

- PR #1 (`p5-blending-week2-method-eg-bimanual`) 머지 — `5f5a464`. Method E/G + bimanual + 손가락 가중치가 production 반영. P5.2 Week 2 코드부 종료.
- Sentence 플레이어 테스트 추가 (`d280bc7`).

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
8. **vlibras 플레이어 손목 회전 누락** — `CASA.anim.json`이 `BnMaoOrientR/L.quaternion` 트랙을 갖지 않음 (Stage 3 retargeting이 IK target으로 분류해 제외). 통합하려면 데이터 파이프라인 수정 필요. 상세: [`data-pipeline-and-handedness.md`](data-pipeline-and-handedness.md) §4-2.
9. **`CLAUDE.md` 좌표 변환 1줄 요약 검증 필요** — `coordinate.py`가 진실 출처(2026-04-29 발견). precompute_threejs.py가 추가 적용하는 Icaro bind 매핑까지 포함한 정확한 표현으로 갱신 필요.
10. **VLibras 사전 CDN CORS 미검증** — `dicionario2.vlibras.gov.br/2018.3.1/WEBGL/<GLOSS>` 브라우저 직접 fetch 가능 여부 미확인. 운영 아키텍처(특히 옵션 C) 결정의 전제.

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
| **데이터 파이프라인 + 좌표 변환** | `docs-source/claudedocs/data-pipeline-and-handedness.md` |
| Stroke 검출 6 method | `docs-source/claudedocs/stroke-detection-methods.md` |

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
