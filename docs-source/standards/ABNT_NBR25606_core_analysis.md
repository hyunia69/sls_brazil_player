# ABNT NBR 25606:2025 핵심 기술 분석 보고서

## 1. 문서 개요

### 1.1 문서 목적 및 범위

ABNT NBR 25606:2025는 브라질 TV 3.0 시스템의 **수어(Sign Language) 전송 메커니즘**을 정의하는 표준 문서이다. 전송 측의 수어 코딩 시스템과 수신 측의 디코딩 프로세스를 포함하며, "Closed Signing"이라는 명칭으로 불린다. 총 62페이지(부속서 포함)로 구성되어 있으며, ABNT/CEE-085(디지털 TV 특별연구위원회)에서 개발되었다.

TV 3.0은 ABNT NBR 25601~25609 표준 스위트로 구성된 디지털 지상파 TV 시스템(DTV+)이며, 본 문서는 그 중 "closed signing" 부분을 담당한다.

### 1.2 참조 표준 (Normative References)

| 참조 표준 | 설명 |
|-----------|------|
| ABNT NBR 25608 | TV 3.0 Application Coding |
| ISO/IEC 14496-30:2018 | ISOBMFF 내 Timed Text 및 Visual Overlay |
| ISO/IEC 23000-19:2024 | CMAF (Common Media Application Format) |
| ATSC A/343:2024-04 | Captions and Subtitles |
| DASH-IF IOP ATSC 3.0 V1.1 | DASH 상호운용성 가이드라인 |
| IEEE 754 | 부동소수점 산술 표준 |
| IETF RFC 5646 | 언어 식별 태그 |
| W3C IMSC1:2020 | TTML 프로파일 (인터넷 미디어 자막) |

### 1.3 TV 3.0 표준 스위트 구성

| 표준 번호 | 담당 영역 |
|-----------|-----------|
| ABNT NBR 25601 | Over-the-air 물리 계층 |
| ABNT NBR 25602 | 전송 계층 (Transport Layer) |
| ABNT NBR 25603 | 비디오 코딩 |
| ABNT NBR 25604 | 오디오 코딩 |
| ABNT NBR 25605 | 자막 (Closed Captioning) |
| **ABNT NBR 25606** | **수어 (Closed Signing) - 본 문서** |
| ABNT NBR 25607 | 긴급 경보 시스템 |
| ABNT NBR 25608 | 애플리케이션 코딩 |
| ABNT NBR 25609 | 수신기 정의 |

---

## 2. 핵심 용어 및 정의

| 영문 용어 | 한글 설명 |
|-----------|-----------|
| **Avatar** | 가상 환경에서 사람을 그래픽으로 표현한 것 |
| **Blend Shape** | 아바타의 메시 지오메트리를 변형하여 특정 표정/모양을 만드는 함수. 모프 타겟(morph target)이라고도 함. 각 꼭짓점에 대해 속성 변경(주로 위치의 변위 벡터)을 정의 |
| **Euler Angles** | 고정 좌표계에 대한 강체의 방향을 기술하는 3개의 각도 |
| **Gloss** | 수어의 기호, 표현, 개념을 문자 텍스트로 표현/식별하는 것 |
| **Mesh** | 3D 컴퓨터 그래픽에서 삼각형들과 해당 꼭짓점에 적용되는 속성(위치, 색상 등)의 집합 |
| **Morph Target Animation** | 하나 이상의 메시를 애니메이션하며, 각 메시에 하나 이상의 블렌드 쉐이프를 사용하는 기법. 각 프레임에서 관련 블렌드 쉐이프의 선형 결합이 메시에 적용됨 |
| **Quaternion** | 4차원 벡터 공간을 형성하는 4개의 수. a + bi + cj + dk 형태. 3D 회전 계산에 널리 사용 |
| **Reference Pose** | 아바타 애니메이션 전의 기본 자세 |
| **Sign Language** | 시각-몸짓 언어. 고유한 문법 구조를 가진 농인의 자연 의사소통 형태 |
| **Skeleton** | 아바타 애니메이션에 사용되는 노드 계층 구조 |
| **Skin** | 스켈레톤 각 부분에 연결될 메시 정의 및 스켈레톤 자세에 따른 메시 변형 방법 |
| **TV 3.0** | ABNT NBR 25601~25609 표준 스위트에 정의된 디지털 지상파 TV 시스템, DTV+로도 알려짐 |

### 주요 약어

| 약어 | 의미 |
|------|------|
| CMAF | Common Media Application Format |
| DASH | Dynamic Adaptive Streaming over HTTP |
| glTF | graphics library Transmission Format |
| IMSC | Internet Media Subtitles and Captions |
| ISOBMFF | ISO Base Media File Format |
| LZMA | Lempel-Ziv-Markov Algorithm |
| MPD | Media Presentation Description |
| OTA | Over-The-Air |
| OTT | Over-The-Top |
| SLMB | Sign Language Motion Bundle |
| TTML | Timed Text Markup Language |
| silsbf | signed integer, lowest significant byte first |
| uilsbf | unsigned integer, least significant byte first |

