# Sentence Player에 VLibras 공식 플러그인 통합 — 구현 계획

작성일: 2026-04-13
구현일: 2026-04-14
대상 파일: `public/players/sentence/index.html`
관련 디렉토리: `vlibras-portal/` (공식 VLibras 포털 참조 클론, `.gitignore` 대상)
상태: ✅ 구현 완료 — Tier 1 (`window.plugin.translate`) 경로로 동기화 동작 확인. Tier 2/3/4 폴백은 불필요해 생략.

## 구현 결과 요약 (2026-04-14)

- **임베드**: `public/players/sentence/index.html` line 1035-1049에 `<div vw>` + CDN 스크립트 + `VLibras.Widget({position:'R', opacity:1})` 추가. 토글 OFF 기본.
- **토글 버튼**: line 216에 `#vlibras-toggle` 추가 (`model-btn` 클래스 재사용). `localStorage['vlibrasPluginEnabled']`로 상태 복원. 첫 ON 시 `[vw-access-button]` 클릭을 자동 디스패치해 `window.plugin` lazy 초기화를 선행.
- **동기화 함수**: line 805-863 `syncToVLibrasPlugin(text)` + `waitForVlibrasPlugin(2500ms)`. Tier 1 `plugin.translate(text)` → fallback `plugin.player.translate(text)`. 두 경로 모두 실패해도 throw하지 않음.
- **호출 지점**: `handleTranslate()` 성공 후 `playQueue()` 직후(line 937)와 글로스 큐가 비어있는 분기(line 931)에서 fire-and-forget 호출.
- **발견한 충돌**: VLibras 위젯이 document capture phase에서 click을 가로채 우리 chrome 버튼의 핸들러 호출을 막고 버튼 textContent까지 자동 번역해버리는 문제 발견. **해결**: line 481-501에 `safeClick()` 헬퍼 추가 — `window` capture phase에서 먼저 가로채는 WeakMap 기반 dispatcher. `translate-btn`, `vlibras-toggle`에 적용. Plan에 없던 추가 구현이지만 필수였음.
- **Plan과 다른 결정**: 토글 핸들러에서 `[vw-access-button]`/`[vw-plugin-wrapper]`의 `active` 클래스는 건드리지 않음 (플러그인 내부 상태머신이 즉시 리셋해서 사용자가 펼치는 순간 원상복구됨). `enabled` 클래스만 관리.
- **Tier 2/3 생략**: Tier 1이 확실히 동작하므로 Selection 트릭과 입력박스 스크래핑은 dead code로 남기지 않고 미구현.
- **Tier 4 안내 UI 생략**: `console.warn` 1회만 남기고 사용자 안내 배너는 추가하지 않음. 필요해지면 별도 작업.

---

## Context

### 왜 이 작업을 하는가
- **현재 상태**: `public/players/sentence/index.html`은 자체 Three.js 파이프라인으로 VLibras 번역 결과를 재생한다. 메인 캔버스에 Padrao/CASA/Icaro 아바타 중 하나를 띄우고 사전 변환된 `.threejs.json` 글로스 번들을 큐잉/크로스페이드한다.
- **요구사항**: `vlibras-portal/`(공식 VLibras 포털 클론) 안에 있는 임베디드 플러그인(통칭 "VLibras Widget" 또는 "barra")을 sentence 페이지에 통합하여, 한 번의 문장 번역으로 **메인 캔버스의 Three.js 아바타**와 **플러그인의 자체 Unity WebGL 아바타**가 동시에 같은 문장을 재생하도록 한다.
- **부가 요구사항**: 플러그인은 hide/unhide 토글이 가능해야 한다(기본은 숨김).

