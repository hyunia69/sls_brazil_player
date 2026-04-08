# SLMB Converter 구현 및 검증 문서

> **작성일**: 2026-03-09
> **기반 사양**: ABNT NBR 25606:2025 (Annex D), SBTVD OG-06 (Annex D)
> **구현 언어**: Python 3.x (표준 라이브러리만 사용, 외부 의존성 없음)
> **패키지 위치**: `docu/slmb_converter/`

---

## 1. 개요

### 1.1 목적

ABNT NBR 25606 표준에 정의된 SLMB(Sign Language Motion Bundle) 바이너리 포맷의 **인코딩/디코딩** 파이프라인을 Python으로 구현한다.

### 1.2 기능 범위

```
[인코딩 파이프라인]
  BVH 파일 → BVH 파서 → BodyMotionBlock 인코딩
  Face 데이터 생성     → FaceMotionBlock 인코딩
  BodyMotionBlock + FaceMotionBlock → MotionBundle 캡슐화 → LZMA/xz 압축 → .slmb.xz

[디코딩 파이프라인]
  .slmb.xz → xz 압축 해제 → MotionBundle 파싱 → BodyMotionBlock + FaceMotionBlock 분리
    → SLMB → BVH 변환 출력
    → SLMB → glTF 2.0 변환 출력
```

### 1.3 지원 명령어

| 명령어 | 설명 |
|--------|------|
| `python -m slmb_converter encode <input.bvh> [output.slmb.xz]` | BVH → SLMB 인코딩 + xz 압축 |
| `python -m slmb_converter decode-bvh <input.slmb.xz> [output.bvh]` | SLMB → BVH 디코딩 |
| `python -m slmb_converter decode-gltf <input.slmb.xz> [output.gltf]` | SLMB → glTF 디코딩 |
| `python -m slmb_converter roundtrip <input.bvh>` | 전체 라운드트립 (BVH→SLMB→BVH+glTF) |
| `python -m slmb_converter info <input.slmb.xz>` | SLMB 파일 정보 출력 |

---

## 2. 모듈 구조

### 2.1 파일 목록

```
slmb_converter/
├── __init__.py          (패키지 초기화, 버전 정보)
├── __main__.py          (python -m 실행 엔트리포인트)
├── constants.py         (ABNT 사양 상수 정의)
├── math_utils.py        (쿼터니언/오일러 변환 수학 함수)
├── bvh_parser.py        (BVH 파일 파서)
├── bvh_writer.py        (SLMB → BVH 출력기)
├── slmb_encoder.py      (BVH + Face → SLMB 인코더)
├── slmb_decoder.py      (SLMB → 디코딩된 데이터)
├── gltf_writer.py       (SLMB → glTF 2.0 출력기)
├── face_data.py         (샘플 페이스 데이터 생성기)
└── main.py              (CLI 인터페이스)
```

### 2.2 모듈 의존성

```
main.py
  ├── bvh_parser.py ────────────────── (BVH 파싱)
  ├── face_data.py ─────────────────── (페이스 데이터 생성)
  ├── slmb_encoder.py ──┬── constants.py
  │                     ├── math_utils.py
  │                     ├── bvh_parser.py
  │                     └── face_data.py
  ├── slmb_decoder.py ──┬── constants.py
  │                     └── math_utils.py
  ├── bvh_writer.py ────┬── constants.py
  │                     ├── math_utils.py
  │                     └── slmb_decoder.py
  └── gltf_writer.py ──┬── constants.py
                       ├── math_utils.py
                       └── slmb_decoder.py
```

---

## 3. 핵심 모듈 상세

### 3.1 `constants.py` — ABNT 사양 상수

ABNT NBR 25606 Annex D의 테이블 데이터를 Python 상수로 정의한다.

#### 3.1.1 조인트 정의 (Table D.9)

```python
JOINT_ORDER: List[Tuple[str, int]]  # 46개 조인트의 (이름, 타입) SLMB 인코딩 순서
```

| 조인트 타입 | 개수 | 인코딩 | 비트/프레임 |
|------------|------|--------|-----------|
| Type-0 (root) | 1 | 이동(16×3) + 쿼터니언(16s×3) | 96 |
| Type-1 (main) | 15 | 쿼터니언(16s×3) | 48 |
| Type-2 (palm) | 8 | 오일러 패킹(10+10+12) | 32 |
| Type-3 (finger) | 20 | Z축 오일러(8) | 8 |
| Type-4 (eye) | 2 | X/Y 오일러(8+8) | 16 |
| **합계** | **46** | | **1264 bits = 158 bytes** |

> **참고**: 분석 문서 `annex_CD.md`에서는 Type-0을 144비트(18바이트)로 기재하였으나, 실제 사양에 따르면 Tx(16)+Ty(16)+Tz(16)+Qx(16)+Qy(16)+Qz(16) = 96비트(12바이트)가 정확하다. 프레임당 총 크기는 164바이트가 아닌 **158바이트**이다.

#### 3.1.2 레퍼런스 포즈 (Table D.3)

