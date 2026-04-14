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
| **Bundle 사전 변환기** | ✅ 완료 (27 글로스) | `tools/vlibras2slmb/batch/precompute_threejs.py` |
| Model Viewer | ✅ 완료 | `public/players/viewer/` |
| VLibras→SLMB 변환기 | 🔄 매핑 완료, 파이프라인 미완 | `tools/vlibras2slmb/` |
| 랜딩 페이지 | ✅ 완료 | `public/index.html` |
| 문서 페이지 | ✅ 완료 | `public/docs/` |
| Vercel 배포 | ✅ 완료 | Git push 자동 배포 |

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

### P5: 모션 블렌딩 — 글로스 간 자연스러운 연결
- **목표**: 수어문의 글로스 시퀀스(예: `EU BEBER AGUA`)가 현재는 고정 `CROSSFADE_SEC=0.2s`의 단순 fade로만 이어지는데, 글로스 경계에서 손목·팔꿈치·어깨 관절이 튀는 현상을 개선해 실제 수어와 유사한 연속 동작을 만든다.
- **현재 한계**:
  - `public/players/sentence/index.html`의 `playQueue()`가 `mixer.crossFadeTo(next, 0.2, true)` 호출만으로 전환 — 두 클립의 시작/끝 포즈 간 위치 차이가 크면 "워프" 효과 발생
  - crossfade는 quaternion SLERP 기반이라 긴 거리 이동 시 직선 보간이 돼 실제 손 궤적과 맞지 않음
  - 글로스 간 휴지(idle gap) 포즈가 없어서 의미 경계가 흐려짐
- **접근 후보**:
  1. **동적 crossfade 길이**: 두 클립 경계의 관절 delta에 비례해 전환 시간 조정 (delta 크면 longer, 작으면 shorter)
  2. **Transition 구간 생성**: 글로스 끝 포즈 → neutral rest pose → 다음 글로스 시작 포즈 3-segment bridging
  3. **IK-based 손 궤적 보정**: 손목 위치를 Cubic Bezier/Catmull-Rom으로 보간하면서 팔꿈치는 2-bone IK로 역산
  4. **Anticipation/overshoot easing**: 글로스 시작 직전 anticipation(역방향 미세 이동), 끝 직후 overshoot로 실제 수어의 리듬 재현
- **검증**: Playwright 영상 녹화 + VLibras 공식 위젯 비교 (같은 문장의 부드러움 상대 평가). 정량 metric은 손목 velocity profile의 평균 jerk 값.
- **관련 파일**: `public/players/sentence/index.html:playQueue`, `rebuildActionsForCurrentModel`, `CROSSFADE_SEC` 상수

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

### 종합 정리 (아이템별)

- Sentence Player (P1) 파이프라인 구축
  1. VLibras 번역 API 스펙 실측·확정
     1) `POST https://traducao2.vlibras.gov.br/translate`, JSON body `{"text":"..."}`, plain text 응답
     2) `\s+` split 파싱, CORS 직접 허용 → Vercel rewrite 불필요
  2. AssetBundle → Three.js JSON 배치 변환기 (`tools/vlibras2slmb/batch/precompute_threejs.py`)
     1) UnityPy 1.25 lowercase API 대응 인라인 리더 내장
     2) `--legacy` 기본 적용
  3. 레거시 retarget 파이프라인 역공학
     1) yz sign flip `(x,y,z,w)→(x,-y,-z,w)` 모든 body bone 회전에 적용
     2) Icaro-bind 7개 헬퍼 본 (`BnBacia001`, `BnMaoOrientR/L`, `BnPolyVR/L`, `ik_FKR/L`) 정적 override
     3) position tracks는 Icaro bind pose 값으로 2-keyframe static 고정
     4) Playwright 픽셀 검증 — `CASA`·`ESCOLA` 레퍼런스 대비 bone delta ≤ 6mm
  4. 신규 플레이어 `public/players/sentence/index.html`
     1) 문장 입력 → 번역 → ASCII 키 정규화(`NFKD`) → 사전 변환 번들 fetch → 재생
     2) 글로스 칩 UI (미싱 ⚠️ 표시)
     3) 큐잉 + crossfade 연속 재생 (`CROSSFADE_SEC=0.2s`)
     4) `mixer.addEventListener('finished')` + 렌더 루프 timeLeft 체크 → `crossFadeTo`로 다음 액션
     5) `stopAndDisposeQueue()` 메모리 정리, 재번역 5연속 누수 없음 확인
  5. 융합 토큰 폴백
     1) `BOM_DIA` 같은 융합 토큰을 `_`로 split하여 sub-token 재조회
     2) 모든 sub-token이 resolve될 때만 fallback 적용 (부분 확장 금지)
  6. Playwright E2E 검증 — `Olá casa`(4.833s), `Sim bom dia`(7.1s), `Casa escola não`(8.367s) 등 20+ 시나리오
