# Sentence Player 비수지 표현(NMS) 처리 — 데이터 + 흐름 문서

> **작성일**: 2026-04-29
> **범위**: VLibras 사전의 얼굴 본 데이터 구조, 어휘 NMS 분포, 문법 마커 NMS 클립, 처리 흐름
> **검증 방식**: 사전 카탈로그(22,508 키) 직접 조사 + 번들 트랙 정량 측정 + VLibras 위젯 동작 비교
> **관련 문서**:
> - [`vlibras-portal/claudedocs/NMS_Analysis.md`](../../vlibras-portal/claudedocs/NMS_Analysis.md) — 학술적 NMS 이론
> - [`stroke-detection-methods.md`](stroke-detection-methods.md) — Stroke 검출 (NMS와 별개 라인업)

---

## 1. 핵심 결론

| 질문 | 답 |
|---|---|
| **VLibras는 블렌드쉐이프(blend shape)를 쓰는가?** | ❌ 아니오. 본(bone) 기반 얼굴 리깅. ABNT Annex D 68 블렌드쉐이프 방식과 다름. |
| **각 단어(글로스)에 얼굴 데이터가 있는가?** | ✅ **모든 글로스에 44개 얼굴 본 트랙이 *구조적으로* 존재**. 단, 글로스마다 *키프레임 활성도*가 다름. |
| **문법 마커(`[INTERROGAÇÃO]` 등)는 별도 클립인가?** | ✅ **사전에 NMS 전용 클립으로 등록**. 일반 글로스와 동일한 방식으로 사전 lookup → 재생. |
| **VLibras 위젯이 NMS를 *합성*하는가?** | ❌ 합성 안 함. 마커 토큰을 사전 키로 *그대로* lookup해서 미리 만들어진 NMS 클립 재생. |
| **학술적 NMS scope(범위)를 인코딩하는가?** | ❌ 안 함. 토큰 단위 마커만 있고, scope 표기는 부재. |

---

## 2. VLibras 얼굴 본 카탈로그

VLibras 84본 스켈레톤에는 **44개의 얼굴 본**이 포함되어 있다. 모든 글로스 클립에 이 본들의 트랙이 *position + quaternion* 형태로 들어가 있으며, 글로스의 NMS 표현 강도에 따라 키프레임 수와 값 범위가 결정된다.

### 2.1 부위별 본 분류

| 부위 | 본 (원어) | 본 수 | 기능 |
|---|---|---|---|
| **머리** | `BnCabeca` | 1 | 머리 회전·기울임 (의문문, 부정 등) |
| **턱** | `BnMandibula` | 1 | 입 벌림 |
| **입꼬리** | `BnBocaCantoL`, `BnBocaCantoR` | 2 | 미소·찌푸림 |
| **입술 중앙** | `BnLabioCentroSuper`, `BnLabioCentroInfer` | 2 | 윗·아랫입술 |
| **볼** | `BnBochechaL`, `BnBochechaR` | 2 | 볼 부풀림·축소 (강도 표시) |
| **혀** | `BnLingua`, `BnLingua001~003` | 4 | 혀 동작 (특정 어휘) |
| **눈** | `BnOlhoL`, `BnOlhoR` | 2 | 눈동자 회전 |
| **시선 타겟** | `BnOlhosMira`, `BnOlhoMiraL`, `BnOlhoMiraR` | 3 | 시선 방향 IK 타겟 |
| **눈썹 (외측)** | `BnSobrancLateralL`, `BnSobrancLateralR` | 2 | 외측 눈썹 올림·내림 |
| **눈썹 (내측)** | `BnSobrancCentroL`, `BnSobrancCentroR` | 2 | 내측 눈썹 올림·내림 |
| **눈썹 (중앙)** | `BnSobrancCentro` | 1 | 미간 |

각 본의 `position` + `quaternion` = 총 22 본 × 2 트랙 = **44 트랙**.
(scale 트랙은 운영 번들에서 제거됨, 원본 변환에는 포함됨)

### 2.2 ABNT Annex D 블렌드쉐이프와의 비교

