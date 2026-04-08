# Brazil Sign Language Player - Project Analysis

**Date**: 2026-03-25
**Goal**: Three.js 기반 SLMB Player 구현을 위한 사전 분석

---

## 1. 프로젝트 구조 개요

```
player/
├── docu/              # ABNT NBR 25606 표준 문서 + SBTVD OG-06 운영 가이드
├── vlibras-portal/    # VLibras 공식 포털 (위젯, Unity WebGL 플레이어, 샘플)
├── data/              # 아바타 모델(glTF) + CASA 애니메이션 번들
├── slmb-player/       # SLMB 변환기 (Python) - Three.js 플레이어 구현 대상
└── claudedocs/        # 분석 문서
```

---

## 2. ABNT NBR 25606 표준 (docu/)

### 수어 전송 4가지 방식

| 방식 | 데이터 | 대역폭 | 렌더링 |
|------|--------|--------|--------|
| **A: 비디오** | VVC H.266 영상 스트림 | HIGH | 비디오 재생 |
| **B: 글로스** | IMSC1/TTML 텍스트 | LOW | 수신측 아바타 합성 |
| **C: 자막** | IMSC1/TTML 자막 | LOW | 수신측 번역+아바타 |
| **D: 모션** | SLMB 바이너리 번들 | MEDIUM | 3D 스켈레톤 애니메이션 |

**Three.js 플레이어 구현 대상: Method D (Motion Stream)**

### SLMB 파이프라인

```
BVH/Animation → BodyMotionBlock + FaceMotionBlock → MotionBundle → LZMA/xz → .slmb.xz
```

### 스켈레톤 구조 (46 조인트)

| 조인트 타입 | 개수 | 인코딩 | 프레임당 바이트 |
|------------|------|--------|----------------|
| Type-0 (루트/hips) | 1 | Position(uint16x3) + Quat(int16x3) | 12 |
| Type-1 (메인) | 15 | Quaternion(int16x3) | 6 |
| Type-2 (손바닥) | 8 | Euler Packed(10+10+12bit) | 4 |
| Type-3 (손가락) | 20 | Z-Euler(uint8) | 1 |
| Type-4 (눈) | 2 | X/Y Euler(8+8bit) | 2 |
| **합계** | **46** | | **158 bytes/frame** |

### 페이스 블렌드셰이프 (268개)

| 메시 | ID 범위 | 개수 |
|------|---------|------|
| head_GEO | 0~67 | 68 |
| mouth_GEO | 1020~1067 | 48 |
| eyelash_GEO | 2000~2059 | 60 |
| eyebrow_l_GEO | 3014~3058 | 45 |
| eyebrow_r_GEO | 4014~4058 | 45 |
| iris_l/r_GEO | 5059, 6059 | 2 |

### 양자화 공식

| 데이터 | 범위 | 공식 | 결과 |
|--------|------|------|------|
| Translation | [-0.5m, 0.5m] | `(val+0.5)*65535` | uint16 |
| Quaternion | [-1, 1] | `val*32767` | int16 |
| Euler(Type-2 xy) | [-90, 90] | `(val+90)/180*1023` | 10bit |
| Euler(Type-2 z) | [-180, 180] | `(val+180)/360*4095` | 12bit |
| Euler(Type-3) | [-180, 180] | `(val+180)/360*255` | 8bit |
| Eye Euler | [-90, 90] | `(val+90)/180*255` | 8bit |
| Blendshape | [0, 1] | `val*65535` | uint16 |

---

## 3. VLibras Portal (vlibras-portal/)

### 기존 VLibras 시스템 아키텍처

```
사용자 텍스트 선택
    → POST traducao2.vlibras.gov.br/translate (PT→글로스 변환)
    → dicionario2.vlibras.gov.br/bundles (애니메이션 번들 조회)
    → Unity WebGL 플레이어 (3D 아바타 렌더링)
```

### 핵심 기술 스택

- **렌더링**: Unity WebGL + WebAssembly (256MB 메모리)
- **애니메이션**: Unity AssetBundle (legacy format, 30fps)
- **스켈레톤**: 104+ 본 계층 (포르투갈어 명명)
- **API**: 공개 (인증 없음, 접근성 목적)

