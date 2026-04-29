# VLibras 애니메이션 데이터 파이프라인 + 좌표계 변환

브라질 수어 글로스를 Unity AssetBundle 원본에서 브라우저 재생 가능한 Three.js JSON까지 변환하는 전체 흐름과 좌표계 변환 수학을 단일 진실 출처로 정리한다.

작성일: 2026-04-29

---

## 1. 단일 글로스 변환 파이프라인 (오프라인)

```
[Stage 0]  CASA (Unity AssetBundle, UnityFS 2018.3.1)        Unity LH
              │ UnityPy 파싱 (tools/vlibras2slmb/parsing/asset_bundle.py)
              ▼
[Stage 1]  CASA_full.json   (Unity raw curves dump)          Unity LH
              │ Blender IK bake
              ▼
[Stage 2]  CASA_ik_fixed.json   (forearm IK-baked + dense)   Unity LH
              │ ① 좌표변환 (LH→RH)
              │ ② Armature.001 루트 회전 제거
              │ ③ bind-pose 보정
              │ ④ uniform 30fps resample
              │ ⑤ position을 frame0 delta로 인코딩
              │ ⑥ 본 이름 정규화 (leaf + dot strip)
              ▼
[Stage 3]  CASA.anim.json   (gltf + delta_from_frame0)       glTF RH (76 quat)
              │ precompute_threejs.py (Icaro bind 적용)
              │   · delta → absolute 위치
              │   · scale 트랙 합성 (identity)
              │   · 손목·머리·IK 보조본 보존 (총 83 quat)
              ▼
[Stage 4]  bundles/<GLOSS>.threejs.json   (sentence/v3 사용)   glTF RH
```

### 각 단계 산출물 위치

| 산출물 | 위치 | 사용처 |
|--------|------|--------|
| Unity AssetBundle | `public/animations/vlibras/CASA` | (변환 입력) |
| `CASA_full.json` | `public/animations/vlibras/` | 디버깅 (Unity raw dump) |
| `CASA_ik_fixed.json` | `public/animations/vlibras/` | 디버깅 (IK 중간 산출물) |
| `CASA.anim.json` | `public/animations/vlibras/` | **vlibras 플레이어** |
| `CASA_threejs.json` | `public/animations/vlibras/` | **vlibras-v3 플레이어** |
| `bundles/<GLOSS>.threejs.json` (27개) | `public/animations/vlibras/bundles/` | **sentence + sentence-stroke-test** |
| `bundles/index.json` | 동상 | 사전 색인 |

### 메타데이터 단일 진실 출처 — `CASA.anim.json` 헤더

```json
{
  "name": "CASA",
  "duration": 2.466667,
  "sample_rate": 30.0,
  "_source": "CASA_ik_fixed.json",
  "_coordinate_space": "gltf",
  "_position_encoding": "delta_from_frame0",
  "tracks": [...]
}
```

`_position_encoding: delta_from_frame0`이 **vlibras 플레이어의 14줄 런타임 fixup이 필요한 이유의 단일 진실 출처**다. `CASA_threejs.json`에는 이 메타데이터가 없으며 absolute 인코딩이라 fixup이 불필요하다.

---

## 2. 단계별 처리 상세

### Stage 0 → 1: AssetBundle → `CASA_full.json`

**입력**: Unity AssetBundle (UnityFS 컨테이너, 2018.3.1f1로 빌드).
**도구**: UnityPy (`pip install UnityPy`).
**출력**: 84본 모든 회전·위치·플로트(블렌드셰이프) 곡선의 raw dump.

핵심 코드 (`tools/vlibras2slmb/parsing/asset_bundle.py:42-138`):
- `m_RotationCurves` → quaternion `(w, x, y, z)` 키프레임 추출
- `m_PositionCurves` → position `(x, y, z)` 키프레임 추출
- `m_FloatCurves` → 블렌드셰이프 가중치 추출
- 본 경로는 **계층 full path** 보존: `Armature.001/BnBacia.001/BnCol-01/.../BnAntBraco.L`
- 키프레임은 **sparse** (Unity 원본 그대로): 정지 본은 시작/끝 2개만

**왜 raw dump 보관**: Unity AssetBundle을 매번 파싱하지 않고 빠른 디버깅 + IK bake 입력.