### 의도하는 결과물
사용자가 sentence 페이지에서 포르투갈어 문장을 입력하고 "번역 & 재생"을 누르면:
1. 메인 Three.js 아바타가 기존대로 글로스 큐를 재생한다 (변경 없음).
2. 플러그인이 숨김 상태가 아니라면, 같은 문장을 플러그인 내부 경로로 재생한다 (두 아바타가 나란히 동일 문장을 보여줌).
3. 상단 컨트롤 바의 토글 버튼으로 플러그인을 언제든 보이거나 숨길 수 있다.

이 기능은 ABNT/VLibras 두 축의 시각적 비교, 데모, QA 검증에 직접 활용된다.

---

## 발견 사항 요약 (탐색 결과)

### vlibras-portal 플러그인 구조 (확정)
- **공식 임베드 스니펫** (출처: `vlibras-portal/doc/widget/_sources/installation/webpageintegration.rst.txt` 및 `vlibras-portal/app/index.html:199-209`):
  ```html
  <div vw class="enabled">
    <div vw-access-button class="active"></div>
    <div vw-plugin-wrapper>
      <div class="vw-plugin-top-wrapper"></div>
    </div>
  </div>
  <script src="https://vlibras.gov.br/app/vlibras-plugin.js"></script>
  <script>
    new window.VLibras.Widget({
      rootPath: 'https://vlibras.gov.br/app',
      position: 'R',
      opacity: 1,
      avatar: 'icaro'
    });
  </script>
  ```
- **CDN 로드**: 자체 호스팅 불필요. `vlibras.gov.br/app/vlibras-plugin.js`가 14.9KB 부트스트랩 + 동적으로 ~300KB chunk를 로드한다. 브라우저는 `dicionario2.vlibras.gov.br/bundles`(사인 번들)와 `traducao2.vlibras.gov.br/translate`(번역 API)에 자체적으로 접근한다.
- **렌더링**: iframe 아님. Unity WebGL이 `<div vw>` 내부의 캔버스에 렌더링된다.
- **DOM 루트**: `<div vw>` (커스텀 attribute, 클래스 아님). 기본 `display:none`, `.enabled` 추가시 표시.

### Hide/Show 메커니즘 (확정)
| 동작 | 조작 |
|---|---|
| 위젯 자체 표시/숨김 | `[vw]`에 `enabled` 클래스 추가/제거 |
| 위젯 펼치기/접기 | `[vw-access-button]`, `[vw-plugin-wrapper]`에 `active` 클래스 추가/제거 |
| 위치 변경 | `dispatchEvent(new CustomEvent('vp-widget-wrapper-set-side', {detail:'R'}))` (값: TL/T/TR/L/R/BL/B/BR) |

### 프로그래매틱 재생 API (핵심 위험)
- **공식 API 없음**. 플러그인은 의도적으로 "선택 텍스트 → 번역 → 재생" 사용자 흐름만 지원하도록 블랙박스화되어 있다.
- **존재 가능성 있는 비공식 메서드** (`vlibras-plugin.js` / `vlibras-plugin.chunk.js` 정적 분석에서 발견된 prototype 식별자):
  - `window.plugin` (위젯 첫 클릭 후 생성되는 Plugin 인스턴스)
  - `window.plugin.translate` (확률 높음, 시그니처 미상)
  - `window.plugin.setGloss`, `window.plugin.play` (확률 중간)
  - `window.plugin.player.translate(text)` (확률 중간)
  - `window.plugin.player.avatar` (확정, 현재 아바타 참조)
- **확정된 우회 경로**:
  - `window.getSelection()`로 페이지 안 텍스트를 강제 선택 → 플러그인이 Selection 변화를 감지해 "번역" 미니 버튼을 띄움 → 그 버튼을 프로그래매틱 클릭.
  - 또는 플러그인이 펼쳐졌을 때 내부에 노출되는 입력 박스를 DOM 스크래핑으로 찾아 값 주입.
- **확정된 커스텀 이벤트** (위치 제어용, 재생에는 쓸 수 없음):
  - `vp-widget-wrapper-set-side`
  - `vp-widget-close`
  - `vw-change-opacity`

