# player_bvh_slmb 구현 문서

## 개요

SLMB 파이프라인 전체 검증용 Three.js 플레이어. BVH 원본에서 SLMB 인코딩/디코딩을 거친 3가지 출력 포맷(JSON, BVH, glTF)을 모두 재생하여 파이프라인 정합성을 검증한다.

- **위치**: `slmb-player/player_bvh_slmb/index.html`
- **단일 파일**: HTML + CSS + JS (ES Module) 올인원, 외부 의존성은 CDN Three.js만
- **Three.js**: v0.170.0 (importmap CDN)
- **아바타**: `data/avatarModel/model_external.gltf` (Samsung MyEmoji v3.1, SLMB 표준 호환)

## 실행 방법

```bash
cd D:/lg/work/SLS/brazil/code/player
python -m http.server 8080
# 브라우저: http://localhost:8080/slmb-player/player_bvh_slmb/
```

## 아키텍처

### 파이프라인 위치

```
avatarModel.bvh (원본)
    ↓ slmb_converter encode
    .slmb.xz (압축 바이너리)
    ↓ slmb_converter decode
    ├── avatarModel_roundtrip_slmb.json  ← SOURCE 1: SLMB JSON
    ├── avatarModel_roundtrip.bvh        ← SOURCE 2: Roundtrip BVH
    └── avatarModel_roundtrip.gltf/.bin  ← SOURCE 3: Roundtrip glTF
    ↓
    player_bvh_slmb (이 플레이어)
    ↓
    model_external.gltf 아바타에 애니메이션 적용 → 3D 렌더링
```

### 씬 구성

| 요소 | 설정 |
|------|------|
| Renderer | WebGLRenderer, antialias, SRGBColorSpace |
| Camera | PerspectiveCamera(60, ..., 0.01, 100) |
| Controls | OrbitControls (damping 0.1) |
| Lighting | AmbientLight(0.8) + DirectionalLight(1.0) + BackLight(0.3) |
| Grid | GridHelper(4, 20) + AxesHelper(0.3) |

### 3가지 소스 로더

#### SOURCE 1: SLMB JSON (`loadSLMBJson`)

SLMB 디코더의 `json_writer`가 출력한 JSON을 직접 파싱하여 Three.js `AnimationClip`을 수동 빌드한다.

```
JSON 구조:
{
  body: {
    num_frames, frame_time,
    joints: [{ name, type, frames: [{ q: [qw,qx,qy,qz], t: [x,y,z] }] }]
  },
  face: { blendshapes: [...] }  // 미구현
}
```

- **쿼터니언 변환**: JSON `[qw, qx, qy, qz]` → Three.js `[qx, qy, qz, qw]`
- **위치 트랙**: `type === 0` (ROOT) 조인트만 position 트랙 생성 (미터 단위 그대로)
- **AnimationMixer**: 아바타 모델에 직접 바인딩

#### SOURCE 2: Roundtrip BVH (`loadBVH`)

Three.js `BVHLoader`로 파싱 후 트랙을 필터링/스케일링한다.

- **Position 필터링**: `hips_JNT.position` 트랙만 유지, 나머지 position 트랙 제거
  - 이유: BVH의 모든 조인트에 position이 있으면 아바타 본의 rest position을 덮어써서 포즈가 망가짐
- **BVH_SCALE**: 0.01 (cm → m 변환)
  - hips position 값에만 적용 (회전은 스케일 불변)
- **프레임 정보**: BVH 텍스트에서 `Frames:`, `Frame Time:` 직접 파싱

#### SOURCE 3: Roundtrip glTF (`loadGLTFAnimation`)

Three.js `GLTFLoader`로 로드하여 내장 `AnimationClip`을 추출한다.

- **로드 방식 2가지**:
  - 파일 선택기: `URL.createObjectURL` → GLTFLoader.load (외부 .bin 미지원)
  - 프리셋 버튼: 서버 URL로 직접 로드 (외부 .bin 자동 해석)
- **프레임 계산**: `totalFrames = Math.round(duration * 30)`, 고정 30fps 가정
- **블렌드셰이프**: `morphTargetInfluences` 트랙 수 카운트하여 UI 표시

### 공통 아바타 시스템

#### 아바타 로드 (`loadAvatarModel`)

```javascript
avatarModel.scale.set(0.01, 0.01, 0.01);  // RootNode scale=100 상쇄
```

- glTF 아바타의 `RootNode`에 `scale=[100,100,100]`이 내장 (Samsung MyEmoji 특성)
- Three.js 로드 시 ×0.01 적용하여 미터 단위로 정규화
- 본 이름 맵 구축: `avatarBoneMap[boneName] = boneNode`
- SkinnedMesh에 `frustumCulled = false` 설정 (애니메이션 중 컬링 방지)

#### 스켈레톤 헬퍼 (`addSkeletonHelper`)

- `SkeletonHelper`로 본 구조 시각화 (토글 가능)
- Rest pose 저장: 각 본의 초기 quaternion/position을 `userData`에 캐싱
- cleanup 시 rest pose 복원

#### 카메라 추적

- `getAvatarCenterY()`: hips_JNT의 월드 Y + 0.25m (상체 중심 근사)
- 렌더 루프에서 `orbit.target.y`를 부드럽게 보간 (lerp 0.1)

### UI 컴포넌트

#### 로드 프롬프트

