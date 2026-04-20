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
| **Sentence Player ↔ VLibras 공식 위젯 sync** | ✅ 완료 (2026-04-14) | `public/players/sentence/index.html` (`#vlibras-toggle` + `syncToVLibrasPlugin`) |
| **Sentence Player 동적 모션 블렌딩 (P5 Phase A)** | ✅ 완료 (2026-04-14) | `public/players/sentence/index.html` (`computeTransitionDuration`, `BONE_WEIGHTS`) |
| **Sentence Player Stroke Trim (P5.1)** | ✅ 완료 (2026-04-14) | `public/players/sentence/index.html` (`computeStrokeRange`, `extractPoseAt`, `effectiveStart/End`, `STROKE_*`) |
| **Stroke Verification Tool** | ✅ 완료 (2026-04-15), UI 정리 + profile 동기화 (2026-04-20) | `public/players/sentence-stroke-test/index.html` (4-method 비교 + motion profile 차트 + 배치 crossfade + 글로스 칩 UI + 배치 sync) |
| **Bundle 사전 변환기** | ✅ 완료 (27 글로스) | `tools/vlibras2slmb/batch/precompute_threejs.py` |
| Model Viewer | ✅ 완료 | `public/players/viewer/` |
| VLibras→SLMB 변환기 | 🔄 매핑 완료, 파이프라인 미완 | `tools/vlibras2slmb/` |
| 랜딩 페이지 | ✅ 완료 | `public/index.html` |
| 문서 페이지 | ✅ 완료 | `public/docs/` |
| Vercel 배포 | ✅ 완료 | Git push 자동 배포 |

---

## 오늘의 작업 중점 (2026-04-20)