### Sentence Player 코드 지점 (변경 대상)
모두 `public/players/sentence/index.html` 한 파일. 탐색 시점 기준 라인 번호.

| 영역 | 라인 | 역할 |
|---|---|---|
| `<style>` | 7-201 | CSS — 토글 버튼/플러그인 위치 보정 추가 위치 |
| `#controls` 래퍼 | 207-216 | 토글 버튼 추가 위치 (모델 선택 버튼 옆) |
| body 끝 | 246 직전 | VLibras 임베드 스니펫 삽입 위치 |
| import map | 249-256 | 변경 없음 |
| `MODELS` 등 config | 263-270 | 변경 없음 |
| `handleTranslate()` | 783-858 | 번역 성공 후 `syncToVLibrasPlugin(text)` 호출 추가 (~line 850) |
| `translateBtnEl` 바인딩 | 860 | 변경 없음 |
| 초기화 시퀀스 | 905-911 | 플러그인 부트스트랩 헬퍼 등록 추가 |

**주요 함수 (기존)**:
- `handleTranslate()` (line 783): 번역 버튼 클릭 핸들러
- `translateSentence(text)` (line 417): VLibras 번역 API 호출
- `loadGlossClip(gloss)` (line 383): 글로스 → clip 매핑
- `playQueue()` (line 621): 큐 재생 시작
- `rebuildActionsForCurrentModel()` (line 549): 믹서/액션 재생성

플러그인 기본 위치 `'R'`(우측 세로 중앙)은 기존 `#controls`(상단 가로 전체), `#info`(좌측 상단), `#player-bar`(하단 가로 전체), `#error-banner`(중앙 상단)와 시각적으로 충돌하지 않는다.

---

## 권장 구현 전략

### 핵심 원칙
1. **메인 파이프라인은 절대 건드리지 않는다**: 기존 Three.js 큐잉/크로스페이드 로직은 단 한 줄도 수정하지 않는다. 동기화는 `handleTranslate()` 성공 분기에 비동기 fire-and-forget 호출 한 줄을 추가하는 형태로만.
2. **다층 폴백**: 비공식 API → Selection 트릭 → 독립 운영. 각 단계는 try/catch + 시간 제한으로 격리한다.
3. **사용자가 명시적으로 끌 수 있어야 한다**: 토글 OFF 상태에서는 동기화도 시도하지 않는다 (자원 절약 + 의도 명확).
4. **단일 파일 유지**: sentence 플레이어는 본래 `index.html` 한 파일 구조다. 새 JS/CSS 파일을 만들지 말고 같은 파일 안에 추가한다.

### 동기화 전략 — 우선순위 사다리

`syncToVLibrasPlugin(text)` 호출 시 아래 순서로 시도하고, 첫 성공에서 멈춘다. 각 시도는 50~150ms 타임아웃.

**Tier 1 — 비공식 메서드 직접 호출**
```js
if (window.plugin?.translate) { window.plugin.translate(text); return; }
if (window.plugin?.player?.translate) { window.plugin.player.translate(text); return; }
```
**구현 단계 필수 작업**: 먼저 devtools 콘솔에서 `console.dir(window.plugin)`을 실행해 실제로 어떤 메서드가 prototype에 노출되어 있는지 직접 확인할 것. 미리 추측해서 코드 박지 말 것.

**Tier 2 — Selection API 트리거**
- `#vlibras-text-buffer`라는 화면에 안 보이는 (visually hidden, but selectable) 스팬을 미리 body에 만들어둔다.
- `text`를 그 스팬의 textContent에 넣는다.
- `Range`로 그 스팬을 감싸 `window.getSelection().removeAllRanges() / addRange()` 호출.
- `mouseup` 이벤트 디스패치.
- 위젯이 selection을 감지해 작은 "번역" 버튼을 띄우면 그것을 전용 selector로 찾아 `.click()`.
- 100ms 후 selection 해제.

