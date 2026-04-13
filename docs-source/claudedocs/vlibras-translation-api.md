# VLibras 번역 API 스펙 (실측)

**작성일**: 2026-04-13
**방법**: curl 기반 실측 (WebFetch 미사용, 모든 응답 헤더/본문 직접 관찰)
**대상 호스트**: `traducao2.vlibras.gov.br` (IPv4: 54.232.73.63, 18.228.243.52, 54.207.243.105, `server: istio-envoy`)

## 확정 정보

| 항목 | 값 |
|---|---|
| **엔드포인트 URL** | `https://traducao2.vlibras.gov.br/translate` |
| **HTTP 메서드** | `POST` (GET은 404 반환 → 미지원) |
| **요청 Content-Type** | `application/json` (권장) 또는 `application/x-www-form-urlencoded` 둘 다 동작 |
| **요청 body 필드** | `text` (필수, 최대 5000자) |
| **응답 Content-Type** | `text/html; charset=utf-8` (주의: 실제 본문은 JSON이 아닌 **plain text**) |
| **응답 body 형식** | UPPERCASE 공백 구분 문자열 (예: `"CASA BONITA"`) |
| **글로스 추출 경로** | `responseText.trim().split(/\s+/)` — JSON 파싱 없이 문자열 split |
| **CORS** | 허용됨 (`access-control-allow-origin`이 요청 Origin을 echo, `credentials: true`) |
| **인증** | 없음 (공개 API) |

## 테스트 로그

### 샘플 1 — "Ola" (단일 단어)
```
$ curl -v -X POST "https://traducao2.vlibras.gov.br/translate" \
       -H "Content-Type: application/json" \
       -d '{"text":"Ola"}'

> POST /translate HTTP/1.1
> Content-Type: application/json
> Content-Length: 14

< HTTP/1.1 200 OK
< Content-Type: text/html; charset=utf-8
< Content-Length: 3
< access-control-allow-origin: *
< server: istio-envoy
<
OLA
```

### 샘플 2 — "Casa bonita" (2단어)
```
$ curl -X POST "https://traducao2.vlibras.gov.br/translate" \
       -H "Content-Type: application/json" \
       -d '{"text":"Casa bonita"}'

< HTTP/1.1 200 OK
< Content-Type: text/html; charset=utf-8
< Content-Length: 11
<
CASA BONITA
```

### 샘플 3 — "Eu morar casa" (3단어, 주어 탈락 관찰)
```
$ curl -X POST "https://traducao2.vlibras.gov.br/translate" \
       -H "Content-Type: application/json" \
       -d '{"text":"Eu morar casa"}'

< HTTP/1.1 200 OK
< Content-Length: 10
<
MORAR CASA
```
**관찰**: 주어 "Eu"가 번역 결과에서 탈락. Libras 문법 특성 반영 (번역기가 주어 생략).

### 샘플 4 — "O menino come maçã vermelha" (관사·활용 처리)
```
$ curl -X POST "https://traducao2.vlibras.gov.br/translate" \
       -H "Content-Type: application/json" \
       -d '{"text":"O menino come maçã vermelha"}'

< HTTP/1.1 200 OK
< Content-Length: 26
<
MENINO COMER MACA VERMELHO
```
**관찰**: 관사 "O" 탈락, "come" → 원형 "COMER", 특수문자 `ç` → `C`, 성(性) 변화 "vermelha" → 남성형 "VERMELHO".

### 샘플 5 — "O cachorro está correndo no parque" (분류사 구분자 `&` 발견)
```
$ curl -X POST "https://traducao2.vlibras.gov.br/translate" \
       -H "Content-Type: application/json" \
       -d '{"text":"O cachorro está correndo no parque"}'

< HTTP/1.1 200 OK
<
CACHORRO CORRER&PESSOA PARQUE
```
**중요 관찰**: `&` 문자가 복합 글로스(classifier) 마커로 사용됨. 이는 VLibras 전용 포맷으로, **단어 구분은 공백이며 `&`는 단일 글로스 내부의 복합 표현**.

### 샘플 6 — "casa" (CASA 번들 매칭 검증)
```
$ curl -X POST "https://traducao2.vlibras.gov.br/translate" \
       -H "Content-Type: application/json" \
       -d '{"text":"casa"}'

< HTTP/1.1 200 OK
<
CASA
```
**중요**: 프로젝트의 `public/animations/vlibras/` CASA 번들명과 대문자 표기가 정확히 일치. 번들 키 매칭 시 응답 문자열을 그대로 쓸 수 있음.

### 샘플 7 — form-urlencoded 대안 (동작 확인)
```
$ curl -X POST "https://traducao2.vlibras.gov.br/translate" \
       -H "Content-Type: application/x-www-form-urlencoded" \
       -d "text=Ola"

< HTTP/1.1 200 OK
<
OLA
```
**관찰**: JSON과 form 둘 다 수용. 서버는 `text` 필드만 추출.

### 샘플 8 — 빈 body (에러 스키마 확인)
```
$ curl -X POST "https://traducao2.vlibras.gov.br/translate" \
       -H "Content-Type: application/json" \
       -d '{}'

< HTTP/1.1 422 Unprocessable Entity
< Content-Type: application/json; charset=utf-8
<
{"error":[{"field":"text","message":"'text' field is required."},
          {"field":"text","message":"'text' exceeded 5000 characters limit."}]}
```
**관찰**: 에러 응답만 진짜 JSON, 정상 응답은 plain text. 에러 스키마는 `{error: [{field, message}]}` 배열 형태. **제한**: `text` 필드는 최대 5000자.