**집중 대상**: `public/players/sentence-stroke-test/` (http://localhost:8080/players/sentence-stroke-test/)

**목표**: 모션 블렌딩 전략의 근본 재검토. 현행(stroke trim + crossfade — P5.1 production은 Method A, 검증 도구는 Method C 권장)이 적절한지 원점에서 평가하고, 대안을 탐색한다.

**핵심 질문**
1. **Stroke 기반 단어 연결이 옳은 방향인가?** prep/recovery를 잘라내면 차렷 왕복 dead time은 줄지만, 각 글로스의 자연스러운 리듬(수어 고유 accent/beat, hold, 방향성)이 훼손될 가능성. 시각 검증이 필요하다.
2. **검토할 대안**
   - **(A) 현행**: stroke trim + Three.js native crossfade (Method A/B/C/D 비교)
   - **(B) Full clip + smart crossfade**: 이전 글로스 recovery와 다음 글로스 prep을 겹쳐 recovery가 prep에 자연스럽게 녹아들게
   - **(C) Hand-trajectory 보간**: 글로스 사이 손목 world position을 Cubic Bezier/Catmull-Rom으로 직접 보간, 2-bone IK로 팔꿈치 해석. "차렷 미하강"을 기하학적으로 보장
   - **(D) Hold plateau 브리지**: stroke 종점에서 손을 짧게 hold(수어 자연 hold 구간)한 뒤 다음 prep으로 전환
3. **P5.2(Method C production 적용 결정) 진행 전에 전제부터 재점검**

**세션 계획**
1. `sentence-stroke-test/`에서 다양한 글로스(CASA/ESCOLA/AGUA/VOCE/AMIGO/TRABALHO + SIM/BOM/DIA) × Method A/B/C/D 시각 비교
2. 스파이크 문장 5개 이상 배치 재생 육안 평가 — stroke 연결의 자연스러움, 글로스 accent 보존도, 손 궤적 연속성
3. 대안 B/C/D 중 실험 가치가 있는 방향 식별 → 검증 도구에 실험 분기 추가할지 결정
4. 결론에 따라 P5.2 진행/보류/재정의, 필요 시 P5 Phase B 재설계

**산출물**
- 검증 관찰 요약 → 작업 이력 `### 2026-04-20` 추가
- Stroke 전략 유지/변경/보강 결정
- 결정 반영한 "다음 세션 작업" 재배열

**진행 상황 (2026-04-20)**
- ✅ **UI 정리 완료**: `sentence-stroke-test/index.html` 2단 컨트롤 + "번역 & 배치" 주 동선 + 단일 글로스 분석 보조 동선, "Sim bom dia" 하드코딩 버튼 제거
- ✅ **Motion profile 동기화 완료**: 배치 진행에 따라 현재 재생 글로스의 profile을 자동 표시, 글로스 칩 UI 추가 (칩 클릭 시 단일 분석으로 override)
- ⏳ **평가 남음**: 다양한 글로스(CASA/ESCOLA/AGUA/VOCE/AMIGO/TRABALHO 등) × Method A/B/C/D 시각 비교, 배치 5문장 육안 평가, 대안 B/C/D 검토

---

## 다음 세션 작업

### P1-후속: 어휘 확장 (27 → 100)
- **목표**: 자주 쓰이는 명사·동사·대명사·부사 100개 수준으로 확장
- **진입점**: `tools/vlibras2slmb/data/spike_glosses.txt` 편집 → `PYTHONIOENCODING=utf-8 python -m tools.vlibras2slmb.batch.precompute_threejs --gloss-list tools/vlibras2slmb/data/spike_glosses.txt --output-dir public/animations/vlibras/bundles` 재실행
- **검증**: `project-status.md` 하단 테스트 가이드의 회귀 5문장 + 추가 10문장으로 리그레션 확인
- **부수 작업**: `precompute_threejs.py` 상단에 `sys.stdout.reconfigure(encoding='utf-8')` 추가 (Windows cp949 이슈 근본 해결)

### P2: SLMB 아바타에 VLibras 애니메이션 적용
- **선행 차단**: `tools/vlibras2slmb/parsing/asset_bundle.py` UnityPy 1.25+ 마이그레이션 (uppercase `X/Y/Z/W` → lowercase `x/y/z/w`). `precompute_threejs.py`의 인라인 리더 `_read_unity_clip()`를 공용 모듈로 승격
- **본 작업**: VLibras 84본 → ABNT 46조인트 리타겟팅
- **변환 흐름**: CASA (VLibras) → vlibras2slmb → `.slmb.xz` → decode → JSON → SLMB Pipeline Player

### P3: VLibras 레거시 플레이어 하체 좌표계 보정
- **문제**: `public/players/vlibras/`, `public/players/vlibras-v3/`에서 Unity LH → glTF RH 변환이 하체 관절에 불완전
- **접근**: Sentence Player에서 성공한 legacy retarget(yz sign flip + Icaro bind pose) 로직을 레거시 플레이어 런타임에도 적용하거나, 레거시 플레이어를 Sentence Player 방식으로 통합

### P4: Sentence Player 타임라인 seek 활성화
- **문제**: M4 MVP에서 timeline slider `disabled=true`
- **구현**: 글로벌 시간 → 로컬 클립 시간 역산, 이전 클립 `stop()`/`uncacheAction()`, 목표 클립 `action.time` 설정, `mixer.update(0)`으로 포즈 반영

### P5.2: Method C asymmetric을 sentence/index.html production에 적용 결정
- **배경**: P5.1이 Method A(Cumulative 12%) 기반으로 출시됐으나 사용자가 BOM 배치 재생에서 "손이 차렷까지 내려간다"고 보고. `sentence-stroke-test`에서 4개 방법 비교 결과, Method C(asymmetric prep + hold plateau 90%)가 recovery를 확실히 배제함을 확인(BOM strokeEnd 1.597→1.190, SIM 3.062→2.478, DIA 2.055→1.364)
- **결정 사항**: `sentence/index.html`의 `computeStrokeRange`를 Method C로 교체할지, 두 방법을 선택 가능하게 할지 판단. Method C의 PLATEAU_RATIO(0.90) 고정값을 노출할지 여부
- **영향 범위**: `fetchClipFromEntry`가 startPose/endPose sample 시점에도 strokeStart/strokeEnd 사용 → boundary pose 측정값 변화 → `computeTransitionDuration` fade sec 재계산 → 기존 5케이스 회귀 결과(Sim bom dia 5.903s 등) 재측정 필요
- **검증 방법**: 동일 문장을 sentence/index.html 기존 버전과 C 적용 버전으로 병렬 재생 → 시각 비교 + Playwright duration 측정 비교
- **선행**: `sentence-stroke-test`에서 SIM/BOM/DIA 외 다양한 글로스(CASA, ESCOLA, AGUA, VOCE, AMIGO, TRABALHO 등)에 대해 Method C 결과 육안 검증

### P5: 모션 블렌딩 — 글로스 간 자연스러운 연결 [✅ Phase A + P5.1 완료 (2026-04-14)]
- **Phase A (출시)**: 글로스 경계 포즈 차이에 비례하는 동적 crossfade 길이. `computeTransitionDuration` + `BONE_WEIGHTS` 13개 본 가중 RMS 각거리, sqrt 곡선으로 [FADE_MIN 0.12s, FADE_MAX 0.45s] 매핑. `computeTotalDuration`과 `updateTimeline`도 가변 overlap 합산으로 재작성. Plan: `C:\Users\admin\.claude\plans\curried-shimmying-bengio.md`
- **P5.1 Stroke Trim (출시)**: 클립이 prep(차렷→손) + stroke(핵심) + recovery(손→차렷) 구조라는 진단 기반. `computeStrokeRange`가 활성 팔 본(`BnBracoR/L`, `BnAntBracoR/L`, `BnMaoOrientR/L`)의 누적 angular delta를 60샘플링해서 head/tail 12% 임계로 stroke 경계 검출, ±50ms padding + 40% 최소 길이 안전망 적용. `fetchClipFromEntry`가 stroke 시점의 quaternion으로 `startPose`/`endPose`를 sample(차렷이 아닌 의미적 포즈). `rebuildActionsForCurrentModel`에 큐 위치별 `effectiveStart/effectiveEnd` 분기: 단일 글로스 = trim X, 첫 글로스 = head trim X(자체 prep로 손 올림), 마지막 글로스 = tail trim X(자체 recovery로 차렷 복귀), 중간 = 양쪽 trim. animate 루프의 fade window는 `effectiveEnd - action.time` 기준, `next.action.time = next.effectiveStart`. `updateTimeline` elapsed도 effective 길이 합산.
- **Playwright 검증 (P5.1 결과)**:
  - `Sim bom dia` → SIM[0.00→3.06/3.40s,266ms] | BOM[0.23→1.60/1.80s,274ms] | DIA[0.28→2.30/2.30s], total **5.903s** (baseline 7.082s, **−1.18s**)
  - `Eu beber agua` → EU[0.00→1.69/1.93s,235ms] | BEBER[0.31→1.96/2.23s,285ms] | AGUA[0.37→3.80/3.80s] (P5 Phase A에서 124ms FADE_MIN clamp 되던 문제가 stroke 시점 quaternion 사용으로 235/285ms 의미적 거리로 해결됨)
  - `Olá casa` → OLÁ[0.00→2.21/2.57s,274ms] | CASA[0.30→2.47/2.47s] (총 ~4.10s)
  - `Casa escola não` → CASA[0.00→2.12/2.47s,256ms] | ESCOLA[0.29→3.30/3.53s,268ms] | NÃO[0.33→2.77/2.77s] (총 ~7.05s)
  - 단일 글로스 `Olá` → OLÁ[0.00→2.57/2.57s] (trim X, 차렷→stroke→차렷 자체 재생). JS 에러 0.
- **향후 후보 (Phase B/C, 시각 검토 후 결정)**:
  1. **Stroke trim 임계값 튜닝**: 12% → 8/15/18% 비교, 시각 검토 후 적정값. 특정 글로스에서 prep/recovery가 너무 일찍/늦게 잘릴 가능성
  2. **Cosine easing**: linear ramp 대신 cosine ease-in-out — 큰 delta transition에 잔존 kink 있을 때만
  3. **IK-based 손 궤적 보정 (arc dip)** (P5.5/P6): 사용자가 더 자연스러운 dip을 원하면 손목 Cubic Bezier/Catmull-Rom + 2-bone IK 팔꿈치
  4. **Anticipation/overshoot easing** (P6): 실제 수어 리듬
- **관련 파일**: `public/players/sentence/index.html` (`computeStrokeRange`, `extractPoseAt`, `computeTransitionDuration`, `BONE_WEIGHTS`, `STROKE_*`, `rebuildActionsForCurrentModel`, `computeTotalDuration`, `updateTimeline`, animate 루프 fade window)

### P6: 수어문 비수지(non-manual) 노테이션 해석 및 재생
- **배경**: LIBRAS에서 비수지 요소(얼굴 표정, 눈썹 위치, 머리 기울임, 구형·입 모양, 시선)는 문법적으로 필수다. 부정·의문·조건·topic 표시가 모두 비수지로 처리된다. VLibras 번역 API가 반환하는 글로스 시퀀스에 이런 메타 정보가 포함되지만 현재 Sentence Player는 단순 글로스 토큰만 추출한다.
- **현재 한계**:
  - `translateSentence()`(line 417)가 `\s+` split만 수행 → 노테이션 마커(`[NEG]`, `[INT]`, `^`, `_q` 등)를 글로스로 오인할 수 있음
  - 사전 변환된 `.threejs.json` 번들은 body bone quaternion만 담고 blendshape/morph track이 없음 → 얼굴 표정 재생 경로 자체가 부재
  - 머리 기울임은 neck bone에 있지만 "부정 shake" 같은 주기 동작은 연속 재생에서 누락됨
- **선행 조사**:
  1. VLibras 번역 API가 실제로 어떤 노테이션 마커를 반환하는지 실측 (부정문·의문문·조건문 다양한 입력으로 샘플링)
  2. VLibras 내부 문법에 대한 1차 자료 검색 (LAVID/UFPB 논문, GLOSS SchemA 명세)
  3. 사전 변환 bundle의 `.threejs.json`에 blendshape/morph track을 추가할 수 있는지 Unity AssetBundle 원본 구조 재검토
- **구현 후보 (단계적)**:
  1. **Parser 확장**: `translateSentence()`에 노테이션 마커 분리 로직 추가 — 마커와 글로스 페어링, 마커 스코프(단일 글로스 vs. 문장 전체) 판정
  2. **Bundle 확장**: Unity 원본에서 face blendshape curve를 추출해 `.threejs.json`의 `tracks`에 포함 → `buildClipFromJson`이 `NumberKeyframeTrack`으로 morph 처리
  3. **Runtime overlay**: 마커 해석 결과(부정 → 머리 좌우 shake, 의문 → 눈썹 올림)를 body clip 위에 overlay mixer로 합성
- **관련 파일**: `public/players/sentence/index.html:translateSentence`, `loadGlossClip`, `buildClipFromJson` / `tools/vlibras2slmb/batch/precompute_threejs.py` (bundle 재설계 시)
- **참고**: `docs-source/claudedocs/vlibras-translation-api.md` (API 스펙), LIBRAS 5 parameters 자료

### P7: 다른 아바타로 리타겟팅 — BVH/ABNT `avatarModel`
- **목표**: 현재 Sentence Player는 VLibras 90본 스켈레톤(Padrao/CASA/Icaro GLB)만 지원한다. ABNT NBR 25606 표준의 46조인트 아바타(`public/avatars/abnt/avatarModel/model_external.gltf`)에서도 동일 글로스 시퀀스를 재생할 수 있게 runtime 리타겟팅 지원을 추가한다.
- **P2와의 차이**: P2는 offline 변환(VLibras bundle → `.slmb.xz` → SLMB Pipeline Player)이고, P7은 **Sentence Player 내부에서 런타임 본 매핑**으로 다른 스켈레톤에 동일 애니메이션을 적용한다. 사용자가 모델 선택 버튼으로 즉시 전환 가능.
- **선행 조사**:
  1. VLibras 90본 ↔ ABNT 46조인트 매핑 (이미 `tools/vlibras2slmb/data/skeleton_map.py`에 정의됨)
  2. 두 스켈레톤의 bind pose 차이 — bone local axis 정렬(forward/up), bone length 비율
  3. ABNT 아바타의 finger bone 구성 (46조인트에 손가락이 충분히 포함되는지)
- **구현 후보**:
  1. **Runtime retarget util**: `retargetClipToSkeleton(clip, sourceSkel, targetSkel)` — VLibras `.threejs.json`의 track을 target bone 이름으로 rename + bind pose offset 보정
  2. **모델 config 확장**: `MODELS`(line 263-270)에 `abnt_avatarmodel` 엔트리 추가, 로드 시 skeleton type 판별해 retarget 경로 분기
  3. **UI**: 컨트롤 바 모델 선택 버튼에 "ABNT" 추가. 전환 시 현재 큐를 재빌드(`rebuildActionsForCurrentModel` 확장)
- **검증**: 동일 문장(`Casa`, `Sim bom dia`)을 Padrao/CASA/Icaro와 ABNT avatarModel에서 나란히 재생해 포즈 consistency 확인. 손가락 ConfigurationComposite가 단순화되는지 육안 비교.
- **관련 파일**: `public/players/sentence/index.html` (`MODELS`, `loadModel`, `rebuildActionsForCurrentModel`) / `public/avatars/abnt/avatarModel/model_external.gltf` / `tools/vlibras2slmb/data/skeleton_map.py`
- **참고**: `CLAUDE.md` (ABNT 스켈레톤 사양), `docs-source/standards/ABNT_NBR25606_core_analysis.md`

### 후보: Sentence Player UX 개선
- 글로스 칩에 `duration` 툴팁 표시
- Loop ON 시 다음 반복 시작 전에 `IDLE_GAP_SEC` 대기 옵션
- 모델 전환 시 현재 큐 유지(clip은 재사용, mixer만 재바인딩)
- 자주 쓰는 문장 프리셋 버튼 (인사·예의·자기소개)

---

## 주간보고

### 2026-04-15 (수)

- [완료] **Stroke 검증 전용 테스트 플레이어** (`public/players/sentence-stroke-test/index.html`, 신규 ~1200 라인, `sentence/index.html` 일절 수정 없음)
  - **배경**: P5.1 Stroke Trim 출시 후 사용자가 Sim bom dia 배치 재생에서 BOM의 recovery가 "차렷까지" 포함되는 현상을 보고. Production 코드(`sentence/index.html`)는 튜닝/실험에 부적합 → 검증 대상과 도구를 격리한 독립 플레이어 구축.
  - **골격**: `vlibras-v3/index.html` 단일 글로스 구조 기반, `sentence/index.html:331-572`의 stroke 검출 블록(`STROKE_*` 상수, `asciiKey`, `loadBundleIndex`, `buildClipFromJson`, `sampleQuaternionAt`, `extractPoseAt`, `computeStrokeRange`)을 `// SYNC: ...:<line>` 주석과 함께 복제.
  - **4가지 stroke 검출 방법 동시 비교**:
    - **Method A — Cumulative %**: sentence player와 동일. 누적 angular delta 기반, slider head/tail 각 5-35% (기본 12/12)
    - **Method B — Peak-hold window**: `velocity ≥ peakVel × threshold%` 인 구간, slider 15-85% (기본 45)
    - **Method C — Rest-pose + hold plateau (asymmetric)**: strokeStart는 peak 왼쪽 scan에서 `restDist < restPct%`, strokeEnd는 **peak 오른쪽 scan에서 `restDist < 90%` 첫 지점**(hold 끝). slider 10-90% (기본 30)
    - **Method D — Peak drop (centered)**: peak 기준 좌우 스캔, `velocity < peakVel × (1-drop%)` 첫 지점, slider 10-70% (기본 40)
  - **Motion profile SVG 차트**: 496×180 viewBox, velocity(파랑 실선) + cumulative(회색 점선) + rest-pose distance(주황 실선) + peak marker + 각 method의 strokeStart/strokeEnd 수직 점선. Active method는 굵은 실선 + 음영 rect + 재생 커서(노랑).
  - **실시간 재계산**: slider 조정 시 해당 method만 재계산 → 차트 + 정보 패널 + stroke-bar 즉시 업데이트. Active method radio 변경 시 재생 경계 전환.
  - **Method C 진화 기록** (BOM 사례):
    1. 초기 bidirectional `restDist >= thresh` first/last index: BOM [0.183, 1.617] — recovery 후반 포함
    2. Peak-centered scan: 단일 peak 구조에선 동일 결과 — 미해결
    3. **최종 asymmetric + plateau 90%**: BOM [0.183, **1.190**] — recovery 427ms 배제. SIM 3.062→2.478, DIA 2.055→1.364
  - **단일 단어 재생**: Full/Stroke only 토글, LoopRepeat 모드. animate 루프에서 `[strokeStart, strokeEnd]` 외부 clamp. 미니 stroke 바에 전체 clip 대비 stroke 구간 하이라이트.
  - **범용 배치 재생** (`_runBatch(words, label)`):
    - 여러 clip을 `batchMixer`에 LoopOnce + clampWhenFinished로 바인딩, 각 action은 `time = strokeStart`부터 play
    - animate 루프에서 **두 가지 작업**: (1) `timeLeft ≤ nextFadeSec(200ms)` 시 `crossFadeTo(next, fadeSec)` 트리거, (2) `action.time ≥ strokeEnd` 시 `paused = true` + `batchCurrentIdx++`
    - **중요 수정**: 초기 `finished` 이벤트 기반 advance는 중간 clip이 strokeEnd를 115ms 지난 뒤 trigger되어 recovery 재생 → animate 루프 `strokeEnd` 수동 감지로 전환해 정확히 1 프레임 오버런 이내로 정지
    - **Delta cap**: `Math.min(clock.getDelta(), 0.1)` — tab throttling/fetch wait으로 경계 건너뛰기 방지
  - **프리셋 배치**: "Sim bom dia" 버튼 = `runBatch(['SIM','BOM','DIA'], 'Sim bom dia')` 래퍼
  - **임의 문장 번역 배치**: 새 `#sentence-input` + `#translate-btn`. `translateSentence(text)`가 `POST traducao2.vlibras.gov.br/translate`(sentence/index.html:612-623 포팅) → plain text `\s+` split → 글로스 배열. 미매칭 단어는 skip + 에러 배너에 "미매칭 단어 N개: ..." 표시. "Bom dia amigo" 실 API 호출 검증 완료.
  - **Debug hook**: `window.__strokeTest.getBatchState()` — 외부 테스트 harness가 live batch state(각 action의 `time/weight/paused/_fadeStarted/strokeStart/strokeEnd`) 조회. Playwright 내부 상태 샘플링에 활용.
  - **Playwright 검증**:
    - 단일 단어 각 method 수치: SIM A=[0.338,3.062]80.1%/C=[0.346,2.478]62.7%, BOM A=[0.233,1.597]75.8%/C=[0.183,1.190]55.9%, DIA A=[0.284,2.055]77.0%/C=[0.234,1.364]49.2%
    - 슬라이더 실시간(C 30→50% → [0.305,1.525]67.8%)
    - Active method 전환 A→C: info 패널 + stroke-bar + 재생 경계 모두 전환
    - 배치 내부 샘플링(Method C): SIM strokeEnd 2.478에서 paused, BOM strokeEnd 1.190에서 **최대 1.204 오버런(14ms = 1 프레임 미만)** 후 paused. crossfade weight BOM 1.0→0.40→0.0 / DIA 0.0→0.60→1.0 (200ms linear)
    - "Bom dia amigo" 실 번역 API → `BOM DIA AMIGO` → 4.3s 완료, JS 에러 0
  - **결정**: `sentence/index.html`(P5.1 production)은 일절 수정하지 않음. Method C가 현재 권장. sentence 파일에 적용 여부는 P5.2로 별도 결정.
  - **Plan 파일**: `C:\Users\admin\.claude\plans\twinkling-snacking-diffie.md`

- [예정] **P5.2 — Method C asymmetric 적용 결정**: 검증 도구에서 튜닝한 Method C를 `sentence/index.html`에 back-port할지, PLATEAU_RATIO(0.90) 고정값을 노출할지, 다양한 글로스(CASA/ESCOLA/AGUA/VOCE/AMIGO/TRABALHO 등)에서 육안 검증 후 결정
- [예정] 어휘 확장 (27 → 100), `asset_bundle.py` UnityPy 1.25+ 마이그레이션, Sentence Player seek(P4)

---

## 작업 이력

### 2026-04-20
- **Sentence Stroke Test 페이지 UI 정리 + motion profile 배치 동기화** (`public/players/sentence-stroke-test/index.html` 단일 파일)
  - **배경**: 오늘의 중점 작업 "모션 블렌딩 전략 재검토" 준비 단계. 사용자가 페이지를 열고 "상단 [로드] 버튼과 [Sim bom dia] 버튼이 무엇인지, motion profile이 왜 비어있는지" 지적. 세 가지 불명확 지점 진단:
    1. 컨트롤 바에 `[번역 & 배치]`, `[로드]`, `[Sim bom dia]` 3버튼이 동등 노출돼 주 동선 모호
    2. `[Sim bom dia]` = `['SIM','BOM','DIA']` 하드코딩 프리셋으로 번역 API만 스킵. 번역 입력과 결과 동일 → 잔여 디버그 버튼
    3. `renderChart()`가 `currentProfile` 있을 때만 그리는데 `currentProfile`은 `loadWordClip()`(단일 로드 경로)에서만 설정. `_runBatch`는 건드리지 않아 배치 재생 후에도 차트 비어있음
  - **UI 재구성**:
    - `#controls` 단일 행 → `display: flex-direction: column` + `.controls-row` 2단 (주: `sentence-input` + `번역 & 배치` + 모델 선택기 / 보조: `단일 글로스 분석` 라벨 + `word-input` + `로드`)
    - `#batch-btn` 버튼 제거, `runBatchSimBomDia()` 함수 제거, `batchBtnEl` DOM 참조와 이벤트/disabled 토글 전부 정리
    - `#error-banner` top 62→108, `#info`/`#compare-panel` top 66→112, `#compare-panel` max-height `calc(100vh - 250px)`로 두 행 컨트롤 바에 맞춰 조정
  - **글로스 칩 UI 신설**:
    - `#error-banner` 아래 `#gloss-chips` 컨테이너 + `.chip`/`.chip.active`/`.chip-missing` CSS (primary #ff9c47 활성, 미매칭은 빨강 ⚠️)
    - `#gloss-chips:empty { display: none }`로 초기·미사용 시 자동 숨김
    - `renderGlossChips(items, missing)`/`highlightChip(idx)`/`clearChipActive()`/`clearGlossChips()` 헬퍼
    - 칩 클릭 delegation: 매칭 칩 클릭 시 `loadWordClip(raw)` 호출 (배치 실행 중이면 `endBatch()` 선행) — 단일 분석으로 override
  - **Motion profile ↔ 배치 동기화**:
    - `_runBatch`의 fetchResults가 반환하는 item에 `profile` 첨부 (재계산 회피)
    - 신설 `syncInspectionToBatchItem(idx)` = `batchQueue[idx]`의 clip/duration/raw/profile을 `currentClip`/`currentDuration`/`currentRaw`/`currentProfile`에 반영 → `recomputeAllMethods` + `applyActiveMethod` + `renderChart` + `highlightChip`
    - 호출 지점: `_runBatch`의 첫 action play 직후(idx=0), animate 루프의 `batchCurrentIdx += 1` 직후(새 idx). `endBatch`가 `clearChipActive()` 호출해 배치 종료 시 칩 강조 해제 (차트는 마지막 글로스 유지 — 종료 후에도 검사 가능)
    - 단일 "로드" 경로(`loadBtnEl` click + `wordInputEl` Enter)는 `clearGlossChips()`로 이전 번역 칩 정리. 칩 클릭 경로는 칩 유지 → 다른 칩 연속 클릭 가능
  - **Playwright 검증**:
    - 페이지 로드 정상, 번들 27 글로스 + 모델 로드 완료, JS 에러 0 (favicon 404만)
    - 주 동선: `sentence-input`에 `Sim bom dia` → `번역 & 배치` → `translated → SIM BOM DIA` 로그 → 칩 `[SIM][BOM][DIA]` 렌더링 + 차트 26 child (3 path + 13 line) 그려짐. `batch advance → BOM @ 0.433s` / `→ DIA @ 0.483s` 로그로 sync 호출 확인. 배치 종료 시 차트는 DIA profile 유지 (Method A [0.284, 2.055] 77.0%, B [0.156, 2.261] 91.5%, C [0.234, 1.364] 49.2%, D [0.156, 0.507] 15.3%)
    - 칩 클릭 override: SIM 칩 클릭 → `activeChip=SIM` + `infoWord=SIM (SIM)` + Method A `[0.338, 3.062] 80.1%`로 즉시 전환
    - 단일 로드 회귀: `word-input=AGUA` + `로드` → 칩 컨테이너 display:none + `infoWord=ÁGUA (AGUA)` + Method A `[0.372, 3.364] 78.7%`로 차트 재렌더
  - **영향 범위**: 단일 파일 변경. `public/players/sentence/index.html`(P5.1 production) 및 기타 플레이어·공용 모듈 무영향
  - **다음 단계**: UI prep 완료 → 여러 글로스 × Method A/B/C/D 시각 비교, 배치 문장 5개 이상 육안 평가, 대안 B(full clip smart crossfade) / C(hand-trajectory IK) / D(hold plateau) 실험 가치 판단
  - **Plan 파일**: `C:\Users\admin\.claude\plans\keen-yawning-ullman.md`

### 2026-04-15
- **Stroke 검증 전용 테스트 플레이어 신설** (`public/players/sentence-stroke-test/index.html`, ~1200 라인, `sentence/index.html` 수정 없음)
  - **배경**: P5.1 Stroke Trim 출시 후 사용자가 "Sim bom dia 배치에서 BOM이 손이 많이 내려올 때까지 재생된다"고 보고. Production 코드는 튜닝/실험 위험 → 격리된 검증 도구 필요.
  - **구조**: `vlibras-v3/index.html` 단일 글로스 구조를 골격으로, `sentence/index.html:331-572`의 stroke 블록 복제. 복제된 상수/함수 각 블록에 `// SYNC: public/players/sentence/index.html:<line>` 주석으로 원본 추적.
  - **복제 대상**: 상수 `STROKE_PAD_HEAD/TAIL`, `MIN_STROKE_RATIO`, `STROKE_SAMPLE_N`, `STROKE_BONES`, 함수 `asciiKey`(368-370), `loadBundleIndex`(373-377), `buildClipFromJson`(380-397), `sampleQuaternionAt`(400-422), `extractPoseAt`(425-437), `computeStrokeRange`(443-522)
  - **Motion Profile 계산** (`computeMotionProfile(clip)`, 신규): 60 sample 등간격 분할, STROKE_BONES 6개 본의 per-step angular delta/cumulative/velocity/rest-pose distance를 한 번에 반환. 피크 index, 최대 rest 포함.
  - **4가지 stroke 검출 방법**:
    1. **Method A — Cumulative %** (sentence/index.html:443-522 로직 포팅): head/tail 임계 slider(5-35%, 기본 12/12). ±50ms padding + 40% 최소 길이 안전망. `clampTriggered` 플래그 fork 추가.
    2. **Method B — Peak-hold window**: `velocities[i] >= peakVel × thresholdPct%` 인 첫/마지막 sample. slider 15-85% (기본 45)
    3. **Method C — Rest-pose + hold plateau (asymmetric)**: strokeStart는 peak 왼쪽 scan으로 `restDist < restPct%` 지점, strokeEnd는 peak 오른쪽 scan으로 `restDist < PLATEAU_RATIO(0.90)` 지점. strokeStart slider만 노출(10-90%, 기본 30). PLATEAU_RATIO=0.90 상수 고정 — "peak의 90% 이상 유지되는 마지막 지점" = hold 끝 = recovery 시작 직전
    4. **Method D — Peak drop (centered)**: peak 기준 좌우 스캔, `velocity < peakVel × (1 - dropPct/100)` 첫 지점. slider 10-70% (기본 40)
  - **SVG Motion Profile 차트**: 496×180 viewBox. 3 path(velocity 파랑, cumulative 회색 점선, rest-dist 주황) + peak marker + 각 method strokeStart/End 수직선 + active method 음영 rect + playback cursor(노랑). `renderChart()`가 `chartEl.textContent=''` 후 `svgElem(tag, attrs)` 헬퍼로 SVG element를 createElementNS로 append.
  - **Method C 진화 기록** (BOM, duration 1.800s):
    1. 초기 bidirectional last-index: BOM [0.183, 1.617] 79.7% — recovery 후반 포함
    2. Peak-centered scan: 단일 peak 구조라 동일 결과 — 미해결
    3. Asymmetric + plateau 90% (최종): BOM [0.183, **1.190**] 55.9% — recovery 427ms 배제. SIM strokeEnd 3.062→2.478(584ms 당김), DIA 2.055→1.364(691ms)
  - **UI 구성**:
    - 상단 `#controls`: sentence-input(번역 문장) + translate-btn + word-input(단일 단어) + load-btn + batch-btn("Sim bom dia" 프리셋) + model selector. `flex-wrap` 적용
    - 좌측 `#info`: Clip 섹션(word/duration/model) + Active Stroke 섹션(method/stroke/frames/ratio/clamp/mode)
    - 우측 `#compare-panel`: motion profile SVG + 4개 method row(radio + slider + 결과 표시)
    - 하단 `#player-bar`: stroke-legend + stroke-bar(highlight + cursor) + timeline + play/pause/stop/loop + Full/Stroke only 토글
  - **단일 단어 재생 제어**: `applyPlaybackMode()`가 `[strokeStart, strokeEnd]` 외부면 clamp. animate 루프 LoopRepeat + strokeEnd 도달 시 루프 or 정지.
  - **범용 배치 재생** (`_runBatch(words, label)`):
    - Promise.all로 parallel fetch, 각 clip의 active method stroke 범위 계산
    - 미매칭 단어는 `missing[]`에 누적, 에러 배너에 한 번에 표시 ("미매칭 단어 N개: X, Y, ...")
    - 재생 가능한 단어 0개면 "재생 가능한 단어가 없습니다" 표시 + endBatch
    - `batchMixer = new AnimationMixer(currentModel)` 새로 생성, 각 clip을 LoopOnce + clampWhenFinished action으로 바인딩, `nextFadeSec = 200ms`
    - 첫 action을 `time = strokeStart`로 reset + play + mixer.update(0)
    - animate 루프:
      1. `batchMixer.update(delta)` (delta cap 0.1)
      2. Crossfade trigger: `!curr._fadeStarted && timeLeft ≤ curr.nextFadeSec && currentIdx < N-1` → next.reset + next.time = strokeStart + next.play + `curr.action.crossFadeTo(next.action, curr.nextFadeSec, false)`
      3. **strokeEnd 수동 advance**: `curr.action.time >= curr.strokeEnd - 1e-4` → `curr.action.paused = true` + (중간이면 `batchCurrentIdx++`, 마지막이면 `endBatch()`)
  - **`finished` 이벤트 제거 (중요 수정)**: 초기 구현은 LoopOnce+clampWhenFinished의 finished 이벤트로 idx advance했으나, SIM(duration 3.4, strokeEnd 2.478)이 clip 끝까지 재생되는 동안 BOM이 이미 strokeEnd+115ms까지 진행 → recovery 보이는 버그. animate 루프 수동 감지로 전환하면서 `batchOnFinished = null`.
  - **Delta cap**: `Math.min(clock.getDelta(), 0.1)` — Playwright headless tab throttling / fetch wait 후 첫 raf tick의 대용량 delta가 경계를 건너뛰는 것 방지 (표준 Three.js animate 패턴).
  - **프리셋 버튼**: `runBatchSimBomDia()` = `runBatch(['SIM','BOM','DIA'], 'Sim bom dia')` 래퍼. 기존 하드코딩 제거.
  - **임의 문장 번역 배치**:
    - `TRANSLATE_URL = 'https://traducao2.vlibras.gov.br/translate'` 상수 추가
    - `translateSentence(text)`가 POST JSON body `{text}`, plain text 응답을 `\s+` split (sentence/index.html:612-623 포팅)
    - `onTranslateAndBatch()`: sentence-input 값 → translateSentence → `runBatch(glosses, text)`
    - Enter 키 또는 translate-btn 클릭, 번역 중 translate-btn disabled
  - **Debug hook**: `window.__strokeTest.getBatchState()` — `batchMode`, `batchCurrentIdx`, `activeMethod`, 각 queue item의 `raw/time/paused/weight/fadeStarted/strokeStart/strokeEnd/duration` 반환. 외부 테스트 harness에서 live state 조회.
  - **Playwright 검증 (단일 단어)**:
    - 페이지 로드 정상, 콘솔 "bundle index loaded: 27 glosses"
    - SIM/BOM/DIA 순차 로드 각 method 결과 DOM 읽기 확인
    - 슬라이더 실시간 재계산 (C slider 30→50% → 재계산 + 차트 재렌더)
    - Active method 전환 A→C → info 패널 + stroke-bar left/width + 재생 경계 모두 전환
    - chart SVG 3 path + 13 line + 7 text 렌더링 확인
  - **Playwright 검증 (배치)**:
    - 내부 state 샘플링 (200ms 간격):
      - t=2063ms: SIM.time=2.378 w=0.50, BOM.time=0.283 w=0.50 → crossfade 진행
      - t=2271ms: SIM.time=**2.479 w=0 paused=true**, BOM.time=0.503 w=1.00 → SIM strokeEnd 2.478 정확히 도달 후 정지
      - t=2891ms: BOM.time=1.124 w=0.40, DIA.time=0.354 w=0.60 → BOM→DIA crossfade
      - t=3091ms: BOM.time=**1.204 w=0 paused=true**, DIA.time=0.554 w=1.00 → BOM strokeEnd 1.190 + 14ms(1 프레임 미만) 오버런 후 정지
      - t=3915ms: 배치 종료
    - "Bom dia amigo" 실 번역 API 호출 → `translated → BOM DIA AMIGO` → `batch start "Bom dia amigo" (method: C, fade: 200ms) BOM[0.183→1.190/1.80s] DIA[0.234→1.364/2.30s] AMIGO[0.233→1.267/1.97s]` → 4.3s 총 시간, JS 에러 0
  - **결정 사항**:
    - `sentence/index.html`(P5.1 production)은 일절 수정하지 않음 → 검증 대상과 도구 격리
    - Method C가 현재 권장 방법 (recovery 배제가 가장 명확)
    - PLATEAU_RATIO = 0.90 고정, slider 미노출 (필요 시 노출)
    - sentence 파일에 Method C 적용 여부는 P5.2로 별도 결정
  - **관련 파일**:
    - 신규: `public/players/sentence-stroke-test/index.html`
    - 참조(수정 없음): `public/players/sentence/index.html`, `public/players/vlibras-v3/index.html`
  - **Plan 파일**: `C:\Users\admin\.claude\plans\twinkling-snacking-diffie.md`

### 2026-04-14
- **P5.1 — Sentence Player Stroke Trim 출시** (`public/players/sentence/index.html` 단일 파일)
  - **문제**: P5 Phase A 출시 후 사용자가 "단어와 단어 사이에 손이 차렷자세까지 내려갔다 다시 올라온다"고 보고. 진단: 모든 글로스 클립이 prep(차렷→손 올림) + stroke(핵심) + recovery(손→차렷) 구조. 큐 연결 시 매 글로스마다 recovery+prep = 양쪽 60%가 차렷 왕복 dead time.
  - **데이터 진단**: SIM/BOM/DIA/EU/BEBER/AGUA/OLA/CASA/ESCOLA 8개 글로스에서 활성 팔 본의 quintile-wise angular delta 측정 → 모두 강한 U-shape. 첫·마지막 quintile이 25-42%, 중간 quintile이 0.7-9.3%. 키프레임 density는 정반대 분포 (양 끝에 더 많음 — Unity가 t=0과 t=duration에 항상 박는 관습)이므로 키프레임 시간 직접 활용은 거부.
  - **알고리즘**: `computeStrokeRange(clip)`이 STROKE_BONES(`BnBraco{R,L}`, `BnAntBraco{R,L}`, `BnMaoOrient{R,L}`)의 합산 angular delta를 60샘플링(`sampleQuaternionAt` 헬퍼)해서 누적값이 head 12% / tail 88% 임계에 도달하는 시점을 stroke 경계로 잡는다. ±50ms padding(`STROKE_PAD_HEAD/TAIL`) 적용 + 40% 최소 길이 안전망.
  - **헬퍼 신설**: `sampleQuaternionAt(track, t)` (binary search + SLERP), `extractPoseAt(clip, t)` (BONE_WEIGHTS 본 quaternion 추출 일반화), `computeStrokeRange(clip)`. 기존 `extractBoundaryPoses`는 `extractPoseAt`으로 일반화되어 제거.
  - **`fetchClipFromEntry`**: stroke 시점의 quaternion으로 `startPose`/`endPose` sample (이전 P5 Phase A는 t=0/t=duration 차렷 quaternion이라 거리 측정이 부정확했음). entry에 `strokeStart`/`strokeEnd`도 첨부.
  - **큐 위치별 trim 분기** (`rebuildActionsForCurrentModel`):
    - 단일 글로스 (N=1): trim X (차렷 → 글로스 → 차렷 자체 재생)
    - 첫 글로스: head trim X (차렷에서 자체 prep로 손 올림)
    - 마지막 글로스: tail trim X (자체 recovery로 차렷 복귀)
    - 중간 글로스: 양쪽 trim (stroke만)
  - **재생 통합**: `restartQueueFromStart`가 첫 액션 `time = effectiveStart`. animate 루프 fade window가 `effectiveEnd - action.time` 기준, 다음 액션 시작 시 `next.action.time = next.effectiveStart`. `computeTotalDuration`/`updateTimeline` elapsed가 effective 길이 합산으로 재작성.
  - **Playwright 검증** (5케이스):
    - `Sim bom dia` → SIM[0.00→3.06,266ms] | BOM[0.23→1.60,274ms] | DIA[0.28→2.30] = **5.903s** (P5 Phase A 7.082s에서 −1.18s)
    - `Eu beber agua` → EU[0.00→1.69,235ms] | BEBER[0.31→1.96,285ms] | AGUA[0.37→3.80] (P5 Phase A의 124ms FADE_MIN clamp 문제가 stroke 시점 quaternion 사용으로 235/285ms 의미적 거리로 해결)
    - `Olá casa` → OLÁ[0.00→2.21,274ms] | CASA[0.30→2.47]
    - `Casa escola não` → CASA[0.00→2.12,256ms] | ESCOLA[0.29→3.30,268ms] | NÃO[0.33→2.77]
    - 단일 글로스 `Olá` → OLÁ[0.00→2.57] (trim X, 전체 재생). JS 에러 0.
  - **결정 사항**: stroke 사이는 Three.js native crossfade (quaternion SLERP)만 사용. 손이 가슴/배까지 내려왔다 올라오는 dip arc는 P5.1 범위 외 — 사용자가 "stroke end → stroke start 사이는 보간만 하면 되고 손이 내려올 필요 없다"고 명시.
- **P5 Phase A — Sentence Player 동적 모션 블렌딩 출시** (`public/players/sentence/index.html` 단일 파일, +99/-8 라인)
  - **Plan**: `C:\Users\admin\.claude\plans\curried-shimmying-bengio.md` (사전 탐색에서 vlibras-portal 소스가 Unity wasm이라 JS-level 블렌딩 코드 재사용 불가임을 확인)
  - **상수 블록 (line 304)**: `CROSSFADE_SEC = 0.2` 제거 → `FADE_MIN=0.12`, `FADE_MAX=0.45`, `D_REF=1.5` (라디안), `BONE_WEIGHTS` 13개 본 (어깨 0.6 + 상박 1.5 + 전박 1.2 + 손목 1.8 + 손가락 root 0.3 + 목 0.3, R/L 대칭)
  - **헬퍼 신설** (`buildClipFromJson` 직후): `extractBoundaryPoses(clip)`이 `THREE.QuaternionKeyframeTrack`만 골라 첫/마지막 keyframe 값을 `Map<bone, Quaternion>`으로 추출 (mixer 인스턴스 불필요, O(track 수)). `computeTransitionDuration(prevEnd, nextStart)`이 가중 RMS 각거리 D를 sqrt 곡선으로 [FADE_MIN, FADE_MAX]에 매핑.
  - **`fetchClipFromEntry`**: 반환 객체에 `startPose`/`endPose` 필드 첨부 (한 번만 계산)
  - **`computeTotalDuration`**: 고정 `CROSSFADE_SEC * (n-1)` → 각 인접 쌍의 `nextFadeSec` 합산으로 가변 overlap 반영
  - **`rebuildActionsForCurrentModel`**: `queueActions.map` 직후 per-pair `nextFadeSec` 패스 추가 (마지막 엔트리는 0). `__debugBlend` 게이트 뒤에 `console.log('[P5] queue fades: ...')` 1회성 디버그 라인 보존 (production-safe).
  - **`updateTimeline` elapsed 계산**: 가변 `nextFadeSec` 합산으로 정확한 wall-clock 위치 유지
  - **animate 루프 fade window**: `CROSSFADE_SEC` → `curr.nextFadeSec ?? FADE_MIN` 폴백으로 동적화. `crossFadeTo(next, fadeSec, false)`는 그대로 (Three.js linear ramp 유지)
  - **Playwright 검증** (자동 회귀 5케이스):
    - `Sim bom dia` → SIM→BOM **294ms**, BOM→DIA **124ms**, total 7.082s ✓
    - `Eu beber agua` → EU→BEBER **124ms**, BEBER→AGUA **124ms** (모두 FADE_MIN clamp — 글로스 boundary가 quaternion 기준으로는 비슷)
    - `Olá casa` → OLÁ→CASA **294ms**, total 4.739s ✓
    - `Casa escola não` → CASA→ESCOLA **294ms**, ESCOLA→NÃO **123ms**, total 8.350s, finished exact match ✓
    - 모델 전환 (Padrão→CASA) 후 동일 큐 동일 fade 값 정상 재구성. JS 에러 0.
  - **관찰**: SIM/CASA/OLÁ 같은 글로스의 끝 포즈와 BOM/ESCOLA의 시작 포즈는 quaternion 거리 큼 → 294ms 동적 확장. EU/BEBER/AGUA는 손 위치가 다른데 손목 회전이 비슷한 케이스 → quaternion만으로는 distinguishing 어려움. Phase B 후보(wrist world position 거리 추가) 식별.
  - **vlibras-portal 소스 검증**: `app/vlibras-plugin.{js,chunk.js}` + `barra*.js` 전수 grep 결과 `crossfade/blend/lerp/slerp/interpolat*` 0건. JS 계층은 `SendMessage("PlayerManager", "playNow"|"setSlider"|"setPauseState"|"stopAll", ...)` 4개 API만 노출. 블렌딩 로직 전체가 `playerweb.wasm.code.unityweb` 바이너리 안 → JS-level 재사용 불가능. 위젯은 시각 비교 레퍼런스로만 사용 (`🤟 위젯` 토글 그대로).
- **Sentence Player ↔ VLibras 공식 위젯 통합 완료** (`public/players/sentence/index.html` 단일 파일, +145/-8 라인)
  - **Step 1 임베드** (line 1035-1049): `<div vw><div vw-access-button>...</div></div>` + `https://vlibras.gov.br/app/vlibras-plugin.js` + `new VLibras.Widget({position:'R', opacity:1})`. 토글 OFF 기본 (`enabled` 클래스 없음).
  - **Step 2 토글 버튼** (line 216, 1002-1032): `#vlibras-toggle`(`🤟 위젯`) 컨트롤 바 우측에 추가. `setVlibrasPluginEnabled(enabled)` 헬퍼가 `[vw]`의 `enabled` 클래스만 관리. 첫 ON에서는 `[vw-access-button]` 자동 클릭을 디스패치해 `window.plugin` lazy 초기화를 선행. `localStorage['vlibrasPluginEnabled']`로 상태 복원.
  - **Step 3 호출 지점** (line 931, 937): `handleTranslate()` 성공 후 `playQueue()` 직후에 `syncToVLibrasPlugin(text)` fire-and-forget. 로컬 번들에 없는 미싱 글로스 분기에서도 호출 (공식 위젯엔 있을 수 있으므로).
  - **Step 4 Tier 1 동기화** (line 805-863): `plugin.translate(text)` → `plugin.player.translate(text)` 순차 시도. `waitForVlibrasPlugin(2500ms)`가 `window.plugin` 존재 여부를 50ms 간격 polling. 실패 시 `console.warn` 1회 + 메인 파이프라인 영향 없음.
  - **Tier 2/3/4 생략**: Tier 1이 확실히 동작 → Selection 트릭, 입력박스 스크래핑, 안내 UI 모두 미구현.
- **VLibras click 가로챔 버그 우회** (line 481-501, 947, 1022): 위젯이 document capture phase listener로 전역 click을 가로채 ① 우리 버튼 핸들러 실행 차단, ② 버튼 textContent(`🤟 위젯`)를 자동 번역 트리거 두 가지 문제 발생. **해결**: `__vlibrasSafeClickHandlers` WeakMap + `window` capture phase listener로 우리 버튼을 먼저 처리하고 `stopImmediatePropagation()`. `safeClick(el, handler)` API로 `translate-btn`과 `vlibras-toggle`에 바인딩. Plan에 없던 추가 구현.
- **Plan과 다른 결정**: 토글 ON에서 `[vw-access-button]`/`[vw-plugin-wrapper]`의 `active` 클래스는 강제 토글하지 않음 — 플러그인 내부 상태머신이 즉시 리셋하여 사용자가 펼치는 순간 원상복구되는 부작용. `enabled`만 관리. 주석 line 1003-1004에 기록.
- **문서·워크스페이스 정리**:
  - `sentence-vlibras-plugin-integration-plan.md` 헤더에 "구현 결과 요약 (2026-04-14)" 섹션 추가, 상태를 "✅ 구현 완료"로 갱신.
  - `.gitignore`에 `/vlibras-portal/` 추가 (로컬 참조 클론 2.1GB, 커밋 대상 아님).
  - 루트 `sentence-toggle-on.png` 검증용 스크린샷 삭제.
- **메인 vs. VLibras 위젯 chirality 차이 분석** (`docs-source/claudedocs/avatar-handedness-analysis.md` 신규):
  - **현상**: 같은 글로스에서 메인은 signer 오른손, 위젯은 signer 왼손. 사용자가 gov.br 공식 사이트 위젯도 동일하게 왼손인 것을 확인 → random pick 아닌 일관 베이크.
  - **코드 추적**: `precompute_threejs.py:494-495`의 `(x,y,z,w)→(x,-y,-z,w)` 회전 변환 = X-축 미러. `coordinate.py`의 표준 변환은 정의돼 있지만 호출 안 됨. `icaro_bind_pose.json`의 R/L bone 배치도 X-mirror된 구조여서 self-consistent. 메인 = double-mirror 결과로 right-handed dominance 출력.
  - **위젯 측 조사**: VLibras Widget 6.0.0 docs, `configs.json`, `vlibras-plugin.chunk.js` 모두 dominant-hand 옵션 부재. 위젯은 Unity 자산 베이크 그대로 재생, 우리 통제 밖.
  - **LIBRAS 컨벤션 조사**: 양손 모두 valid (`libras.com.br` 5 parameters), 학술 문서화는 오른손이 표준, 학습 연구는 right/left 대신 dominant/non-dominant로 명시.
  - **결론**: 둘 다 valid, 메인이 학술 컨벤션·인구통계 다수에 부합, 위젯이 VLibras 공식 채널 일관성에 부합. 수정 작업 없음. project-status.md "알려진 이슈 #7"에 한 줄 요약 + 분석 문서 링크 추가.

### 2026-04-13
- **P1 파이프라인 M0~M5 완료** (에이전트 병렬 실행)
  - **M0**: VLibras 번역 API 스펙 실측 (`POST https://traducao2.vlibras.gov.br/translate`, JSON body `{"text":"..."}`, plain text 응답, `\s+` split 파싱, CORS 직접 허용). 상세: `docs-source/claudedocs/vlibras-translation-api.md`
  - **M1**: `tools/vlibras2slmb/batch/precompute_threejs.py` 신설 — VLibras Unity AssetBundle → Three.js tracks JSON 배치 변환. UnityPy 1.25 lowercase API 대응 인라인 리더 내장. 레거시 파이프라인 변환(yz sign flip `(x,y,z,w)→(x,-y,-z,w)` + 7개 헬퍼 본 Icaro-bind override + static position tracks) 역공학 후 `--legacy` 기본 적용. Icaro bind pose `tools/vlibras2slmb/data/icaro_bind_pose.json`에 베이크.
  - **M2**: 스킵 — M0에서 CORS 직접 허용 확인, Vercel rewrites 불필요
  - **M3**: `public/players/sentence/index.html` 신설. 문장 입력 → POST 번역 → ASCII 키 정규화(`NFKD`) → 사전 변환 번들 fetch → 첫 글로스 재생. 글로스 칩 UI(미싱 `⚠️` 표시). `buildClipFromJson`, `loadGlossClip`, `asciiKey`, `translateSentence` 순수 함수화
  - **M4**: 큐잉 + crossfade 연속 재생. `CROSSFADE_SEC=0.2s`, `mixer.addEventListener('finished')` + 렌더 루프 timeLeft 체크로 다음 액션 `crossFadeTo`. `stopAndDisposeQueue()` 메모리 정리, 재번역 5연속 누수 없음 확인. 전체 duration 기반 타임라인 갱신
  - **M5**: 융합 토큰 폴백 (`BOM_DIA` → `BOM`+`DIA` split 재조회), 에러 배너 폴리싱(수동 닫기, shake 애니메이션), `loadBundleIndex` cache `no-store`
  - **Playwright 픽셀/E2E 검증**: M1에서 `CASA`·`ESCOLA` 레퍼런스 대비 bone delta ≤ 6mm, M3~M5에서 20+ 문장 시나리오 실측 (총 duration 수치 검증 포함)
  - **배포 영향 없음**: 순수 정적 사이트 제약 그대로 유지 (`vercel.json` 무수정)
- **어휘 확장 (21 → 27 글로스)**: 사용자 "Eu morar casa" 테스트 중 `MORAR` 미싱 발견 → `spike_glosses.txt`에 MORAR, QUERER, ESTUDAR, IR, TER, FALAR 6개 동사 추가 → `precompute_threejs.py` 재실행 → 27/27 성공
- **테스트 가이드 작성**: 24개 VLibras 실측 문장을 `project-status.md` 하단에 5범주로 정리
  - 기초(1~2어) 10개, 주어+동사+목적어(2~3어) 8개, 3~4어 큐잉 2개, 융합 토큰 폴백 1개, 엣지케이스 4개
  - `OBRIGAR` (단독 시 동사 원형 변환), `BOM(+)` (강도 수식자), `GOSTAR` 문장 축약 같은 VLibras 특이 동작 기록
  - 회귀 테스트 5문장 시퀀스: Casa → Sim bom dia → Obrigado bom dia → Eu morar casa → Casa bonita
- **워크스페이스 정리**: 세션 중 Playwright 검증으로 쌓인 루트 PNG 31개와 `.playwright-mcp/` 디렉토리 제거, `.gitignore`에 재발 방지 규칙(`/*.png`, `.playwright-mcp/`) 추가
- **Git 커밋 시퀀스**: `c213429` (배치 변환기 + 21 번들) → `2d94138` (Sentence Player + API 문서) → `e474b48` (docs + gitignore) → `a482322` (어휘 27 확장) → `deca3df` (테스트 가이드). 모두 `origin/main` 반영
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

### 7. 메인 캔버스 vs. VLibras 위젯 — 손잡이(chirality) 차이
- **현상**: 같은 글로스에서 메인 Three.js 아바타는 signer 오른손, VLibras 공식 위젯 아바타는 signer 왼손으로 signing. gov.br 공식 사이트 위젯도 동일하게 왼손.
- **결론**: 둘 다 LIBRAS 측면에서 valid. 메인이 학술 문서화 컨벤션과 인구통계 다수에 부합하고, 위젯은 VLibras 공식 채널 모두에서 일관된 베이크 정책. **수정 작업 없음**.
- **결정(2026-04-14)**: 현재 상태 유지. 메인·위젯 모두 valid 표현이므로 P5/P6/P7 작업 사이클에서도 chirality 변경을 전제하지 않음. 향후 방향 전환이 필요해지면 `avatar-handedness-analysis.md`의 Option A/B/C를 재평가.
- **원인 요약**: precompute_threejs.py의 X-mirror 회전 변환(`(x,y,z,w)→(x,-y,-z,w)`)이 Icaro 스켈레톤의 X-mirror된 R/L bone 배치와 self-consistent하게 결합돼 학술 컨벤션 dominance를 만들어냄. 위젯은 Unity 자산이 베이크된 그대로 재생하며 dominant-hand 옵션 부재.
- **상세 분석**: [`avatar-handedness-analysis.md`](avatar-handedness-analysis.md) — 코드 추적, LIBRAS 컨벤션 자료, 위젯 옵션 조사, 가설 평가 포함.

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
