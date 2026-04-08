# ABNT NBR 25606 - Annex C/D 기술 분석

> **문서**: ABNT NBR 25606:2025 - TV 3.0 Closed Signing
> **분석 범위**: Annex C (자막 스트리밍), Annex D (모션 스트림)
> **작성일**: 2026-02-12

---

## 1. Annex C: 자막 스트리밍 기반 수어 자동 번역

### 1.1 개요

Annex C는 TV 3.0에서 사용되는 **자막 스트리밍을 통한 수어 자동 번역 및 적응(Closed Caption Streaming for Automatic Translation and Adaptation to Sign Language)** 기술을 규정한다.

이 기술의 핵심 개념은 방송국이 전송하는 음성 언어(예: 브라질 포르투갈어)의 자막 스트림에 수신기 측 애플리케이션이 접근하여, 해당 자막 내용을 수어(예: 브라질 수어, Libras)로 자동 번역하는 것이다.

### 1.2 기술 동작 흐름

```
방송국 측:
  오디오 + 비디오 + 자막(음성 언어) → OTT/OTA 다중화 전송

수신기 측:
  등록된 앱 → API를 통해 자막 스트림 요청
       ↓
  자막 수신 → 수어 기계 번역(Machine Translation)
       ↓
  수어 사전 참조 → 수어 플레이어로 아바타 애니메이션
```

**핵심 특징**:
- 수어 기계 번역, 수어 사전, 수어 플레이어 컴포넌트가 모두 수신기 또는 컴패니언 디바이스에서 실행되는 애플리케이션 내에 임베딩됨
- 방송국 측에서 별도의 수어 콘텐츠를 제작/전송할 필요 없음
- 수신기 측에서 실시간 자동 번역 수행

### 1.3 WebServices API 사양

자막 스트림 접근을 위한 API 메커니즘:

| 항목 | 내용 |
|------|------|
| **API 규격** | ABNT NBR 25608, Annex C에 정의된 TV 3.0 WebServices API |
| **용도** | 수신기/컴패니언 디바이스의 앱이 자막 콘텐츠에 접근 |
| **접근 방식** | 등록된 애플리케이션이 API를 통해 자막 스트림 파일 요청 |
| **대상 콘텐츠** | 음성 언어로 작성된 자막 스트림 |

### 1.4 자동 번역 파이프라인

Annex C의 자동 번역 파이프라인은 다음 컴포넌트로 구성된다:

1. **자막 스트림 수신**: WebServices API를 통해 음성 언어 자막 접근
2. **수어 기계 번역(Sign Language Machine Translation)**: 텍스트를 수어 글로스/모션으로 변환
3. **수어 사전(Sign Dictionary)**: 글로스에 대응하는 수어 동작 데이터 참조
4. **수어 플레이어(Sign Player)**: 아바타를 통한 수어 동작 렌더링

---

## 2. Annex D: 수어 모션 스트림

### 2.1 개요 및 아키텍처

Annex D는 TV 3.0에서 사용되는 **수어 모션 스트림(Sign Language Motion Stream)** 기술을 규정한다. 이 기술은 Annex C의 자동 번역 방식과 달리, 방송국 측에서 전문 번역사가 생성한 모션 데이터를 전송하는 방식이다.

#### 전체 파이프라인

```
[방송국 측]
  수어 번역사 → 글로스 시퀀스 정의
       ↓
  수어 사전 → 모션 데이터 파일 생성 (SLMB 포맷)
       ↓
  IMSC1 포맷으로 코딩 → 오디오/비디오/자막과 다중화

[수신기 측]
  DASH 디먹싱 → ISOBMFF → CMAF 트랙 추출
       ↓
  IMSC1 콘텐츠에서 모션 파일(SLMB) 추출
       ↓
  SLMB 디코딩 → BodyMotionBlock + FaceMotionBlock
       ↓
  아바타 애니메이션 엔진 → 아바타 렌더링
```

#### 기술 계층 구조

```
┌─────────────────────────────────────────────┐
│              DASH MPD 매니페스트              │
│  (codecs="stpp.ttml.im1m")                  │
├─────────────────────────────────────────────┤
│           CMAF IMSC1 SLM 트랙               │
│  (File Brand: 'im1m')                       │
├─────────────────────────────────────────────┤
│         ISOBMFF 캡슐화                       │
│  (ISO/IEC 14496-30 기반)                    │
├─────────────────────────────────────────────┤
│    IMSC1 수어 모션 프로파일 문서              │
│  (TTML + sbtvd:signlanguagemotion)          │
├─────────────────────────────────────────────┤
│            SLMB 파일 (.slmb.xz)             │
│  (LZMA/xz 압축된 모션 번들)                 │
├──────────────────┬──────────────────────────┤
│ BodyMotionBlock  │    FaceMotionBlock       │
│ (관절 이동 데이터) │  (블렌드쉐이프 가중치)    │
└──────────────────┴──────────────────────────┘
```

---

### 2.2 바디 무브먼트

#### 2.2.1 스켈레톤 조인트 구조

아바타는 인간형(humanoid) 상체 모델로, **46개 조인트**로 구성된 트리 구조의 스켈레톤을 사용한다.

- **단위**: 미터(m)
- **기준 인체 크기**: 1.67m
- **루트 조인트**: `hips_JNT` (엉덩이)
- **표시 범위**: 상체만 (머리, 몸통, 상지)
- **좌표계**: 오른손 좌표계 (x: 오른쪽→왼쪽, y: 아래→위, z: 뒤→앞)

##### 조인트 계층 구조 (Table D.1)

```
hips_JNT (루트)
├── spine_JNT
│   └── spine1_JNT
│       └── spine2_JNT
│           ├── neck_JNT
│           │   └── head_JNT
│           │       ├── r_eye_LOC
│           │       └── l_eye_LOC
│           ├── r_shoulder_JNT
│           │   └── r_arm_JNT
│           │       └── r_forearm_JNT
│           │           └── r_hand_JNT
│           │               ├── r_handThumb1_JNT → r_handThumb2_JNT → r_handThumb3_JNT
│           │               ├── r_handIndex1_JNT → r_handIndex2_JNT → r_handIndex3_JNT
│           │               ├── r_handMiddle1_JNT → r_handMiddle2_JNT → r_handMiddle3_JNT
│           │               ├── r_handRing1_JNT → r_handRing2_JNT → r_handRing3_JNT
│           │               └── r_handPinky1_JNT → r_handPinky2_JNT → r_handPinky3_JNT
│           └── l_shoulder_JNT
│               └── l_arm_JNT
│                   └── l_forearm_JNT
│                       └── l_hand_JNT
│                           ├── l_handThumb1_JNT → l_handThumb2_JNT → l_handThumb3_JNT
│                           ├── l_handIndex1_JNT → l_handIndex2_JNT → l_handIndex3_JNT
│                           ├── l_handMiddle1_JNT → l_handMiddle2_JNT → l_handMiddle3_JNT
│                           ├── l_handRing1_JNT → l_handRing2_JNT → l_handRing3_JNT
│                           └── l_handPinky1_JNT → l_handPinky2_JNT → l_handPinky3_JNT
```

##### 전체 조인트 목록 (46개)

