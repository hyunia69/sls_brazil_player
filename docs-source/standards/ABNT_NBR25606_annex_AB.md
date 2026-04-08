# ABNT NBR 25606 - Annex A/B 기술 분석

**문서**: ABNT NBR 25606:2025 - TV 3.0 수어(Sign Language) 전송 표준
**분석 범위**: Annex A (수어 비디오 스트림), Annex B (수어 글로스 스트림)
**표준 상태**: Normative (규범적 부속서)

---

## 1. Annex A: 수어 비디오 스트림 (Sign Language Video Stream)

### 1.1 개요

Annex A는 TV 3.0에서 사용할 수어 비디오 스트림 기술을 규정한다. 이 전략은 수어 통역이 포함된 **제2 비디오 스트림**을 방송사가 전송하는 방식이다.

- 비디오 소스: 인간 수어 통역사 또는 아바타 기반 기계 번역 영상
- 전송 경로: OTA(Over-The-Air) 또는 OTT(Over-The-Top) 전송 체인 지원
- 비디오 포맷: 세로형(Portrait) 9:16 화면비

### 1.2 기술 사양

#### 1.2.1 비디오 코덱, 프로파일, 티어, 레벨

| 항목 | 사양 |
|------|------|
| 코덱 | **VVC (Versatile Video Coding)** |
| 프로파일 | Main 10 Profile |
| 티어 | Main Tier |
| 레벨 | Level 4.0 |

VVC Main 10 Profile, Main Tier, Level 4.0이 수어 비디오 스트림의 인코딩 및 디코딩에 **필수(shall)** 사용된다.

#### 1.2.2 공간 해상도 및 화면비

수어 비디오 스트림의 공간 해상도는 메인 비디오 해상도에 연동된다.

**필수 화면비**: 모든 공간 해상도에 대해 **9:16 포맷** 적용

| 메인 비디오 해상도 (pixels) | 수어 콘텐츠 해상도 (pixels) |
|-----------------------------|----------------------------|
| 1280 x 720 (HD) | 360 x 640 |
| 1920 x 1080 (FHD) | 540 x 960 |
| 2560 x 1440 (QHD) | 720 x 1280 |
| 3840 x 2160 이상 (UHD/4K+) | 1080 x 1920 |

> **참고**: 해상도 대응 관계는 Section 8의 Table 1에 정의되어 있으며, 메인 비디오는 16:9, 수어 콘텐츠는 9:16 화면비를 사용한다.

#### 1.2.3 프레임 레이트

수어 비디오 스트림의 프레임 레이트는 메인 비디오 비트스트림의 프레임 레이트와 동일하거나, 절반 또는 1/4이어야 한다.

**Table A.1 - 허용 프레임 레이트 값:**

| 프레임 레이트 |
|--------------|
| 60 fps |
| 60000/1001 fps (~59.94) |
| 50 fps |
| 30 fps |
| 30000/1001 fps (~29.97) |
| 25 fps |
| 24 fps |
| 24000/1001 fps (~23.976) |

- 스캐닝 포맷: **프로그레시브 스캐닝** 필수 (인터레이스 불허)

#### 1.2.4 다이내믹 레인지, 색도, 비트 심도

- 수어 비디오 스트림은 메인 비디오 스트림과 **동일한 사양**을 따라야 한다
- **HDR Dynamic Mapping Information은 수어 비디오 스트림에서 지원되지 않음**
- 방송사는 수어 비디오 스트림의 피크 휘도(peak luminance)를 메인 비디오와 일관되게 유지해야 함
- 수신기는 메인 비디오가 HDR Dynamic Mapping Information이 포함된 HDR을 사용하고 수어 비디오 스트림이 정적 메타데이터(static metadata)가 있는 HDR10을 사용하는 경우에도 두 영상의 프레젠테이션을 일관되게 유지해야 함

### 1.3 전송 메커니즘

#### 1.3.1 OTA/OTT 전송

- 수어 비디오 스트림은 OTA 또는 OTT 전송 체인을 통해 TV 3.0 수신기로 전달
- DASH(Dynamic Adaptive Streaming over HTTP) 기반 멀티플렉싱