| 측면 | ABNT Annex D | VLibras |
|---|---|---|
| 얼굴 표현 방식 | 블렌드쉐이프 68종 (morph target) | 본(bone) 회전·이동 |
| 메시 분리 | head/eyelash/mouth/eyebrow_l/r/iris_l/r 7개 | 단일 메시 + 본 weight |
| 데이터 형식 | weight 0~1 + frame range | quaternion + position |
| 인코딩 효율 | 가중치 0인 블렌드쉐이프 생략 가능 | 본 트랙은 항상 존재 |
| 운영 환경 | TV 3.0 표준 (방송 인프라) | 웹 위젯 + Three.js |

**시사점**: 우리 sentence player는 VLibras 본 기반 데이터를 그대로 사용하므로, ABNT 68 블렌드쉐이프 매핑 테이블을 *직접 만들 필요 없음*. NMS 합성 시에도 본 키프레임을 추가/덮어쓰는 방식이 자연스럽다.

---

## 3. 어휘 NMS — 글로스별 얼굴 본 활성도 (실측)

> **측정 방법**: 각 트랙의 `times`/`values`에서 component별 max-min 변화량을 계산. `> 1e-3` 이면 활성, 아니면 정적(rest pose 고정).
> **데이터 출처**: `public/animations/vlibras/bundles/*.threejs.json` (운영 번들, 30개 어휘+마커).
> **측정 도구**: PowerShell + Node 스크립트 (이번 세션에서 실측).

### 3.1 분포 (운영 번들 30개 글로스)

| 글로스 | duration | 활성 얼굴 본 | 최대 변화 본 | 활성 손 본 | 어휘 NMS 종류 |
|---|---|---|---|---|---|
| **NAO** | 2.77s | **3** | `BnCabeca` 0.249 | 17 | **머리 좌우 흔듦** (부정) |
| **MUITO** | 2.80s | **5** | `BnSobrancLateralL` 0.082 | 36 | **눈썹** (강도 표시) |
| **SIM** | 3.40s | **5** | `BnCabeca` 0.084 | 21 | **머리 끄덕임** (긍정) |
| **OBRIGADO** | 2.13s | **3** | `BnOlhoR` 0.078 | (활성) | 눈 (감사 표정) |
| **OLA** | 2.57s | 4 | `BnOlhoL` 0.034 | (활성) | 눈 (인사) |
| **QUERER** | 2.47s | 3 | `BnCabeca` 0.037 | (활성) | 머리 (가벼움) |
| **CASA** | 2.47s | 2 | `BnOlhoL` 0.003 | 30 | 사실상 무표정 |
| **BOM** | 1.80s | 2 | `BnOlhoR` 0.008 | (활성) | 사실상 무표정 |
| **EU** | 1.93s | 2 | `BnOlhoL` 0.009 | (활성) | 사실상 무표정 |
| **VOCE** | 2.03s | 2 | `BnOlhoR` 0.016 | (활성) | 사실상 무표정 |
| **POR_FAVOR** | 2.83s | 2 | `BnOlhoL` 0.004 | (활성) | 사실상 무표정 |
| **GOSTAR** | 3.03s | 0 | — | (활성) | **무표정** |

> 변화량 단위: quaternion component의 (max - min). 0.249는 큰 변화(머리 회전 약 30°에 해당), 0.01 이하는 미세 변화(거의 정적).

### 3.2 NAO 케이스 — 머리 흔듦 키프레임 분석

가장 명확한 어휘 NMS 사례.

`BnCabeca.quaternion` 15 키프레임:
```
t=0.000  q=(-0.072,  0.703, -0.072,  0.703)   ← 정면
t=0.467  q=(-0.064,  0.769, -0.079,  0.631)   ← 한쪽
t=0.700  q=(-0.062,  0.789, -0.081,  0.606)   ← 더 기울임
t=0.967  q=(-0.084,  0.565, -0.058,  0.819)   ← 반대쪽
t=1.700  q=(-0.085,  0.540, -0.055,  0.835)   ← 반대쪽 최대
t=2.000  q=(-0.063,  0.785, -0.080,  0.612)   ← 한쪽
t=2.767  q=(-0.072,  0.703, -0.072,  0.703)   ← 정면 복귀
```

Y component가 0.540 ↔ 0.789 사이 진동 → **명확한 좌우 흔듦 패턴**. Libras 부정 NMS의 표준 형태와 일치.

`BnOlhoL/R` 17 키프레임 변화량 0.217 → 머리 흔들림에 따른 시선 보상 회전(머리가 흔들려도 눈은 정면 유지).

### 3.3 글로스 분류

