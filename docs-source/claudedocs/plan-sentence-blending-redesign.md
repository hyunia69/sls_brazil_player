# 수어 문장 블렌딩 로직 전면 재검토 계획

## Context (왜 이 재검토인가)

`sentence/index.html` (production, P5.1 완료)과 `sentence-stroke-test/index.html` (검증 도구)에서 사용 중인 **"stroke(의미구간) trim + 동적 crossfade"** 패러다임이 품질상 완벽하지 않다. 품질 지표가 정성적("어색하다")에 머물러 있고, 다음 갈림길에서 객관적 판단 근거가 없다:

- Method A/C 중 선택
- stroke 기반을 유지할지 vs 시간/공간 기반으로 전환할지
- 27 → 100 글로스 확장과 병행 가능한지

학술(수어 음운론) + 산업(VLibras, JASigning, PAULA, SignAvatars) 조사 결과, 우리는 **VLibras 원본(단순 concat)보다는 이미 진보적이지만 JASigning 수준의 segmental awareness(M-H model)에는 못 미친다**. 완전 교체 대신 **점진 마이그레이션 + 데이터 기반 의사결정**이 합리적이며, 그 첫 단추는 **정량 메트릭 도입**이다.

---

## 핵심 발견 요약

### Phase 1: 코드 실상

| 요소 | 현재 상태 |
|---|---|
| **production stroke 검출** | Method A만 (누적 angular delta 12%/12%, ±50ms padding) — `sentence/index.html:443-522` |
| **Method 비교 도구** | A/B/C/D 4종 + SVG 차트 — `sentence-stroke-test/index.html:853-993` |
| **Crossfade** | 가중 RMS 각거리 → sqrt → [0.12s, 0.45s] 매핑 — `sentence/index.html:525-545` |
| **Stroke 검출 대상 본** | 팔/손목 6개 (양손 구분 없음) |
| **알려진 공백** | 손가락·얼굴·몸통 미반영, 양손 비대칭 미처리, 60fps 고정 샘플링, hold 구간 식별 없음 |

### Phase 2: 학술 + 산업 인사이트 (우선순위순)

1. **★★★ "Stroke"은 gesture studies(Kendon-Kita) 용어** — 수어학은 **Movement-Hold model (Liddell & Johnson 1989)**. Hold는 의미 단위이므로 trim 금지.
2. **★★★ "Transitions are the key"** (McDonald/Wolfe, Paula) — transition 자체가 1등급 단위.
3. **★★ "Faster signs, slower transitions"** — 현재 `FADE_MIN=0.12s`는 Deaf user 선호와 반대.
4. **★★ Tyrone & Mauk 2010**: ASL sign lowering/phonetic reduction이 연결 수화에서 자연스럽게 발생할 수 있음을 보고. citation-form height를 맥락 무시 맹목 보존하는 것은 일부 상황에서 부자연스러울 수 있음. (단, "100% 보존이 부자연"은 paper 직접 결론 아닌 확장 해석 — 근거 rationale이지 개선 증명 아님)
5. **★★ SQUAD / Spline quaternion** — EMBR 등 시스템에서 채택 보고. 정량 우위는 분야/구현별 상이 → P6b spike에서 Three.js 환경 독립 검증 필요.
6. **★ Bimanual decoupling**: H1(dominant) / H2(non-dominant) 분리 (Sandler Hand Tier).
7. **★ VLibras 원본 = 단순 sequential concat, phase marker 없음** — 우리는 이미 앞섬.
8. **★ JASigning / SiGML**: targeted vs lax transition 구분을 모델에 설계. 유사 구분이 아바타 블렌딩을 개선하는지는 **우리가 테스트할 가설** — 외부 Deaf user study 직접 인용 근거 없음.

> **중요**: 위 문헌은 **설계 rationale**이지 "이 rollout이 Deaf 평가를 개선한다"는 증명 아님. 실제 개선 여부는 P5.2 메트릭 + P6.5 user eval로만 판정.

---

## 상위 전략 (3문장)

- **급진적 패러다임 교체 대신 hybrid 점진 마이그레이션**: stroke 유지 + M-H 인식 + bimanual + targetted/lax 이원화 (P6a 본궤도). SQUAD는 **P6b 별도 spike**로 격리 (Codex 지적 — 구현 risk).
- **sentence-stroke-test를 정량+정성 평가 실험대로 승격** (Method E/F/G + 자동 메트릭 **+ 수동 ground truth 라벨**) — 자동 메트릭은 diagnostic signal, 최종 채택은 수동 라벨 + 시각 A/B 합의.
- **production(`sentence/`)은 저위험 개선만 선반영**(FADE_MIN 상향, bimanual union), 구조 변경은 P5.2 방향성 + 수동 라벨 합의 승자만.