| # | 조인트 이름 | 부모 조인트 | 자식 조인트 |
|---|-----------|-----------|-----------|
| 1 | hips_JNT | (없음 - 루트) | spine_JNT |
| 2 | spine_JNT | hips_JNT | spine1_JNT |
| 3 | spine1_JNT | spine_JNT | spine2_JNT |
| 4 | spine2_JNT | spine1_JNT | neck_JNT, r_shoulder_JNT, l_shoulder_JNT |
| 5 | neck_JNT | spine2_JNT | head_JNT |
| 6 | head_JNT | neck_JNT | r_eye_LOC, l_eye_LOC |
| 7 | r_eye_LOC | head_JNT | (없음) |
| 8 | l_eye_LOC | head_JNT | (없음) |
| 9 | r_shoulder_JNT | spine2_JNT | r_arm_JNT |
| 10 | r_arm_JNT | r_shoulder_JNT | r_forearm_JNT |
| 11 | r_forearm_JNT | r_arm_JNT | r_hand_JNT |
| 12 | r_hand_JNT | r_forearm_JNT | r_handThumb1~Pinky1_JNT |
| 13-15 | r_handThumb1~3_JNT | 이전 관절 | 다음 관절 또는 없음 |
| 16-18 | r_handIndex1~3_JNT | 이전 관절 | 다음 관절 또는 없음 |
| 19-21 | r_handMiddle1~3_JNT | 이전 관절 | 다음 관절 또는 없음 |
| 22-24 | r_handRing1~3_JNT | 이전 관절 | 다음 관절 또는 없음 |
| 25-27 | r_handPinky1~3_JNT | 이전 관절 | 다음 관절 또는 없음 |
| 28 | l_shoulder_JNT | spine2_JNT | l_arm_JNT |
| 29 | l_arm_JNT | l_shoulder_JNT | l_forearm_JNT |
| 30 | l_forearm_JNT | l_arm_JNT | l_hand_JNT |
| 31 | l_hand_JNT | l_forearm_JNT | l_handThumb1~Pinky1_JNT |
| 32-34 | l_handThumb1~3_JNT | 이전 관절 | 다음 관절 또는 없음 |
| 35-37 | l_handIndex1~3_JNT | 이전 관절 | 다음 관절 또는 없음 |
| 38-40 | l_handMiddle1~3_JNT | 이전 관절 | 다음 관절 또는 없음 |
| 41-43 | l_handRing1~3_JNT | 이전 관절 | 다음 관절 또는 없음 |
| 44-46 | l_handPinky1~3_JNT | 이전 관절 | 다음 관절 또는 없음 |

#### 2.2.2 레퍼런스 포즈

레퍼런스 포즈(Reference Pose)는 T-포즈(팔을 수평축으로 편 자세)이며, 모든 조인트 이동 기술의 기준점이 된다. Body Geometry ID 1로 식별된다.

##### 좌표축 정의 (Table D.2)

| 좌표축 | 방향 | 방위 |
|--------|------|------|
| **x** | 몸의 횡단축 (수평) | 신체 오른쪽에서 왼쪽으로 |
| **y** | 몸의 종단축 (수직) | 아래에서 위로 |
| **z** | 몸의 전후축 | 뒤에서 앞으로 |

##### 조인트 위치 데이터 (Table D.3) - 주요 조인트

| From | To | x (m) | y (m) | z (m) |
|------|----|-------|-------|-------|
| `<origin>` | hips_JNT | 0.00000000 | 0.00000000 | 0.00000000 |
| hips_JNT | spine_JNT | 0.00000000 | 0.04130373 | -0.00008512 |
| spine_JNT | spine1_JNT | 0.00000000 | 0.10693992 | -0.00005568 |
| spine1_JNT | spine2_JNT | 0.00000000 | 0.10153212 | -0.00012624 |
| spine2_JNT | neck_JNT | 0.00000000 | 0.17065638 | 0.00263754 |
| neck_JNT | head_JNT | 0.00000000 | 0.08137577 | 0.00007754 |
| head_JNT | r_eye_LOC | -0.05100100 | 0.12306628 | 0.09664178 |
| head_JNT | l_eye_LOC | 0.05100100 | 0.12306628 | 0.09664178 |
| spine2_JNT | r_shoulder_JNT | -0.02886765 | 0.12539096 | -0.00534970 |
| r_shoulder_JNT | r_arm_JNT | -0.10265322 | -0.00000050 | -0.00000020 |
| r_arm_JNT | r_forearm_JNT | -0.25572863 | 0.00000000 | -0.00000009 |
| r_forearm_JNT | r_hand_JNT | -0.19807005 | -0.00346000 | -0.00000001 |
| spine2_JNT | l_shoulder_JNT | 0.02886657 | 0.12539132 | -0.00534974 |
| l_shoulder_JNT | l_arm_JNT | 0.10265323 | 0.00000035 | 0.00000019 |
| l_arm_JNT | l_forearm_JNT | 0.25572872 | 0.00000003 | 0.00000003 |
| l_forearm_JNT | l_hand_JNT | 0.19806792 | -0.00345714 | 0.00000008 |

##### 오른손 손가락 위치 데이터

| From | To | x (m) | y (m) | z (m) |
|------|----|-------|-------|-------|
| r_hand_JNT | r_handThumb1_JNT | -0.01817488 | -0.01260972 | 0.03617090 |
| r_handThumb1_JNT | r_handThumb2_JNT | -0.02639243 | -0.00023618 | -0.00053143 |
| r_handThumb2_JNT | r_handThumb3_JNT | -0.02698978 | -0.00823875 | 0.00000033 |
| r_hand_JNT | r_handIndex1_JNT | -0.08251890 | -0.00108337 | 0.03749100 |
| r_handIndex1_JNT | r_handIndex2_JNT | -0.03896140 | 0.00288500 | -0.00000463 |
| r_handIndex2_JNT | r_handIndex3_JNT | -0.02318387 | 0.00159236 | -0.00000487 |
| r_hand_JNT | r_handMiddle1_JNT | -0.09047189 | 0.00040404 | 0.01280809 |
| r_handMiddle1_JNT | r_handMiddle2_JNT | -0.03918013 | 0.00058125 | -0.00000245 |
| r_handMiddle2_JNT | r_handMiddle3_JNT | -0.02517173 | 0.00020933 | -0.00000344 |
| r_hand_JNT | r_handRing1_JNT | -0.08770376 | -0.00316066 | -0.01406740 |
| r_handRing1_JNT | r_handRing2_JNT | -0.03670816 | 0.00003664 | 0.00000012 |
| r_handRing2_JNT | r_handRing3_JNT | -0.02391655 | 0.00005686 | -0.00000005 |
| r_hand_JNT | r_handPinky1_JNT | -0.07380626 | -0.01009364 | -0.03361094 |
| r_handPinky1_JNT | r_handPinky2_JNT | -0.02923373 | 0.00065774 | -0.00000015 |
| r_handPinky2_JNT | r_handPinky3_JNT | -0.01903112 | -0.00013694 | 0.00000004 |

##### 왼손 손가락 위치 데이터

| From | To | x (m) | y (m) | z (m) |
|------|----|-------|-------|-------|
| l_hand_JNT | l_handThumb1_JNT | 0.01812944 | -0.01252033 | 0.03615281 |
| l_handThumb1_JNT | l_handThumb2_JNT | 0.02639235 | -0.00023623 | -0.00053106 |
| l_handThumb2_JNT | l_handThumb3_JNT | 0.02817296 | 0.00161941 | -0.00000019 |
| l_hand_JNT | l_handIndex1_JNT | 0.08246994 | -0.00097605 | 0.03748598 |
| l_handIndex1_JNT | l_handIndex2_JNT | 0.03896263 | 0.00286875 | -0.00000004 |
| l_handIndex2_JNT | l_handIndex3_JNT | 0.02318424 | 0.00158303 | -0.00000001 |
| l_hand_JNT | l_handMiddle1_JNT | 0.09042166 | 0.00054560 | 0.01280483 |
| l_handMiddle1_JNT | l_handMiddle2_JNT | 0.03918027 | 0.00055923 | -0.00000003 |
| l_handMiddle2_JNT | l_handMiddle3_JNT | 0.02517179 | 0.00019623 | -0.00000001 |
| l_hand_JNT | l_handRing1_JNT | 0.08765368 | -0.00298586 | -0.01407511 |
| l_handRing1_JNT | l_handRing2_JNT | 0.03670795 | 0.00003694 | 0.00000002 |
| l_handRing2_JNT | l_handRing3_JNT | 0.02391658 | 0.00005747 | 0.00000001 |
| l_hand_JNT | l_handPinky1_JNT | 0.07375719 | -0.00989721 | -0.03362722 |
| l_handPinky1_JNT | l_handPinky2_JNT | 0.02923453 | 0.00065764 | 0.00000007 |
| l_handPinky2_JNT | l_handPinky3_JNT | 0.01903052 | -0.00013621 | 0.00000002 |