- VLibras 공식 위젯 통합
  1. CDN 임베드 (`vlibras.gov.br/app/vlibras-plugin.js`)
     1) `<div vw>` 컨테이너 + `vw-access-button` + `vw-plugin-wrapper` 마크업
     2) `new VLibras.Widget({rootPath, position:'R', opacity:1})` 인스턴스화
  2. 토글 버튼 (`#vlibras-toggle`)
     1) 컨트롤 바 우측에 `🤟 위젯` 버튼 추가, `model-btn` 클래스 재사용
     2) 토글 OFF 기본 — `[vw]`의 `enabled` 클래스만 관리 (active 강제 토글은 제거)
     3) `localStorage['vlibrasPluginEnabled']`로 상태 복원
     4) 첫 ON에서 `[vw-access-button]` 자동 클릭 디스패치 → `window.plugin` lazy 초기화 선행
  3. 동기화 함수 `syncToVLibrasPlugin(text)`
     1) Tier 1: `plugin.translate(text)` 직접 호출
     2) `plugin.player.translate(text)` 폴백
     3) `waitForVlibrasPlugin(2500ms)` polling으로 lazy 인스턴스 생성 대기
     4) Tier 2/3/4(Selection 트릭·입력박스 스크래핑·안내 UI) 미구현 — Tier 1이 동작하므로 dead code 회피
     5) `handleTranslate()` 성공 후 `playQueue()` 직후 fire-and-forget 호출, throw 없음
  4. `safeClick` WeakMap dispatcher로 위젯 click 가로챔 우회
     1) 위젯이 document capture phase에서 전역 click을 가로채 chrome 버튼 핸들러 차단 + 버튼 textContent 자동 번역 트리거
     2) `window` capture phase에서 먼저 가로채는 `__vlibrasSafeClickHandlers` WeakMap dispatcher 추가
     3) `translate-btn`, `vlibras-toggle`에 적용
     4) Plan에 없던 추가 구현이지만 필수
  5. Plan과 다른 결정 — `[vw-access-button]`/`[vw-plugin-wrapper]`의 `active` 클래스는 강제 토글하지 않음 (플러그인 내부 상태머신이 사용자가 펼치는 순간 즉시 리셋)
- 어휘 확장 21 → 27 (MORAR/QUERER/ESTUDAR/IR/TER/FALAR), 다음 100 목표
- 테스트 가이드 — 24개 실측 문장 5범주 + 회귀 5문장 시퀀스
- 메인 vs. VLibras 위젯 chirality 차이 분석
  1. 관찰 — 메인 = 오른손, 위젯 = 왼손 (gov.br 공식도 동일)
  2. 원인 — precompute X-mirror가 Icaro bind pose의 X-mirror된 R/L 배치와 self-consistent
  3. LIBRAS 컨벤션
     1) 양손 모두 valid (signer dominance 자유)
     2) 학술 문서화는 오른손 표준, 위젯 dominant-hand 옵션 부재
  4. 결론 — 둘 다 valid, 코드 수정 없음. 분석 문서 + 알려진 이슈 #7 추가
- 저장소·배포 인프라
  1. `slmb/` + `vlibras/` → `sls_brazil_player` 단일 저장소 통합
  2. 공유 `public/avatars`·`public/animations` + 랜딩·문서 페이지
  3. GitHub 저장소 + Vercel 정적 배포 (Git push 자동)
- 문서·워크스페이스 정리
  1. `CLAUDE.md`, `project-status.md`, plan 문서 헤더 갱신
  2. `.gitignore` — `/*.png`, `.playwright-mcp/`, `/vlibras-portal/`(2.1GB)
  3. 루트 Playwright PNG 31개·캐시 디렉토리·검증 스크린샷 삭제

---