---

## Phase별 실행 계획

### Phase P5.2 — 실험대 확장 (1주)
**단일 수정 파일**: `public/players/sentence-stroke-test/index.html`

1. **Method E (M-H 인식)**: `computeMotionProfile` (L786) 확장. velocity ≤ peakVel×0.15 **AND** restDist ≥ maxRest×0.8 **AND** ≥100ms 지속 구간을 hold로 라벨링. stroke = [첫 hold 시작, 마지막 hold 끝]. `methodE(profile, holdVelPct, holdPosePct)` 추가.
2. **Method F (SQUAD crossfade)**: Method A 범위 + THREE.AnimationMixer `crossFadeTo` 대신 4-control-point SQUAD pose-blend를 `animate()` (L1681)에 inject. 토글로 선택.
3. **Method G (Bimanual separated)**: `STROKE_BONES` (L338)를 R/L 세트로 분리. `computeMotionProfile`를 `{R, L}` 반환으로 분기. stroke range = `{min(startR, startL), max(endR, endL)}`.
4. **수동 ground truth 라벨링 (Codex 반영 — 순환 평가 방지)**:
   - 5 시나리오 × 원본 클립 frame-by-frame 검토로 hold 구간 수동 annotation. 포맷: `{scenario, gloss, bone_group, holdFrames:[[startFrame, endFrame], ...]}`.
   - 라벨러: 개발자 1명 + 동료 1명 cross-check. 불일치 시 재검토 후 합의.
   - 저장: `docs-source/claudedocs/hold-ground-truth.json`.
   - 이 수동 라벨이 **유일한** Hold Retention 메트릭의 ground truth. 자동 휴리스틱 검출은 **Method E 입력**이지 평가 기준 아님.
5. **자동 메트릭 (diagnostic signal — acceptance criterion 아님)**:
   - **Jerk RMS** (d³θ/dt³ via 3차 차분) — 매끄러움 시그널
   - **Boundary discontinuity** (기존 `computeTransitionDuration` 수식 재사용) — 경계 각거리
   - **Velocity continuity** (crossfade 전/후 1 샘플 velocity 비) — 운동 연속성
   - **Hold Retention Rate** — **수동 ground truth 기준** (Method E 자체 휴리스틱과 독립). HPR은 "원본 hold 프레임이 재생에서 살아남았는가"만 측정 → linguistic naturalness 직접 증명 아님, signal 중 하나.
   - **Quaternion Plateau Rate (Codex 원안 변형 — flat skeleton 대응 proxy)**: STROKE_BONES 6본의 quaternion rolling window 각거리가 threshold(기본 0.05 rad) 이하로 ≥100ms 유지되는 구간 비율. Codex 원안(FK 손목 월드 위치 2cm)은 VLibras 스켈레톤이 flat hierarchy(`BnMaoOrientR.parent = Armature001`)여서 월드 위치가 애니메이션 영향 안 받음 → 불가. quaternion 기반 proxy는 Method E의 summed-velocity 휴리스틱과 **별개 정의**이므로 순환 평가 회피 목표 유지. 수동 라벨과 triangulate (합치도 측정).
   - **Spatial drift** (VLibras flat skeleton에선 보류 — SkinnedMesh vertex 또는 수동 FK chain 구축 필요, 2주차 검토)
   - **해석 원칙**: 이 수치는 **방향성** 판단용. 복수 지표 + 수동 라벨 수렴만 신뢰. 단일 지표 개선으로 채택 금지.
6. **문장 비교 모드**: 같은 문장을 Method A/C/E/F 4회 재생, 4-row stacked 차트 (`renderChart` L1058 확장).
7. **대표 시나리오 5종 preset** (현재 27 글로스 bundle 가용 단어로 구성):
   - Single motion: `OLA`
   - Multi-peak: `BOM DIA AMIGO`
   - Bimanual asymmetric: `FAMILIA AGUA`
   - Hold-dominant: `TER CASA`
   - Rapid succession: `EU IR ESTUDAR`