#### 2.2.3 조인트 무브먼트

아바타 신체 애니메이션은 스켈레톤 조인트의 이동으로 수행된다.

##### 이동(Translation) 운동
- 부모 조인트 위치를 기준으로 한 상대적 위치 변경
- 부모 조인트의 좌표축 기준
- 대부분의 조인트에는 적용되지 않음 (Type-0 조인트인 hips_JNT에만 적용)

##### 회전(Rotation) 운동
- 조인트의 좌표축(x/y/z)의 변경으로 정의
- 회전된 축은 모든 하위 조인트에 적용됨
- `l_eye_LOC`와 `r_eye_LOC`의 회전은 각각 좌/우 안구 회전에 해당

##### 오일러 각(Euler Angles)

3개의 좌표축을 중심으로 한 회전 각도의 조합:
- **회전 순서**: z축(alpha) → x축(beta) → y축(gamma)
- **방향**: 반시계 방향이 양수, 시계 방향이 음수

##### 쿼터니언(Quaternion)

4개 요소로 구성된 수학적 표현:

```
(qw, qx, qy, qz) = (cos(theta/2), Xe * sin(theta/2), Ye * sin(theta/2), Ze * sin(theta/2))
```

- `theta`: 회전 각도
- `(Xe, Ye, Ze)`: 회전축 위의 단위 거리 위치
- 마지막 3개 요소(qx, qy, qz)로 회전 이동 정의 가능
- `qw`는 나머지 3개 요소로 계산 가능: `qw^2 + qx^2 + qy^2 + qz^2 = 1`
- `qw`는 항상 양수여야 함 (바이너리 인코딩에서 생략됨)

#### 2.2.4 무브먼트 제한 (조인트 타입)

##### 조인트 타입 분류 (Table D.4)

| 타입 | 이동 제한 | 회전 제한 | 해당 조인트 |
|------|----------|----------|-----------|
| **Type-0** | 이동 허용 (각 축 [-0.50m, 0.50m]) | 회전 자유 | hips_JNT (루트 조인트) |
| **Type-1** | 이동 없음 | 회전 자유 | spine, neck, head, shoulder, arm, forearm, hand, thumb1 조인트들 |
| **Type-2** | 이동 없음 | z축 360도 자유, x/y축 [-90, 90] 제한 | 손바닥 조인트 (엄지 제외) - Index1, Middle1, Ring1, Pinky1 |
| **Type-3** | 이동 없음 | z축만 회전 | 손가락 조인트 - Index2/3, Middle2/3, Ring2/3, Pinky2/3, Thumb2/3 |
| **Type-4** | 이동 없음 | z축 회전 없음, x/y축 [-90, 90] 제한 | r_eye_LOC, l_eye_LOC |

##### 조인트 순서 및 타입 (Table D.9) - SLMB 바이너리 인코딩 순서

| 순서 | 조인트 이름 | 타입 | 순서 | 조인트 이름 | 타입 |
|------|-----------|------|------|-----------|------|
| 0 | hips_JNT | 0 | 23 | r_handPinky1_JNT | 2 |
| 1 | spine_JNT | 1 | 24 | l_handIndex2_JNT | 3 |
| 2 | spine1_JNT | 1 | 25 | l_handIndex3_JNT | 3 |
| 3 | spine2_JNT | 1 | 26 | l_handMiddle2_JNT | 3 |
| 4 | neck_JNT | 1 | 27 | l_handMiddle3_JNT | 3 |
| 5 | head_JNT | 1 | 28 | l_handRing2_JNT | 3 |
| 6 | l_shoulder_JNT | 1 | 29 | l_handRing3_JNT | 3 |
| 7 | l_arm_JNT | 1 | 30 | l_handPinky2_JNT | 3 |
| 8 | l_forearm_JNT | 1 | 31 | l_handPinky3_JNT | 3 |
| 9 | l_hand_JNT | 1 | 32 | l_handThumb2_JNT | 3 |
| 10 | r_shoulder_JNT | 1 | 33 | l_handThumb3_JNT | 3 |
| 11 | r_arm_JNT | 1 | 34 | r_handIndex2_JNT | 3 |
| 12 | r_forearm_JNT | 1 | 35 | r_handIndex3_JNT | 3 |
| 13 | r_hand_JNT | 1 | 36 | r_handMiddle2_JNT | 3 |
| 14 | l_handThumb1_JNT | 1 | 37 | r_handMiddle3_JNT | 3 |
| 15 | r_handThumb1_JNT | 1 | 38 | r_handRing2_JNT | 3 |
| 16 | l_handIndex1_JNT | 2 | 39 | r_handRing3_JNT | 3 |
| 17 | l_handMiddle1_JNT | 2 | 40 | r_handPinky2_JNT | 3 |
| 18 | l_handRing1_JNT | 2 | 41 | r_handPinky3_JNT | 3 |
| 19 | l_handPinky1_JNT | 2 | 42 | r_handThumb2_JNT | 3 |
| 20 | r_handIndex1_JNT | 2 | 43 | r_handThumb3_JNT | 3 |
| 21 | r_handMiddle1_JNT | 2 | 44 | r_eye_LOC | 4 |
| 22 | r_handRing1_JNT | 2 | 45 | l_eye_LOC | 4 |

**타입별 조인트 수**:
- Type-0: 1개 (hips_JNT)
- Type-1: 15개 (spine~hand, thumb1 조인트들)
- Type-2: 8개 (손바닥 제1관절, 엄지 제외)
- Type-3: 20개 (손가락 제2/3관절, 엄지2/3 포함)
- Type-4: 2개 (눈 조인트)
- **합계: 46개**

##### Type-2, Type-3 조인트의 회전축 좌표 (Table D.5)

Type-2, Type-3 조인트의 회전축은 조인트 좌표축과 약간 다르며, 레퍼런스 포즈에서의 조인트 위치에 따라 정의된다.

**왼손 조인트 회전축:**

| 조인트 | 축 | X | Y | Z |
|--------|---|---|---|---|
| l_handThumb2/3_JNT | X | 0.99975759 | -0.00894864 | -0.02011682 |
| | Y | 0.00894864 | 0.99995996 | -0.00009002 |
| | Z | 0.02011682 | -0.00009002 | 0.99979763 |
| l_handIndex1/2/3_JNT | X | 0.99730041 | 0.07342955 | -0.00000095 |
| | Y | -0.07342955 | 0.99730041 | 0.00000004 |
| | Z | 0.00000095 | 0.00000004 | 1.00000000 |
| l_handMiddle1/2/3_JNT | X | 0.99989815 | 0.01427188 | -0.00000065 |
| | Y | -0.01427188 | 0.99989815 | 0.00000000 |
| | Z | 0.00000065 | 0.00000000 | 1.00000000 |
| l_handRing1/2/3_JNT | X | 0.99999949 | 0.00100632 | 0.00000062 |
| | Y | -0.00100632 | 0.99999949 | 0.00000000 |
| | Z | -0.00000062 | 0.00000000 | 1.00000000 |
| l_handPinky1/2/3_JNT | X | 0.99974707 | 0.02248970 | 0.00000248 |
| | Y | -0.02248970 | 0.99974707 | -0.00000003 |
| | Z | -0.00000248 | -0.00000003 | 1.00000000 |

**오른손 조인트 회전축:**