---

## 3. TV 3.0 아키텍처

TV 3.0 시스템은 다음 계층 구조로 구성된다:

```
+-------------------------------------------+
|          Application Coding                |
|          (ABNT NBR 25608)                 |
+-------------------------------------------+
| Video  | Audio  | Closed   | Closed  | EWS|
| Coding | Coding | Caption  | Signing |    |
| (25603)| (25604)| (25605)  | (25606) |(25607)|
+-------------------------------------------+
|          Transport Layer                   |
|          (ABNT NBR 25602)                 |
+-------------------------------------------+
| Over-the-Air    | Broadband              |
| Physical Layer  | Interface              |
| (ABNT NBR 25601)| (IP 기반 양방향)        |
+-------------------------------------------+
```

- **Over-the-Air Physical Layer**: 지상파 방송 물리 계층 (ABNT NBR 25601)
- **Broadband Interface**: IP 기반 양방향 인터넷 접속 인터페이스
- **Transport Layer**: 전송 계층 (ABNT NBR 25602)
- **Application Coding**: 애플리케이션 코딩 (ABNT NBR 25608)
- **Closed Signing**: 본 문서가 정의하는 수어 전송 계층

---

## 4. Closed Signing 시스템 개요: 4가지 전송 전략

### 4.1 전송 전략 비교 분석

| 구분 | 전략 1: Video Stream | 전략 2: Gloss Stream | 전략 3: CC Translation | 전략 4: Motion Stream |
|------|---------------------|---------------------|----------------------|---------------------|
| **Annex** | Annex A | Annex B | Annex C | Annex D |
| **전송 데이터** | 보조 비디오 스트림 | IMSC1 파일 내 글로스 시퀀스 | 자막 스트림 (앱이 접근) | IMSC1 세그먼트 내 모션 블록 |
| **수어 표현** | 실제 통역사 영상 또는 아바타 생성 영상 | 수신기에서 아바타로 렌더링 | 앱에서 자동 번역 후 아바타 렌더링 | 수신기의 아바타 애니메이션 엔진 |
| **전송 경로** | OTA 또는 OTT | OTA 또는 OTT | OTT (앱 기반) | OTA 또는 OTT |
| **방송사 부담** | 높음 (별도 비디오 인코딩) | 중간 (글로스 데이터 생성) | 낮음 (자막만 제공) | 중간 (모션 데이터 생성) |
| **수신기 부담** | 낮음 (비디오 디코딩) | 높음 (사전 + 아바타 렌더링) | 매우 높음 (번역 + 렌더링) | 높음 (아바타 애니메이션 엔진) |
| **비디오 코덱** | VVC Main 10 | N/A | N/A | N/A |
| **대역폭 사용** | 높음 | 낮음 | 매우 낮음 | 낮음~중간 |
| **품질 수준** | 가장 높음 (실제 통역사 가능) | 사전 의존적 | 자동 번역 품질 의존 | 높음 (정교한 모션 데이터) |

### 4.2 각 전략의 기술적 특징

#### 전략 1: Sign Language Video Stream (Annex A)

- 방송사가 수어 해석이 포함된 **보조 비디오 스트림**을 전송
- 실제 인간 통역사 영상 또는 기계 번역 아바타 영상 가능
- **비디오 코덱**: VVC Main 10 Profile, Main Tier, Level 4.0
- **화면비**: 9:16 (세로 포맷)
- **해상도**: 메인 비디오 해상도에 따라 결정 (Table 1 참조)
- **프레임 레이트**: 메인 비디오의 동일, 1/2, 또는 1/4 (24~60fps 범위)
- **HDR**: 메인 비디오와 동일 사양, Dynamic Mapping Information 미지원

**지원 프레임 레이트 (Table A.1)**:
- 60 fps, 60000/1001 fps, 50 fps
- 30 fps, 30000/1001 fps, 25 fps
- 24 fps, 24000/1001 fps

#### 전략 2: Sign Language Gloss Stream (Annex B)

- 수어 콘텐츠를 **글로스 시퀀스**(수어의 텍스트 표현)로 전달
- IMSC1 파일에 임베딩하여 DASH 스트림으로 전송
- 수신기에서 IMSC1 파일 디코딩 후 **수어 사전**을 참조하여 아바타로 렌더링
- 글로스 언어 식별: `xml:lang` 속성 사용 (예: 브라질 수어 = "bzs")
- 글로스 콘텐츠는 `<span>` 태그에 삽입
- 수어 사전: 수신기 내부 메모리, 외부 저장장치, 또는 인터넷 원격 접근 가능
- 인증 기관이 사전 파일에 디지털 서명 가능

