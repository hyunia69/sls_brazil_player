# player_vlibras 설계 문서 v2

## 1. 개요

VLibras CASA 수어 애니메이션을 Icaro 3D 아바타에서 재생하는 Three.js 웹 플레이어.
**단계적 접근**: 먼저 화면에 재생하는 것을 최우선으로, 이후 변환 파이프라인 정리.

---

## 2. 이전 시도의 문제점 분석

### 2.1 근본 원인: 두 파이프라인의 좌표 변환 불일치

```
경로A (애니메이션): Unity JSON → vlibras_to_gltf.py [-x,-y,z,w] → glTF
경로B (아바타):     Unity FBX → Blender (axis_forward=-Z, axis_up=Y) → GLB
```

경로A와 경로B가 **다른 쿼터니언 변환 규칙**을 사용하여:
- 상체: 우연히 W값이 양수인 본들 → 정상 작동
- 하체: W값이 음수인 본들(BnBacia_L: w=-0.49) → 렌더러 정규화 시 회전 반전

### 2.2 구체적 증거

| 본 | Unity 원본 W | 변환 후 W | 증상 |
|---|---|---|---|
| BnOmbro.L (어깨) | +양수 | +양수 | 정상 ✅ |
| BnBraco.L (팔) | +양수 | +양수 | 정상 ✅ |
| BnBacia (골반) | -1.48e-07 | -1.48e-07 | 왜곡 ❌ |
| BnBacia_L (왼골반) | -0.4945 | -0.4945 | 심한 왜곡 ❌ |

### 2.3 기존 접근의 실패 이유

1. **점진적 패치**: `[-x,-y,z,w]` 변환 후 개별 본 보정 → 근본 해결 안됨
2. **scale 100x 불일치**: 컨버터 position이 100x인데 아바타는 다른 스케일
3. **두 파이프라인 유지**: 서로 다른 변환 규칙을 맞추려는 시도 자체가 취약

---

## 3. 새로운 접근: JavaScript 직접 로딩

### 3.1 핵심 아이디어

glTF 중간변환을 건너뛰고, **CASA_full.json을 JavaScript에서 직접 파싱**하여
Icaro.glb 아바타의 본 좌표계에 맞는 AnimationClip을 실시간 생성한다.

```
기존: Unity JSON → Python 컨버터 → glTF → Three.js GLTFLoader → 재생
신규: Unity JSON → JavaScript 직접 파싱 → AnimationClip 빌드 → 재생
                                    ↑
                    Icaro.glb의 본 좌표계에 맞춰 변환
```

### 3.2 왜 이 방법이 맞는가

1. **단일 파이프라인**: 아바타와 애니메이션이 같은 좌표계 변환을 거침
2. **즉각 검증 가능**: 변환 공식을 바꿔가며 브라우저에서 바로 확인
3. **Python 의존성 제거**: UnityPy/Blender 없이 순수 웹 기술로 재생
4. **근본 해결**: 좌표 변환을 한 곳에서 통제

---

## 4. 단계별 구현 계획

### Stage 1: Icaro 아바타 + CASA JSON 직접 재생 (핵심 목표)

**목표**: CASA 수어가 Icaro 아바타에서 올바르게 재생되는 것을 화면에서 확인

#### 4.1.1 아바타 로딩
- GLTFLoader로 `Icaro.glb` 로드
- 본 맵 구축: `{ boneName: THREE.Bone }`
- 아바타의 본 계층과 rest pose 쿼터니언을 콘솔에 출력 (디버그용)

#### 4.1.2 CASA_full.json 파싱
- fetch()로 JSON 로드
- bone_paths, rotation_curves, position_curves 추출
- 본 경로에서 리프 이름 추출 (예: `Armature.001/BnBacia.001/BnCol-01` → `BnCol-01`)

#### 4.1.3 쿼터니언 변환 (핵심 과제)

**Unity 원본** `[x, y, z, w]` → **Icaro.glb 호환** `[?, ?, ?, ?]`

Icaro.glb는 Unity FBX에서 왔으므로, 본 로컬 쿼터니언이 거의 보존됨:
```
FBX(Unity) → Blender(axis_forward=-Z, axis_up=Y, auto_orient=False)
           → GLB(export_yup=True)
```
Blender의 Y-up→Z-up→Y-up 변환이 상쇄되어, 본 로컬 회전은 거의 그대로.

**검증 방법**: Armature.001의 rest pose를 비교
- CASA_full.json: `[-0.7071, 0, 0, 0.7071]` (Rx -90°)
- Icaro.glb: 로드 후 `avatarBoneMap['Armature.001'].quaternion` 확인
- 두 값의 관계에서 변환 공식 도출

**후보 변환 공식** (실험으로 검증):
```javascript
// 후보 1: 변환 없이 그대로 (FBX→Blender→GLB가 상쇄될 경우)
q_avatar = [x, y, z, w]

// 후보 2: Z-flip (현재 컨버터 방식)
q_avatar = [-x, -y, z, w]

// 후보 3: W 정규화 후 Z-flip
if (w < 0) { x=-x; y=-y; z=-z; w=-w; }
q_avatar = [-x, -y, z, w]

// 후보 4: 완전한 Z-negate
q_avatar = [x, y, -z, w]
```

**실험 전략**: 4가지 후보를 드롭다운으로 선택할 수 있게 구현하여 시각적으로 비교.