**구현 단계 필수 작업**: Tier 2 selection-translate 버튼의 정확한 selector는 devtools로 직접 발견해야 한다. 페이지에서 임의 텍스트를 마우스로 선택했을 때 플러그인이 만들어주는 DOM을 Elements 탭에서 관찰할 것.

**Tier 3 — 입력 박스 스크래핑** (위젯이 펼쳐진 상태에서만 동작)
- 펼친 플러그인 wrapper 안에서 `input[type=text]`를 찾아 값 주입 후 Enter 키 이벤트 디스패치.
- 가장 깨지기 쉬움 — 플러그인 버전 업그레이드시 매번 검증 필요. Tier 2 실패시에만 고려.

**Tier 4 — 독립 운영 안내**
- 위 셋 모두 실패시: 콘솔에 한 번만 `console.warn`하고, `#info` 영역에 작은 회색 자막으로 "VLibras 위젯은 독립 동작 모드입니다" 표시. 사용자가 위젯의 자체 입력으로 계속 사용할 수 있다.

`syncToVLibrasPlugin`은 절대 throw하지 않으며, 메인 재생을 절대 막지 않는다. 모든 시도는 `Promise`로 감싸고 외부에서 `void`로 호출한다.

### 토글 동작
- 컨트롤 바 우측 끝(모델 선택 버튼들 다음)에 `<button id="vlibras-toggle" class="model-btn">🤟 위젯</button>` 추가.
- 클릭시:
  - **OFF → ON**: `[vw]`에 `enabled` 추가, `[vw-access-button]`/`[vw-plugin-wrapper]`에 `active` 추가, 버튼에 `.active` 추가, `localStorage`에 상태 저장.
  - **ON → OFF**: 위 클래스들 모두 제거, 버튼 비활성화 모양으로 복귀.
- **초기 상태**: `localStorage.vlibrasPluginEnabled === 'true'`면 ON, 그 외에는 OFF (기본 숨김).
- **첫 ON 시점에 플러그인 부트스트랩**: 플러그인 스크립트와 컨테이너 div는 페이지 로드시 항상 삽입하지만 `enabled` 클래스만 빠진 상태로 둔다. (지연 부트스트랩보다 단순하고, CDN 다운로드는 어차피 한 번이라 비용 차이 없음.)

### 시각 충돌 회피
- 플러그인 위치는 `'R'` 고정 (생성자 인자로 전달).
- `#info` 패널이 스크롤되지 않으므로 좌측 상단은 충돌 없음.
- `#player-bar`(하단)와 `#controls`(상단)는 가로 전체이지만 플러그인은 우측 세로 중앙(약 40px 너비 collapsed, 300x450 expanded)이라 컨트롤 바 우측 끝(speed 슬라이더 영역)과 약간 겹칠 수 있다 → 플러그인 펼침시에만 z-index로 위에 뜨게 두고, 사용자가 닫으면 원상복구된다. 추가 CSS 보정 불필요.

---

## 단계별 구현 순서

각 단계는 독립적으로 검증 가능하다. 단계 사이마다 브라우저에서 수동 확인.

### Step 1 — 플러그인 임베드 (정적, 동기화 없음)
**목표**: 페이지 로드시 플러그인이 DOM에 존재하고, 우측에 떠 있고, 자체 입력으로 번역/재생이 동작.

1. `index.html` `</body>` 직전(라인 246-247 사이)에 임베드 스니펫 삽입:
   ```html
   <!-- VLibras 공식 위젯 (CDN). 토글 OFF 기본. -->
   <div vw>
     <div vw-access-button></div>
     <div vw-plugin-wrapper>
       <div class="vw-plugin-top-wrapper"></div>
     </div>
   </div>
   <script src="https://vlibras.gov.br/app/vlibras-plugin.js"></script>
   <script>
     new window.VLibras.Widget({
       rootPath: 'https://vlibras.gov.br/app',
       position: 'R',
       opacity: 1
     });
   </script>
   ```