**IMSC1 글로스 스트림 예시**:
```xml
<tt ... xml:lang="bzs" ...>
  <p xml:id="p1" begin="00:00:00" end="00:00:02" region="rRight">
    <span> GLOSS SENTENCE 1 </span>
  </p>
  <p xml:id="p2" begin="00:00:02" end="00:00:05" region="rRight">
    <span> GLOSS SENTENCE 2 </span>
  </p>
</tt>
```

#### 전략 3: Closed Caption Streaming for Automatic Translation (Annex C)

- TV 3.0 수신기 또는 컴패니언 디바이스에서 실행되는 **앱**이 자막 스트림에 접근
- ABNT NBR 25608에서 정의한 API 메커니즘 사용
- 구어(예: 브라질 포르투갈어) 자막을 수어로 **자동 번역**
- 수어 기계 번역, 수어 사전, 수어 플레이어 컴포넌트가 모두 **앱 내에 내장**
- TV 3.0 WebServices API (ABNT NBR 25608, Annex C)를 통해 자막 콘텐츠 접근

#### 전략 4: Sign Language Motion Stream (Annex D)

- 수어 콘텐츠를 시간에 따른 **모션 블록**으로 코딩
- IMSC1 세그먼트에 임베딩하여 전송
- 수신기의 **아바타 애니메이션 엔진**이 모션 블록을 해석하여 아바타 구동
- 신체 움직임(스켈레톤 기반)과 얼굴 움직임(모프 타겟 기반)을 분리 처리
- SLMB(Sign Language Motion Bundle) 파일 형식 사용
- LZMA 압축 적용 (xz 파일 포맷)

---

## 5. 수어 콘텐츠 활성화/비활성화

### 5.1 Closed Sign Language Content

수어 콘텐츠는 **기본적으로 비활성(closed)** 상태이며, 방송사가 강제 표시할 수 있다.

**활성화 메커니즘** (3가지):

| 메커니즘 | 설명 | 즉시 효과 |
|----------|------|-----------|
| 1. Viewer Profile 설정 | 시청자 프로필에서 수어 시청 기본설정 활성화 | 재생 중 즉시 효과 아닐 수 있음 |
| 2. 리모컨 기능 | 리모컨의 수어 기능 버튼 접근 | 즉시 |
| 3. API 메커니즘 | TV 3.0 Application Coding (ABNT NBR 25608) API 활용 | 구현 의존 |

- 동일한 메커니즘으로 비활성화 가능
- 시청자 프로필 설정(메커니즘 1)은 현재 재생 중인 미디어에 즉시 적용되지 않을 수 있음

### 5.2 강제 활성화 (Forced Activation)

방송사는 선택적으로 **모든 시청자에게 수어를 강제 활성화**(open sign language)할 수 있다.

**DASH MPD 시그널링**:
```xml
<SupplementalProperty
  schemeIdUri="tag:sbtvd.org.br,2024:forcedSignLanguage"
  value="true" />
```

- 이 시그널링이 MPD에 없으면 수어 콘텐츠는 closed 상태
- 있으면 모든 시청자에게 수어가 표시됨

---

## 6. 수어 프레젠테이션

### 6.1 비중첩 표시 (Non-overlapping, Section 8.1)

수어 콘텐츠가 **메인 비디오 옆에 겹치지 않게** 렌더링되는 기본 모드.

**시청자 프로필 속성**:

| 속성 | 타입 | 설명 |
|------|------|------|
| `closedSigning` | Boolean | 수어 창 표시 여부 |
| `closedSigningSide` | String | 수어 창 위치 (left / right) |
| `closedSigningWidth` | Percentage | 수어 창 너비 (백분율) |

- 메인 비디오: 16:9 화면비
- 수어 콘텐츠: **9:16 화면비** (세로)
- 메인 비디오는 남은 수평 공간에 맞게 비례 축소
- 수어 창과 메인 비디오가 각각의 영역 내에서 수직 중앙 정렬

**해상도 매핑 테이블 (Table 1)**:

| 메인 비디오 해상도 | 수어 콘텐츠 해상도 |
|-------------------|-------------------|
| 1280 x 720 (HD) | 360 x 640 |
| 1920 x 1080 (FHD) | 540 x 960 |
| 2560 x 1440 (QHD) | 720 x 1280 |
| 3840 x 2160+ (4K+) | 1080 x 1920 |

### 6.2 오버레이 모드 (Section 8.2)

수어 콘텐츠를 메인 비디오 위에 **오버레이**하여 표시.

**오버레이 활성화 DASH MPD 시그널링**:
```xml
<SupplementalProperty
  schemeIdUri="tag:sbtvd.org.br,2024:SL_Window_Presentation"
  value="true" />
```

#### 6.2.1 수어 창 위치 (Sign Language Window Position)

| DASH MPD 속성 | schemeIdUri | value 설명 |
|--------------|------------|-----------|
| 수평 위치 (X) | `tag:sbtvd.org.br,2024:SL_Window_Position_X` | 디스플레이 너비 기준 백분율 (좌측 기준, 좌->우) |
| 수직 위치 (Y) | `tag:sbtvd.org.br,2024:SL_Window_Position_Y` | 디스플레이 높이 기준 백분율 (상단 기준, 위->아래) |