### 2026-04-14 (화)
- [완료] **Sentence Player ↔ VLibras 공식 위젯 통합** — 한 번의 문장 입력으로 로컬 Three.js 아바타와 공식 위젯 Unity WebGL 아바타가 동시에 같은 문장을 재생
  - 공식 CDN 위젯 임베드 (`vlibras.gov.br/app/vlibras-plugin.js`), 토글 OFF 기본, `localStorage`로 상태 복원
  - `syncToVLibrasPlugin(text)` + `waitForVlibrasPlugin(2500ms)` 구현. Tier 1 `plugin.translate(text)` 성공 확인 → Tier 2/3/4 폴백 생략
  - 첫 ON에서 `[vw-access-button]` 자동 클릭해 `window.plugin` lazy 초기화 선행
- [완료] **VLibras 위젯 click 가로챔 우회**: 위젯이 document capture phase에서 전역 click을 가로채 우리 chrome 버튼의 핸들러 호출을 막고 버튼 textContent까지 자동 번역해버리는 충돌 발견 → `safeClick()` WeakMap 기반 window-capture dispatcher로 우회. `translate-btn`, `vlibras-toggle`에 적용
- [완료] **문서 정리**: `sentence-vlibras-plugin-integration-plan.md` 헤더에 구현 결과 요약 추가, `vlibras-portal/`(2.1GB 참조 클론)을 `.gitignore`에 등록, 루트 검증용 PNG 제거
- [완료] **메인 vs. 위젯 chirality 차이 분석**: 사용자가 두 아바타의 손잡이(메인=오른손, 위젯=왼손) 차이를 보고 → 코드 추적, LIBRAS 학술 컨벤션 조사, VLibras 위젯 옵션 조사. 결론: 두 표현 모두 LIBRAS 측면에서 valid (메인은 학술 문서화 컨벤션에 부합, 위젯은 VLibras 공식 채널 일관 베이크). 수정 작업 없음. 분석 문서 [`avatar-handedness-analysis.md`](avatar-handedness-analysis.md) 작성 + 알려진 이슈 #7 추가
- [예정] 어휘 확장 (27 → 100 수준), `asset_bundle.py` UnityPy 1.25+ 마이그레이션(P2 선행), Sentence Player seek(P4)

### 2026-04-13 (월)
- [완료] **P1 end-to-end 파이프라인 구축 완료** (M0~M5)
  - VLibras 번역 API 스펙 실측 확정 (POST JSON, plain text 응답, CORS 직접 허용)
  - Unity AssetBundle → Three.js JSON 배치 변환기 구현
  - 레거시 변환 파이프라인 역공학 성공 (yz sign flip + Icaro-bind override + Playwright 픽셀 검증)
  - `public/players/sentence/` 신규 플레이어 구현 (번역 + 큐잉 + crossfade)
  - Playwright E2E 검증: `Olá casa`(4.833s), `Sim bom dia`(7.1s), `Casa escola não`(8.367s) 모두 성공
  - 융합 토큰 폴백 로직 (`BOM_DIA` → `BOM`+`DIA` 자동 분해)
- [완료] **어휘 확장 (21 → 27)**: MORAR, QUERER, ESTUDAR, IR, TER, FALAR 추가. "Eu morar casa" 같은 흔한 문장이 바로 작동
- [완료] **테스트 가이드 작성**: 24개 VLibras 실측 문장을 project-status.md 하단에 5개 범주로 정리. 회귀 테스트 5문장 시퀀스 제안
- [완료] **Git 커밋·푸시 6회**: C213429 → 2D94138 → E474B48 → A482322 → DECA3DF 등
- [완료] **워크스페이스 정리**: 루트 Playwright PNG 31개 + `.playwright-mcp/` 디렉토리 삭제, `.gitignore`에 재발 방지 규칙 추가
- [예정] 어휘 확장 (27 → 100 수준), `asset_bundle.py` UnityPy 드리프트 수정, Sentence Player seek 기능(P4)

### 2026-04-08 (화)
- [완료] `slmb/`, `vlibras/` 두 프로젝트를 단일 저장소로 통합
- [완료] 공유 아바타/애니메이션 폴더 구성, 메인 랜딩 페이지 생성
- [완료] Git 저장소 생성, Vercel 배포 완료
- [완료] 프로젝트 현황 문서 작성
- [완료] P1 번역 파이프라인 구축 (2026-04-13로 이관)

---

## 작업 이력

### 2026-04-14
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