**완료 기준**: 5 시나리오 × 4 Method = 20회 batch 재생 완주 + 메트릭 JSON > 10KB + hold 구간 시각 구분 + 수동 라벨 `hold-ground-truth.json` commit.

### Phase P5.3 — production 저위험 개선 (3-5일, P5.2와 병렬)
**수정 파일**: `public/players/sentence/index.html`

1. `FADE_MIN` (L307) **0.12 → 0.20** ("slower transitions"). 런타임 `window.__fadeMin` override.
2. `BONE_WEIGHTS` (L314)에 손가락 본 `BnDedo{2..5}{R,L}` 각 0.15 추가 — handshape 차이 반영.
3. `STROKE_BONES` (L338) bimanual union: `computeStrokeRange` (L443)를 R/L 본 그룹별 독립 stroke 후 union 반환.

**완료 기준**: 27 글로스 단독 재생 가시적 회귀 0건 + 5 문장 preset 끊김 보고 0건.

### Phase P6a — 구조 변경 (Winner Port + Targetted/Lax, 3주, P5.2 완료 후)
**수정 대상**: `sentence/index.html` 상수/메서드 + 신규 `sentence/blending.js` 모듈 분리 검토

1. **Winner Method 포팅**: P5.2 메트릭+수동 라벨 합의 승자를 `computeStrokeRange`로 교체. Feature flag `window.__blendingAlgo = 'A' | 'E' | 'hybrid'` (기본 OFF).
2. **Targetted vs Lax transition**:
   - Gloss end-pose가 static(velocity ≈ 0 ≥100ms 지속) → **targetted** (길게, 정확 매칭)
   - 아니면 **lax** (짧게, ballistic)
   - `fetchClipFromEntry` (L548)에서 `endIsStatic: bool` 부여 → `computeTransitionDuration`에서 분기
3. **FADE_MIN 최종**: P5.2 데이터로 재확정.

**완료 기준**: 5 시나리오 방향성 지표(jerk RMS, boundary discontinuity) 둘 다 Method A 대비 악화 없음 + 수동 A/B 검수 (개발자 + 동료 2명) 2/3 "동등 이상" 합의 + 60fps 유지. (15% 정량 개선 요구는 Codex 지적대로 과도 → 삭제)

### Phase P6b — SQUAD 도입 spike (1-2주, P6a와 분리)
**목적**: SQUAD(Spline Quaternion)가 Three.js `AnimationMixer.crossFadeTo`(linear slerp)보다 실제로 나은지 **독립 타당성 검증**. 실패 시 과감히 버리고 slerp+M-H 조합으로 rollout.

1. **spike 구현**: P5.2 Method F 이식. `animate()` `crossFadeTo`(L1242)를 커스텀 pose-blend로 교체, 실패 시 pose-baking fallback(`onBeforeRender` bone.quaternion 강제).
2. **Go/No-Go 판정** (3일 내): 60fps 유지 불가 OR Method A 대비 jerk 동등 이하 → **즉시 폐기**. 이 경우 P6a 결과만으로 P6.5 진행.
3. **Go 시**: feature flag `window.__squadBlend = true` 추가, P6a 결과와 중첩 A/B.

**완료 기준**: Go 또는 명확한 No-Go 결정 문서화. "어중간하게 병합"은 금지.

### Phase P6.5 — Hybrid user 평가 (P6a/P6b 종료 직후 1회, 2주)

**Codex 지적 반영**: LIBRAS 사용자 한국 섭외는 현실적으로 매우 어려움. 3-track hybrid로 재설계:

| Track | 대상 | N | 측정 항목 | 방법 |
|---|---|---|---|---|
| A. Naturalness (universal) | KSL 수어 사용자 | 3-5명 | Likert: naturalness, smoothness (LIBRAS 이해 불필요) | 대면 또는 화상 |
| B. Comprehensibility (LIBRAS 필수) | Brazilian Deaf 원격 | 2-3명 | 5 시나리오 의미 맞추기 + 선호도 | 비동기 video + 설문 (Gmail/Discord 등) |
| C. Fallback | 개발자 + 수어학 전문가 | 2-3명 | Track A 축약판 | 섭외 0명일 때만 |

- **방법 공통**: A/B pair (Method A baseline vs Phase P6a [+P6b Go면]) 5 시나리오 재생.
- **결정 반영**: 통계 유의성 아님 — **방향성 signal + 다수 합의**. Track A가 과반 P6 선호 + Track B에서 comprehensibility 저하 없음 → rollout. Track B 섭외 0명이면 rollout 대신 **제한적 canary 배포**(feature flag ON 시만) 후 재평가.
- **섭외 실패 시**: Track C로 강등 + rollout 보류. 재평가 조건 문서화.