| 조인트 | 축 | X | Y | Z |
|--------|---|---|---|---|
| r_handThumb2/3_JNT | X | -0.99975732 | -0.00894659 | -0.02013100 |
| | Y | -0.00894659 | 0.99995997 | -0.00009006 |
| | Z | 0.02013100 | 0.00009006 | -0.99979735 |
| r_handIndex1/2/3_JNT | X | -0.99726970 | 0.07384535 | -0.00011862 |
| | Y | 0.07384535 | 0.99726971 | 0.00000439 |
| | Z | 0.00011862 | -0.00000439 | -0.99999999 |
| r_handMiddle1/2/3_JNT | X | -0.99988997 | 0.01483368 | -0.00006243 |
| | Y | 0.01483368 | 0.99988997 | 0.00000046 |
| | Z | 0.00006243 | -0.00000046 | -1.00000000 |
| r_handRing1/2/3_JNT | X | -0.99999950 | 0.00099809 | 0.00000332 |
| | Y | 0.00099809 | 0.99999950 | 0.00000000 |
| | Z | -0.00000332 | 0.00000000 | -1.00000000 |
| r_handPinky1/2/3_JNT | X | -0.99974698 | 0.02249369 | -0.00000500 |
| | Y | 0.02249369 | 0.99974698 | 0.00000006 |
| | Z | 0.00000500 | -0.00000006 | -1.00000000 |

---

### 2.3 페이스 무브먼트

#### 2.3.1 일반 사항

얼굴 애니메이션은 **모프 타겟(Morph Target)** 방식을 사용한다. 3D 메쉬에 하나 이상의 얼굴 변형(블렌드쉐이프)을 적용하여 표정을 생성한다. Face Geometry ID 1로 식별된다.

#### 2.3.2 페이스 메쉬 (Table D.6)

| 메쉬 이름 | 설명 |
|----------|------|
| head_GEO | 머리 |
| eyelash_GEO | 속눈썹 |
| mouth_GEO | 치아/혀 |
| eyebrow_l_GEO | 왼쪽 눈썹 |
| eyebrow_r_GEO | 오른쪽 눈썹 |
| iris_l_GEO | 왼쪽 안구 |
| iris_r_GEO | 오른쪽 안구 |

얼굴 지오메트리는 glTF 2.0 사양에 따른 파일로 정의된다:
- `SignLanguageMotionFace.glTF` (구조 정의)
- `SignLanguageMotionFace.bin` (바이너리 데이터)

#### 2.3.3 블렌드쉐이프 목록 (68개, Table D.7)

##### 눈 관련 (12개)

| 블렌드쉐이프 | 설명 | 영향 메쉬 |
|------------|------|----------|
| EyeBlink_Left | 왼쪽 눈 깜빡임 | head_GEO, eyelash_GEO |
| EyeBlink_Right | 오른쪽 눈 깜빡임 | head_GEO, eyelash_GEO |
| EyeSquint_Left | 왼쪽 눈 찡그림 | head_GEO, eyelash_GEO |
| EyeSquint_Right | 오른쪽 눈 찡그림 | head_GEO, eyelash_GEO |
| EyeDown_Left | 왼쪽 눈 아래로 | head_GEO, eyelash_GEO |
| EyeDown_Right | 오른쪽 눈 아래로 | head_GEO, eyelash_GEO |
| EyeIn_Left | 왼쪽 눈 안쪽으로 | head_GEO, eyelash_GEO |
| EyeIn_Right | 오른쪽 눈 안쪽으로 | head_GEO, eyelash_GEO |
| EyeOpen_Left | 왼쪽 눈 뜨기 | head_GEO, eyelash_GEO |
| EyeOpen_Right | 오른쪽 눈 뜨기 | head_GEO, eyelash_GEO |
| EyeOut_Left | 왼쪽 눈 바깥으로 | head_GEO, eyelash_GEO |
| EyeOut_Right | 오른쪽 눈 바깥으로 | head_GEO, eyelash_GEO |
| EyeUp_Left | 왼쪽 눈 위로 | head_GEO, eyelash_GEO |
| EyeUp_Right | 오른쪽 눈 위로 | head_GEO, eyelash_GEO |

##### 눈썹 관련 (5개)

| 블렌드쉐이프 | 설명 | 영향 메쉬 |
|------------|------|----------|
| BrowsDown_Left | 왼쪽 눈썹 내리기 | head_GEO, eyebrow_l_GEO, eyebrow_r_GEO |
| BrowsDown_Right | 오른쪽 눈썹 내리기 | head_GEO, eyebrow_l_GEO, eyebrow_r_GEO |
| BrowsUp_Center | 양쪽 눈썹 안쪽 올리기 | head_GEO, eyebrow_l_GEO, eyebrow_r_GEO |
| BrowsUp_Left | 왼쪽 눈썹 올리기 | head_GEO, eyebrow_l_GEO, eyebrow_r_GEO |
| BrowsUp_Right | 오른쪽 눈썹 올리기 | head_GEO, eyebrow_l_GEO, eyebrow_r_GEO |

##### 턱 관련 (5개)

| 블렌드쉐이프 | 설명 | 영향 메쉬 |
|------------|------|----------|
| JawFwd | 턱 앞으로 | head_GEO |
| JawLeft | 턱 왼쪽으로 | head_GEO, mouth_GEO |
| JawOpen | 입 벌리기 | head_GEO, mouth_GEO |
| JawChew | 씹기 | head_GEO |
| JawRight | 턱 오른쪽으로 | head_GEO, mouth_GEO |

##### 입 관련 (6개)

| 블렌드쉐이프 | 설명 | 영향 메쉬 |
|------------|------|----------|
| MouthLeft | 입 왼쪽 모서리 올리기 | head_GEO, mouth_GEO |
| MouthRight | 입 오른쪽 모서리 올리기 | head_GEO, mouth_GEO |
| MouthFrown_Left | 입 왼쪽 모서리 내리기 | head_GEO |
| MouthFrown_Right | 입 오른쪽 모서리 내리기 | head_GEO |
| MouthSmile_Left | 왼쪽 미소 | head_GEO |
| MouthSmile_Right | 오른쪽 미소 | head_GEO |
| MouthDimple_Left | 왼쪽 보조개 | head_GEO |
| MouthDimple_Right | 오른쪽 보조개 | head_GEO |

##### 입술 관련 (10개)

| 블렌드쉐이프 | 설명 | 영향 메쉬 |
|------------|------|----------|
| LipsStretch_Left | 왼쪽 입술 늘리기 | head_GEO |
| LipsStretch_Right | 오른쪽 입술 늘리기 | head_GEO |
| LipsUpperClose | 윗입술 닫고 좁히기 | head_GEO |
| LipsLowerClose | 아랫입술 닫고 좁히기 | head_GEO |
| LipsUpperUp | 윗입술 올리기 | head_GEO, mouth_GEO |
| LipsLowerDown | 아랫입술 내리기 | head_GEO, mouth_GEO |
| LipsUpperOpen | 윗입술 벌리기 | head_GEO |
| LipsLowerOpen | 아랫입술 벌리기 | head_GEO |
| LipsFunnel | 입을 "o" 모양으로 | head_GEO, mouth_GEO |
| LipsPucker | 입술 오므리기 | head_GEO |

##### 턱/볼 관련 (6개)

| 블렌드쉐이프 | 설명 | 영향 메쉬 |
|------------|------|----------|
| ChinLowerRaise | 아래턱 올리기 | head_GEO |
| ChinUpperRaise | 위턱 올리기 | head_GEO |
| Sneer | 이마 찡그린 분노 표현 | head_GEO, eyebrow_l_GEO, eyebrow_r_GEO |
| Puff | 볼 부풀리기 (양쪽) | head_GEO |
| CheekSquint_Left | 왼쪽 볼 찡그리기 | head_GEO, eyelash_GEO |
| CheekSquint_Right | 오른쪽 볼 찡그리기 | head_GEO, eyelash_GEO |

##### 감정 표현 관련 (13개)