2. `enabled` 클래스가 빠져 있으므로 플러그인은 보이지 않아야 함.
3. devtools에서 수동으로 `document.querySelector('[vw]').classList.add('enabled')` 입력 → 우측에 위젯 버튼이 떠야 함.
4. 클릭 → 펼침 → 자체 입력으로 "casa bonita" 번역/재생 동작 확인.

### Step 2 — 토글 버튼
**목표**: 컨트롤 바 토글로 플러그인 표시/숨김 동작.

1. `#controls`(라인 207-216)에 마지막 자식으로 추가:
   ```html
   <button id="vlibras-toggle" class="model-btn" type="button">🤟 위젯</button>
   ```
   (`model-btn` 클래스 재사용으로 스타일 동일.)
2. `<script type="module">` 안 초기화 영역(라인 905-911 부근)에 토글 핸들러 추가:
   - `localStorage.getItem('vlibrasPluginEnabled') === 'true'`로 초기 상태 결정.
   - 클릭시 `[vw]` 토글, `[vw-access-button]`/`[vw-plugin-wrapper]` `active` 토글, 버튼 `.active` 토글, `localStorage` 저장.
3. 검증: 토글 ON → 우측에 위젯 등장 → 토글 OFF → 사라짐. 새로고침 후 마지막 상태 복원 확인.

### Step 3 — 동기화 함수 골격
**목표**: `handleTranslate()` 성공 후 `syncToVLibrasPlugin(text)` 호출. 토글 OFF면 즉시 리턴.

1. `<script type="module">` 안 적당한 위치(예: `handleTranslate` 직전, 라인 782 부근)에 함수 추가:
   ```js
   async function syncToVLibrasPlugin(text) {
     const wrapper = document.querySelector('[vw]');
     if (!wrapper?.classList.contains('enabled')) return;  // 토글 OFF
     // Tier 1 → 2 → 3 → 4 시도 (아래 Step 4-6 참조)
   }
   ```
2. `handleTranslate()` 안, 라인 850(`playQueue();` 호출 직후)에 한 줄 추가:
   ```js
   playQueue();
   syncToVLibrasPlugin(text);  // fire-and-forget
   ```
3. 검증: 토글 ON 상태로 번역 → 콘솔에 호출됨 확인 (아직 동작 X).

### Step 4 — Tier 1 (비공식 API 시도)
**목표**: `window.plugin.translate(text)` 등 발견된 메서드 호출.

1. **먼저 devtools 콘솔에서 실제 메서드 확인**:
   ```js
   console.dir(window.plugin);
   console.dir(window.plugin.player);
   console.dir(window.plugin.player.player); // Unity Module
   ```
2. 발견한 메서드를 Tier 1 시도에 하드코딩:
   ```js
   const candidates = [
     () => window.plugin?.translate?.(text),
     () => window.plugin?.player?.translate?.(text),
     () => window.plugin?.translateText?.(text),
   ];
   for (const fn of candidates) {
     try {
       const r = fn();
       if (r !== undefined) return; // 성공
     } catch {}
   }
   ```
3. 검증: 토글 ON + 번역 → 플러그인 아바타가 같은 문장 재생하면 성공 → 끝. 실패면 Step 5로.

### Step 5 — Tier 2 (Selection 트릭) — Tier 1 실패시에만 필요
**목표**: 화면 밖 스팬에 텍스트 넣고 강제 선택해 플러그인 selection 핸들러 트리거.

1. body에 한 번만 추가되는 hidden 스팬 만드는 헬퍼:
   ```js
   function ensureTextBuffer() {
     let s = document.getElementById('vlibras-text-buffer');
     if (s) return s;
     s = document.createElement('span');
     s.id = 'vlibras-text-buffer';
     s.style.cssText = 'position:fixed;left:-9999px;top:0;user-select:text;';
     document.body.appendChild(s);
     return s;
   }
   ```