#### 6.2.2 수어 창 크기 (Sign Language Window Size)

| DASH MPD 속성 | schemeIdUri | value 설명 |
|--------------|------------|-----------|
| 너비 | `tag:sbtvd.org.br,2024:SL_Window_Width` | 디스플레이 너비 기준 백분율 |
| 높이 | `tag:sbtvd.org.br,2024:SL_Window_Height` | 디스플레이 높이 기준 백분율 |

- 하나의 차원만 지정 시 화면비 유지

#### 6.2.3 메인 비디오 창 위치 (Main Video Window Position)

| DASH MPD 속성 | schemeIdUri | value 설명 |
|--------------|------------|-----------|
| 수평 위치 (X) | `tag:sbtvd.org.br,2024:Video_Window_Position_X` | 디스플레이 너비 기준 백분율 |
| 수직 위치 (Y) | `tag:sbtvd.org.br,2024:Video_Window_Position_Y` | 디스플레이 높이 기준 백분율 |

- 수어 콘텐츠 재생 중에만 적용

#### 6.2.4 메인 비디오 창 크기 (Main Video Window Size)

| DASH MPD 속성 | schemeIdUri | value 설명 |
|--------------|------------|-----------|
| 너비 | `tag:sbtvd.org.br,2024:Video_Window_Width` | 디스플레이 너비 기준 백분율 |
| 높이 | `tag:sbtvd.org.br,2024:Video_Window_Height` | 디스플레이 높이 기준 백분율 |

- 하나의 차원만 지정 시 화면비 유지
- 수어 콘텐츠 재생 중에만 적용

---

## 7. 아바타 커스터마이제이션

### 7.1 커스터마이제이션 가능 요소

아바타를 사용하는 수어 전송 전략에서 방송사가 **선택적으로** 아바타를 커스터마이즈할 수 있다.

**활성화 DASH MPD 시그널링**:
```xml
<SupplementalProperty
  schemeIdUri="tag:sbtvd.org.br,2024:SL_AvatarCustomization"
  value="true" />
```

#### 커스터마이제이션 속성 테이블 (Table 2)

| 기능 | schemeIdUri | value 형식 | 설명 |
|------|------------|-----------|------|
| **Avatar Profile** | `tag:sbtvd.org.br,2024:SL_AvatarProfile` | `"male"`, `"female"`, `"kid"` | 아바타 프로필 (성별/연령) |
| **Shirt Color** | `tag:sbtvd.org.br,2024:SL_AvatarShirtColor` | `#RRGGBB` | 셔츠 색상 |
| **Pants Color** | `tag:sbtvd.org.br,2024:SL_AvatarPantsColor` | `#RRGGBB` | 바지 색상 |
| **Hair Color** | `tag:sbtvd.org.br,2024:SL_AvatarHairColor` | `#RRGGBB` | 머리카락 색상 |
| **Body Color** | `tag:sbtvd.org.br,2024:SL_AvatarBodyColor` | `#RRGGBB` | 피부 색상 |
| **Iris Color** | `tag:sbtvd.org.br,2024:SL_AvatarIrisColor` | `#RRGGBB` | 눈동자 색상 |
| **Eyebrow Color** | `tag:sbtvd.org.br,2024:SL_AvatarEyebrow` | `#RRGGBB` | 눈썹 색상 |
| **Logo Image** | `tag:sbtvd.org.br,2024:SL_AvatarLogoImage` | URL | 셔츠에 렌더링할 광고 로고 이미지 |
| **Logo Position** | `tag:sbtvd.org.br,2024:SL_AvatarLogoPosition` | `"central"`, `"left"` | 로고 위치 (셔츠 중앙 또는 가슴 좌측) |

- API를 통한 커스터마이제이션도 가능 (ABNT NBR 25608, Annex C)

---

## 8. 코드 구현 시 핵심 참조사항

### 8.1 DASH MPD SupplementalProperty Descriptor 전체 목록

구현 시 파싱/생성해야 하는 모든 DASH MPD SupplementalProperty descriptor:

```
tag:sbtvd.org.br,2024:forcedSignLanguage          -> "true"
tag:sbtvd.org.br,2024:SL_Window_Presentation      -> "true"
tag:sbtvd.org.br,2024:SL_Window_Position_X         -> decimal (%)
tag:sbtvd.org.br,2024:SL_Window_Position_Y         -> decimal (%)
tag:sbtvd.org.br,2024:SL_Window_Width              -> decimal (%)
tag:sbtvd.org.br,2024:SL_Window_Height             -> decimal (%)
tag:sbtvd.org.br,2024:Video_Window_Position_X      -> decimal (%)
tag:sbtvd.org.br,2024:Video_Window_Position_Y      -> decimal (%)
tag:sbtvd.org.br,2024:Video_Window_Width           -> decimal (%)
tag:sbtvd.org.br,2024:Video_Window_Height          -> decimal (%)
tag:sbtvd.org.br,2024:SL_AvatarCustomization       -> "true"
tag:sbtvd.org.br,2024:SL_AvatarProfile             -> "male"|"female"|"kid"
tag:sbtvd.org.br,2024:SL_AvatarShirtColor          -> #RRGGBB
tag:sbtvd.org.br,2024:SL_AvatarPantsColor          -> #RRGGBB
tag:sbtvd.org.br,2024:SL_AvatarHairColor           -> #RRGGBB
tag:sbtvd.org.br,2024:SL_AvatarBodyColor           -> #RRGGBB
tag:sbtvd.org.br,2024:SL_AvatarIrisColor           -> #RRGGBB
tag:sbtvd.org.br,2024:SL_AvatarEyebrow             -> #RRGGBB
tag:sbtvd.org.br,2024:SL_AvatarLogoImage           -> URL
tag:sbtvd.org.br,2024:SL_AvatarLogoPosition        -> "central"|"left"
tag:sbtvd.org.br,2024:SL_AvatarBodyGeometryIds     -> comma-separated IDs
tag:sbtvd.org.br,2024:SL_AvatarFaceGeometryIds     -> comma-separated IDs
```

### 8.2 모션 스트림 데이터 구조 (Annex D)

#### 8.2.1 스켈레톤 구조

- **루트 조인트**: `hips_JNT`
- **총 조인트 수**: 46개 (body geometry ID 1 기준)
- **기준 자세**: T-pose (팔을 수평으로 펼친 자세)
- **단위**: 미터 (1.67m 인체 기반)
- **좌표계**: X(체간 가로, 우->좌), Y(체간 세로, 하->상), Z(전후, 후->전)
- **상반신만** 사용 (머리, 몸통, 상지)

**스켈레톤 계층 구조**:
```
hips_JNT (root, type 0)
  +-- spine_JNT (type 1)
      +-- spine1_JNT (type 1)
          +-- spine2_JNT (type 1)
              +-- neck_JNT (type 1)
              |   +-- head_JNT (type 1)
              |       +-- r_eye_LOC (type 4)
              |       +-- l_eye_LOC (type 4)
              +-- r_shoulder_JNT (type 1)
              |   +-- r_arm_JNT (type 1)
              |       +-- r_forearm_JNT (type 1)
              |           +-- r_hand_JNT (type 1)
              |               +-- r_handThumb1_JNT (type 1) -> 2 -> 3
              |               +-- r_handIndex1_JNT (type 2) -> 2(type 3) -> 3(type 3)
              |               +-- r_handMiddle1_JNT (type 2) -> 2 -> 3
              |               +-- r_handRing1_JNT (type 2) -> 2 -> 3
              |               +-- r_handPinky1_JNT (type 2) -> 2 -> 3
              +-- l_shoulder_JNT (type 1)
                  +-- l_arm_JNT (type 1)
                      +-- l_forearm_JNT (type 1)
                          +-- l_hand_JNT (type 1)
                              +-- (좌측 손 구조 - 우측과 대칭)
```

#### 8.2.2 조인트 타입 및 움직임 제한 (Table D.4)

| 타입 | 회전 자유도 | 이동 자유도 | 해당 조인트 | 비트 수/프레임 |
|------|------------|------------|------------|--------------|
| **0** | 완전 자유 | [-0.50m, 0.50m] 구간 내 | hips_JNT (루트) | 48+48=96 bits |
| **1** | 완전 자유 (쿼터니언) | 없음 | spine, neck, head, shoulder, arm, forearm, hand, thumb1 | 48 bits |
| **2** | Z축 360도, X/Y축 [-90, 90] | 없음 | 손바닥 조인트 (Index1, Middle1, Ring1, Pinky1) | 32 bits |
| **3** | Z축만 | 없음 | 손가락 관절 (2nd, 3rd 마디, Thumb2/3) | 8 bits |
| **4** | Z축 없음, X/Y축 [-90, 90] | 없음 | 눈 (r_eye_LOC, l_eye_LOC) | 16 bits |

#### 8.2.3 BodyMotionBlock 바이너리 형식

```
BodyMotionBlock {
    number_of_frames    : 32 bits (uilsbf)
    frame_time          : 32 bits (IEEE-754 float, 초 단위)

    for each joint (46개):
        for each frame:
            if type 0:  Tx(16), Ty(16), Tz(16)  // 이동: [0, 65535]로 정규화
            if type 0|1: Qx(16s), Qy(16s), Qz(16s)  // 쿼터니언: [-32767, 32767]
            if type 2:  E2(32)  // 10bit(x) + 10bit(y) + 12bit(z)
            if type 3:  E3(8)   // [-180, 180] -> [0, 255]
            if type 4:  E4(16)  // 8bit(x) + 8bit(y), [-90, 90] -> [0, 255]
}
```