#### 1.3.2 DASH MPD 시그널링

수어 비디오 스트림의 표시 방식은 DASH MPD(Media Presentation Description)의 `SupplementalProperty` 디스크립터로 제어된다.

**오버레이 표시 활성화:**
```xml
<SupplementalProperty
  schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Presentation"
  value="true" />
```

**수어 창 위치 설정:**
```xml
<!-- 수평 위치 (왼쪽에서 오른쪽, 디스플레이 폭 기준 %) -->
<SupplementalProperty
  schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Position_X"
  value="70.0" />

<!-- 수직 위치 (위에서 아래, 디스플레이 높이 기준 %) -->
<SupplementalProperty
  schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Position_Y"
  value="10.0" />
```

**수어 창 크기 설정:**
```xml
<!-- 창 너비 (디스플레이 폭 기준 %) -->
<SupplementalProperty
  schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Width"
  value="25.0" />

<!-- 창 높이 (디스플레이 높이 기준 %) -->
<SupplementalProperty
  schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Height"
  value="80.0" />
```

> 한 차원만 지정된 경우, 화면비가 보존되어야 한다(shall).

**강제 수어 활성화:**
```xml
<SupplementalProperty
  schemeIdUri="tag:sbtvd.org.br,2024:forcedSignLanguage"
  value="true" />
```

#### 1.3.3 비-오버레이 모드 (Section 8.1 참조)

오버레이가 설정되지 않은 경우, 수어 콘텐츠는 메인 비디오 옆에 겹침 없이 렌더링된다. 메인 비디오는 남은 수평 공간에 맞추어 비례적으로 축소된다.

시청자 프로파일 속성:
- `closedSigning`: 수어 창 표시 여부
- `closedSigningSide`: 수어 창 위치 (좌/우)
- `closedSigningWidth`: 수어 창 너비 (백분율)

---

## 2. Annex B: 수어 글로스 스트림 (Sign Language Gloss Stream)

### 2.1 개요 및 아키텍처

Annex B는 TV 3.0에서 사용할 수어 글로스 스트림 기술을 규정한다. 글로스(Gloss)는 수어의 기호, 표현, 개념을 문자 텍스트로 표현한 것이다.

**핵심 아키텍처 흐름:**

```
[방송사 측]
텍스트/자막 스트림 → 수어 기계 번역 → 글로스 시퀀스 생성 → IMSC1 파일 캡슐화 → DASH 스트림 멀티플렉싱 → OTT/OTA 전송

[수신기 측]
DASH 스트림 수신 → IMSC1 파일 디코딩 → 글로스 파싱 → 수어 사전 조회 → 아바타 애니메이션 렌더링
```

**구성 요소:**

| 구성 요소 | 위치 | 역할 |
|-----------|------|------|
| 수어 기계 번역 | 방송사 | 음성 언어 텍스트/자막을 수어 글로스 시퀀스로 번역 |
| IMSC1 인코더 | 방송사 | 글로스 시퀀스를 IMSC1 파일로 캡슐화 |
| DASH 멀티플렉서 | 방송사 | IMSC1 파일을 DASH 스트림에 멀티플렉싱 |
| 수어 플레이어 | 수신기 | IMSC1 파일 디코딩 및 아바타 렌더링 |
| 수어 사전 | 수신기/외부 | 글로스-애니메이션 매핑 제공 |

### 2.2 글로스 표현 규칙 요약

글로스는 수어의 텍스트 표현으로, 다음과 같은 특성을 가진다:

- 수어의 기호(signs), 표현(expressions), 개념(concepts)을 문자 텍스트로 표현
- 수어 문법에 따른 텍스트 표현으로, 수어로 렌더링된 콘텐츠의 이해를 돕는 역할
- 캡션 플레이어에서 수어 자막(수어의 문자 언어 표현)으로 렌더링 가능
- 글로스 스트림의 언어 식별은 IETF RFC 5646에 따름 (브라질 수어의 경우 "bzs" 코드 사용)