### 샘플 9 — GET 메서드 시도
```
$ curl "https://traducao2.vlibras.gov.br/translate?text=Ola"
< HTTP/1.1 404 Not Found
{"error":"Not Found"}

$ curl "https://traducao2.vlibras.gov.br/translate/Ola"
< HTTP/1.1 404 Not Found
{"error":"Not Found"}
```
**결론**: GET 방식(경로 파라미터/쿼리 모두)은 404. **POST만 유효.**

### 샘플 10 — CORS preflight (프록시 필요 여부 판단)
```
$ curl -X OPTIONS "https://traducao2.vlibras.gov.br/translate" \
       -H "Origin: https://sls-brazil-player.vercel.app" \
       -H "Access-Control-Request-Method: POST" \
       -H "Access-Control-Request-Headers: content-type"

< HTTP/1.1 200 OK
< access-control-allow-origin: https://sls-brazil-player.vercel.app
< access-control-allow-credentials: true
< access-control-allow-methods: GET,POST,OPTIONS,PUT,DELETE
< access-control-allow-headers: Authorization,Content-Type,X-Requested-With,Accept
< access-control-max-age: 86400
```
**결론**: **CORS 정상 허용됨**. Origin을 echo하는 방식이라 Vercel 도메인이 정확히 허용됨. **브라우저에서 직접 호출 가능** → Vercel rewrites 프록시는 필수가 아님 (단, privacy/속도를 위해 선택적 사용 가능).

## 추가 관찰 사항

1. **응답 Content-Type 불일치 버그**: 서버는 `text/html`을 선언하지만 실제 본문은 plain text. `JSON.parse()` 또는 `response.json()` 호출 시 실패함. 반드시 `response.text()` 사용.
2. **etag 지원**: 응답에 `etag` 헤더가 있어 조건부 요청(`If-None-Match`) 가능 — 배치 사전 변환 시 캐싱에 활용 가능.
3. **응답 시간**: `x-envoy-upstream-service-time` 기준 1~70ms (짧은 문장 빠름, 복잡 문장은 50ms 내외).
4. **IP 회전**: DNS에 3개 IP 등록 — 로드밸런싱 환경.
5. **Libras 문법 특성**: 번역기가 주어/관사 탈락, 동사 원형화, 성(gender) 정규화를 자동 수행. 원문 단어 수와 글로스 수가 다를 수 있음 (1:N, N:1 모두 관찰됨).

## 사용 권장 방식 (프로젝트용)

### 방안 A — 직접 호출 (CORS 정상 작동, 권장)

```javascript
// 클라이언트 직접 호출 (브라우저에서)
async function translateToLibras(portugueseText) {
  const response = await fetch('https://traducao2.vlibras.gov.br/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: portugueseText })
  });

  if (response.status === 422) {
    const err = await response.json();
    throw new Error(`VLibras validation: ${err.error.map(e => e.message).join(', ')}`);
  }
  if (!response.ok) {
    throw new Error(`VLibras HTTP ${response.status}`);
  }

  // CRITICAL: 서버는 text/html을 선언하지만 본문은 plain text
  // response.json() 사용 금지, response.text() 사용
  const glossString = (await response.text()).trim();

  // 공백 구분 글로스 배열 ('&'는 복합 글로스 내부 마커이므로 분리하지 않음)
  return glossString.split(/\s+/);
}

// 사용 예
const glosses = await translateToLibras('Casa bonita');
// → ['CASA', 'BONITA']
```

### 방안 B — Vercel rewrites 프록시 (선택, privacy/CDN 경유 시)

`vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/api/vlibras/translate",
      "destination": "https://traducao2.vlibras.gov.br/translate"
    }
  ]
}
```

주의: 원 요청에서 제안된 `/api/vlibras/translate/:path*` 패턴은 **불필요**. 엔드포인트는 `/translate` 단일 경로이며 경로 파라미터를 받지 않음 (body 기반 POST). 단순 rewrite로 충분.

클라이언트 코드:
```javascript
await fetch('/api/vlibras/translate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: portugueseText })
});
```

### 글로스 배열 파싱 규칙 (정리)

```javascript
// 1. 응답을 text로 읽기 (JSON 아님)
const raw = await response.text();

// 2. trim + 공백 split
const glosses = raw.trim().split(/\s+/);

// 3. 번들 매칭: 응답 대문자 그대로 번들 키로 사용
//    예: glosses[0] === 'CASA' → public/animations/vlibras/CASA/ 번들 로드
//    예외 처리: '&' 포함 글로스는 복합 글로스 → 사전에 존재하지 않으면 fallback 필요
for (const gloss of glosses) {
  if (gloss.includes('&')) {
    // classifier 복합 글로스: 전용 번들 확인, 없으면 분할 시도 또는 스킵
    console.warn(`Classifier gloss: ${gloss}`);
  }
  // 일반 글로스: 번들 로드
  await loadGlossBundle(gloss);
}
```

## 미확인 / 후속 조사 필요 항목

| 항목 | 상태 | 비고 |
|---|---|---|
| 5000자 초과 시 실제 응답 | 미테스트 | 422로 예상되나 미검증 |
| Rate limit 임계값 | 미확인 | 10회 미만 호출에서는 제한 관찰 없음 |
| `&` 복합 글로스의 전체 목록 | 미확인 | 현재 관찰된 것: `CORRER&PESSOA` |
| 번역 실패(사전 미등록 단어) 시 동작 | 미테스트 | 추가 조사 필요 |
| 공식 문서 URL | 미확인 | `vlibras.gov.br/doc` 등 미탐색 |
| Cache 효과 (`If-None-Match` 동작) | 미검증 | etag는 관찰됨 |