**정규화 규칙**:
- Type 0 이동: [-0.5m, 0.5m] -> [0, 65535] (16-bit unsigned)
- Type 0/1 쿼터니언: [-1, 1] -> [-32767, 32767] (16-bit signed), qw는 항상 양수여야 함
- Type 2 E2x/E2y: [-90, 90] -> [0, 1023] (10-bit unsigned)
- Type 2 E2z: [-180, 180] -> [0, 4095] (12-bit unsigned)
- Type 3 E3: [-180, 180] -> [0, 255] (8-bit unsigned)
- Type 4 E4x/E4y: [-90, 90] -> [0, 255] (8-bit unsigned)

#### 8.2.4 FaceMotionBlock 바이너리 형식

```
FaceMotionBlock {
    number_of_frames        : 16 bits (uilsbf)
    frame_time[N]           : 32 bits each (IEEE-754 float, 초 단위)
    number_of_blend_shapes  : 16 bits (uilsbf)

    for each active blend_shape:
        blend_shape_id          : 16 bits (uilsbf)
        number_of_frame_ranges  : 16 bits (uilsbf)

        for each frame_range:
            frame_range_first   : 16 bits (uilsbf)
            frame_range_size    : 16 bits (uilsbf)

        for each frame_in_ranges:
            blend_shape_weight  : 16 bits (uilsbf)  // [0, 1] -> [0, 65535]
}
```

- 가중치 0인 블렌드 쉐이프는 생략하여 크기 최적화
- 프레임 범위로 연속 프레임을 묶어 효율적 표현
- 68개의 블렌드 쉐이프 정의 (총 130개 이상의 blend_shape_id, 메시별로 구분)

#### 8.2.5 블렌드 쉐이프 ID 체계

| 메시 | ID 범위 | 블렌드 쉐이프 수 |
|------|---------|----------------|
| head_GEO | 0~67 | 68개 |
| mouth_GEO | 1020~1067 | 16개 |
| eyelash_GEO | 2000~2059 | 18개 |
| eyebrow_l_GEO | 3014~3058 | 9개 |
| eyebrow_r_GEO | 4014~4058 | 9개 |
| iris_l_GEO | 5059 | 1개 |
| iris_r_GEO | 6059 | 1개 |

**ID 계산 규칙**: `mesh_base + blend_shape_index_in_head_GEO`
- head_GEO: base = 0
- mouth_GEO: base = 1000
- eyelash_GEO: base = 2000
- eyebrow_l_GEO: base = 3000
- eyebrow_r_GEO: base = 4000
- iris_l_GEO: base = 5000
- iris_r_GEO: base = 6000

#### 8.2.6 SLMB 번들 형식

```
MotionBundle {
    for each element:
        header          : 8 bits
            [7:5] = key_length - 1
            [4:0] = payload_config (< 31이면 payload 크기, 31이면 별도 지정)
        key[]           : (key_length + 1) bytes

        if payload_config == 0x1F:
            payload_size : 32 bits (uilsbf)
            payload[]    : payload_size bytes
        else:
            payload[]    : payload_config bytes
}
```

**모션 요소 키 (Table D.12)**:

| 요소 타입 | 키 바이트 | 페이로드 |
|-----------|----------|---------|
| Title | `{0x53, 0x4C, 0x4D, 0x42}` ("SLMB") | empty |
| Body Motion (geometry ID 1) | `{0x01, 0x01}` | BodyMotionBlock |
| Face Motion (face geometry ID 1) | `{0x02, 0x01}` | FaceMotionBlock |

- Title 요소가 번들의 첫 번째 요소여야 함
- 최소 하나의 Body Motion과 하나의 Face Motion 요소 필수
- 동일 키의 중복 요소 불가
- 압축: LZMA 알고리즘, xz 파일 포맷
- 파일 확장자: `.slmb.xz`

### 8.3 IMSC1 Sign Language Motion Profile

#### 프로파일 식별자

- **Profile ID**: `im1m`
- **Profile Designator**: `http://forumsbtvd.org.br/ns/ttml/profile/imsc1/signlanguagemotion`
- **MIME Type**: `application/ttml+xml;codecs=im1m`
- **DASH codecs**: `stpp.ttml.im1m`
- **CMAF Track Brand**: `'im1m'`

#### SBTVD-SLM Extension

- 네임스페이스: `http://forumsbtvd.org.br/schemas/sbtvd-slm`
- 접두사: `sbtvd`
- 속성: `signlanguagemotion` (xs:anyURI 타입, div 요소에 할당)
- SLMB 파일 경로를 참조

**IMSC1 문서 내 사용 예시**:
```xml
<tt xmlns:sbtvd="http://forumsbtvd.org.br/schemas/sbtvd-slm"
    ttp:profile="http://forumsbtvd.org.br/ns/ttml/profile/imsc1/signlanguagemotion">
  <body>
    <div sbtvd:signlanguagemotion="urn:mpeg:14496-30:subs:1"
         begin="00:00:00" end="00:00:05" region="r1">
      <metadata>
        <ittm:altText>Text alternative of sign language</ittm:altText>
      </metadata>
    </div>
  </body>
</tt>
```