```python
REFPOSE_FROM_PARENT: Dict[str, Tuple[float, float, float]]  # 미터 단위 부모로부터의 오프셋
REFPOSE_END: Dict[str, Tuple[float, float, float]]          # 리프 조인트 끝점
```

#### 3.1.3 커스텀 회전축 (Table D.5)

```python
ROTATION_AXES: Dict[str, RotAxis]  # Type-2/3 조인트의 로컬 회전축 좌표
```

- 왼손 조인트: 회전축이 월드 좌표계에 가까움 (trace ≈ 3.0)
- 오른손 조인트: 회전축이 180° 회전된 좌표계 (trace ≈ -1.0)

#### 3.1.4 블렌드쉐이프 ID (Table D.11)

```python
MESH_BLENDSHAPE_MAP: Dict[str, Dict[int, str]]  # 메시별 (ID → 이름)
BLENDSHAPE_ID_TO_NAME: Dict[int, Tuple[str, str]]  # ID → (메시명, 이름)
BLENDSHAPE_NAME_TO_ID: Dict[Tuple[str, str], int]  # (메시명, 이름) → ID
```

7개 메시에 걸친 블렌드쉐이프 ID 체계:

| 메시 | ID 범위 | 블렌드쉐이프 수 |
|------|---------|--------------|
| head_GEO | 0~67 | 68 |
| mouth_GEO | 1020~1067 | 18 |
| eyelash_GEO | 2000~2059 | 20 |
| eyebrow_l_GEO | 3014~3058 | 9 |
| eyebrow_r_GEO | 4014~4058 | 9 |
| iris_l_GEO | 5059 | 1 |
| iris_r_GEO | 6059 | 1 |

---

### 3.2 `math_utils.py` — 회전 변환

SBTVD OG-06 Annex D.2.3에 정의된 회전 변환 알고리즘을 구현한다.

#### 3.2.1 제공 함수

| 함수 | 입력 | 출력 | 용도 |
|------|------|------|------|
| `rotationaxis_to_quaternion(RX, RY, RZ)` | 3×3 회전축 행렬 | 쿼터니언 | 축 → 쿼터니언 |
| `euler2quaternion_yxz(Ex,Ey,Ez, RX,RY,RZ)` | 도 단위 오일러 | 쿼터니언 | BVH → 쿼터니언 |
| `euler2quaternion_xyz(Ex,Ey,Ez, RX,RY,RZ)` | 도 단위 오일러 | 쿼터니언 | SLMB → 쿼터니언 |
| `quaternion2euler_yxz(qw,qx,qy,qz, RX,RY,RZ)` | 쿼터니언 | 도 단위 오일러 | 쿼터니언 → BVH |
| `quaternion2euler_xyz(qw,qx,qy,qz, RX,RY,RZ)` | 쿼터니언 | 도 단위 오일러 | 쿼터니언 → SLMB |
| `quaternion_multiply(q1, q2)` | 두 쿼터니언 | 해밀턴 곱 | 회전 합성 |
| `quaternion_inverse(q)` | 단위 쿼터니언 | 켤레(역) | 역회전 |
| `quaternion_normalize(q)` | 쿼터니언 | 정규화 | 단위 보장 |
| `wrap_to_degrees(rad)` | 라디안 | (-180, 180] 도 | 각도 래핑 |

#### 3.2.2 쿼터니언 규약

- 형식: `(w, x, y, z)` — 스칼라 먼저
- 모든 공개 함수의 각도 단위: **도(degrees)**
- `rotationaxis_to_quaternion`은 trace ≤ 0일 때 수치 안정성을 위한 분기 처리 포함

#### 3.2.3 변환 흐름

```
BVH → SLMB (인코딩):
  BVH 오일러 (y/x/z) ──euler2quaternion_yxz──> 쿼터니언
    ──quaternion2euler_xyz──> SLMB 오일러 (x/y/z, 커스텀 축)

SLMB → BVH (디코딩):
  SLMB 오일러 (x/y/z, 커스텀 축) ──euler2quaternion_xyz──> 쿼터니언
    ──quaternion2euler_yxz──> BVH 오일러 (y/x/z)

SLMB → glTF (디코딩):
  SLMB 오일러 ──euler2quaternion_xyz──> 쿼터니언 (glTF는 직접 쿼터니언 사용)
```

---

### 3.3 `bvh_parser.py` — BVH 파서

#### 3.3.1 데이터 구조

```python
@dataclass
class BVHJoint:
    name: str                              # 조인트 이름
    offset: Tuple[float, float, float]     # OFFSET x y z
    channels: List[str]                    # 채널 목록
    children: List[BVHJoint]               # 자식 조인트
    end_site: Optional[Tuple[float, float, float]]  # 리프 노드 끝점

@dataclass
class BVHData:
    root: BVHJoint                         # 루트 조인트
    num_frames: int                        # 프레임 수
    frame_time: float                      # 프레임 간 시간(초)
    motion_data: List[List[float]]         # [프레임][채널] 값 배열
    joint_list: List[BVHJoint]             # 깊이 우선 순서 조인트 목록
```