### Phase P7 — 장기 연구 (이번 재검토 **범위 외** — Codex 지적 반영, 결정 path에서 제거)

**이번 계획 범위는 명확히 P5.2 → P5.3 → P6a → P6b spike → P6.5 eval까지.** 아래는 참고 메모이며 **현 단계에서 설계·메트릭·게이트 영향 없음**:
- IK overlay: wrist world-position baked → Cartesian 보간 → IK 역산
- Non-manual track (PAULA multi-track): 얼굴/머리 별도 mixer
- Neural sign connector: 글로스 수 누적 후 rule-based regression table 선행

이 항목들은 P6.5 종료 후 별도 기획 문서에서 재검토.

---

## 의사결정 게이트

| 시점 | 질문 | 판단 데이터 | 분기 |
|---|---|---|---|
| P5.2 종료 | Method E가 A보다 우수? | **수동 라벨 HPR + spatial plateau + 자동 메트릭 방향성 일치** + 개발자 시각 A/B | Yes → P6a / Partial → hybrid 설계 / No → Method A 튜닝만 |
| P5.3 종료 | FADE_MIN 0.20 회귀 없음? | 27 글로스 시각 검수 | Yes → 유지 / No → 0.15 후퇴 |
| P6a 종료 | P6b(SQUAD) spike 시도? | P6a 안정 + 시간 여유 | Yes → P6b 3일 spike / No → P6.5로 직행 |
| P6b 중간(3일) | SQUAD Go? | 60fps 유지 & jerk RMS Method A 대비 개선 | Yes → 유지 / No → **즉시 폐기**, slerp+M-H만 |
| P6a/b 종료 | P6.5 user eval 준비 OK? | 개발자 A/B 2/3 + 메트릭 방향성 일치 | Yes → eval / No → Method A fallback |
| P6.5 종료 | Production rollout? | Track A 과반 + Track B comprehensibility 저하 없음 | Yes → 릴리즈 / Partial → canary / No → P6a 재튜닝 |

---

## 패러다임 선택 기준 (P5.2 결과 해석표)

> 수치 임계값은 **방향성 참조용**. acceptance criterion 아님 — 최종 선택은 수동 라벨 + 다수 지표 + 개발자 시각 A/B 합의.

| 선택지 | 채택 방향 signal | 배제 방향 signal |
|---|---|---|
| **Stroke 유지 (A/C 튜닝)** | 단일 peak 시나리오에서 jerk RMS 하락 + 경계 각거리 감소 | hold-dominant 시나리오 수동 라벨 HPR 현저 저하 |
| **M-H 전환 (Method E)** | 수동 라벨 HPR & spatial plateau rate 상승 + 재생시간 유지 | 단일 peak 시나리오에서 jerk 악화 |
| **Hybrid (권장 가정)** | 시나리오 타입별 signal 혼재 (예: hold-dominant는 E / single motion은 A) | — |

**cut**: IK overlay는 P7 장기 연구 — 이번 재검토 선택지 아님.

---

## 위험 관리

1. **회귀 위험**: 모든 Phase **feature flag 기본 OFF** 배포, 1주 관찰 후 ON.
2. **27→100 확장 충돌**: 신규 글로스 자동 메트릭 임계값(jerk >2×median) 경고 → "이상 글로스" 조기 탐지. **단, 27→100 확장 자체는 본 재검토 scope 밖** (별도 P5.4 트랙으로 분리) — Codex 지적 반영.
3. **"이론은 좋으나 나빠짐"**: 각 Phase git tag 롤백 경로 명문화.
4. **LIBRAS user 섭외 실패 (한국 거주 지역 한계)**: P6.5 hybrid eval로 완화 — Track A(KSL) 우선 + Track B(원격 LIBRAS) fallback + Track C(전문가) final fallback. 섭외 0명 시 canary 배포로 우회.
5. **SQUAD 구현 복잡도 (Three.js bone animation)**: P6b를 **별도 3일 spike**로 격리. Go/No-Go 명확화, 어중간한 병합 금지.
6. **Metric 오용 위험**: 자동 메트릭을 acceptance criterion으로 쓰지 않기 — signal로만. 수동 라벨 + 다수 지표 수렴 + 시각 A/B가 실제 결정 근거.