| 카테고리 | 특징 | 예 |
|---|---|---|
| **NMS-내장 글로스** | 어휘 자체에 NMS 포함 | NAO, MUITO, SIM, OBRIGADO |
| **약한 NMS 글로스** | 미세한 눈동자 움직임 정도 | OLA, QUERER, CASA, BOM |
| **무표정 글로스** | 모든 얼굴 본 정적 | GOSTAR, EU, POR_FAVOR (대부분 동사·대명사) |

**시사점**: 어휘 NMS만으로는 *문법적 의문문/감탄문*을 표현할 수 없음. 마지막 글로스가 무표정 글로스(GOSTAR, ESTUDAR 등)인 경우 별도 NMS 마커 클립이 필요 — 이것이 §4의 마커 클립 시스템.

---

## 4. 문법 마커 — NMS 전용 클립

### 4.1 사전 등록 구조

VLibras 사전 카탈로그(`https://dicionario2.vlibras.gov.br/bundles`, 313KB JSON, 22,508 키)에 마커는 **각각 두 종류씩 등록**되어 있다:

| 마커 | 어휘 형태 (대괄호 없음) | NMS 형태 (대괄호 포함) |
|---|---|---|
| 의문 | `INTERROGAÇÃO` (명사 "물음표") | `[INTERROGAÇÃO]` (문법 NMS) |
| 마침표 | `PONTO` (명사 "점") | `[PONTO]` (종결 NMS) |
| 감탄 | `EXCLAMAÇÃO` (명사 "느낌표") | `[EXCLAMAÇÃO]` (강조 NMS) |

전체 카탈로그에서 대괄호로 시작하는 키는 **정확히 이 3종만**. 꺾쇠/소괄호/기타 특수 시작 키는 없음.

### 4.2 클립 데이터 비교 (실측)

| 키 | duration | 활성 얼굴 본 | 활성 손 본 | 최대 활성 본 | 동작 |
|---|---|---|---|---|---|
| `INTERROGAÇÃO` (어휘) | 2.97s | 0 | **16** | `BnDedo1R002` 0.690 | **공중에 ? 그리기** (오른쪽 검지) |
| `[INTERROGAÇÃO]` (NMS) | 1.63s | **6** | 0 | `BnCabeca` 0.116 | **머리 회전 + 얼굴** ★ |
| `PONTO` (어휘) | 2.10s | 3 | **19** | `BnDedo1R006` 0.714 | **공중에 . 찍기** |
| `[PONTO]` (NMS) | 1.30s | 0 | 0 | (모두 정적) | **정적 휴지(pause)** — 종결 신호 |
| `EXCLAMAÇÃO` (어휘) | 2.13s | 0 | **16** | `BnDedo1R002` 0.690 | **공중에 ! 그리기** |
| `[EXCLAMAÇÃO]` (NMS) | 1.63s | **4** | 0 | `BnOlhoR` 0.131 | **눈·강조 NMS** |

**핵심 관찰**:
- 어휘 클립: 손/팔이 활성, 얼굴은 거의 정적. 시각적 손동작.
- NMS 클립: 얼굴/머리가 활성, 손은 정적. **NMS 전용 클립**.
- `[PONTO]`만 모든 본 정적 — 1.3초 *휴지* 클립으로 문장 종결 시 호흡 표현.

### 4.3 잘못된 추정과 정정 (역사)

이 발견은 두 단계로 이뤄졌다:

1. **2026-04-29 오전**: 처음에는 `INTERROGAÇÃO`(대괄호 없음) 키로 다운로드 → 손가락 ? 그리기 클립 → "VLibras는 NMS 합성 안 한다"고 결론. NMS_Analysis.md §5.2의 "규칙 기반 휴리스틱" 추정이 *틀렸다*고 판단.
2. **2026-04-29 오후**: 사용자 제보로 위젯에서 본 동작이 손가락 ? 그리기가 아니라 *머리·얼굴 NMS*임을 확인. 사전 카탈로그 재조사 → `[INTERROGAÇÃO]`(대괄호 포함)이 *별도 NMS 클립*으로 등록되어 있음을 발견. NMS_Analysis.md §5.2 추정이 *부분적으로 옳았음* — VLibras는 *NMS 클립을 가지고 있고* 사전 lookup으로 처리. JS 합성이 아닌 사전에 미리 만들어진 클립.

---

## 5. 처리 흐름

### 5.1 입력 → 글로스 시퀀스 → 재생