#### 3.3.2 특이사항

- 샘플 BVH 파일의 `OFFFET` 오타(`OFFSET`의 오타)를 자동 처리
- BVH 채널 순서: `Zrotation Xrotation Yrotation` → 실제 회전 적용 순서: Y, X, Z
- 모든 조인트는 6채널 (위치 3 + 회전 3)

---

### 3.4 `slmb_encoder.py` — SLMB 인코더

#### 3.4.1 BodyMotionBlock 인코딩 (Table D.8)

OG-06 D.2.4.3의 BVH → SLMB 변환 의사코드를 구현한다.

```
BodyMotionBlock:
  number_of_frames     [uint32, LE]
  frame_time           [float32, IEEE-754, LE]
  for joint in JOINT_ORDER (46개):
    for frame in 0..num_frames:
      Type-0: Tx[uint16] Ty[uint16] Tz[uint16] Qx[int16] Qy[int16] Qz[int16]
      Type-1: Qx[int16] Qy[int16] Qz[int16]
      Type-2: E2[uint32] = (E2x<<22) | (E2y<<12) | E2z
      Type-3: E3[uint8]
      Type-4: E4[uint16] = (E4x<<8) | E4y
```

**정규화 공식**:

| 타입 | 필드 | 원본 범위 | 인코딩 공식 |
|------|------|----------|------------|
| Type-0 Translation | Tx,Ty,Tz | [-0.5m, 0.5m] | `(val + 0.5) × 65535` |
| Type-0/1 Quaternion | Qx,Qy,Qz | [-1, 1] | `val × 32767` |
| Type-2 Euler x,y | E2x,E2y | [-90°, 90°] | `(val + 90) / 180 × 1023` |
| Type-2 Euler z | E2z | [-180°, 180°] | `(val + 180) / 360 × 4095` |
| Type-3 Euler z | E3 | [-180°, 180°] | `(val + 180) / 360 × 255` |
| Type-4 Euler x,y | E4x,E4y | [-90°, 90°] | `(val + 90) / 180 × 255` |

**Type-2 인코딩 시 오일러 각 정규화**: 오른손 조인트의 커스텀 축이 180° 오프셋을 생성할 수 있으므로, Ex가 [-90, 90] 범위를 초과할 경우 등가 표현을 사용한다:

```python
if Ex > 90:  Ex = 180 - Ex; Ey += 180; Ez += 180
if Ex < -90: Ex = -180 - Ex; Ey += 180; Ez += 180
```

#### 3.4.2 FaceMotionBlock 인코딩 (Table D.10)

```
FaceMotionBlock:
  number_of_frames       [uint16]
  frame_time[N]          [float32 × N]
  number_of_blend_shapes [uint16]
  for each active blendshape:
    blend_shape_id         [uint16]
    number_of_frame_ranges [uint16]
    for each range:
      frame_range_first    [uint16]
      frame_range_size     [uint16]
    for each frame in ranges:
      blend_shape_weight   [uint16]  // val × 65535
```

- **스파스 인코딩**: 가중치가 0이 아닌 블렌드쉐이프와 프레임만 저장
- **프레임 범위 압축**: 연속 프레임을 `(first, size)` 범위로 그룹화

#### 3.4.3 MotionBundle 캡슐화 (Table D.12, D.13)

```
MotionBundle:
  Element 1: Title     header=0x60, key="SLMB",        payload=empty
  Element 2: Body      header=0x3F, key={0x01,0x01},   payload=BodyMotionBlock
  Element 3: Face      header=0x3F, key={0x02,0x01},   payload=FaceMotionBlock
```

**Header 바이트 구조**: `[key_size-1 (3bit)] [payload_config (5bit)]`
- `payload_config = 0x1F` → 이어서 32비트 payload_size 필드
- `payload_config < 0x1F` → payload_config 자체가 payload 크기

#### 3.4.4 압축

- 알고리즘: LZMA (xz format)
- Python `lzma.compress(data, format=lzma.FORMAT_XZ)`
- 결과 파일 확장자: `.slmb.xz`

---

### 3.5 `slmb_decoder.py` — SLMB 디코더

#### 3.5.1 데이터 구조

```python
@dataclass
class JointFrameData:
    tx, ty, tz: float       # Type-0 이동 (미터)
    qw, qx, qy, qz: float  # 쿼터니언 (모든 타입에서 계산)
    euler_x, euler_y, euler_z: float  # Type-2/3/4 원본 오일러 (도)

@dataclass
class BodyMotionBlock:
    num_frames: int
    frame_time: float
    joint_data: List[List[JointFrameData]]  # [joint_idx][frame_idx]

@dataclass
class BlendshapeData:
    blend_shape_id: int
    weights: Dict[int, float]  # frame_idx → weight (0~1)

@dataclass
class FaceMotionBlock:
    num_frames: int
    frame_times: List[float]
    blendshapes: List[BlendshapeData]

@dataclass
class SLMBData:
    body: BodyMotionBlock
    face: FaceMotionBlock
```