#### 주요 프로파일 제약사항

- 텍스트 프로파일과 수어 모션 프로파일은 동일 문서에서 **공존 불가**
- `p`, `span`, `br` 요소 사용 **금지**
- 대부분의 텍스트 관련 TTML 기능(#color, #fontFamily, #fontSize, #textAlign 등) **금지**
- `tts:origin`, `tts:extent`, `tts:backgroundColor`만 **허용** (region 정의)
- `#signlanguagemotion` extension만 **permitted**

### 8.4 ISOBMFF 캡슐화

- IMSC1 문서의 ISOBMFF 캡슐화는 ISO/IEC 14496-30:2018, Section 5를 따름
- SLMB 파일은 TTML 문서가 참조하는 리소스로 취급
- TTML 문서와 SLMB 파일 모두 ISO/IEC 14496-30:2018, 5.6 가이드라인에 따라 포맷

### 8.5 얼굴 지오메트리

- glTF 2.0 사양 기반 (`SignLanguageMotionFace.glTF`, `SignLanguageMotionFace.bin`)
- **7개 메시**: head_GEO, eyelash_GEO, mouth_GEO, eyebrow_l_GEO, eyebrow_r_GEO, iris_l_GEO, iris_r_GEO
- **68개 블렌드 쉐이프**: 눈, 눈썹, 턱, 입, 입술, 턱, 볼, 감정(행복/분노/혐오/슬픔/놀람), 혀 제어
- 각 꼭짓점의 NORMAL, POSITION, TANGENT 속성으로 정의
- 블렌드 쉐이프 가중치: 0(변형 없음) ~ 1(최대 변형)

### 8.6 필수 지원 기능 목록

#### 수신기 필수 기능

1. **DASH MPD 파싱**: 모든 SupplementalProperty descriptor 처리
2. **수어 창 렌더링**: 오버레이 및 비중첩 모드 지원
3. **수어 활성화/비활성화**: 3가지 메커니즘 지원
4. **해상도 매핑**: Table 1에 따른 수어 콘텐츠 해상도 결정
5. **화면비 보존**: 단일 차원 지정 시 자동 화면비 유지

#### 전략별 필수 기능

| 기능 | Video Stream | Gloss Stream | CC Translation | Motion Stream |
|------|:-----------:|:-----------:|:--------------:|:------------:|
| VVC Main 10 디코더 | 필수 | - | - | - |
| 9:16 비디오 렌더링 | 필수 | - | - | - |
| IMSC1 파서 | - | 필수 | - | 필수 |
| 수어 사전 | - | 필수 | 앱 내 | 선택 |
| 아바타 렌더링 엔진 | - | 필수 | 앱 내 | 필수 |
| 글로스 텍스트 렌더링 | - | 선택 | - | - |
| WebServices API | - | - | 필수 | - |
| 스켈레톤 애니메이션 | - | - | - | 필수 |
| 블렌드 쉐이프 처리 | - | - | - | 필수 |
| SLMB 파일 파서 | - | - | - | 필수 |
| LZMA 디코더 | - | - | - | 필수 |
| glTF 2.0 파서 | - | - | - | 필수 |
| 아바타 커스터마이제이션 | 선택 | 선택 | 선택 | 선택 |

---

## 부록: 블렌드 쉐이프 전체 목록 (68개, head_GEO 기준)

| ID | 이름 | 영향 메시 | 설명 |
|----|------|----------|------|
| 0 | EyeBlink_Left | head, eyelash | 왼쪽 눈 깜빡임 |
| 1 | EyeBlink_Right | head, eyelash | 오른쪽 눈 깜빡임 |
| 2 | EyeSquint_Left | head, eyelash | 왼쪽 눈 찡그림 |
| 3 | EyeSquint_Right | head, eyelash | 오른쪽 눈 찡그림 |
| 4 | EyeDown_Left | head, eyelash | 왼쪽 눈 아래로 |
| 5 | EyeDown_Right | head, eyelash | 오른쪽 눈 아래로 |
| 6 | EyeIn_Left | head, eyelash | 왼쪽 눈 안쪽으로 |
| 7 | EyeIn_Right | head, eyelash | 오른쪽 눈 안쪽으로 |
| 8 | EyeOpen_Left | head, eyelash | 왼쪽 눈 뜨기 |
| 9 | EyeOpen_Right | head, eyelash | 오른쪽 눈 뜨기 |
| 10 | EyeOut_Left | head, eyelash | 왼쪽 눈 바깥으로 |
| 11 | EyeOut_Right | head, eyelash | 오른쪽 눈 바깥으로 |
| 12 | EyeUp_Left | head, eyelash | 왼쪽 눈 위로 |
| 13 | EyeUp_Right | head, eyelash | 오른쪽 눈 위로 |
| 14 | BrowsDown_Left | head, eyebrow_l/r | 왼쪽 눈썹 내리기 |
| 15 | BrowsDown_Right | head, eyebrow_l/r | 오른쪽 눈썹 내리기 |
| 16 | BrowsUp_Center | head, eyebrow_l/r | 양쪽 눈썹 안쪽 올리기 |
| 17 | BrowsUp_Left | head, eyebrow_l/r | 왼쪽 눈썹 올리기 |
| 18 | BrowsUp_Right | head, eyebrow_l/r | 오른쪽 눈썹 올리기 |
| 19 | JawFwd | head | 턱 앞으로 |
| 20 | JawLeft | head, mouth | 턱 왼쪽으로 |
| 21 | JawOpen | head, mouth | 입 벌리기 |
| 22 | JawChew | head | 씹기 |
| 23 | JawRight | head, mouth | 턱 오른쪽으로 |
| 24 | MouthLeft | head, mouth | 입 왼쪽 코너 올리기 |
| 25 | MouthRight | head, mouth | 입 오른쪽 코너 올리기 |
| 26 | MouthFrown_Left | head | 입 왼쪽 코너 내리기 |
| 27 | MouthFrown_Right | head | 입 오른쪽 코너 내리기 |
| 28 | MouthSmile_Left | head | 왼쪽 미소 |
| 29 | MouthSmile_Right | head | 오른쪽 미소 |
| 30 | MouthDimple_Left | head | 왼쪽 보조개 |
| 31 | MouthDimple_Right | head | 오른쪽 보조개 |
| 32 | LipsStretch_Left | head | 왼쪽 입술 늘이기 |
| 33 | LipsStretch_Right | head | 오른쪽 입술 늘이기 |
| 34 | LipsUpperClose | head | 윗입술 닫기/좁히기 |
| 35 | LipsLowerClose | head | 아랫입술 닫기/좁히기 |
| 36 | LipsUpperUp | head, mouth | 윗입술 올리기 |
| 37 | LipsLowerDown | head, mouth | 아랫입술 내리기 |
| 38 | LipsUpperOpen | head | 윗입술 열기 |
| 39 | LipsLowerOpen | head | 아랫입술 열기 |
| 40 | LipsFunnel | head, mouth | "오" 모양 입 |
| 41 | LipsPucker | head | 입술 오므리기 |
| 42 | ChinLowerRaise | head | 아래턱 올리기 |
| 43 | ChinUpperRaise | head | 위턱 올리기 |
| 44 | Sneer | head, eyebrow_l/r | 화난 표정 (이마 찡그림) |
| 45 | Puff | head | 볼 부풀리기 (양쪽) |
| 46 | CheekSquint_Left | head, eyelash | 왼쪽 볼 찡그림 |
| 47 | CheekSquint_Right | head, eyelash | 오른쪽 볼 찡그림 |
| 48 | HAPPY_48 | head, eyelash | 행복 - 초승달 모양 눈 |
| 49 | HAPPY_49 | head | 행복 - 입 양쪽 늘이기 |
| 50 | HAPPY_50 | head, mouth | 행복 - 입 살짝 벌리기 |
| 51 | HAPPY_51 | head, mouth, eyebrow_l/r | 행복 - 입 벌리고 눈썹 올리기 |
| 52 | HAPPY_52 | head, mouth | 행복 - 이 드러내기 |
| 53 | ANGRY_53 | head | 분노 - 입 코너 내리기 |
| 54 | ANGRY_54 | head, eyelash | 분노 - 눈꺼풀 내리기 |
| 55 | ANGRY_55 | head, eyebrow_l/r | 분노 - 화난 찡그림 |
| 56 | DISGUST_56 | head | 혐오 - 입 왼쪽 코너 내리기 |
| 57 | DISGUST_57 | head | 혐오 - 입 오른쪽 코너 내리기 |
| 58 | SAD_58 | head, eyelash, eyebrow_l/r | 슬픔 - 입 코너 내리기, 눈썹 중앙 올리기 |
| 59 | SURPRISE_59 | head, eyelash, mouth, iris_l/r | 놀람 - 눈 크게 뜨기, 동공 수축 |
| 60 | SURPRISE_60 | head | 놀람 - 입 코너 내리기 |
| 61 | Puff_Left | head | 왼쪽 볼 부풀리기 |
| 62 | Puff_Right | head | 오른쪽 볼 부풀리기 |
| 63 | Tongue_Out | head, mouth | 혀 내밀기 |
| 64 | Tongue_Up | head, mouth | 혀 위로 |
| 65 | Tongue_Down | head, mouth | 혀 아래로 |
| 66 | Tongue_Left | head, mouth | 혀 왼쪽으로 |
| 67 | Tongue_Right | head, mouth | 혀 오른쪽으로 |