### 2.3 IMSC1 글로스 파일 구조

#### 2.3.1 기반 표준

- **W3C Recommendation IMSC1:2020** (TTML Profiles for Internet Media Subtitles and Captions 1.0.1)
- B.3.2 ~ B.3.4에 규정된 확장 사항 포함

#### 2.3.2 수어 글로스 스트림 식별 (B.3.2)

수어 글로스 스트림은 IMSC1의 `xml:lang` 속성으로 식별된다. 방송사는 IETF RFC 5646에 따라 해당 스트림에서 사용하는 수어를 이 속성에 설정해야 한다.

**XML 구조 예시 - 언어 식별:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml"
    xmlns:ttp="http://www.w3.org/ns/ttml#parameter"
    xmlns:tts="http://www.w3.org/ns/ttml#styling"
    xmlns:ttm="http://www.w3.org/ns/ttml#metadata"
    xml:lang="bzs">
  <!-- bzs = Brazilian Sign Language (Libras) -->
  <!-- 기타 수어 코드 예시: -->
  <!-- ase = American Sign Language (ASL) -->
  <!-- bfi = British Sign Language (BSL) -->
  <!-- ... -->
</tt>
```

**필수 속성:**

| 속성 | 값 | 설명 |
|------|-----|------|
| `xml:lang` | IETF RFC 5646 코드 | 수어 식별 코드 (예: "bzs"는 브라질 수어) |

### 2.4 글로스 콘텐츠 포맷 (B.3.3)

수어 글로스 콘텐츠는 음성 언어 자막과 동일하게 `<span>` 태그 내에 삽입된다.

**데이터 구조 - 글로스 콘텐츠 예시:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml"
    xmlns:ttp="http://www.w3.org/ns/ttml#parameter"
    xmlns:tts="http://www.w3.org/ns/ttml#styling"
    xml:lang="bzs">

  <head>
    <layout>
      <region xml:id="rRight"
              tts:origin="70% 10%"
              tts:extent="25% 80%"
              tts:displayAlign="before"
              tts:textAlign="center" />
    </layout>
  </head>

  <body>
    <div>
      <!-- 글로스 문장 1: 00:00:00 ~ 00:00:02 -->
      <p xml:id="p1" begin="00:00:00" end="00:00:02" region="rRight">
        <span> GLOSS SENTENCE 1 </span>
      </p>

      <!-- 글로스 문장 2: 00:00:02 ~ 00:00:05 -->
      <p xml:id="p2" begin="00:00:02" end="00:00:05" region="rRight">
        <span> GLOSS SENTENCE 2 </span>
      </p>
    </div>
  </body>
</tt>
```

**타이밍 정보:**

| 요소 | 속성 | 형식 | 설명 |
|------|------|------|------|
| `<p>` | `begin` | `HH:MM:SS` 또는 `HH:MM:SS.mmm` | 글로스 문장 시작 시간 |
| `<p>` | `end` | `HH:MM:SS` 또는 `HH:MM:SS.mmm` | 글로스 문장 종료 시간 |
| `<p>` | `xml:id` | 문자열 (예: "p1", "p2") | 단락 고유 식별자 |
| `<p>` | `region` | 리전 참조 ID | 글로스 텍스트 표시 영역 |

**글로스 콘텐츠 요소:**

| XML 요소 | 역할 | 비고 |
|----------|------|------|
| `<p>` | 글로스 문장 단위 (시간 동기화 단위) | 각 `<p>`는 하나의 시간 구간에 대응 |
| `<span>` | 글로스 텍스트 내용 포함 | 음성 언어 자막의 `<span>`과 동일한 방식 |

**이중 활용**: 캡션 플레이어는 `<span>` 태그 내 글로스 텍스트를 수어 자막(문자 언어 형태)으로 렌더링할 수 있다. 이는 수어 문법에 따른 텍스트 표현이므로, 수어로 렌더링된 콘텐츠의 이해를 보완할 수 있다.

### 2.5 사이즈/위치/리전 설정 (B.3.4)