### 아바타 커스터마이징

```json
{
  "calca": "#0E0F18",        // 바지 색상
  "camisa": "#1C204F",       // 셔츠 색상
  "cabelo": "#000000",       // 머리카락
  "corpo": "#C18471",        // 피부톤
  "iris": "#000000",         // 홍채
  "avatar": "icaro|hosana|guga|random"
}
```

### 주요 참고사항

- VLibras는 Unity 기반이므로 Three.js 플레이어는 독립적 구현
- 글로스 기반 애니메이션 재생 방식 참고 가능
- API 엔드포인트 재활용 가능 (번역, 사전)

---

## 4. Data 디렉토리 (data/)

### 아바타 모델 (`data/avatarModel/`)

| 파일 | 크기 | 설명 |
|------|------|------|
| `model_external.gltf` | 395KB | glTF 2.0 메시+스켈레톤 정의 |
| `model.bin` | 4.9MB | 지오메트리+텍스처 바이너리 |
| `avatarModel.bvh` | 545KB | 스켈레톤 모션 (142프레임, 30fps) |
| PNG 텍스처 29개 | ~2.5MB | PBR (Albedo, Normal, ARM) |

**모델 출처**: Samsung MyEmoji v3.1
**머티리얼**: PBR (Metallic-Roughness)
**컴포넌트**: head, hair, body, eyes, eyebrows, eyelashes, mouth, shoes, clothing

### CASA 애니메이션 번들 (`data/CASA/`)

| 파일 | 크기 | 설명 |
|------|------|------|
| `CASA` | 19.7KB | Unity AssetBundle (바이너리) |
| `manifest.json` | 879B | 에셋 메타데이터 |
| `CASA_animation.json` | 5.7KB | 키프레임 데이터 추출 |
| `CASA_full.json` | 131.8KB | 전체 스켈레톤+애니메이션 |

**애니메이션 속성**:
- Duration: 2.47초 (74프레임 @ 30fps)
- 102개 본 경로
- 쿼터니언 회전 + XYZ 위치 곡선
- 84개 스케일 커브 + 22개 플로트 커브 (블렌드셰이프)

---

## 5. SLMB Player 현재 상태 (slmb-player/)

### 기존 Python 패키지

| 패키지 | 버전 | 기능 |
|--------|------|------|
| `slmb_converter` | 1.0.0 | BVH ↔ SLMB ↔ glTF 변환 |
| `vlibras2slmb` | 0.1.0 | VLibras AssetBundle → SLMB 변환 |

### 주요 모듈

```
slmb_converter/           vlibras2slmb/
├── bvh_parser.py         ├── parsing/animation_clip.py
├── slmb_encoder.py       ├── retarget/body_retarget.py
├── slmb_decoder.py       ├── retarget/face_retarget.py
├── gltf_writer.py        ├── encoding/body_encoder.py
├── math_utils.py         ├── encoding/face_encoder.py
└── constants.py          └── encoding/gltf_writer.py
```

### Three.js 플레이어 구현 필요 사항

**있는 것**:
- SLMB 바이너리 포맷 파서/인코더 (Python)
- glTF 내보내기 파이프라인
- 조인트/블렌드셰이프 스펙 (ABNT 표준)
- 샘플 아바타 모델 (glTF + 텍스처)
- 샘플 애니메이션 (CASA)

**없는 것 (구현 대상)**:
- JavaScript/TypeScript SLMB 디코더
- Three.js 씬 세팅 (SkinnedMesh, AnimationMixer)
- 스켈레톤 리깅 (46 조인트 매핑)
- 블렌드셰이프 적용 (morphTargets)
- 실시간 렌더링 + UI 컨트롤

---

## 6. Three.js Player 구현 전략

### 접근 방식 A: glTF 경유 (권장)

```
.slmb.xz → Python 디코더 → .gltf/.glb → Three.js GLTFLoader → 재생
```

