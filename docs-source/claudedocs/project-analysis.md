# Brazil Sign Language Player — 초기 프로젝트 분석 (Historical)

**원본 작성**: 2026-03-25 · **상태 갱신**: 2026-04-29

> 본 문서는 **Three.js SLMB Player를 처음 설계하던 시점의 사전 분석**이다. 현재 디렉토리 구조와 구현 상태는 [`CLAUDE.md`](../../CLAUDE.md)와 [`project-status.md`](project-status.md)가 최신이다. 본 문서의 ABNT 스펙 표(§2)와 핵심 수학(§8) 부분은 여전히 유효하며 reference로 활용 가치 있음. **§3 VLibras Portal·§5 SLMB 현재 상태·§6 구현 전략은 historical**(이미 모두 구현됨).

---

## 1. 프로젝트 구조 (당시 시점, historical)

당시는 별도 폴더(`docu/`, `vlibras-portal/`, `data/`, `slmb-player/`)로 분리되어 있었으며, 2026-04-08에 단일 `sls_brazil_player/` 구조로 통합됨. 현재 구조는 [`CLAUDE.md`](../../CLAUDE.md) 참조.

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

### CASA 애니메이션 번들 (당시 위치, historical)

당시는 `data/CASA/` 안에 Unity AssetBundle과 raw dump JSON이 있었음. 현재는 `public/animations/vlibras/`로 통합됨. 데이터 변환 파이프라인 5단계는 [`data-pipeline-and-handedness.md`](data-pipeline-and-handedness.md) §1 참조.

---

## 5. SLMB Player 구현 상태 (현재)

§1·§5·§6의 historical 내용 대신 현재 구현 상태는 다음을 참조:

- **Python 패키지**: `tools/slmb_converter/`, `tools/vlibras2slmb/` (구조는 [`CLAUDE.md`](../../CLAUDE.md) 디렉토리 도식 참조)
- **Three.js 플레이어들**: `public/players/{bvh,slmb,vlibras,vlibras-v3,sentence,sentence-stroke-test,viewer}/`
- **SLMB Pipeline Player 구현 상세**: [`implement-player-bvh-slmb.md`](implement-player-bvh-slmb.md)

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

## 9. 후속 진행 (당시 시점 기록)

§9의 "Three.js 플레이어 구현 우선순위" 5단계는 모두 구현 완료. 현재 진행 중인 작업과 다음 단계는 [`project-status.md`](project-status.md)를 참조.