수어 글로스 스트림에서 `<region>`의 IMSC1 속성(`tts:origin`, `tts:position`, `tts:extent`)은 음성 언어 폐쇄 자막 스트림과 동일하게 해석된다.

**핵심 구분:**

| 구분 | 설명 | 제어 방법 |
|------|------|-----------|
| 글로스 텍스트 표시 영역 | `<region>` 속성이 정의하는 영역 | IMSC1 `tts:origin`, `tts:extent` |
| 수어 비디오/애니메이션 렌더링 영역 | 수어 영상이 표시되는 영역 | Section 8에서 규정 |

즉, `<region>` 속성은 글로스 **텍스트가 자막으로 표시될 위치**를 나타내며, 수어 비디오(또는 애니메이션)가 **렌더링되는 위치**를 나타내지 않는다.

**좌표계:**

- 원점: 화면 좌상단 (0%, 0%)
- X축: 왼쪽에서 오른쪽 (백분율)
- Y축: 위에서 아래 (백분율)
- 단위: 디스플레이 크기 기준 백분율(%)

**리전 파라미터 값:**

| IMSC1 속성 | 용도 | 값 형식 | 예시 |
|------------|------|---------|------|
| `tts:origin` | 리전 좌상단 위치 | "X% Y%" | "70% 10%" |
| `tts:position` | 리전 위치 (대체) | "X% Y%" | "70% 10%" |
| `tts:extent` | 리전 크기 (폭 x 높이) | "W% H%" | "25% 80%" |
| `tts:displayAlign` | 수직 정렬 | before/center/after | "before" |
| `tts:textAlign` | 수평 텍스트 정렬 | left/center/right | "center" |

**수어 비디오/애니메이션의 위치 및 크기는 Section 8에서 별도로 규정:**

| schemeIdUri | 용도 | 값 |
|-------------|------|-----|
| `tag:sbtvd.org.br,2024:SL_Window_Position_X` | 수어 창 수평 위치 | 디스플레이 폭 기준 % |
| `tag:sbtvd.org.br,2024:SL_Window_Position_Y` | 수어 창 수직 위치 | 디스플레이 높이 기준 % |
| `tag:sbtvd.org.br,2024:SL_Window_Width` | 수어 창 너비 | 디스플레이 폭 기준 % |
| `tag:sbtvd.org.br,2024:SL_Window_Height` | 수어 창 높이 | 디스플레이 높이 기준 % |

### 2.6 수어 사전 (B.4)

#### 2.6.1 사전 구조

수어 사전은 수어의 기호(signs), 표현(expressions), 개념(concepts)에 대한 애니메이션을 포함한다.

**형식적 정의:**

```
Dictionary = { <gloss, anim> | gloss ∈ SignLanguage, anim ∈ Animation }
```

| 구성 요소 | 설명 |
|-----------|------|
| `gloss` | 수어의 기호, 표현 또는 개념을 나타내는 글로스 텍스트 |
| `anim` | 해당 글로스에 대응하는 아바타 애니메이션 |

- 각 글로스의 애니메이션은 수어 플레이어가 렌더링하는 **아바타**를 사용하여 표현된다

#### 2.6.2 접근 방법

수어 사전은 다음 세 가지 방법으로 접근할 수 있다:

| 접근 방법 | 설명 |
|-----------|------|
| 수신기 내부 메모리 | 수신기에 사전이 사전 설치됨 |
| 외부 저장 장치 | USB 플래시 드라이브 등의 외부 저장 매체 |
| 원격 접근 | 인터넷 연결 시 원격 서버에서 사전 접근 |

#### 2.6.3 보안 및 무결성

- 인증 기관(certifying entity)이 애니메이션 파일에 **디지털 서명**을 적용할 수 있다
- 이를 통해 수어 사전에 포함된 정보의 **보안성과 무결성**을 보장

---

## 3. 코드 구현 참조사항

### 3.1 IMSC1/TTML XML 구조 템플릿