### Stage 1 → 2: `CASA_full.json` → `CASA_ik_fixed.json`

**무엇이 변하는가**: Blender에서 IK 솔버를 풀어 forearm(아래팔)의 sparse 회전 키프레임을 dense per-frame 회전으로 다시 굽기.

`_source: "CASA_full.json with IK-baked forearm rotations from Blender"` 메타가 직접 명시.

**왜 필요**: VLibras 원본은 IK 컨트롤로 만들어졌고 Unity 엔진은 런타임에 IK를 푼다. 우리는 IK 없이 quaternion만 사용하므로 빌드 타임에 한 번 풀어둠.

**검증**: `BnAntBraco.L` 트랙이 full에서 sparse, ik_fixed에서 75 키프레임(30fps × 2.467s).

좌표계는 여전히 Unity LH (수치 보정 없음).

### Stage 2 → 3: `CASA_ik_fixed.json` → `CASA.anim.json`

가장 처리량이 많은 단계. 6가지가 동시에 적용된다.

#### 2-3-① Armature.001 루트 회전 제거

VLibras 모델은 Blender → Unity export 시 `Armature.001` 루트에 -90° X 회전이 들어 있다 (Blender Z-up과 Unity Y-up axis convention). 그대로 두면 자손 본이 90° 기울어진다.

코드 (`tools/vlibras2slmb/math_utils/coordinate.py:25-78`):
```python
_ROOT_ROTATION = (cos(-π/4), sin(-π/4), 0, 0)  # (w, x, y, z)
def remove_root_rotation(q_wxyz):
    return q_wxyz * inverse(_ROOT_ROTATION)
```

#### 2-3-② Bind-pose 보정 (특히 손가락)

각 VLibras 본은 bind pose가 있다. 새끼손가락 `BnDedo5.L`은 bind pose 자체가 ~90° 굽어 있어 SLMB euler 분해 시 표현 범위를 벗어나 round-trip 오차가 최대 180°까지 발생할 수 있다.

코드 (`tools/vlibras2slmb/retarget/body_retarget.py:323-376` 주석):
```python
# Q_correction = inv(Q_bind_abnt) * Qr
Q_correction = multiply(inverse(Q_bind_abnt), Qr)
for q in quats:
    q_corrected = q * Q_correction
```

#### 2-3-③ 좌표계 변환 — Unity LH → glTF RH

**§3에서 별도 상세 설명.** 핵심은 quaternion `(w, x, y, z) → (w, -x, y, -z)`, position `(x, y, z) → (-x, y, -z)`.

#### 2-3-④ Uniform 30fps 리샘플링

ik_fixed는 본별 키프레임 수가 다르다(forearm 75개, 정지 본 2개). 모든 트랙을 동일한 시간 그리드(30fps × duration)에 SLERP/선형 보간으로 다시 샘플.

#### 2-3-⑤ Position의 frame-0 delta 인코딩

`_position_encoding: delta_from_frame0`. 각 position 트랙은 frame 0 기준 변위로 저장:
```
저장값[i] = 원본_위치[i] - 원본_위치[0]
```

정지 본은 모두 (0,0,0)이 되어 gzip 압축률 극대화. **단점**: 런타임에 모델 rest pose를 더해 복원해야 함 → vlibras 플레이어의 14줄 fixup이 그것.

#### 2-3-⑥ 본 이름 정규화

| 변환 전 | 변환 후 |
|---------|---------|
| `Armature.001/BnBacia.001/BnCol-01/.../BnAntBraco.L` | `BnAntBracoL` |

leaf 이름만 추출 + dot 제거 (Three.js property accessor 호환).

### Stage 3 → 4: `CASA.anim.json` → `CASA_threejs.json` (또는 bundles)

`tools/vlibras2slmb/batch/precompute_threejs.py` (`--match-legacy` 모드)가 수행:

- delta → absolute (Icaro bind pose 기준 더하기)
- scale 트랙 합성 (대부분 identity)
- 본 이름 정규화는 이미 됨
- **8본 추가 보존**: `BnMaoOrientR/L`, `BnPolyVR/L`, `cabecaModifAlisson_1/2`, `ik_FKR/L`
  - Stage 3의 ABNT 46관절 retargeting 경로는 이들을 IK target으로 분류해 제외함
  - precompute_threejs.py 경로는 Three.js 직접 재생용이라 모두 보존