#### 4.1.4 AnimationClip 빌드
```javascript
function buildClipFromJSON(jsonData, conversionFn) {
    const tracks = [];
    for (const rc of jsonData.rotation_curves) {
        const boneName = leafName(rc.path);  // 경로에서 리프 이름
        const times = rc.keyframes.map(kf => kf.time);
        const values = [];
        for (const kf of rc.keyframes) {
            const [qx, qy, qz, qw] = conversionFn(kf.value);
            values.push(qx, qy, qz, qw);
        }
        tracks.push(new THREE.QuaternionKeyframeTrack(
            `${boneName}.quaternion`, times, values
        ));
    }
    return new THREE.AnimationClip('CASA', -1, tracks);
}
```

#### 4.1.5 재생
```javascript
const mixer = new THREE.AnimationMixer(avatarModel);
const clip = buildClipFromJSON(casaData, selectedConversion);
mixer.clipAction(clip).play();
```

### Stage 2: UI 완성

Stage 1에서 올바른 변환 공식이 확정되면:
- 재생 컨트롤 (Play/Pause, Stop, Timeline, Speed)
- 스켈레톤 시각화 오버레이
- 파일 업로드 (CASA_full.json 또는 다른 VLibras JSON)
- 키보드 단축키

### Stage 3: 변환 파이프라인 정리 (이후)

- 확정된 변환 공식을 vlibras_to_gltf.py에 반영
- 또는 glTF 중간 단계를 제거하고 JSON 직접 로딩으로 통일

---

## 5. 기술 상세

### 5.1 본 이름 매핑

CASA_full.json의 bone_paths는 전체 경로:
```
Armature.001/BnBacia.001/BnCol-01/BnCol-02/BnCol-03/BnOmbro.L
```

Three.js AnimationMixer는 **리프 이름**으로 매칭:
```
BnOmbro.L.quaternion → avatarModel 내 name="BnOmbro.L"인 Bone에 적용
```

경로에서 리프 추출:
```javascript
function leafName(path) {
    return path.includes('/') ? path.split('/').pop() : path;
}
```

주의: `Armature.001` 같은 이름은 리프이면서 동시에 경로 접두사.
Three.js PropertyBinding은 scene 트리를 탐색하여 이름으로 매칭하므로,
리프 이름이 유니크하면 정상 작동.

### 5.2 scale 처리

CASA_full.json의 position 값은 Unity 단위 (미터급).
Icaro.glb의 bone translation은 Blender FBX import 시 결정된 스케일.

**Stage 1 전략**: position 트랙을 일단 적용하지 않고 rotation만 적용.
수어는 대부분 회전만 사용하므로 position 없이도 동작 표현 가능.
(필요 시 empirical scale factor를 실험으로 결정)

### 5.3 보조 본 처리

IK/FK 컨트롤러, 폴벡터 등은 시각화에서 제외:
```javascript
const AUX_PREFIXES = ['BnMaoOrient', 'BnPolyV', 'ik_FK'];
```
이 본들의 애니메이션 트랙도 아바타에는 적용하지 않음 (아바타에 해당 본이 없을 수 있음).

### 5.4 Armature.001 루트 회전

Unity에서 Armature.001은 Rx(-90°) = `[-0.707, 0, 0, 0.707]`.
이것은 Unity의 Y-up 씬에서 스켈레톤을 세우는 회전.

Icaro.glb에서 Armature.001의 rest 회전을 확인하여:
- 같은 값이면 → 애니메이션 트랙의 Armature.001 rotation을 그대로 적용
- 다른 값이면 → 아바타의 rest를 유지하고 Armature.001 트랙은 skip

---

## 6. 파일 구성

### 입력 (변경 없음)
| 파일 | 용도 |
|---|---|
| `data/vlibras_avatar/Icaro.glb` | 아바타 모델 |
| `data/CASA/CASA_full.json` | 애니메이션 원본 데이터 |

### 출력 (새로 작성)
| 파일 | 용도 |
|---|---|
| `slmb-player/player_vlibras/index.html` | 플레이어 (clean rewrite) |

### 참조 (수정 불필요)
| 파일 | 용도 |
|---|---|
| `slmb-player/player_vlibras/vlibras_to_gltf.py` | Stage 3에서 수정 검토 |
| `slmb-player/player_vlibras/CASA_vlibras.*` | Stage 3에서 재생성 검토 |

---

## 7. Stage 1 검증 체크리스트

- [ ] Icaro.glb 로드: 텍스처 정상 (피부, 옷, 머리카락)
- [ ] CASA_full.json 파싱: 102개 본, 회전 커브 확인
- [ ] Armature.001 rest pose 비교 (JSON vs avatar)
- [ ] 쿼터니언 변환 후보 4가지 시각적 비교
- [ ] **최적 변환 공식 결정**
- [ ] 상체 수어 동작 정확 (팔, 손가락, 머리)
- [ ] 하체 자연스러운 직립 (또는 수용 가능한 상태)
- [ ] 재생/정지 기본 동작

---

## 8. 이전 구현 대비 변경점 요약

| 항목 | 이전 (v1) | 신규 (v2) |
|---|---|---|
| 애니메이션 소스 | CASA_vlibras.gltf (Python 변환) | CASA_full.json (JS 직접 파싱) |
| 좌표 변환 | Python `[-x,-y,z,w]` 고정 | JS에서 실험, 최적 공식 결정 |
| 중간 파일 | glTF 필요 | 불필요 (JSON → AnimationClip 직접) |
| 하체 처리 | 트랙 필터링 (증상 숨김) | 올바른 변환으로 근본 해결 시도 |
| position 트랙 | 100x scale 불일치 | Stage 1에서 skip, 이후 해결 |
| 디버그 | console.log | 변환 공식 선택 UI |