**완전한 수어 글로스 IMSC1 문서 템플릿:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml"
    xmlns:ttp="http://www.w3.org/ns/ttml#parameter"
    xmlns:tts="http://www.w3.org/ns/ttml#styling"
    xmlns:ttm="http://www.w3.org/ns/ttml#metadata"
    xml:lang="bzs"
    ttp:timeBase="media">

  <head>
    <!-- 스타일 정의 -->
    <styling>
      <style xml:id="defaultStyle"
             tts:fontFamily="proportionalSansSerif"
             tts:fontSize="100%"
             tts:color="white"
             tts:backgroundColor="transparent" />
    </styling>

    <!-- 리전 정의: 글로스 텍스트 자막 표시 영역 -->
    <layout>
      <region xml:id="rRight"
              tts:origin="70% 10%"
              tts:extent="25% 80%"
              tts:displayAlign="before"
              tts:textAlign="center"
              tts:overflow="visible" />

      <region xml:id="rLeft"
              tts:origin="5% 10%"
              tts:extent="25% 80%"
              tts:displayAlign="before"
              tts:textAlign="center"
              tts:overflow="visible" />
    </layout>
  </head>

  <body>
    <div>
      <!-- 시간 동기화된 글로스 문장들 -->
      <p xml:id="p1" begin="00:00:00.000" end="00:00:02.500" region="rRight">
        <span>OLA MUNDO</span>
      </p>

      <p xml:id="p2" begin="00:00:02.500" end="00:00:05.000" region="rRight">
        <span>EU FELIZ</span>
      </p>

      <p xml:id="p3" begin="00:00:05.000" end="00:00:08.000" region="rRight">
        <span>OBRIGADO VOCE</span>
      </p>
    </div>
  </body>
</tt>
```

### 3.2 글로스 파싱 규칙

수신기 측에서의 글로스 파싱 처리 로직:

```
1. IMSC1 문서 수신 및 XML 파싱
2. xml:lang 속성으로 수어 식별 (예: "bzs" → 브라질 수어)
3. <body> → <div> → <p> 요소 순회
4. 각 <p> 요소에서:
   a. begin/end 속성으로 타이밍 정보 추출
   b. region 속성으로 표시 영역 결정
   c. <span> 내부 텍스트에서 글로스 시퀀스 추출
5. 각 글로스를 수어 사전에서 조회
   - 매칭: 해당 애니메이션(anim) 반환
   - 미매칭: 대체 처리 (스펠링 등)
6. 아바타 애니메이션 시퀀스 구성
7. begin/end 타이밍에 맞춰 동기화 렌더링
```

### 3.3 렌더링 파이프라인

**전체 렌더링 흐름:**

```
DASH 스트림
    │
    ▼
DASH 디멀티플렉서
    │
    ├── 메인 비디오 스트림 → 비디오 디코더 → 메인 비디오 렌더링
    │
    └── IMSC1 글로스 스트림
         │
         ▼
    IMSC1 파서
         │
         ├── 언어 식별 (xml:lang)
         ├── 타이밍 정보 추출 (begin/end)
         ├── 리전 정보 추출 (region)
         └── 글로스 텍스트 추출 (span)
              │
              ▼
    글로스-사전 매칭 엔진
         │
         ├── 사전 소스 (내부 메모리 / USB / 원격)
         └── <gloss, anim> 쌍 조회
              │
              ▼
    아바타 애니메이션 엔진
         │
         ├── 아바타 커스터마이징 (Section 9)
         │   ├── 프로파일 (male/female/kid)
         │   ├── 색상 (셔츠/바지/머리/눈/눈썹/몸)
         │   └── 광고 로고 (이미지 URL + 위치)
         │
         └── 동기화된 렌더링 출력
              │
              ▼
    화면 합성 (Compositing)
         │
         ├── 오버레이 모드: 메인 비디오 위에 수어 창 합성
         │   └── DASH MPD 디스크립터로 위치/크기 제어
         │
         └── 비-오버레이 모드: 메인 비디오 옆에 나란히 표시
             └── closedSigning/closedSigningSide/closedSigningWidth로 제어