- 시간 그리드를 1프레임 shift (`[0.000, 0.033, ...]` → `[0.033, 0.066, ...]`)

---

## 3. LH → RH 좌표계 변환 자세히

### 3-1. 손잡이(handedness)란

3D 좌표계는 **세 축의 방향 관계**가 두 가지로 나뉜다.

| 시스템 | 손잡이 | Y축 | Z축 의미 |
|--------|-------|-----|---------|
| **Unity** | **LH** | up | **+Z = 화면 안쪽 (forward)** |
| OpenGL / glTF / Three.js | **RH** | up | **+Z = 화면 바깥쪽 (toward viewer)** |
| Blender | RH | **Z-up** | +Y = 화면 안쪽 |

오른손 엄지(X)·검지(Y)·중지(Z) 방향이 일치하면 RH.

### 3-2. 왜 둘이 공존하는가

- **Unity**: DirectX 전통(Microsoft) — LH 채택
- **glTF / Three.js**: OpenGL 전통(Khronos) — RH 채택

본 프로젝트는 **Three.js로 웹에서 재생**하므로 반드시 RH가 되어야 한다.

### 3-3. 변환 수학

Unity LH → RH로 갈 때 X와 Z 축 방향이 뒤집힌다 (Y는 유지). mirror 행렬:
```
M = | -1   0   0 |
    |  0   1   0 |
    |  0   0  -1 |
```

#### Position

```
position_RH = M · position_LH = (-x, y, -z)
```

코드 (`tools/vlibras2slmb/math_utils/coordinate.py:81-95`):
```python
def unity_position_to_abnt(pos):
    return np.array([-x, y, -z])
```

#### Quaternion

회전은 **mirror conjugation**:
```
R_RH = M · R_LH · M^T
```

quaternion `(w, x, y, z)`로 풀면:
```
q_RH = (w, -x, y, -z)
```

코드 (`tools/vlibras2slmb/math_utils/coordinate.py:38-55`):
```python
def unity_quat_to_abnt(q_wxyz):
    w, x, y, z = q_wxyz
    return np.array([w, -x, y, -z])
```

> **주의**: `CLAUDE.md`의 좌표 변환 1줄 요약은 ABNT 변환과 정확히 동일하지 않다. 실제 변환 진실 출처는 `coordinate.py`이며, 본 문서가 그것을 반영한다. precompute_threejs.py가 추가로 적용하는 Icaro bind 매핑은 별도(§4-3 참조).

### 3-4. 직관적 이해

- **X 부호 반전**: Unity의 +X(오른쪽)와 RH의 +X(오른쪽)는 같지만, Z가 뒤집히면서 좌우 거울상이 되므로 X도 반전이 필요해진다 (참고용 mental model).
- **Z 부호 반전**: Unity +Z = 화면 안쪽(forward), RH +Z = 화면 바깥(toward viewer). 정반대.
- **Y 유지**: 둘 다 +Y = 위.

좌표 변환을 안 하고 Unity 데이터를 그대로 Three.js로 넣으면:
- 모션이 거울처럼 좌우 반전 (오른손 dominant 동작이 왼손으로 보임 → 수어 의미 파괴)
- 앞뒤 방향이 반대

수어는 handedness가 의미를 결정하는 언어라 좌우 반전은 치명적이다.

### 3-5. Quaternion 변환 증명 (참고)

회전축 `(ax, ay, az)`의 `θ` 회전 quaternion:
```
q = (cos(θ/2), ax·sin(θ/2), ay·sin(θ/2), az·sin(θ/2))
```

X·Z mirror 시 회전축이 `(ax, ay, az) → (-ax, ay, -az)`로 반사. 동시에 LH↔RH 회전 방향이 반대라 `θ → -θ`. 결과:
```
q_RH = (cos(θ/2), ax·sin(θ/2), -ay·sin(θ/2), az·sin(θ/2))
     = (w, -x, y, -z)
```

`w`와 `y` 유지, `x`와 `z` 부호 반전.

---