| 블렌드쉐이프 | 설명 | 영향 메쉬 |
|------------|------|----------|
| HAPPY_48 | 초승달 모양 눈 | head_GEO, eyelash_GEO |
| HAPPY_49 | 입 양쪽 늘리기 | head_GEO |
| HAPPY_50 | 입 약간 벌리기 | head_GEO, mouth_GEO |
| HAPPY_51 | 입 벌리고 눈썹 올리기 | head_GEO, mouth_GEO, eyebrow_l/r_GEO |
| HAPPY_52 | 위/아래 치아 노출 | head_GEO, mouth_GEO |
| ANGRY_53 | 입 모서리 내리기 | head_GEO |
| ANGRY_54 | 눈꺼풀 내리기 | head_GEO, eyelash_GEO |
| ANGRY_55 | 분노의 찡그림 | head_GEO, eyebrow_l/r_GEO |
| DISGUST_56 | 입 왼쪽 모서리 내리기 | head_GEO |
| DISGUST_57 | 입 오른쪽 모서리 내리기 | head_GEO |
| SAD_58 | 입 모서리 내리고 눈썹 중앙 올리기 | head_GEO, eyelash_GEO, eyebrow_l/r_GEO |
| SURPRISE_59 | 눈 크게 뜨고 동공 수축 | head_GEO, eyelash_GEO, mouth_GEO, iris_l/r_GEO |
| SURPRISE_60 | 입 모서리 내리기 | head_GEO |

##### 기타 (7개)

| 블렌드쉐이프 | 설명 | 영향 메쉬 |
|------------|------|----------|
| Puff_Left | 왼쪽 볼 부풀리기 | head_GEO |
| Puff_Right | 오른쪽 볼 부풀리기 | head_GEO |
| Tongue_Out | 혀 내밀기 | head_GEO, mouth_GEO |
| Tongue_Up | 혀 위로 | head_GEO, mouth_GEO |
| Tongue_Down | 혀 아래로 | head_GEO, mouth_GEO |
| Tongue_Left | 혀 왼쪽으로 | head_GEO, mouth_GEO |
| Tongue_Right | 혀 오른쪽으로 | head_GEO, mouth_GEO |

#### 2.3.4 가중치(Weights) 시스템

- **범위**: 0 (변형 없음) ~ 1 (최대 변형)
- **적용 방식**: 각 블렌드쉐이프의 가중치에 따른 변위를 합산하여 최종 변형 계산
- **예시**: EyeBlink_Left 가중치 0.5 = 왼쪽 눈이 반쯤 감긴 상태
- **계산**: 각 메쉬 정점에 대해, 모든 블렌드쉐이프의 가중치별 변위를 합산

#### 2.3.5 페이스 지오메트리

glTF 2.0 사양 기반의 파일 구조:

```
glTF 파일 구조:
├── meshes[] (메쉬 배열)
│   ├── name: "head_GEO" 등
│   └── primitives
│       ├── attributes
│       │   ├── NORMAL (법선 벡터, 3-element float XYZ)
│       │   ├── POSITION (위치, 3-element float XYZ)
│       │   └── TANGENT (접선, 4-element float WXYZ)
│       ├── indices (삼각형 인덱스)
│       └── targets[] (블렌드쉐이프 배열)
│           ├── NORMAL (블렌드쉐이프 법선 변위)
│           ├── POSITION (블렌드쉐이프 위치 변위)
│           └── TANGENT (블렌드쉐이프 접선 변위)
├── accessors[] (접근자 배열 - bufferView 참조)
├── bufferViews[] (버퍼 뷰 - 오프셋/길이)
└── extras.targetNames[] (블렌드쉐이프 이름 목록)
```

블렌드쉐이프 적용 시 정점 속성값 = 원본 속성값 + SUM(각 블렌드쉐이프의 변위 * 가중치)

---

### 2.4 SLMB 바이너리 포맷

#### 2.4.1 개요

SLMB(Sign Language Motion Bundle)은 하나의 수어 문장을 해석하는 데 필요한 모든 모션 데이터를 포함하는 바이너리 파일이다.

- **파일 확장자**: `.slmb.xz`
- **압축**: LZMA 알고리즘, xz 포맷
- **구성**: BodyMotionBlock + FaceMotionBlock을 MotionBundle로 캡슐화 후 압축

```
인코딩 흐름:
  수어 문장 → 모션 데이터 생성 → BodyMotionBlock + FaceMotionBlock
       → MotionBundle 캡슐화 → LZMA(xz) 압축 → .slmb.xz 파일

디코딩 흐름:
  .slmb.xz 파일 → xz 압축 해제 → MotionBundle 파싱
       → BodyMotionBlock 추출 + FaceMotionBlock 추출
       → 아바타 애니메이션 엔진 입력 → 아바타 렌더링
```

#### 2.4.2 BodyMotionBlock 구조 (Table D.8)

```
BodyMotionBlock() {
    number_of_frames          // 32비트 uilsbf - 프레임 수
    frame_time                // 32비트 float (IEEE-754) - 프레임 간 시간(초)
    for (i=0; i<number_of_joints; i++) {    // 46개 조인트
        for (j=0; j<number_of_frames; j++) {
            if (joint_type == 0) {           // Type-0: hips_JNT만
                Tx                // 16비트 uilsbf - x축 이동
                Ty                // 16비트 uilsbf - y축 이동
                Tz                // 16비트 uilsbf - z축 이동
            }
            if (joint_type == 0 || joint_type == 1) {  // Type-0, Type-1
                Qx                // 16비트 silsbf - 쿼터니언 x
                Qy                // 16비트 silsbf - 쿼터니언 y
                Qz                // 16비트 silsbf - 쿼터니언 z
            } else if (joint_type == 2) {              // Type-2
                E2                // 32비트 uilsbf - 3개 오일러 각 패킹
            } else if (joint_type == 3) {              // Type-3
                E3                // 8비트 uilsbf - 1개 오일러 각
            } else if (joint_type == 4) {              // Type-4
                E4                // 16비트 uilsbf - 2개 오일러 각 패킹
            }
        }
    }
}
```

##### 각 타입별 데이터 인코딩 상세

**Type-0 (hips_JNT) - 프레임당 96비트 (이동) + 48비트 (회전) = 144비트**:

| 필드 | 비트 | 포맷 | 원본 범위 | 인코딩 범위 |
|------|------|------|----------|-----------|
| Tx | 16 | uilsbf | [-0.5m, 0.5m] | [0, 65535] |
| Ty | 16 | uilsbf | [-0.5m, 0.5m] | [0, 65535] |
| Tz | 16 | uilsbf | [-0.5m, 0.5m] | [0, 65535] |
| Qx | 16 | silsbf | [-1, 1] | [-32767, 32767] |
| Qy | 16 | silsbf | [-1, 1] | [-32767, 32767] |
| Qz | 16 | silsbf | [-1, 1] | [-32767, 32767] |

**Type-1 (spine, arm 등) - 프레임당 48비트**:

| 필드 | 비트 | 포맷 | 원본 범위 | 인코딩 범위 |
|------|------|------|----------|-----------|
| Qx | 16 | silsbf | [-1, 1] | [-32767, 32767] |
| Qy | 16 | silsbf | [-1, 1] | [-32767, 32767] |
| Qz | 16 | silsbf | [-1, 1] | [-32767, 32767] |

**Type-2 (손바닥 제1관절) - 프레임당 32비트**:

| 필드 | 비트 위치 | 원본 범위 | 인코딩 범위 | 설명 |
|------|----------|----------|-----------|------|
| E2x | 상위 10비트 | [-90, 90] | [0, 1023] | x 회전축 오일러 각 |
| E2y | 중간 10비트 | [-90, 90] | [0, 1023] | y 회전축 오일러 각 |
| E2z | 하위 12비트 | [-180, 180] | [0, 4095] | z 회전축 오일러 각 |

회전 순서: E2x(x축) -> E2y(y축) -> E2z(z축)

**Type-3 (손가락 관절) - 프레임당 8비트**:

| 필드 | 비트 | 원본 범위 | 인코딩 범위 | 설명 |
|------|------|----------|-----------|------|
| E3 | 8 | [-180, 180] | [0, 255] | z 회전축 오일러 각 |

**Type-4 (눈 관절) - 프레임당 16비트**:

| 필드 | 비트 위치 | 원본 범위 | 인코딩 범위 | 설명 |
|------|----------|----------|-----------|------|
| E4x | 상위 8비트 | [-90, 90] | [0, 255] | x 좌표축 오일러 각 |
| E4y | 하위 8비트 | [-90, 90] | [0, 255] | y 좌표축 오일러 각 |

회전 순서: E4y(y축) -> E4x(x축)

##### 프레임당 바디 데이터 크기 계산

| 타입 | 개수 | 프레임당 비트 | 소계 (비트) |
|------|------|-------------|-----------|
| Type-0 | 1 | 144 | 144 |
| Type-1 | 15 | 48 | 720 |
| Type-2 | 8 | 32 | 256 |
| Type-3 | 20 | 8 | 160 |
| Type-4 | 2 | 16 | 32 |
| **합계** | **46** | | **1,312비트 (164바이트)** |

헤더(number_of_frames + frame_time) = 64비트 (8바이트)

**총 BodyMotionBlock 크기** = 8 + (164 * number_of_frames) 바이트

#### 2.4.3 FaceMotionBlock 구조 (Table D.10)

```
FaceMotionBlock() {
    number_of_frames              // 16비트 uilsbf - 프레임 수
    for (i=0; i<number_of_frames; i++) {
        frame_time                // 32비트 float (IEEE-754) - 각 프레임 타임스탬프(초)
    }
    number_of_blend_shapes        // 16비트 uilsbf - 가중치!=0인 블렌드쉐이프 수
    for (j=0; j<number_of_blend_shapes; j++) {
        blend_shape_id            // 16비트 uilsbf - 블렌드쉐이프 식별 번호
        number_of_frame_ranges    // 16비트 uilsbf - 프레임 범위 수
        for (k=0; k<number_of_frame_ranges; k++) {
            frame_range_first     // 16비트 uilsbf - 범위 시작 프레임
            frame_range_size      // 16비트 uilsbf - 범위 내 프레임 수
        }
        for (k=0; k<number_of_frames_in_range; k++) {
            blend_shape_weight    // 16비트 uilsbf - 블렌드쉐이프 가중치
        }
    }
}
```

**핵심 설계 결정**: 대부분의 프레임에서 블렌드쉐이프 가중치가 0이므로, 가중치가 0이 아닌 프레임만 프레임 범위(frame range)로 기록하여 데이터 크기를 줄인다.

**가중치 정규화**: [0, 1] -> [0, 65535] (16비트)

**프레임 범위 예시**:
- 프레임 3,4,5,6,7,10,11,12,15,16에서 가중치가 0이 아닌 경우:
  - 프레임 범위: [3,7], [10,12], [15,16]
  - number_of_frame_ranges = 3
  - number_of_frames_in_ranges = 5 + 3 + 2 = 10

##### 블렌드쉐이프 ID 체계 (Table D.11)

블렌드쉐이프 ID는 메쉬별로 별도의 번호 공간을 사용한다:

| 메쉬 | ID 범위 시작 | 블렌드쉐이프 수 |
|------|-------------|--------------|
| head_GEO | 0 ~ 67 | 68개 |
| mouth_GEO | 1020 ~ 1067 | 16개 |
| eyelash_GEO | 2000 ~ 2059 | 18개 |
| eyebrow_l_GEO | 3014 ~ 3058 | 9개 |
| eyebrow_r_GEO | 4014 ~ 4058 | 9개 |
| iris_l_GEO | 5059 | 1개 |
| iris_r_GEO | 6059 | 1개 |

**head_GEO 블렌드쉐이프 ID (0~67)**:

| ID | 이름 | ID | 이름 | ID | 이름 |
|----|------|----|----- |----|----- |
| 0 | EyeBlink_Left | 23 | JawRight | 46 | CheekSquint_Left |
| 1 | EyeBlink_Right | 24 | MouthLeft | 47 | CheekSquint_Right |
| 2 | EyeSquint_Left | 25 | MouthRight | 48 | HAPPY_48 |
| 3 | EyeSquint_Right | 26 | MouthFrown_Left | 49 | HAPPY_49 |
| 4 | EyeDown_Left | 27 | MouthFrown_Right | 50 | HAPPY_50 |
| 5 | EyeDown_Right | 28 | MouthSmile_Left | 51 | HAPPY_51 |
| 6 | EyeIn_Left | 29 | MouthSmile_Right | 52 | HAPPY_52 |
| 7 | EyeIn_Right | 30 | MouthDimple_Left | 53 | ANGRY_53 |
| 8 | EyeOpen_Left | 31 | MouthDimple_Right | 54 | ANGRY_54 |
| 9 | EyeOpen_Right | 32 | LipsStretch_Left | 55 | ANGRY_55 |
| 10 | EyeOut_Left | 33 | LipsStretch_Right | 56 | DISGUST_56 |
| 11 | EyeOut_Right | 34 | LipsUpperClose | 57 | DISGUST_57 |
| 12 | EyeUp_Left | 35 | LipsLowerClose | 58 | SAD_58 |
| 13 | EyeUp_Right | 36 | LipsUpperUp | 59 | SURPRISE_59 |
| 14 | BrowsDown_Left | 37 | LipsLowerDown | 60 | SURPRISE_60 |
| 15 | BrowsDown_Right | 38 | LipsUpperOpen | 61 | Puff_Left |
| 16 | BrowsUp_Center | 39 | LipsLowerOpen | 62 | Puff_Right |
| 17 | BrowsUp_Left | 40 | LipsFunnel | 63 | Tongue_Out |
| 18 | BrowsUp_Right | 41 | LipsPucker | 64 | Tongue_Up |
| 19 | JawFwd | 42 | ChinLowerRaise | 65 | Tongue_Down |
| 20 | JawLeft | 43 | ChinUpperRaise | 66 | Tongue_Left |
| 21 | JawOpen | 44 | Sneer | 67 | Tongue_Right |
| 22 | JawChew | 45 | Puff | | |

**mouth_GEO 블렌드쉐이프 ID**:

| ID | 이름 |
|----|------|
| 1020 | JawLeft |
| 1021 | JawOpen |
| 1023 | JawRight |
| 1024 | Mouth_Left |
| 1025 | Mouth_Right |
| 1036 | LipsUpperUp |
| 1037 | LipsLowerDown |
| 1040 | LipsFunnel |
| 1042 | ChinLowerRaise |
| 1050 | HAPPY_50 |
| 1051 | HAPPY_51 |
| 1052 | HAPPY_52 |
| 1059 | SURPRISE_59 |
| 1063 | Tongue_Out |
| 1064 | Tongue_Up |
| 1065 | Tongue_Down |
| 1066 | Tongue_Left |
| 1067 | Tongue_Right |

**eyelash_GEO 블렌드쉐이프 ID**:

| ID | 이름 |
|----|------|
| 2000 | EyeBlink_Left |
| 2001 | EyeBlink_Right |
| 2002 | EyeSquint_Left |
| 2003 | EyeSquint_Right |
| 2004 | EyeDown_Left |
| 2005 | EyeDown_Right |
| 2006 | EyeIn_Left |
| 2007 | EyeIn_Right |
| 2008 | EyeOpen_Left |
| 2009 | EyeOpen_Right |
| 2010 | EyeOut_Left |
| 2011 | EyeOut_Right |
| 2012 | EyeUp_Left |
| 2013 | EyeUp_Right |
| 2046 | CheekSquint_Left |
| 2047 | CheekSquint_Right |
| 2048 | HAPPY_48 |
| 2054 | ANGRY_54 |
| 2058 | SAD_58 |
| 2059 | SURPRISE_59 |