```

### 3.4 DASH MPD 구성 예시 (수어 비디오 스트림)

```xml
<AdaptationSet>
  <!-- 수어 비디오 스트림 AdaptationSet -->

  <!-- 강제 수어 활성화 -->
  <SupplementalProperty
    schemeIdUri="tag:sbtvd.org.br,2024:forcedSignLanguage"
    value="true" />

  <!-- 오버레이 표시 활성화 -->
  <SupplementalProperty
    schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Presentation"
    value="true" />

  <!-- 수어 창 위치 -->
  <SupplementalProperty
    schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Position_X"
    value="72.0" />
  <SupplementalProperty
    schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Position_Y"
    value="5.0" />

  <!-- 수어 창 크기 -->
  <SupplementalProperty
    schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Width"
    value="25.0" />
  <SupplementalProperty
    schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Height"
    value="85.0" />

  <!-- 아바타 커스터마이징 -->
  <SupplementalProperty
    schemeIdUri="tag:sbtvd.org.br,2024:SL_AvatarCustomization"
    value="true" />
  <SupplementalProperty
    schemeIdUri="tag:sbtvd.org.br,2024:SL_AvatarProfile"
    value="female" />
  <SupplementalProperty
    schemeIdUri="tag:sbtvd.org.br,2024:SL_AvatarShirtColor"
    value="#0066CC" />
  <SupplementalProperty
    schemeIdUri="tag:sbtvd.org.br,2024:SL_AvatarBodyColor"
    value="#FFE0BD" />

  <!-- VVC 코덱 Representation -->
  <Representation
    id="sl_video_1080"
    codecs="vvc1.1.L120.M10"
    width="1080"
    height="1920"
    frameRate="30" />
</AdaptationSet>
```

### 3.5 아바타 커스터마이징 파라미터 참조 (Section 9)

| 기능 | schemeIdUri | 값 형식 | 예시 |
|------|------------|---------|------|
| 아바타 프로파일 | `SL_AvatarProfile` | "male" / "female" / "kid" | "female" |
| 셔츠 색상 | `SL_AvatarShirtColor` | #RRGGBB | "#0066CC" |
| 바지 색상 | `SL_AvatarPantsColor` | #RRGGBB | "#333333" |
| 머리 색상 | `SL_AvatarHairColor` | #RRGGBB | "#2C1B0E" |
| 몸 색상 | `SL_AvatarBodyColor` | #RRGGBB | "#FFE0BD" |
| 홍채 색상 | `SL_AvatarIrisColor` | #RRGGBB | "#4A90D9" |
| 눈썹 색상 | `SL_AvatarEyebrow` | #RRGGBB | "#2C1B0E" |
| 광고 로고 이미지 | `SL_AvatarLogoImage` | URL | "http://ebc.br/logo.png" |
| 광고 로고 위치 | `SL_AvatarLogoPosition` | "central" / "left" | "central" |

> 모든 schemeIdUri에는 `tag:sbtvd.org.br,2024:` 접두사가 적용된다.

---

## 4. Annex A와 B의 비교 분석

| 비교 항목 | Annex A (비디오 스트림) | Annex B (글로스 스트림) |
|-----------|----------------------|----------------------|
| **전송 데이터** | VVC 인코딩된 비디오 비트스트림 | IMSC1 캡슐화된 글로스 텍스트 |
| **대역폭 요구** | 높음 (비디오 스트림) | 낮음 (텍스트 데이터) |
| **수어 소스** | 인간 통역사 또는 아바타 영상 | 기계 번역 기반 글로스 시퀀스 |
| **코덱** | VVC Main 10 Profile | IMSC1/TTML |
| **수신기 요구사항** | VVC 디코더 | IMSC1 파서 + 수어 사전 + 아바타 엔진 |
| **화면비** | 9:16 (세로형) | N/A (텍스트 기반) |
| **실시간 품질** | 인코딩 품질에 의존 | 사전 완성도 및 아바타 품질에 의존 |
| **전송 방식** | OTA / OTT | OTA / OTT (DASH 스트림 내 멀티플렉싱) |
| **유연성** | 낮음 (고정 비디오) | 높음 (아바타 커스터마이징 가능) |