- 장점: Three.js의 기존 glTF 지원 활용, 빠른 프로토타이핑
- 단점: 오프라인 변환 필요, 실시간 스트리밍 불가

### 접근 방식 B: 네이티브 SLMB 디코더

```
.slmb.xz → JS SLMB Decoder → Three.js SkinnedMesh + AnimationClip → 재생
```

- 장점: 실시간 스트리밍 가능, 완전한 제어
- 단점: SLMB 바이너리 파서를 JS로 재구현 필요

### 접근 방식 C: 하이브리드

```
Phase 1: glTF 경유로 프로토타입 구현
Phase 2: JS SLMB 디코더로 전환
```

### 핵심 Three.js 컴포넌트

```
Three.js Player
├── Scene Setup (WebGLRenderer, Camera, Lights)
├── Avatar Loader (GLTFLoader → SkinnedMesh)
├── Animation System
│   ├── AnimationMixer (재생 제어)
│   ├── AnimationClip (키프레임 데이터)
│   └── MorphTarget (페이셜 블렌드셰이프)
├── SLMB Decoder (바이너리 → 애니메이션 데이터)
└── UI Controls (재생/정지/속도/아바타 선택)
```

---

## 7. VLibras 본 이름 vs SLMB 조인트 매핑 (중요)

| SLMB (ABNT 표준) | VLibras (기존 시스템) | 설명 |
|-------------------|----------------------|------|
| hips_JNT | BnBacia.001 | 루트/골반 |
| spine_JNT | BnCol-01 | 척추 하부 |
| spine1_JNT | BnCol-02 | 척추 중부 |
| spine2_JNT | BnCol-03 | 척추 상부 |
| neck_JNT | BnPescoco | 목 |
| head_JNT | BnCabeca | 머리 |
| r_shoulder_JNT | BnOmbro.R | 우측 어깨 |
| r_arm_JNT | BnBraco.R | 우측 상완 |
| r_forearm_JNT | BnAntBraco.R | 우측 전완 |
| r_hand_JNT | BnMao.R | 우측 손 |
| r_handIndex1_JNT | BnDedo.2.R | 우측 검지 |

**주의**: 두 시스템의 본 계층, 명명 규칙, 좌표계가 다름 → 리타겟팅 필요

---

## 8. 핵심 수학 연산

### 오일러 → 쿼터니언 (SLMB XYZ 순서)

```
euler2quaternion_xyz(Ex, Ey, Ez, RX, RY, RZ):
  cx, sx = cos/sin(Ex/2), cy, sy = cos/sin(Ey/2), cz, sz = cos/sin(Ez/2)
  qw = cx*cy*cz + sx*sy*sz
  qx = sx*cy*cz - cx*sy*sz
  qy = cx*sy*cz + sx*cy*sz
  qz = cx*cy*sz - sx*sy*cz
  → 커스텀 회전축 RX,RY,RZ 적용
```

### 디양자화 (SLMB → 실수 값)

```
Translation: val/65535 - 0.5 (meter)
Quaternion:  val/32767 (normalized)
Euler 10bit: val/1023*180 - 90 (degrees)
Euler 12bit: val/4095*360 - 180 (degrees)
```

---

## 9. 요약 및 다음 단계

### 현재 보유 자산
1. **표준 문서**: ABNT NBR 25606 완전 분석 (SLMB 바이너리 스펙)
2. **참조 구현**: VLibras Unity WebGL 플레이어 (아키텍처 참조)
3. **데이터**: glTF 아바타 모델 + CASA 애니메이션 샘플
4. **변환기**: Python SLMB encoder/decoder + glTF writer

### Three.js 플레이어 구현 우선순위
1. **glTF 모델 로딩**: data/avatarModel/ 의 모델을 Three.js로 로드
2. **애니메이션 재생**: CASA 샘플을 glTF로 변환 후 재생 테스트
3. **SLMB JS 디코더**: Python 구현을 JavaScript로 포팅
4. **블렌드셰이프**: 페이셜 애니메이션 적용
5. **UI**: 재생 컨트롤, 아바타 커스터마이징