---

## 가장 중요한 첫 실험 (당장 시작할 수 있는 한 가지)

**Week 1 — sentence-stroke-test에 ① 자동 메트릭(Jerk RMS, boundary discontinuity, velocity continuity, spatial plateau) ② 5 시나리오 preset ③ 수동 hold ground truth 라벨링을 추가하여, 4 Method 방향성 baseline + HPR 계산 가능한 상태를 만든다.**

이유: "Method A가 완벽하지 않다"는 **정성적 판단**만 존재. 새 Method 설계 전에 **방향성 signal + 수동 라벨 ground truth** 확보 필요. 수동 라벨이 없으면 Method E의 HPR 평가가 순환 평가가 됨 (Codex 지적). 약 2-3일, read-only + JSON annotate라 회귀 위험 0.

**구체 실행**:
- `computeMotionProfile` (`sentence-stroke-test/index.html:786`) 재사용 → `computeBlendingMetrics(batchQueue)` 작성
- `endBatch` (L1656) 직전에 호출, `console.table` + JSON blob download
- `SCENARIOS = [...]` 상수 + 5개 preset 버튼 추가
- **수동 라벨링 프로토콜**: 5 시나리오 원본 클립을 sentence-stroke-test `frame-by-frame` 모드(신규)로 재생하며 hold 프레임 범위를 `[[start, end], ...]`로 annotate. 파일 저장: `docs-source/claudedocs/hold-ground-truth.json` (개발자 1차 + 동료 cross-check).
- Spatial Plateau 자동 검출기: FK 손목 월드 위치 `position.distanceTo(prev) ≤ 2cm` & ≥100ms 구간 → 수동 라벨과 합치도 계산.

---

## 재사용 가능한 기존 함수 / 패턴

- `sampleQuaternionAt` — `sentence/index.html:400` (바이너리 서치 + slerp)
- `extractPoseAt` — `sentence/index.html:425` (boundary pose 추출)
- `computeMotionProfile` — `sentence-stroke-test/index.html:786` (velocity/restDist/cumulative — Jerk는 velocity 1차 차분으로 파생)
- `computeTransitionDuration` — `sentence/index.html:528` (가중 RMS 각거리 = boundary discontinuity 메트릭)
- `methodA~D` — `sentence-stroke-test/index.html:854-993` (Method E/F/G 동일 signature)
- Batch crossfade animate 루프 — `sentence-stroke-test/index.html:1687-1723` (문장 비교 모드는 4 mixer 병렬로 확장)
- `METHOD_COLORS` + chart multi-trace — `sentence-stroke-test/index.html:1163-1187` (E/F/G 색 추가)

---

## Critical Files

| 파일 | 역할 |
|---|---|
| `public/players/sentence-stroke-test/index.html` | P5.2 실험대 확장 주요 타깃 |
| `public/players/sentence/index.html` | P5.3 저위험 개선 + P6a 구조 변경 + P6b spike |
| `docs-source/claudedocs/hold-ground-truth.json` | **신규** — 5 시나리오 수동 hold 라벨 (순환 평가 방지) |
| `public/animations/vlibras/bundles/index.json` | (참고) 27→100 글로스 확장은 별도 트랙 |
| `CLAUDE.md` | 의사결정 기록 + 상태 업데이트 |
| `docs-source/claudedocs/project-status.md` | Phase 진행 / 주간보고 반영 |

---

## End-to-End 검증 방법

1. **로컬 dev**: `cd public && python -m http.server 8080` → `http://localhost:8080/players/sentence-stroke-test/`
2. **Phase P5.2 검증**:
   - 5 시나리오 preset 버튼 클릭 → batch 자동 재생
   - console에 5 × 5 메트릭 표 출력 확인
   - JSON export 버튼 → 다운로드 파일 검사
   - 4-row stacked 차트에서 Method별 stroke 경계 비교
3. **Phase P5.3 검증**:
   - `http://localhost:8080/players/sentence/` 에서 27 글로스 단독 재생
   - 5 preset 문장 재생 → 끊김 없음 + fade 0.20-0.45s 분포 (`__debugBlend` 로그)