2. Tier 2 시도:
   - 스팬에 텍스트 주입.
   - `Range`로 감싸 `getSelection().addRange()`.
   - `mouseup` 이벤트 디스패치(플러그인이 selection 핸들러를 mouseup으로 감지하는 패턴이 일반적).
   - 100ms 대기 후 플러그인이 만들어준 selection-translate 버튼 selector로 `.click()`.
   - 성공 후 selection 해제.
3. **selector는 devtools로 직접 발견해야 함** — 미리 추측 금지.
4. 검증: 같은 방법으로 두 아바타가 동시에 재생되면 성공.

### Step 6 — Tier 3/4 폴백 — Tier 2도 실패시
**Tier 3**: 펼친 플러그인 안 입력 박스 직접 스크래핑. 구현은 단순하지만 깨지기 쉽다. 위젯 펼침 상태가 전제이므로 사용자 경험이 떨어짐 → 권장 안 함.

**Tier 4**: 플러그인을 독립 운영으로 두고 사용자 안내 한 줄 표시. 동기화는 포기. 사용자가 직접 위젯 입력에 같은 문장을 다시 입력해서 재생할 수 있다. 마지막 안전망.

---

## 변경 파일 목록

단 한 파일만 수정한다.

| 파일 | 변경 종류 | 위치 |
|---|---|---|
| `public/players/sentence/index.html` | HTML 추가 | 라인 215 직후 (토글 버튼), 라인 246 직전 (플러그인 임베드) |
| 같은 파일 | 모듈 스크립트 추가 | 라인 782 부근 (`syncToVLibrasPlugin` 함수), 라인 850 (`handleTranslate` 호출 추가), 라인 911 부근 (토글 핸들러 등록) |
| 같은 파일 | CSS 추가 (필요시) | 기존 `.model-btn.active` 스타일 재사용으로 대부분 스킵 가능 |

새 파일 생성하지 않는다. 기존 함수(`handleTranslate`, `playQueue`, 모델 로더 등)의 시그니처는 건드리지 않는다.

---

## 검증 계획

각 단계마다 로컬 서버를 띄우고 수동 테스트.

```bash
cd D:/lg/work/SLS/brazil/code/sls_brazil_player/public
python -m http.server 8080
# http://localhost:8080/players/sentence/
```

### 시나리오 1 — 토글 동작
1. 페이지 첫 방문 → 우측에 위젯 보이지 않음
2. "🤟 위젯" 토글 클릭 → 우측에 VLibras 위젯 등장
3. 다시 클릭 → 사라짐
4. ON 상태에서 새로고침 → ON 유지

### 시나리오 2 — 메인 파이프라인 회귀
1. 토글 OFF로 "casa" 번역 → 메인 캔버스 아바타가 기존대로 재생
2. "bom dia" 번역 → 글로스 chip이 정상 표시되고 큐가 흐름
3. 모델 변경(Padrao/CASA/Icaro) → 정상 동작
4. 알 수 없는 단어 입력 → `#error-banner` 정상 표시

### 시나리오 3 — 동기화 (핵심)
1. 토글 ON으로 "casa bonita" 번역 → 메인 아바타와 위젯 아바타 둘 다 재생을 시도해야 함.
2. 어느 Tier가 동작했는지 콘솔 로그로 명시.
3. 메인 아바타가 글로스를 끝낼 때까지 위젯이 최소한 시작은 했는지 확인 (시간차 허용 — 동기 타이밍 보장은 비목표).
4. Tier 4(독립 운영)로 떨어진 경우 `#info` 안에 안내 문구 표시 확인.