**eyebrow_l_GEO 블렌드쉐이프 ID**: 3014(BrowsDown_Left), 3015(BrowsDown_Right), 3016(BrowsUp_Center), 3017(BrowsUp_Left), 3018(BrowsUp_Right), 3044(Sneer), 3051(HAPPY_51), 3055(ANGRY_55), 3058(SAD_58)

**eyebrow_r_GEO 블렌드쉐이프 ID**: 4014(BrowsDown_Left), 4015(BrowsDown_Right), 4016(BrowsUp_Center), 4017(BrowsUp_Left), 4018(BrowsUp_Right), 4044(Sneer), 4051(HAPPY_51), 4055(ANGRY_55), 4058(SAD_58)

**iris 블렌드쉐이프 ID**: iris_l_GEO = 5059(SURPRISE_59), iris_r_GEO = 6059(SURPRISE_59)

#### 2.4.4 MotionBundle 캡슐화 (Table D.13)

```
MotionBundle() {
    for (i=0; i<N; i++) {           // 각 요소
        header                       // 8비트 uilsbf
        for (j=0; j<key_length+1; j++) {
            key                      // 8비트 uilsbf (각 바이트)
        }
        if (payload_config == 0x1F) {
            payload_size             // 32비트 uilsbf
            for (j=0; j<payload_size; j++) {
                payload              // 8비트 uilsbf
            }
        } else {
            for (j=0; j<payload_config; j++) {
                payload              // 8비트 uilsbf
            }
        }
    }
}
```

**Header 바이트 구조**:
- 상위 3비트: key 파라미터 크기(바이트) - 1
- 하위 5비트: payload 크기 (31바이트 미만일 경우) 또는 0x1F (31바이트 이상일 경우)

##### 모션 요소 타입 (Table D.12)

| 요소 타입 | Key 바이트 | Payload |
|----------|-----------|---------|
| **Title** | {0x53, 0x4C, 0x4D, 0x42} = "SLMB" | 비어 있음 |
| **Body Motion** (Body Geometry ID 1) | {0x01, 0x01} | BodyMotionBlock (Table D.8) |
| **Face Motion** (Face Geometry ID 1) | {0x02, 0x01} | FaceMotionBlock (Table D.10) |

**규칙**:
- Title 요소가 번들의 첫 번째 요소여야 함
- Body motion 요소의 key 두 번째 바이트 = Body Geometry ID
- Face motion 요소의 key 두 번째 바이트 = Face Geometry ID
- 최소 1개의 body motion 요소와 1개의 face motion 요소를 포함해야 함
- 같은 키의 요소가 중복되면 안 됨

#### 2.4.5 압축 (D.5.4)

MotionBundle 데이터는 **LZMA(Lempel-Ziv-Markov chain) 알고리즘**으로 압축되며, **xz 파일 포맷** 사양에 따라 캡슐화된다. 결과물이 `.slmb.xz` 파일이 된다.

---

### 2.5 IMSC1 수어 모션 프로파일

#### 2.5.1 프로파일 정의

SLMB 파일 전송은 W3C IMSC1:2020 권고안에 기반하며, 수어 모션 전용 새 프로파일을 추가한다.

| 항목 | 값 |
|------|-----|
| **프로파일 식별자** | im1m |
| **프로파일 지정자** | `http://forumsbtvd.org.br/ns/ttml/profile/imsc1/signlanguagemotion` |
| **정의 문서** | ABNT NBR 25606 |
| **요청자** | SBTVD |

#### 2.5.2 SBTVD-SLM 확장

TTML 사양의 확장으로 `signlanguagemotion` 속성을 정의:

```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:sbtvd="http://forumsbtvd.org.br/schemas/sbtvd-slm"
    targetNamespace="http://forumsbtvd.org.br/schemas/sbtvd-slm"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    version="2024-03-25">
    <xs:import namespace="http://www.w3.org/XML/1998/namespace"
        schemaLocation="http://www.w3.org/2001/03/xml.xsd"/>
    <xs:attribute name="signlanguagemotion" type="xs:anyURI"/>
</xs:schema>
```

- `sbtvd:signlanguagemotion` 속성은 `div` 요소에 할당
- 값은 SLMB 파일 경로를 포함

#### 2.5.3 네임스페이스 (Table D.15)

| 이름 | 접두사 | 값 |
|------|--------|-----|
| SBTVD-SLM Extension | sbtvd | `http://forumsbtvd.org.br/schemas/sbtvd-slm` |
| IMSC1 SLM 프로파일 | (없음) | `http://forumsbtvd.org.br/ns/ttml/profile/imsc1/signlanguagemotion` |

#### 2.5.4 프로파일 제약사항

**핵심 제약**:
- 수어 모션 프로파일은 텍스트 프로파일과 호환 불가
- 동시 전송 시 별도 문서 인스턴스 필요
- `div` 요소에 `sbtvd:signlanguagemotion` 속성 지정 시:
  - div의 시간 길이 = SLMB 애니메이션 길이
  - `ittm:altText`로 대체 텍스트 제공 가능
  - SLMB 파일 경로 참조

**기능/확장 처분 (Table D.17 요약)**:

| 허용 | 금지 |
|------|------|
| #content (p, span, br 불가, div 제약 적용) | 텍스트 관련: #color, #fontFamily, #fontSize, #fontStyle, #fontWeight |
| #extent-region (px 또는 % 단위 필수) | 레이아웃 관련: #displayAlign, #textAlign, #padding, #lineHeight |
| #signlanguagemotion (SBTVD 확장) | 장식 관련: #textDecoration, #textOutline |
| #timing | 방향 관련: #direction, #unicodeBidi, #writingMode-vertical |
| | 구조 관련: #nested-div, #nested-span |
| | 이미지: #image (SMPTE-TT) |

---

### 2.6 ISOBMFF 캡슐화

- IMSC1 이미지 프로파일 가이드라인에 따름 (ISO/IEC 14496-30:2018, Section 5)
- SLMB 파일은 TTML 문서가 참조하는 리소스로 취급
- TTML 문서와 SLMB 파일 모두 ISO/IEC 14496-30:2018, 5.6의 가이드라인에 따라 포맷

서브샘플 구조:
```
Subtitle Sample
├── TTML Document
└── Subsamples
    └── SLMB File(s)
```

### 2.7 CMAF 트랙

CMAF(Common Media Application Format)에서의 수어 모션 트랙 선언:

| 항목 | 값 |
|------|-----|
| **기반 표준** | ISO/IEC 23000-19:2024 |
| **codecs 파라미터** (MIME box) | `im1m` |
| **content_type 필드** | `application/ttml+xml;codecs=im1m` |
| **미디어 타입 codecs** | `stpp.ttml.im1m` |
| **파일 브랜드** | `'im1m'` |
| **URN 형식** | `urn:mpeg:14496-30:subs:{숫자}` |

### 2.8 DASH 구현

DASH-IF IOP ATSC 3.0 V1.1 (2018-06), 5.5 기반으로 다음 변경 적용:

1. **프로파일 추가**: 수어 모션 프로파일을 프로파일 목록에 추가
2. **프로파일 메타데이터**: 수어 프로파일 사용 여부 표시 가능
3. **codecs 값**: `stpp.ttml.im1m`을 유효한 @codecs 값에 추가
4. **Property 디스크립터**:
   - @schemeIdURI: `http://dashif.org/guidelines/dash-atsc-closedcaption`
   - @value의 profile 파라미터: 0~2 범위 (2 = IMSC1 수어 모션 프로파일)

5. **아바타 호환성 시그널링**:

| 디스크립터 | @schemeIdURI | @value |
|-----------|-------------|--------|
| Body 지오메트리 | `tag:sbtvd.org.br,2024:SL_AvatarBodyGeometryIds` | 쉼표로 구분된 Body Geometry ID 목록 |
| Face 지오메트리 | `tag:sbtvd.org.br,2024:SL_AvatarFaceGeometryIds` | 쉼표로 구분된 Face Geometry ID 목록 |