## 4. vlibras vs vlibras-v3 데이터 핸들링 차이

두 플레이어는 같은 글로스(CASA)를 표현하지만 **포함 본·시간 그리드·rest pose 가정·트랙 종류**가 다르다. "단지 변환 시점만 다른 것"이 아니다.

### 4-1. 검증된 차이점 (실측)

| 비교 | vlibras (`CASA.anim.json`) | vlibras-v3 (`CASA_threejs.json`) |
|------|---------------------------|--------------------------------|
| 본 개수 | 77 | **85** (+8) |
| 트랙 수 | 153 (77 pos + 76 quat) | **249** (83 pos + 83 quat + 83 scale) |
| 추가 본 | — | `BnMaoOrientL/R`, `BnPolyVL/R`, `cabecaModifAlisson_1/2`, `ik_FKL/R` |
| 시간 그리드 | `[0.000, 0.033, ...]` | `[0.033, 0.066, ...]` (+1 frame shift) |
| Duration | 2.467s | 2.500s |
| Position 인코딩 | delta_from_frame0 | absolute |
| Rest pose 출처 | 런타임 GLB 모델 | 빌드 타임 Icaro bind |
| Quaternion 값 (공통 76 트랙) | 사실상 동일 (max diff 2×10⁻⁴) | |

### 4-2. 가장 큰 의미 차이 — 손목 회전 트랙

`BnMaoOrientR.quaternion`, `BnMaoOrientL.quaternion`이 **vlibras에는 없고 v3에만 있다**.

수어 음운론에서 손바닥 방향(palm orientation)은 **의미를 결정하는 5대 요소** 중 하나(handshape, location, movement, palm orientation, non-manual markers). 손목 회전이 빠지면 같은 손동작이라도 의미가 약하게 전달되거나 왜곡된다.

원인: Stage 3의 retargeting 경로(ABNT 46관절 지향)가 BnMaoOrient를 IK target으로 분류해 제외. precompute_threejs.py 경로는 Three.js 직접 재생용이라 보존.

### 4-3. Rest pose 출처 차이

```
vlibras 동작:
  delta 데이터 + 로드된 모델 GLB의 본 rest = 절대 위치 (런타임)
   ┌────────────┐    ┌─────────────────┐
   │ Padrao 로드 │ →  │ Padrao rest 더함 │
   │ CASA 로드   │ →  │ CASA rest 더함   │
   │ Icaro 로드  │ →  │ Icaro rest 더함  │
   └────────────┘    └─────────────────┘

vlibras-v3 동작:
  precompute_threejs.py가 빌드 타임에 Icaro bind 더하기
   ┌──────────────────────────────────────┐
   │ 어떤 모델을 로드해도 Icaro rest 가정    │
   └──────────────────────────────────────┘
```

세 모델(Padrao/CASA/Icaro)은 "공통 90본 스켈레톤"이지만 본의 절대 rest 위치가 정확히 같다는 보장은 없다. 미세하게 다르면 v3는 Padrao/CASA에 Icaro의 rest를 강제 적용한 셈이라 본 위치가 살짝 어긋날 수 있다.

### 4-4. 코드 차이 — 정확한 위치

#### vlibras (`public/players/vlibras/index.html:268-301`)

```js
if (animClip) {
  // ① 본 lookup
  const boneByName = {};
  model.traverse(c => { if (c.isBone) boneByName[c.name] = c; });

  // ② position 트랙에 GLB rest 더하기 (delta → absolute)
  const fixedTracks = animClip.tracks.map(track => {
    if (!track.name.endsWith('.position')) return track;
    const bone = boneByName[track.name.split('.')[0]];
    if (!bone) return track;
    const rest = bone.position;
    const values = new Float32Array(track.values.length);
    for (let i = 0; i < track.values.length; i += 3) {
      values[i]     = track.values[i]     + rest.x;
      values[i + 1] = track.values[i + 1] + rest.y;
      values[i + 2] = track.values[i + 2] + rest.z;
    }
    return new THREE.VectorKeyframeTrack(track.name, track.times, values);
  });
  const clip = new THREE.AnimationClip(animClip.name, animClip.duration, fixedTracks);
  ...
}
```

#### vlibras-v3 (`public/players/vlibras-v3/index.html:268-278`)