```
사용자 입력: "Você gosta de estudar?"
    ↓
번역 API (https://traducao2.vlibras.gov.br/translate)
    ↓
응답 (ASCII): "VOCE GOSTAR ESTUDAR [INTERROGAÇÃO]"
    ↓
공백 split → ["VOCE", "GOSTAR", "ESTUDAR", "[INTERROGAÇÃO]"]
    ↓
각 토큰을 사전 키로 매칭 후 클립 재생
```

### 5.2 메인 아바타 (sentence player Three.js)

`public/players/sentence/index.html` (`asciiKey` 함수):

```javascript
function asciiKey(gloss) {
  return gloss
    .replace(/[\[\]]/g, '')                        // 대괄호 제거 ([INTERROGAÇÃO]→INTERROGAÇÃO)
    .normalize('NFKD').replace(/[̀-ͯ]/g, '')        // 악센트 제거 (VOCÊ→VOCE)
    .toUpperCase();
}
```

토큰 → 키 매핑:
- `VOCE` → `VOCE` → bundleIndex의 `VOCE.threejs.json` 클립
- `[INTERROGAÇÃO]` → `INTERROGACAO` → bundleIndex의 `INTERROGACAO.threejs.json` (NMS 클립)

`bundles/index.json`의 마커 항목:
```json
{ "raw": "[INTERROGAÇÃO]", "key": "INTERROGACAO", "file": "INTERROGACAO.threejs.json", "duration": 1.6333 }
```

### 5.3 위젯 sync (raw 글로스 직접 주입)

VLibras 위젯의 사전 키는 *악센트 보존* 형태(`VOCÊ`)이지만 번역 API는 *ASCII* 응답(`VOCE`). 위젯이 자체 번역할 경우 미스매칭 → 지문자 폴백 발생.

**해결**: 사전 카탈로그(`/bundles`, 22,508 키)로 ASCII↔raw 매핑을 만들어 raw 글로스를 직접 주입.

```javascript
// 사전 카탈로그 lazy fetch + 매핑 캐시
async function loadVlibrasDictMap() {
  const list = await (await fetch('https://dicionario2.vlibras.gov.br/bundles')).json();
  const map = new Map();
  for (const raw of list) {
    const norm = raw.normalize('NFKD').replace(/[̀-ͯ]/g, '').toUpperCase();
    if (!map.has(norm)) map.set(norm, raw);
  }
  return map;
}

// ASCII 글로스 시퀀스 → raw 형태로 변환
function toRawGlossString(asciiGlosses, dictMap) {
  return asciiGlosses
    .map(g => {
      const norm = g.normalize('NFKD').replace(/[̀-ͯ]/g, '').toUpperCase();
      return dictMap.get(norm) || g;
    })
    .join(' ');
}

// 변환 후 위젯에 직접 주입 (위젯 자체 번역 우회)
plugin.play("VOCÊ GOSTAR ESTUDAR [INTERROGAÇÃO]");  // raw 형태
```

매핑 예:
- `VOCE` → `VOCÊ`
- `FAMILIA` → `FAMÍLIA`
- `NAO` → `NÃO`
- `[INTERROGAÇÃO]` → `[INTERROGAÇÃO]` (이미 raw 형태, 변환 없음)

### 5.4 두 아바타의 일관성

```
사용자 입력
    ↓
"VOCE GOSTAR ESTUDAR [INTERROGAÇÃO]" (ASCII, 우리 번역)
    ↓                                ↓
[메인 큰 아바타]                  [VLibras 위젯 작은 아바타]
asciiKey 정규화                  toRawGlossString 변환
    ↓                                ↓
bundleIndex 매칭                 "VOCÊ GOSTAR ESTUDAR [INTERROGAÇÃO]"
    ↓                                ↓
NMS 클립 재생                   plugin.play(rawGloss) → Unity NMS 클립 재생
    ↓                                ↓
머리·얼굴 NMS 동작 ✓            동일한 NMS 동작 ✓
```

---

## 6. 학술 vs 실측 — VLibras의 NMS 표현력

### 6.1 학술 표준 (Quadros & Karnopp, 2004)

NMS scope를 overline + 약어로 명시:
```
     ___ef:interrogativa___
VOCÊ ESTUDAR
→ "ef:interrogativa"가 두 글로스 전체에 걸쳐 적용됨 (눈썹 올림)
```