4. **Phase P6a 검증**: 위 + feature flag OFF 기본 + 시각 A/B 3명 이상 + 메트릭 방향성 일치
5. **Phase P6b 검증**: 60fps 유지(Chrome DevTools Performance) & jerk RMS Method A 대비 개선 — 둘 다 3일 내 확인 안 되면 폐기
6. **Git tag**: 각 Phase 종료 시 `p5.2-baseline`, `p5.3-safe`, `p6a-hybrid`, `p6b-squad-<go|nogo>` 태깅

---

## 확정된 의사결정 (2026-04-20 초안 → 2026-04-21 Codex 2차 검토 반영)

1. **투자 범위**: 단/중기까지 — **P5.2 + P5.3 + P6a + P6b(spike) + P6.5 eval**. P7 항목 및 27→100 확장은 이번 범위 **외**.
2. **User evaluation**: P6a(+P6b) 종료 후 hybrid 3-track — KSL(naturalness) + 원격 LIBRAS(comprehensibility) + 전문가 fallback.
3. **첫 실험 우선순위**: **baseline 수치 + 수동 ground truth 라벨링 먼저** — 5 시나리오 × Method A/B/C/D × (자동 메트릭 + 수동 HPR). Method E/F/G는 baseline 확보 후.
4. **Metric 철학**: 자동 메트릭은 **diagnostic signal**. acceptance criterion은 수동 라벨 + 다수 지표 수렴 + 시각 A/B.
5. **SQUAD 격리**: P6b 3일 spike 이상은 금지. 어중간한 부분 적용 금지.

---

## 실행 순서 (2차 확정)

```
Week 1: P5.2 Step 1-2 (메트릭 + 5 시나리오 preset) + P5.3 Step 1 (FADE_MIN 상향)
  ↓ Gate: baseline 수치 표 확보
Week 2: P5.2 Step 3-4 (수동 hold ground truth 라벨링 + Method E/G + 문장 비교 모드)
        P5.2 Step 2 (Method F SQUAD 토글 prototype — P6b spike 준비용)
  ↓ Gate: baseline + 수동 라벨 + Method E/G 메트릭
Week 3-5: P6a (Winner 포팅 + targetted/lax). feature flag OFF 배포.
  ↓ Gate: 시각 A/B 2/3 + 메트릭 방향성 일치
Week 6: P6b SQUAD 3일 spike → Go/No-Go 결정
  ↓ Gate: Go면 flag 통합, No-Go면 폐기
Week 7-8: P6.5 hybrid eval (Track A KSL 3-5명 + Track B 원격 LIBRAS 2-3명)
  ↓ Gate: Track A 과반 + Track B 저하 없음 → rollout / Partial → canary / No → P6a 재튜닝 (+2주)
```

---

## 참고 자료 (주요 인용)

### 학술 논문
- **Liddell & Johnson (1989)** — M-H model 원전
- **Brentari (1998)** — *A Prosodic Model of Sign Language Phonology*, MIT Press
- **Tyrone & Mauk (2010)** — "Sign lowering and phonetic reduction in ASL", *J. Phonetics* 38(2), [DOI](https://doi.org/10.1016/j.wocn.2010.02.003)
- **Naert, Larboulette, Gibet (2020)** — "A survey on the animation of signing avatars", *Computers & Graphics* 92
- **Wolfe, McDonald et al.** — Paula 시스템, "Transitions are the key"
- **Heloir & Kipp (2009)** — EMBR, IVA 2009 (spline quaternion 실증)
- **Kovar, Gleicher, Pighin (2002)** — Motion Graphs, SIGGRAPH
- **Kendon (1980/2004)** — *Gesture: Visible Action as Utterance* (stroke 용어 원전)

### 산업/오픈소스
- **VLibras** — [spbgovbr-vlibras GitHub](https://github.com/spbgovbr-vlibras), WikiLibras 애니메이션 가이드
- **JASigning / SiGML** — [UEA Virtual Humans](https://vh.cmp.uea.ac.uk/index.php/JASigning_Demos), SLPA 기반 posture-transition 모델
- **SignAvatars** — ECCV 2024, neural sign connector
- **Hand Talk** — 브라질 LIBRAS (기술 비공개)
- **Kara Technologies** — KNS + Sign Blending Engine

### 프로젝트 내 참조
- `docs-source/claudedocs/vlibras-translation-api.md` — 번역 API 스펙
- `docs-source/standards/ABNT_NBR25606_annex_CD.md` — SLMB 모션 전송
- `tools/vlibras2slmb/parsing/asset_bundle.py` — AssetBundle 파싱 (phase marker 없음 확인)