```js
if (animClip) {
  // 보정 없음 — 데이터가 이미 absolute
  mixer = new THREE.AnimationMixer(model);
  currentAction = mixer.clipAction(animClip);
  ...
}
```

### 4-5. 두 플레이어의 존재 이유

| 플레이어 | 검증 목적 |
|---------|---------|
| **vlibras** | delta 인코딩 데이터 + 모델 GLB rest 합산이 시각적으로 올바른가 검증 (Stage 3 산출물 무결성) |
| **vlibras-v3** | precompute_threejs.py 결과(Stage 4)가 무손실인가 검증 (Stage 4 산출물 무결성) |

운영 가치 비교:
- **수어 의미 보존 측면에서는 v3가 절대적으로 우수** (손목 회전 보존)
- vlibras는 데이터 파이프라인 중간 산출물 디버깅용으로만 의미

### 4-6. "vlibras에 v3 로직 적용 가능한가" 검토 결과 (2026-04-29)

**결론: 기술적으로는 가능하나, 실용 가치 거의 없음. 추천 안 함.**

3가지 시나리오 검토:

| 시나리오 | 가능성 | 결과 품질 | 비용 | 권장도 |
|---------|-------|----------|------|------|
| A. `CASA.anim.json`에서 v3 흉내 (delta→abs, scale 합성, time shift, Icaro rebase) | ⚠️ 부분 | 손목 회전 여전히 없음 | +50줄 | ❌ |
| B. `CASA_ik_fixed.json` → 런타임 retarget (precompute_threejs.py 포팅) | ✅ | v3 거의 동일 | +200~300줄 + bind pose JSONs | ❌ |
| C. vlibras가 `CASA_threejs.json`을 직접 fetch (한 줄 변경) | ✅ | v3 동일 | -14줄 | △ (= v3와 같아짐) |

**근본 이유**:
1. 두 플레이어는 검증 단계 차이라는 다른 정체성을 가짐 → 통합 시 검증 가치 소멸
2. 시나리오 B는 빌드 타임 변환을 매 모델 로드마다 반복하는 비효율
3. 손목 회전 누락은 데이터 출처 자체의 문제 — 런타임 변환으로 만들 수 없음

만약 통합이 필요하다면 **데이터 파이프라인 수정** (Stage 3 retargeting이 BnMaoOrient를 보존하도록)이 정답.

---

## 5. 운영(production) 변환 위치 결정 검토 (2026-04-29)

실서비스에서는 사용자 입력 시점에 어휘를 동적으로 가져와야 한다. 사전 변환된 27개 글로스(`bundles/`)만으로는 부족.

### 5-1. 3가지 아키텍처

| 옵션 | 변환 위치 | 첫 호출 latency | 백엔드 필요? | 권장 시나리오 |
|------|---------|--------------|------------|------------|
| **A. 일괄 사전 변환** (현재) | 빌드 타임 | 50–100ms | ❌ | 어휘 < 100, 변경 빈도 낮음 |
| **B. 서버 on-demand** | Python 백엔드 (UnityPy) | 300–800ms | ✅ | 어휘 1000+, 백엔드 운영 가능 |
| **C. 브라우저 직접** | JS 런타임 | 150–430ms | ❌ | 백엔드 절대 불가, CORS 허용 |
| **하이브리드 A+B** | 자주: CDN, 드물게: 서버 | 자주 50ms / 드물게 500ms | ✅ | **실서비스 권장** |

### 5-2. 옵션 C(브라우저 직접) 기술적 평가

| 부품 | 가능성 | 비용 |
|------|------|------|
| CORS (`dicionario2.vlibras.gov.br`) | ⚠️ **검증 필요** | 5분 작업 |
| UnityFS 헤더 파싱 | ✅ | ~30줄 |
| LZ4/LZMA 압축 해제 | ✅ | `lz4js` + `lzma-js` ~40KB |
| TypeTree + 직렬화 객체 추출 | ⚠️ **어려움** | 직접 작성 vs Pyodide(WASM) |
| precompute_threejs.py 로직을 JS로 포팅 | ✅ | ~250줄 |
| **합계 페이로드** | | **~105KB minified** |
| 첫 호출 latency 추정 | | **150–430ms** |
| 캐시 후 latency | | <30ms (IndexedDB) |