| NMS 종류 | scope | 표기 |
|---|---|---|
| 부정 | 문장 전체 또는 동사구 | `mc:neg` (head movement) |
| Y/N 의문문 | 문장 전체 | `ef:interrogativa` |
| WH 의문문 | WH 단어부터 끝 | `ef:wh` |
| 조건문 | 조건절 | `ef:condicional` |
| 주제 | 주제부 | `ef:topico` |

### 6.2 VLibras 실측

```
입력: "Você estuda?"
번역 API: "VOCE ESTUDAR [INTERROGAÇÃO]"
재생: VOCE 클립 → ESTUDAR 클립 → [INTERROGAÇÃO] NMS 클립 (1.6초)
```

| 측면 | 학술 표준 | VLibras 실측 |
|---|---|---|
| NMS scope 표시 | overline 범위 명시 | **부재** — 마커는 글로스 끝에 단일 토큰 |
| NMS 종류 세분화 | `mc:neg`, `ef:interrogativa` 등 다양 | `[PONTO]`/`[INTERROGAÇÃO]`/`[EXCLAMAÇÃO]` 3종 |
| 강도 그라데이션 | 문맥 기술 가능 | **부재** |
| 동시성 표시 | 여러 NMS 중첩 가능 | **부재** |
| 어휘 NMS | 일부 (수어 자체에 내장) | ✅ 있음 (글로스마다 활성도 다름) |
| 문법 NMS | 별도 표기 | ✅ 사전 등록 클립 (마커) |

**결론**: VLibras는 학술 표준의 *부분 집합*만 표현. scope·강도·동시성은 부재. 단, 어휘 NMS와 문법 NMS의 *데이터*는 가지고 있고 사전 lookup으로 정확히 재생.

---

## 7. 한계점 + 후속 개선 라인업

### 7.1 현재 처리 가능

✅ 어휘 NMS (글로스 클립 자체에 내장된 얼굴 본 키프레임)
✅ 문법 마커 NMS (3종: `[PONTO]`, `[INTERROGAÇÃO]`, `[EXCLAMAÇÃO]`)
✅ ASCII↔raw 매핑으로 위젯 sync 일관성

### 7.2 미처리 / Phase B 후보

| 항목 | 현재 상태 | 후속 처리 방향 |
|---|---|---|
| **`(+)` 강조 마커** | 글로스 뒤에 `(+)` 접미사 → 사전에 별도 클립 없음 | 동일 글로스 2회 큐잉 + 진폭 가중 |
| **`&` 분류사** | `CORRER&PESSOA` 단일 키 매칭 시도 → 사전에 없으면 ⚠️ | base 글로스(`CORRER`) 폴백 |
| **인칭 일치 동사** | `1S_AJUDAR_2S` 같은 토큰 → 사전에 *별도 클립으로 존재* | 사전 카탈로그 raw 매핑으로 매칭 시도 (이미 작동 가능) |
| **NMS scope 확장** | 마커는 마지막 글로스 시점에만 적용 | WH 의문문에서 의문사부터 끝까지 NMS 지속 |
| **블렌딩 통합** | 마커 클립이 단순 순차 재생 | 마지막 어휘 글로스 stroke와 NMS 클립 stroke 겹침 (cross-fade) |

### 7.3 학술적 NMS 합성 (Phase B)

ABNT Annex D 부록 68 블렌드쉐이프 + VLibras 84본 얼굴 본을 *additive blend*로 합성하는 방법은 별도 라인업으로 진행 가능. 단:
- VLibras NMS 클립이 이미 있으니 *기본 처리는 충분*
- 학술적 정밀도가 필요한 경우(예: 학술 출판물용)에만 필요
- ABNT Annex D 호환성을 위해서만 필요 (Three.js 환경에서는 본 합성이 더 자연스러움)

---

## 8. 운영 가이드

### 8.1 새 마커 추가 시 절차

마커 후보 → 사전 카탈로그 조회 → 변환 → 번들 등록.

```bash
# 1. 사전 카탈로그에 키 존재 확인
curl -s "https://dicionario2.vlibras.gov.br/bundles" | \
    node -e "let d=''; process.stdin.on('data',c=>d+=c); process.stdin.on('end',()=>{const l=JSON.parse(d); console.log(l.includes('[NEW_MARKER]'));})"

# 2. precompute로 변환 (대괄호 키)
echo "[NEW_MARKER]" > /tmp/new.txt
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python tools/vlibras2slmb/batch/precompute_threejs.py \
    --gloss-list /tmp/new.txt --output-dir /tmp/out

# 3. bundles/에 복사 + index.json 등록
# (file: NEW_MARKER.threejs.json, key: NEW_MARKER, raw: [NEW_MARKER])
```