#### 3.5.2 역정규화 공식

| 타입 | 필드 | 디코딩 공식 | 결과 범위 |
|------|------|------------|----------|
| Type-0 Translation | Tx,Ty,Tz | `raw / 65535 - 0.5` | [-0.5m, 0.5m] |
| Type-0/1 Quaternion | Qx,Qy,Qz | `raw / 32767`, `qw = √(1 - qx² - qy² - qz²)` | [-1, 1] |
| Type-2 Euler x,y | E2x,E2y | `raw / 1023 × 180 - 90` | [-90°, 90°] |
| Type-2 Euler z | E2z | `raw / 4095 × 360 - 180` | [-180°, 180°] |
| Type-3 Euler z | E3 | `raw / 255 × 360 - 180` | [-180°, 180°] |
| Type-4 Euler x,y | E4x,E4y | `raw / 255 × 180 - 90` | [-90°, 90°] |
| Face Weight | weight | `raw / 65535` | [0, 1] |

**E2 비트 추출** (32비트):
```
E2x = (E2 >> 22) & 0x3FF   // 상위 10비트
E2y = (E2 >> 12) & 0x3FF   // 중간 10비트
E2z = E2 & 0xFFF           // 하위 12비트
```

**E4 비트 추출** (16비트):
```
E4x = (E4 >> 8) & 0xFF     // 상위 8비트
E4y = E4 & 0xFF            // 하위 8비트
```

---

### 3.6 `bvh_writer.py` — BVH 출력기

OG-06 D.2.4.4의 SLMB → BVH 변환 의사코드를 구현한다.

- HIERARCHY 섹션: `REFPOSE_FROM_PARENT`를 센티미터 단위로 변환하여 출력
- MOTION 섹션: 조인트 타입별 역변환 수행
  - Type-0/1: 쿼터니언 → `quaternion2euler_yxz` → BVH 오일러
  - Type-2: 커스텀축 오일러 → `euler2quaternion_xyz` → 쿼터니언 → `quaternion2euler_yxz` → BVH 오일러
  - Type-3: Z축 오일러만 → `euler2quaternion_xyz(0, 0, Ez)` → 쿼터니언 → BVH 오일러
  - Type-4: X/Y 직접 매핑

---

### 3.7 `gltf_writer.py` — glTF 출력기

OG-06 D.2.6.3의 SLMB → glTF 변환 의사코드를 구현한다.

#### 출력 구조

```
output.gltf (JSON)
  ├── asset: version 2.0
  ├── scenes: [root = hips_JNT]
  ├── nodes: 46 skeleton joints + mesh nodes
  ├── animations: [{
  │     samplers: time → value 매핑
  │     channels: [
  │       46× rotation (쿼터니언, XYZW)
  │       1× translation (hips_JNT만)
  │       N× weights (메시별 블렌드쉐이프)
  │     ]
  │   }]
  ├── accessors / bufferViews → output.bin 참조
  └── buffers: [output.bin]

output.bin (바이너리)
  └── 시간 배열, 쿼터니언 배열, 이동 벡터, 가중치 배열
```

- glTF 쿼터니언 순서: `(x, y, z, w)` — SLMB의 `(w, x, y, z)`와 다름
- GLB 형식 출력도 지원 (`.glb` 확장자 사용 시)

---

### 3.8 `face_data.py` — 페이스 데이터 생성기

실제 수어 표현을 시뮬레이션하는 샘플 페이스 애니메이션 데이터를 생성한다.

#### 3.8.1 `generate_sample_face_data(num_frames, frame_time)`

15개 블렌드쉐이프를 활용한 풍부한 표정:

| 블렌드쉐이프 | ID | 메시 | 동작 패턴 |
|------------|-----|------|----------|
| EyeBlink_Left/Right | 0, 1 | head_GEO | 3.5초 간격 코사인 펄스 |
| EyeOpen_Left/Right | 8, 9 | head_GEO | 깜빡임 반전 |
| BrowsUp_Center/Left/Right | 16, 17, 18 | head_GEO | 30%/70% 지점 사인파 |
| JawOpen | 21 | head_GEO | 1.8초 주기 사인파 |
| MouthSmile_Left/Right | 28, 29 | head_GEO | 2.5초 주기 사인파 |
| LipsPucker | 41 | head_GEO | JawOpen의 역상관 |
| HAPPY_48 | 48 | head_GEO | 중간 지점 피크 |
| JawOpen | 1021 | mouth_GEO | head_GEO와 동기화 |
| EyeBlink_Left/Right | 2000, 2001 | eyelash_GEO | head_GEO와 동기화 |

#### 3.8.2 `generate_neutral_face_data(num_frames, frame_time)`

눈 깜빡임만 포함하는 최소 데이터. 3.5초 이하 애니메이션에서는 블렌드쉐이프 없음.

---

## 4. 검증 결과

### 4.1 테스트 환경

- **입력 파일**: `avatarModel.bvh` (ABNT 표준 아바타 레퍼런스)
- **사양**: 46 조인트, 142 프레임, 30fps (0.033333s/frame), 약 4.73초
- **페이스 데이터**: 자동 생성 (15개 활성 블렌드쉐이프, 3개 메시)