- 미제공 시 기본값: Body Geometry ID 1, Face Geometry ID 1

**DASH 매니페스트 시그널링 예시**:
```xml
@mimeType="application/mp4"
@codecs="stpp.ttml.im1m"
```

---

## 3. 코드 구현 참조사항

### 3.1 SLMB 파서 구현 가이드

#### 디코딩 순서

```
1. xz 압축 해제 (LZMA)
2. MotionBundle 파싱
   a. Header 읽기 (key_length, payload_config 추출)
   b. Key 읽기 (요소 타입 식별)
   c. Payload 읽기 (크기에 따라 분기)
3. "SLMB" 타이틀 확인
4. Body Motion 요소 파싱 → BodyMotionBlock 추출
5. Face Motion 요소 파싱 → FaceMotionBlock 추출
```

#### BodyMotionBlock 디코딩

```
1. number_of_frames 읽기 (32비트)
2. frame_time 읽기 (32비트 float)
3. 조인트 순서대로(Table D.9) 각 프레임 데이터 읽기:
   - Type-0: Tx(16), Ty(16), Tz(16), Qx(16), Qy(16), Qz(16) = 12바이트
   - Type-1: Qx(16), Qy(16), Qz(16) = 6바이트
   - Type-2: E2(32) = 4바이트 → E2x(상위10), E2y(중간10), E2z(하위12) 추출
   - Type-3: E3(8) = 1바이트
   - Type-4: E4(16) = 2바이트 → E4x(상위8), E4y(하위8) 추출
4. 정규화 역변환 수행
```

#### FaceMotionBlock 디코딩

```
1. number_of_frames 읽기 (16비트)
2. frame_time 배열 읽기 (각 32비트 float)
3. number_of_blend_shapes 읽기 (16비트)
4. 각 블렌드쉐이프에 대해:
   a. blend_shape_id 읽기 (16비트) → Table D.11에서 식별
   b. number_of_frame_ranges 읽기 (16비트)
   c. 프레임 범위 읽기: frame_range_first(16), frame_range_size(16)
   d. 모든 범위 내 프레임의 blend_shape_weight 읽기 (각 16비트)
   e. 가중치 역정규화: weight = raw_value / 65535.0
```

### 3.2 정규화 역변환 공식

```
// Type-0 Translation 역정규화
position_m = (raw_value / 65535.0) * 1.0 - 0.5    // [0,65535] → [-0.5, 0.5]

// Type-0, Type-1 Quaternion 역정규화
quaternion_component = raw_value / 32767.0          // [-32767,32767] → [-1, 1]
qw = sqrt(1.0 - qx*qx - qy*qy - qz*qz)           // qw는 항상 양수

// Type-2 Euler 역정규화
E2x_deg = (E2x_raw / 1023.0) * 180.0 - 90.0        // [0,1023] → [-90, 90]
E2y_deg = (E2y_raw / 1023.0) * 180.0 - 90.0        // [0,1023] → [-90, 90]
E2z_deg = (E2z_raw / 4095.0) * 360.0 - 180.0       // [0,4095] → [-180, 180]

// Type-3 Euler 역정규화
E3_deg = (E3_raw / 255.0) * 360.0 - 180.0          // [0,255] → [-180, 180]

// Type-4 Euler 역정규화
E4x_deg = (E4x_raw / 255.0) * 180.0 - 90.0         // [0,255] → [-90, 90]
E4y_deg = (E4y_raw / 255.0) * 180.0 - 90.0         // [0,255] → [-90, 90]

// Face 블렌드쉐이프 가중치 역정규화
weight = raw_value / 65535.0                         // [0,65535] → [0, 1]
```

### 3.3 아바타 렌더링 파이프라인

```
1. 스켈레톤 초기화
   - Table D.3의 레퍼런스 포즈 좌표로 46개 조인트 배치
   - 조인트 트리 구조 구축 (Table D.1)

2. 페이스 메쉬 초기화
   - glTF 파일에서 7개 메쉬 로드
   - 블렌드쉐이프 데이터 로드

3. 프레임별 업데이트 루프:
   a. BodyMotionBlock에서 현재 프레임 데이터 추출
   b. 루트 조인트(hips_JNT) 이동 적용
   c. 조인트 트리를 루트부터 순회하며 회전 적용:
      - Type-0/1: 쿼터니언 회전 적용
      - Type-2: 커스텀 회전축(Table D.5) 기반 오일러 회전 (x→y→z 순서)
      - Type-3: 커스텀 회전축(Table D.5) 기반 z축 오일러 회전
      - Type-4: 좌표축 기반 오일러 회전 (y→x 순서)
   d. 스킨 메쉬 업데이트 (스켈레톤에 따라)
   e. FaceMotionBlock에서 현재 프레임 블렌드쉐이프 가중치 추출
   f. 각 메쉬 정점에 블렌드쉐이프 변형 적용
   g. 렌더링
```

### 3.4 필수 수학 함수

#### 쿼터니언 연산

```
// 쿼터니언 정규화
normalize(q) = q / |q|

// 쿼터니언에서 qw 복원
qw = sqrt(max(0, 1.0 - qx*qx - qy*qy - qz*qz))

// 쿼터니언 곱 (회전 합성)
q1 * q2 = (
    q1.w*q2.w - q1.x*q2.x - q1.y*q2.y - q1.z*q2.z,
    q1.w*q2.x + q1.x*q2.w + q1.y*q2.z - q1.z*q2.y,
    q1.w*q2.y - q1.x*q2.z + q1.y*q2.w + q1.z*q2.x,
    q1.w*q2.z + q1.x*q2.y - q1.y*q2.x + q1.z*q2.w
)

// 쿼터니언 → 회전 행렬
mat3x3 from_quaternion(qw, qx, qy, qz):
    return [
        [1-2(qy^2+qz^2),  2(qx*qy-qz*qw),  2(qx*qz+qy*qw)],
        [2(qx*qy+qz*qw),  1-2(qx^2+qz^2),  2(qy*qz-qx*qw)],
        [2(qx*qz-qy*qw),  2(qy*qz+qx*qw),  1-2(qx^2+qy^2)]
    ]
```

#### 오일러 각 → 회전 행렬 (Type-2 커스텀 축)

```
// Type-2 조인트의 회전 적용 (커스텀 축 기반)
// 1. Table D.5의 회전축 행렬 M을 사용하여 좌표축 변환
// 2. 변환된 축 기준으로 Rx(E2x) * Ry(E2y) * Rz(E2z) 적용
// 3. 역변환으로 원래 좌표계로 복원

// 실제 회전 행렬:
R_type2 = M * Rx(E2x) * Ry(E2y) * Rz(E2z) * M^(-1)

// 여기서 M은 Table D.5의 3x3 회전축 행렬
// Rx, Ry, Rz는 각 축 중심의 기본 회전 행렬
```

#### E2 비트 추출 (32비트 → 3개 각도)

```
// E2 (32비트) 비트 필드 추출
E2x_raw = (E2 >> 22) & 0x3FF    // 상위 10비트
E2y_raw = (E2 >> 12) & 0x3FF    // 중간 10비트
E2z_raw = E2 & 0xFFF            // 하위 12비트
```

#### E4 비트 추출 (16비트 → 2개 각도)

```
// E4 (16비트) 비트 필드 추출
E4x_raw = (E4 >> 8) & 0xFF     // 상위 8비트
E4y_raw = E4 & 0xFF            // 하위 8비트
```

---

## 부록: 바이트 오더 참고

문서에서 사용하는 데이터 포맷 약어:
- **uilsbf**: unsigned integer, least significant bit first (리틀 엔디안 비트 순서)
- **silsbf**: signed integer, least significant bit first
- **float (IEEE-754)**: 32비트 단정밀도 부동소수점