| 버튼 | 색상 | 동작 |
|------|------|------|
| SLMB JSON | #0a8 (녹색) | 파일 선택기 (.json) |
| Roundtrip BVH | #e94560 (적색) | 파일 선택기 (.bvh) |
| Roundtrip glTF | #6c5ce7 (보라) | 파일 선택기 (.gltf) |
| Preset JSON | 녹색 소형 | `data/avatarModel_roundtrip_slmb.json` 서버 로드 |
| Preset BVH | 적색 소형 | `data/avatarModel_roundtrip.bvh` 서버 로드 |
| Preset glTF | 보라 소형 | `data/avatarModel_roundtrip.gltf` 서버 로드 |

#### 재생 컨트롤

| 컨트롤 | 기능 |
|--------|------|
| Play/Pause | 재생 토글 (Space 키) |
| Stop | 프레임 0으로 리셋 |
| Timeline | 슬라이더 스크러빙 (0~1000 매핑) |
| Speed ±0.1x | 0.1x ~ 5.0x 재생 속도 |
| Bones 토글 | SkeletonHelper 표시/숨김 (S 키) |
| Cam | 카메라 리셋 (아바타 중심) |
| Back | cleanup 후 로드 프롬프트로 복귀 |
| ← / → | 1프레임 전진/후퇴 |

#### 정보 패널

- Source (현재 로드된 소스 타입)
- Joints: 46 (SLMB 표준)
- Frames / FPS / Duration
- Blendshapes 수

## 해결한 기술 이슈

### 1. SLMB JSON Qr 역변환 누락

**문제**: `json_writer`가 Type-2/3 조인트(손바닥/손가락)의 `Q_enc`를 `inv(Qr)` 없이 그대로 출력.

**원인**: 인코더가 `Q_enc = Q_bvh * Qr`로 인코딩하는데, 디코더 json_writer가 `Q_enc`를 그대로 JSON에 썼음. 왼손은 `Qr ≈ identity`라 오차 미미했으나, 오른손은 `Qr ≈ 180°Y회전`이라 ~180도 오차 발생.

**해결**: `json_writer.py`에서 `_get_bvh_quaternion()` 함수로 Type별 `Qr` 제거. `Q_bvh = Q_enc * inv(Qr)`

### 2. BVH 전조인트 Position 덮어쓰기

**문제**: BVHLoader가 파싱한 모든 조인트의 position 트랙이 아바타 본의 rest position을 덮어써서 포즈 붕괴.

**원인**: BVH 포맷은 모든 조인트에 6 채널(Xpos Ypos Zpos Xrot Yrot Zrot)을 갖는데, Three.js AnimationMixer가 position 트랙을 적용하면 아바타 본 위치가 BVH OFFSET 값으로 대체됨.

**해결**: `filteredTracks`에서 `hips_JNT.position`만 유지하고 나머지 position 트랙 전부 제거. 회전 트랙은 전부 유지.

### 3. BVH Writer Qr 역변환 누락

**문제**: `bvh_writer.py`에서도 json_writer와 동일한 Qr 누락 버그.

**해결**: Type-2/3에서 `Q_bvh = Q_enc * inv(Qr)` 후 오일러 변환. 수정 후 최대 오차 180.53° → 0.71°, 평균 오차 18.65° → 0.13°.

### 4. glTF RootNode Scale 100

**문제**: Samsung MyEmoji가 생성한 glTF의 `RootNode`에 `scale=[100,100,100]` 내장. Three.js에서 그대로 로드하면 아바타가 100배 크기.

**해결**: `avatarModel.scale.set(0.01, 0.01, 0.01)` 적용하여 RootNode 스케일 상쇄.

### 5. 카메라 중심 문제

**문제**: 고정 카메라 타겟으로 인해 아바타가 이동하면 프레임 밖으로 나감.

**해결**: hips_JNT 월드 위치 기반 자동 추적. `orbit.target.y`를 매 프레임 lerp 보간.

## 수정 후 검증 결과

3가지 소스 모두 동일 아바타(model_external.gltf)에서 시각적으로 동일한 모션을 재생함을 확인:

| 소스 | 프레임 | FPS | Duration | 검증 |
|------|--------|-----|----------|------|
| SLMB JSON | 142 | 30 | 4.73s | 정상 |
| Roundtrip BVH | 142 | 30 | 4.73s | 정상 |
| Roundtrip glTF | 142 | 30 | 4.73s | 정상 |

## 미구현 사항

- **Face Blendshape 재생**: SLMB JSON의 face.blendshapes 데이터를 아바타 morphTarget에 매핑하는 로직 (TODO 상태)
- **파일 선택기 glTF + .bin**: 외부 .bin 참조가 있는 glTF는 파일 선택기로 로드 불가 (프리셋 버튼 사용 필요)

## 의존 파일

| 파일 | 역할 |
|------|------|
| `data/avatarModel/model_external.gltf` + `model.bin` + PNG 텍스처 | 렌더링 아바타 |
| `data/avatarModel_roundtrip_slmb.json` | SLMB JSON 프리셋 (slmb_converter 출력) |
| `data/avatarModel_roundtrip.bvh` | Roundtrip BVH 프리셋 (slmb_converter 출력) |
| `data/avatarModel_roundtrip.gltf` + `.bin` | Roundtrip glTF 프리셋 (slmb_converter 출력) |