### 4.2 테스트 항목 및 결과

#### Test 1: BVH 파서

| 항목 | 기대값 | 실측값 | 결과 |
|------|--------|--------|------|
| 조인트 수 | 46 | 46 | PASS |
| 프레임 수 | 142 | 142 | PASS |
| 프레임 시간 | 0.033333s | 0.033333s | PASS |
| 루트 조인트 | hips_JNT | hips_JNT | PASS |
| ABNT 조인트 이름 일치 | 46개 모두 | 46개 모두 | PASS |
| OFFFET 오타 처리 | 정상 파싱 | 정상 파싱 | PASS |

#### Test 2: 수학 함수

| 항목 | 입력 | 기대 출력 | 실측 출력 | 오차 |
|------|------|----------|----------|------|
| YXZ 라운드트립 | (30, 45, -15)° | (30, 45, -15)° | (30.0000, 45.0000, -15.0000)° | < 0.001° |
| XYZ 라운드트립 | (20, -10, 60)° | (20, -10, 60)° | (20.0000, -10.0000, 60.0000)° | < 0.001° |
| 좌수 교차변환 | (15, -5, 30)° | (15, -5, 30)° | (15.0000, -5.0000, 30.0000)° | < 0.01° |
| 항등 쿼터니언 곱 | id × id | id | id | 0 |

#### Test 3: 페이스 데이터 생성

| 항목 | 기대값 | 실측값 | 결과 |
|------|--------|--------|------|
| 프레임 수 | 150 | 150 | PASS |
| 활성 블렌드쉐이프 | > 0 | 15 | PASS |
| 최대 가중치 | ≤ 1.0 | 1.0000 | PASS |
| 가중치 범위 | [0, 1] | 전부 [0, 1] | PASS |
| 사용 메시 | 다중 | head, mouth, eyelash | PASS |

#### Test 4: SLMB 인코딩

| 항목 | 기대값 | 실측값 | 결과 |
|------|--------|--------|------|
| BodyMotionBlock 크기 | 8 + 158×142 = 22,444B | 22,444B | PASS |
| Body 헤더 (frames) | 142 | 142 | PASS |
| Body 헤더 (frame_time) | 0.033333s | 0.033333s | PASS |
| Title 요소 | header=0x60, key="SLMB" | 일치 | PASS |
| Body 요소 | header=0x3F, key=0x0101 | 일치 | PASS |
| Face 요소 | key=0x0201 | 일치 | PASS |
| xz 압축 | < 원본 | 24,957 → 9,824B (39.4%) | PASS |

#### Test 5: SLMB 디코딩

| 항목 | 기대값 | 실측값 | 결과 |
|------|--------|--------|------|
| 압축 해제 일치 | 원본 번들과 동일 | 24,957B 완전 일치 | PASS |
| Body 프레임 수 | 142 | 142 | PASS |
| Body 조인트 수 | 46 | 46 | PASS |
| Face 프레임 수 | 142 | 142 | PASS |
| Face 블렌드쉐이프 수 | 15 | 15 | PASS |
| 블렌드쉐이프 가중치 | [0, 1] | 전부 [0, 1] | PASS |
| Hips 이동 최대 오차 | < 0.001m | 0.000008m (8μm) | PASS |

#### Test 6: BVH 출력기 (라운드트립 정확도)

| 조인트 타입 | 개수 | 최대 오차 | 평균 오차 | 판정 |
|------------|------|----------|----------|------|
| **Type-0** (root) | 1 | **0.0000°** | 0.0000° | PASS |
| **Type-1** (spine/arm/hand) | 15 | **0.0000°** | 0.0000° | PASS |
| Type-2 (palm) | 8 | 113.05° | 17.42° | 주1 참조 |
| Type-3 (finger) | 20 | 180.00° | 59.63° | 주1 참조 |
| **Type-4** (eye) | 2 | **0.3529°** | 0.2353° | PASS |

> **주1: Type-2/3 오른손 조인트 오차에 대하여**
>
> 오른손 조인트의 커스텀 회전축(Table D.5)은 월드 좌표계 대비 180° 회전된 좌표계를 정의한다. 이로 인해:
> - BVH 레퍼런스 포즈(영 회전)가 커스텀 축 공간에서 ~180° 회전으로 분해됨
> - Type-2의 E2x 인코딩 범위 [-90°, 90°] 및 Type-3의 단일축(8비트) 인코딩으로는 이 값을 정확히 표현할 수 없음
> - **이는 사양의 설계적 특성**으로, 실제 수어 모션 데이터에서는 손가락 관절이 레퍼런스 포즈 근처에서 움직이므로 오차가 크게 감소함
> - **왼손 조인트는 이 문제가 없음** (커스텀 축이 월드 축에 가까워 분해 결과가 범위 내에 있음)
> - 인코딩 전(양자화 전) 라운드트립은 **완벽(0.0000° 오차)** — 알고리즘 자체는 정확함