**핵심 위험**: Unity 직렬화 형식은 버전마다 다르며 UnityPy가 수년간 처리해온 edge case를 JS로 다시 구현하는 부담이 큼. WASM Pyodide+UnityPy는 가능하지만 첫 로드 ~3초 + 메모리 ~50MB → 비현실적.

### 5-3. 권장 — 하이브리드 A + B

```
브라우저
   │ 글로스 요청
   ├─→ /animations/vlibras/bundles/<KEY>.threejs.json
   │     └ Cache hit → 즉시 재생
   │
   └─→ Cache miss → 백엔드 (/api/gloss/<KEY>)
                     └ Redis 확인
                        ├ Hit → 즉시 반환
                        └ Miss → VLibras CDN fetch
                                 + precompute_threejs.py 실행
                                 + Redis + CDN 캐시 저장
                                 → 응답 반환 (~500ms)
```

**이유**:
- 변환 코드를 Python 한 군데(`precompute_threejs.py`)에 유지 → JS 포팅·동기화 부담 0
- 자주 쓰는 어휘는 정적 CDN으로 빠름
- long-tail은 서버에서 lazy compute + 캐시
- Unity 포맷 변화 시 서버만 업데이트
- CORS 의존 없음

### 5-4. 옵션 C가 의미 있는 단 하나의 시나리오

오프라인 우선 PWA / 전용 키오스크 / 정적 호스팅 의무 — 백엔드를 절대 둘 수 없는 환경에서만 ~3-4주 투자 가치.

---

## 6. 운영 결정 전 확인 사항

1. **CORS 검증** (5분): `curl -I -H "Origin: https://sls-brazil-player.vercel.app" https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/CASA` → `Access-Control-Allow-Origin` 확인
2. **트래픽 추정**: DAU × 평균 글로스 수 → 어휘 캐시 사이즈 산정
3. **신규 어휘 빈도**: VLibras 사전 update 주기 → 사전변환 빌드 자동화 가능성
4. **백엔드 제약**: 회사 정책상 서버 운영이 가능한지

이 4가지 답이 A·B·C·하이브리드 선택을 거의 결정한다.

---

## 7. 핵심 파일 참조

| 목적 | 파일 |
|------|------|
| AssetBundle 파서 | `tools/vlibras2slmb/parsing/asset_bundle.py` |
| 좌표 변환 | `tools/vlibras2slmb/math_utils/coordinate.py` |
| Body retargeting (Stage 3) | `tools/vlibras2slmb/retarget/body_retarget.py` |
| precompute_threejs.py (Stage 4) | `tools/vlibras2slmb/batch/precompute_threejs.py` |
| Icaro bind pose | `tools/vlibras2slmb/data/icaro_bind_pose.json` |
| VLibras bind pose | `tools/vlibras2slmb/data/vlibras_bind_pose.py` |
| 스파이크 어휘 목록 | `tools/vlibras2slmb/data/spike_glosses.txt` |
| 다운로더 | `tools/vlibras2slmb/batch/downloader.py` |
| 사전 CDN | `https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/<GLOSS>` |
| 사전 색인 API | `https://dicionario2.vlibras.gov.br/bundles` |

---

## 8. 알려진 이슈 / 주의

1. **CLAUDE.md의 좌표 변환 1줄 요약은 본 문서와 일치하지 않는다** — `coordinate.py`가 진실 출처. CLAUDE.md는 별도 verification 필요 (precompute_threejs.py가 추가 적용하는 Icaro bind 매핑이 다른 표현을 만들 가능성).
2. **`asset_bundle.py` UnityPy 1.25+ 마이그레이션 미완** — uppercase `X/Y/Z/W` 사용. `precompute_threejs.py`는 자체 lowercase 리더로 정상.
3. **Windows Python cp949 인코딩** — `precompute_threejs.py` 비ASCII print에서 `UnicodeEncodeError`. 우회: `PYTHONIOENCODING=utf-8`.
4. **CORS 미검증** — `dicionario2.vlibras.gov.br` 사전 CDN의 CORS 허용 여부 확인 필요 (옵션 C 결정의 전제).