### 8.2 글로스 매칭 디버깅

브라우저 콘솔(F12)에서:

```javascript
// 우리 sentence player 매칭 확인
asciiKey('[INTERROGAÇÃO]');                                          // → "INTERROGACAO"
bundleIndex.glosses.find(g => g.key === 'INTERROGACAO');             // → { raw, key, file, duration }

// VLibras 위젯 sync 매칭 확인
loadVlibrasDictMap().then(m => console.log('size:', m.size));        // → 22508
loadVlibrasDictMap().then(m => console.log(m.get('VOCE')));          // → "VOCÊ"
loadVlibrasDictMap().then(m =>
  console.log(toRawGlossString(['VOCE','BOM','[INTERROGAÇÃO]'], m))
);  // → "VOCÊ BOM [INTERROGAÇÃO]"
```

### 8.3 chip UI 표시

| chip 상태 | 의미 | 색상 |
|---|---|---|
| 정상 | bundleIndex 키 매칭 + 클립 로드됨 | 파란색 (`.gloss-chip.playing` 시 강조) |
| `expanded` | `_` 분리 폴백으로 매칭됨 (예: `1S_AJUDAR_2S` → `AJUDAR`) | 점선 outline + `→` 표시 |
| `missing` | 매칭 실패 + 클립 없음 | 흐리게 + ⚠️ 아이콘 |

마커는 `raw` 필드를 `[INTERROGAÇÃO]` 형태로 저장하므로 chip에 대괄호 포함 표시됨 — 사용자가 *마커임을 시각적으로 인지 가능*.

---

## 9. 데이터 출처 검증 가능성

본 문서의 모든 정량 데이터는 다음 명령으로 재생산 가능:

```bash
# 사전 카탈로그
curl -s "https://dicionario2.vlibras.gov.br/bundles" | wc -c       # → 313412 bytes
curl -s "https://dicionario2.vlibras.gov.br/bundles" | \
    node -e "let d=''; process.stdin.on('data',c=>d+=c); process.stdin.on('end',()=>console.log(JSON.parse(d).length))"
# → 22508

# 마커 직접 다운로드 (대괄호 포함 vs 없음 비교)
curl -sL "https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/INTERROGA%C3%87%C3%83O" -o /tmp/p.bundle
curl -sL "https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/%5BINTERROGA%C3%87%C3%83O%5D" -o /tmp/b.bundle
ls -la /tmp/{p,b}.bundle
# → p: 21339 bytes (어휘), b: 17350 bytes (NMS)

# 변환된 클립 트랙 분석 (Node)
node -e "
const j = JSON.parse(require('fs').readFileSync('public/animations/vlibras/bundles/INTERROGACAO.threejs.json','utf8'));
console.log('name:', j.name, 'dur:', j.duration, 'tracks:', j.tracks.length);
"
```

---

## 부록: 본 이름 ↔ 학술 매개변수 매핑

| VLibras 본 | 학술 매개변수 (Quadros & Karnopp, 2004) |
|---|---|
| `BnSobrancLateralL/R` | 외측 눈썹 (`ef:sobrancelhas levantadas/franzidas`) |
| `BnSobrancCentroL/R/Centro` | 내측 눈썹 + 미간 (`ef:wh`, 분노) |
| `BnOlhoL/R` | 눈동자 회전 (시선 방향) |
| `BnOlhoMiraL/R/OlhosMira` | 시선 IK 타겟 (동사 일치) |
| `BnBocaCantoL/R` | 입꼬리 (`ef:alegria/tristeza`) |
| `BnLabioCentroSuper/Infer` | 윗·아랫입술 (입 모양 viseme) |
| `BnBochechaL/R` | 볼 (`ef:augmentativo/diminutivo`) |
| `BnMandibula` | 턱 (입 벌림) |
| `BnLingua/001~003` | 혀 (특정 어휘) |
| `BnCabeca` | 머리 회전 (`mc:neg`, 끄덕임, 기울임) |

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-29 | 초안 작성. 사전 카탈로그·마커 클립·어휘 NMS 분포·위젯 sync 처리 흐름 통합. |