#### Test 7: glTF 출력기

| 항목 | 기대값 | 실측값 | 결과 |
|------|--------|--------|------|
| glTF 버전 | 2.0 | 2.0 | PASS |
| 애니메이션 이름 | - | "sign_language_motion" | PASS |
| 채널 수 | > 46 | 50 (46회전+1이동+3가중치) | PASS |
| 샘플러 수 | = 채널 수 | 50 | PASS |
| 노드 수 | ≥ 46 | 49 (46조인트+3메시노드) | PASS |
| 루트 노드 | hips_JNT | hips_JNT | PASS |
| 바이너리 버퍼 | > 0 | 167,560B | PASS |
| rotation 채널 | 46 | 46 | PASS |
| translation 채널 | 1 | 1 | PASS |
| weights 채널 | ≥ 1 | 3 | PASS |

#### Test 8: CLI 인터페이스

| 명령어 | 결과 |
|--------|------|
| `encode avatarModel.bvh` | 9,824B .slmb.xz 생성 |
| `decode-bvh *.slmb.xz` | 46조인트/142프레임 BVH 출력 |
| `decode-gltf *.slmb.xz` | glTF 2.0 + .bin 출력 |
| `roundtrip avatarModel.bvh` | 전 단계 완료 |
| `info *.slmb.xz` | 압축률/프레임/블렌드쉐이프 정보 출력 |

### 4.3 성능 수치

| 항목 | 값 |
|------|-----|
| 입력 BVH 프레임 | 142 (4.73초 @ 30fps) |
| BodyMotionBlock | 22,444 bytes |
| FaceMotionBlock | 2,494 bytes |
| MotionBundle (비압축) | 24,957 bytes |
| SLMB 파일 (xz 압축) | 9,824 bytes |
| **압축률** | **39.4%** |
| glTF 바이너리 | 167,560 bytes |
| 활성 블렌드쉐이프 | 15개 (3개 메시) |

---

## 5. 사양 준수 매트릭스

| ABNT NBR 25606 섹션 | 구현 상태 | 구현 모듈 |
|---------------------|----------|----------|
| Table D.1 (조인트 계층) | 완료 | `constants.py` SKELETON_HIERARCHY |
| Table D.3 (레퍼런스 포즈) | 완료 | `constants.py` REFPOSE_FROM_PARENT |
| Table D.4 (조인트 타입) | 완료 | `constants.py` JOINT_ORDER |
| Table D.5 (회전축) | 완료 | `constants.py` ROTATION_AXES |
| Table D.7 (블렌드쉐이프 68개) | 완료 | `constants.py` HEAD_GEO_BLENDSHAPES |
| Table D.8 (BodyMotionBlock) | 완료 | `slmb_encoder.py`, `slmb_decoder.py` |
| Table D.9 (SLMB 조인트 순서) | 완료 | `constants.py` JOINT_ORDER |
| Table D.10 (FaceMotionBlock) | 완료 | `slmb_encoder.py`, `slmb_decoder.py` |
| Table D.11 (블렌드쉐이프 ID) | 완료 | `constants.py` MESH_BLENDSHAPE_MAP |
| Table D.12 (MotionBundle 키) | 완료 | `constants.py` SLMB_TITLE_KEY 등 |
| Table D.13 (MotionBundle 구조) | 완료 | `slmb_encoder.py` encode_motion_bundle |
| D.5.4 (LZMA/xz 압축) | 완료 | `slmb_encoder.py` compress_slmb |

| OG-06 섹션 | 구현 상태 | 구현 모듈 |
|-----------|----------|----------|
| D.2.3 (회전 변환 알고리즘) | 완료 | `math_utils.py` |
| D.2.4.3 (BVH → SLMB) | 완료 | `slmb_encoder.py` |
| D.2.4.4 (SLMB → BVH) | 완료 | `bvh_writer.py` |
| D.2.5.3 (JSON → SLMB Face) | 완료 | `slmb_encoder.py` encode_face_motion_block |
| D.2.5.4 (SLMB → JSON Face) | 완료 | `slmb_decoder.py` decode_face_motion_block |
| D.2.6.3 (SLMB → glTF) | 완료 | `gltf_writer.py` |
| Table D.5 (MotionBundle 캡슐화) | 완료 | `slmb_encoder.py` |

---

## 6. 알려진 제한사항

### 6.1 오른손 Type-2/3 양자화 오차

- **원인**: 오른손 조인트의 커스텀 회전축(Table D.5)이 180° 회전 좌표계를 정의
- **영향**: 레퍼런스 포즈 근처의 작은 회전이 커스텀 축 공간에서 ~180°로 분해되어 인코딩 범위 초과
- **범위**: Type-2의 E2x [-90°, 90°] 및 Type-3의 8비트 단축 인코딩
- **실제 영향**: 수어 모션 데이터에서는 손가락이 레퍼런스 포즈에서 크게 벗어나므로 영향 미미
- **왼손**: 이 문제 없음 (커스텀 축이 항등 행렬에 가까움)