### 시나리오 4 — 시각 충돌
1. 위젯 ON + 펼침 → `#player-bar`의 speed 슬라이더 영역과 약간 겹치는지 확인. 펼침 상태에서만 z-index로 위에 떠야 함.
2. `#error-banner` 표시중에 위젯 ON → 둘 다 보여야 함.
3. 모바일/좁은 viewport에서 위젯이 컨트롤 영역을 가리지 않는지 확인.

### 시나리오 5 — 네트워크 오프라인
1. devtools Network 탭을 offline으로 → 토글 ON → 위젯이 로드 실패해도 메인 페이지/메인 재생은 영향받지 않아야 함.
2. 콘솔 에러만 발생하고 사용자에게는 조용히 실패.

### 시나리오 6 — Tier 검증 (구현 단계에서 발견 필요)
- Step 4 구현 후 콘솔에서 `window.plugin`을 확인하고, 어떤 메서드가 실제 호출 가능한지 발견하면 plan에 기록.
- Tier 1이 동작하면 Tier 2/3은 dead code로 두지 말고 제거.
- Tier 1이 동작 안 하면 devtools로 selection 트리거 시 플러그인이 어떤 selector(예: `.vw-translate-button`)를 만드는지 직접 확인하고 그 selector를 코드에 박는다.

---

## 미해결 질문 / 구현 단계에서 결정할 것

1. **Tier 1 실제 시그니처**: `window.plugin.translate(text)`가 동작하는지, 동작한다면 String 단일 인자인지 객체 인자인지는 구현하면서 확인. 첫 시도에서 콘솔에 `console.dir(window.plugin)` 출력해 prototype 메서드를 모두 확인할 것.
2. **Tier 2 selection-translate 버튼 selector**: 플러그인이 만드는 임시 버튼의 정확한 selector는 devtools로 직접 발견해야 한다. 이 selector를 모르고 코드를 미리 작성하면 안 된다.
3. **위치 변경 옵션 노출 여부**: 사용자가 위젯 위치를 R/L/TL 등으로 바꿀 수 있게 노출할지 — 이번 범위에서는 **하지 않는다**. 필요해지면 별도 작업.
4. **localStorage 키 네임스페이스**: `vlibrasPluginEnabled` 단일 키 사용. 다른 sentence 페이지 설정과 충돌 없음.

---

## 완료 조건

- [ ] sentence 페이지에 토글 버튼이 추가되었고, 토글 ON시 우측에 VLibras 공식 위젯이 표시된다.
- [ ] 토글 OFF가 기본이며, 마지막 상태가 새로고침 후에도 유지된다.
- [ ] 토글 ON 상태에서 "번역 & 재생"을 누르면 메인 캔버스 아바타와 위젯 아바타가 둘 다 같은 문장을 재생한다 (Tier 1~3 중 하나).
- [ ] Tier 1~3 모두 실패하더라도 메인 파이프라인은 영향받지 않으며, 사용자에게 독립 운영 모드 안내가 표시된다.
- [ ] 토글 OFF 상태에서는 동기화 호출 자체가 일어나지 않는다 (네트워크 탭에서 확인).
- [ ] 기존 시나리오 (모델 변경, 글로스 chip, 에러 배너, loop/speed 컨트롤) 모두 회귀 없음.
- [ ] 새 파일 생성 0개. `public/players/sentence/index.html` 한 파일만 변경.

---

## 다음 세션에서 바로 시작할 때

1. 이 문서를 Read로 먼저 읽는다.
2. `public/players/sentence/index.html`의 현재 라인 번호가 이 문서의 라인 번호와 일치하는지 확인 (다른 커밋이 들어갔을 가능성).
3. Step 1(플러그인 임베드)부터 순차 진행. 각 단계는 로컬 서버로 즉시 검증.
4. Step 4 시작 전에 반드시 devtools 콘솔에서 `console.dir(window.plugin)`로 실제 API surface를 먼저 확인할 것 — Tier 1 하드코딩 전제 조건.
5. Tier 1이 실패하면 Step 5의 selection selector를 devtools로 직접 발견할 것.