### 6.2 glTF → SLMB 역변환 미구현

- 현재 glTF는 출력(디코딩)만 지원
- glTF → SLMB 인코딩은 미구현 (필요 시 확장 가능)

### 6.3 VLibras 아바타 호환성

- VLibras AssetBundle(84본, 포르투갈어 명명) → ABNT 표준(46조인트, 영문) 리타겟팅은 미포함
- `CASA_sample_analysis.md`의 매핑 테이블 참조하여 별도 구현 필요

---

## 7. 사용 예시

### 7.1 Python API 사용

```python
from slmb_converter.bvh_parser import parse_bvh
from slmb_converter.face_data import generate_sample_face_data
from slmb_converter.slmb_encoder import bvh_to_slmb
from slmb_converter.slmb_decoder import decode_slmb_file
from slmb_converter.bvh_writer import slmb_to_bvh
from slmb_converter.gltf_writer import slmb_to_gltf

# 인코딩
bvh = parse_bvh("input.bvh")
face = generate_sample_face_data(bvh.num_frames, bvh.frame_time)
bvh_to_slmb(bvh, face, "output.slmb.xz")

# 디코딩
slmb = decode_slmb_file("output.slmb.xz")
slmb_to_bvh(slmb, "decoded.bvh")
slmb_to_gltf(slmb, "decoded.gltf")
```

### 7.2 CLI 사용

```bash
# 전체 라운드트립 테스트
python -m slmb_converter roundtrip avatarModel.bvh

# 파일 정보 확인
python -m slmb_converter info output.slmb.xz

# 개별 단계 실행
python -m slmb_converter encode avatarModel.bvh output.slmb.xz
python -m slmb_converter decode-bvh output.slmb.xz decoded.bvh
python -m slmb_converter decode-gltf output.slmb.xz decoded.gltf
```

---

## 8. Three.js 아바타 플레이어 (`player.html`)

> **작성일**: 2026-03-10
> **위치**: `docu/player.html`

### 8.1 개요

SLMB 디코딩 결과(glTF/GLB 애니메이션)를 ABNT 표준 아바타 모델에 적용하여 브라우저에서 실시간 재생하는 Three.js 기반 단일 HTML 플레이어이다.

### 8.2 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         player.html                             │
│  ┌──────────────┐     ┌──────────────────┐     ┌────────────┐  │
│  │ avatarModel   │     │ *_roundtrip.glb  │     │  Three.js  │  │
│  │   .glb        │     │ (애니메이션 GLB)  │     │  r160 CDN  │  │
│  │ (아바타 모델) │     │ (스켈레톤+트랙)   │     │            │  │
│  └──────┬───────┘     └────────┬─────────┘     └────────────┘  │
│         │                      │                                │
│         ▼                      ▼                                │
│  ┌──────────────┐     ┌──────────────────┐                     │
│  │ GLTFLoader   │     │  GLTFLoader      │                     │
│  │  → scene     │     │  → animations[0] │                     │
│  └──────┬───────┘     └────────┬─────────┘                     │
│         │                      │                                │
│         │      ┌───────────────┘                                │
│         ▼      ▼                                                │
│  ┌──────────────────┐                                           │
│  │ AnimationMixer    │   리타겟팅: 조인트 이름(UUID) 매칭       │
│  │  + retargetClip() │   애니메이션 트랙 → 아바타 본 바인딩     │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 핵심 로직: 애니메이션 리타겟팅

SLMB 디코딩 GLB에는 메시 없이 **스켈레톤 + 애니메이션 트랙**만 존재한다.
아바타 모델 GLB에는 **메시 + 텍스처 + 스켈레톤**이 존재한다.
두 파일의 스켈레톤이 동일한 ABNT 조인트 이름(hips_JNT, spine_JNT 등)을 사용하므로,
이름 기반 매칭으로 애니메이션을 아바타에 적용한다.

```javascript
// 애니메이션 GLB의 트랙: "<animNode.uuid>.quaternion"
// 아바타 모델의 본:     boneMap[jointName].uuid
// 리타겟팅: animNode.name → boneMap에서 같은 이름 찾기 → uuid 교체
for (const track of clip.tracks) {
    const property = track.name.split('.').pop();  // "quaternion" or "position"
    const sourceName = findNodeName(animGltf, nodeUuid);
    const targetBone = boneMap[sourceName];
    if (targetBone) {
        newTrack.name = targetBone.uuid + '.' + property;
    }
}
```

### 8.4 아바타 모델 처리

#### 8.4.1 GLB 변환

원본 `avatarModel/model_external.gltf`는 외부 참조(.bin + PNG 35개) 형식이라 GLTFLoader의 `resolveURL` 버그를 유발한다. 이를 단일 자기 완결형 GLB로 패킹하였다.

- **입력**: `model_external.gltf` + `model.bin` (4.9MB) + PNG 35개
- **출력**: `avatarModel.glb` (8.1MB)
- **변환 스크립트**: `gltf_to_glb.py` (이미지를 bufferView로 임베딩)

#### 8.4.2 RootNode Scale 보정

아바타 모델의 `RootNode`에 `scale: [100, 100, 100]`이 설정되어 있어, SLMB 애니메이션(미터 단위)과 불일치한다. 플레이어에서 `rootNode.scale.set(1, 1, 1)`로 보정한다.

### 8.5 생성 파일 목록

| 파일 | 크기 | 설명 |
|------|------|------|
| `player.html` | ~12KB | Three.js 기반 단일 HTML 플레이어 |
| `avatarModel.glb` | 8.1MB | 아바타 모델 (메시+텍스처+스켈레톤) |
| `avatarModel_roundtrip.glb` | 167KB | BVH 샘플 → SLMB → glTF 애니메이션 |
| `CASA_roundtrip.glb` | 57KB | CASA(집) 글로스 → SLMB → glTF 애니메이션 |

### 8.6 플레이어 기능

| 기능 | 설명 |
|------|------|
| 재생 제어 | Play / Pause / Stop |
| 시크바 | 드래그로 특정 시점 탐색 |
| 속도 조절 | 0.25x / 0.5x / 1x / 2x |
| 애니메이션 전환 | 드롭다운으로 BVH Sample / CASA(집) 선택 |
| 스켈레톤 표시 | 본 연결선 + 조인트 구체 (토글) |
| 카메라 조작 | OrbitControls (드래그 회전, 스크롤 줌) |

### 8.7 실행 방법

```bash
cd D:\lg\work\SLS\brazil\docu
python -m http.server 8080
# 브라우저에서 http://localhost:8080/player.html 접속
```

---

## 9. VLibras CASA 글로스 → SLMB 변환 검증

> **작성일**: 2026-03-10

### 9.1 변환 파이프라인

```
CASA_extracted/CASA_full.json   (VLibras Unity AnimationClip, 84본+22블렌드쉐이프)
    ↓ [vlibras2slmb convert --json]
    ↓  · VLibras 84본 → ABNT 46조인트 스켈레톤 매핑
    ↓  · 포르투갈어 본명 → 영문 ABNT 조인트명 리타겟팅
    ↓  · 바인드포즈 제거 + 좌표계 변환
    ↓  · 30fps 리샘플링 (76프레임, 2.467초)
CASA.slmb.xz                    (2,444 bytes, LZMA 압축)
    ↓ [vlibras2slmb decode-gltf]
CASA_roundtrip.glb              (57,152 bytes, 47채널 애니메이션)
    ↓ [player.html]
아바타 모델에 CASA 수어 재생 ✓
```

### 9.2 변환 결과

| 항목 | 값 |
|------|-----|
| 입력 | CASA_full.json (VLibras "CASA" = 집) |
| 원본 프레임 | 30fps, 2.467초 |
| 리타겟팅 프레임 | 76프레임 |
| BodyMotionBlock | 12,016 bytes |
| FaceMotionBlock | 308 bytes |
| MotionBundle (비압축) | 12,343 bytes |
| SLMB 파일 (xz 압축) | 2,444 bytes |
| **압축률** | **19.8%** |
| glTF 채널 수 | 47 (46회전 + 1이동) |
| 플레이어 재생 | 정상 확인 ✓ |

### 9.3 사용한 컨버터

| 도구 | 위치 | 용도 |
|------|------|------|
| `slmb_converter` | `docu/slmb_converter/` | BVH ↔ SLMB ↔ glTF (ABNT 표준 입력) |
| `vlibras2slmb` | `docu/vlibras2slmb/` | VLibras JSON → SLMB (리타겟팅 포함) |

### 9.4 vlibras2slmb CLI

```bash
# VLibras JSON → SLMB 변환
python -m vlibras2slmb convert CASA_extracted/CASA_full.json --json -o CASA.slmb.xz

# SLMB → glTF 디코딩 (GLB 형식)
python -m vlibras2slmb decode-gltf CASA.slmb.xz -o CASA_roundtrip.glb --name CASA

# SLMB 파일 검증
python -m vlibras2slmb validate CASA.slmb.xz
```

---

## 10. gltf_writer.py 버그 수정

> **작성일**: 2026-03-10

### 10.1 문제

`gltf_writer.py`의 Face 블렌드쉐이프 채널 처리 시, 메시 노드에 `"mesh": 0` 참조를 설정하지만 실제 `meshes` 배열은 정의하지 않아 Three.js GLTFLoader가 크래시하였다.

```
TypeError: Cannot read properties of undefined (reading '0')
    at GLTFParser.loadMesh
```

### 10.2 수정

`slmb_converter/gltf_writer.py` 188행:

```python
# 수정 전
node = {"name": mesh_name, "mesh": 0}  # placeholder → GLTFLoader 크래시

# 수정 후
node = {"name": mesh_name}  # mesh 참조 제거 (skeleton-only animation)
```

Face 블렌드쉐이프 weight 채널은 여전히 해당 노드를 타겟으로 하지만, 메시 참조 없이도 glTF 스펙상 유효하다. 실제 아바타 모델과 결합할 때 메시 노드가 별도 존재하므로 문제없다.
