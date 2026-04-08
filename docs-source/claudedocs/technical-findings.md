# Technical Findings - 대화 중 발견사항

**Date**: 2026-03-26

---

## 1. data/avatarModel.bvh 정체

OG-06 문서(SBTVD_OG06_analysis.md:695)에서 공식 제공하는 **SLMB 표준 레퍼런스 파일**.

- SLMB→BVH 디코딩 시 HIERARCHY 섹션(스켈레톤 구조) 참조용
- BVH→SLMB 인코딩의 입력 포맷 예시
- 46 조인트, 142프레임 @ 30fps, cm 단위

## 2. data/avatarModel/ (model_external.gltf) 정체

OG-06 문서(SBTVD_OG06_analysis.md:960)에서 `avatarModel.zip`으로 제공하는 **공식 렌더링 타겟 아바타**.

- Samsung MyEmoji v3.1 기반
- SLMB 디코딩 결과를 시각적으로 렌더링하기 위한 3D 모델
- **RootNode에 scale=[100,100,100] 내장** (중요!)

## 3. BVH ↔ glTF 호환성 검증

### 조인트 이름: 100% 일치
SLMB 표준 46개 조인트 전부 glTF 모델에 존재. glTF에는 38개 추가 조인트(하체, 머리카락 등).

### 좌표값: 정확히 100배 비율
```
BVH OFFSET (cm)        glTF translation (m)     ratio
spine:    4.1304       0.041304                 100.00
neck:    17.0656       0.170656                 100.00
r_forearm: -25.5729    -0.255729                100.00
(모든 조인트에서 동일)
```

### 블렌드셰이프: SLMB 표준 완전 적합
- head_GEO: 68개 (표준 68개 완전 일치)
- mouth_GEO: 17개 (표준 16 + 1)
- eyelash_GEO: 20개 (표준 18 + 2)
- eyebrow_l/r_GEO: 각 9개 (완전 일치)
- iris_l/r_GEO: 각 1개 (완전 일치)

**결론: SLMB 바디+페이셜 모션 모두 매핑 없이 직접 적용 가능**

## 4. BVH vs SLMB 차이

| 항목 | BVH | SLMB |
|------|-----|------|
| 용도 | 제작/편집용 원본 | 방송 전송용 압축본 |
| 내용 | 바디 모션만 | 바디 + 페이셜 번들 |
| 포맷 | 텍스트 (무압축) | LZMA/xz 바이너리 |
| 정밀도 | float (고정밀) | 8~16bit 양자화 (손실) |

파이프라인: `BVH(바디) + JSON(페이셜) → SLMB 인코딩 → .slmb.xz → 방송 → 디코딩 → 아바타 렌더링`

## 5. glTF 스케일 문제 (Three.js)

model_external.gltf 노드 구조:
```
model → RootNode(scale: [100,100,100]) → rig_GRP → hips_JNT → ...
```

- 본 translation은 **미터** 단위
- RootNode ×100으로 인해 실제 렌더링은 **cm** 스케일
- Three.js bbox: Y: -1.3 ~ 163.5 (cm)
- **해결**: `avatarModel.scale.set(0.01, 0.01, 0.01)` 적용

## 6. player_bvh 구현 상태

위치: `slmb-player/player_bvh/index.html`

구현 완료:
- BVH 드래그&드롭 로드 + Three.js 스켈레톤 시각화
- 재생/정지/속도/타임라인 컨트롤
- glTF 아바타 자동 로드 + BVH 모션 리타겟팅
- Avatar/Bones 모드 토글

실행: 프로젝트 루트에서 `python -m http.server 8080` → `http://localhost:8080/slmb-player/player_bvh/`

## 7. slmb_converter 버그 수정 (2026-03-26)

### bvh_writer.py / json_writer.py - Type-2/3 Qr 역변환 누락
- 인코더: `Q_enc = Q_bvh * Qr` → 오일러 저장
- 디코더(기존): `Q_enc` → BVH 오일러 (Qr 미제거, 오른손 ~180도 오차)
- 디코더(수정): `Q_bvh = Q_enc * inv(Qr)` → BVH 오일러 (최대 0.71도 오차)

### json_writer.py 신규 추가
- `decode-json` CLI 커맨드 추가
- SLMBData를 웹 플레이어용 JSON으로 출력
- Type별 Qr 처리: `_get_bvh_quaternion()` 함수

## 8. player_bvh_slmb 구현 (2026-03-26)

위치: `slmb-player/player_bvh_slmb/index.html`

3가지 SLMB 디코딩 출력 모두 재생 가능:
- SLMB JSON: JSON → AnimationClip 빌드 → AnimationMixer
- Roundtrip BVH: BVHLoader (hips만 position 트랙) → AnimationMixer
- Roundtrip glTF: GLTFLoader → AnimationClip 추출 → AnimationMixer

플레이어 BVH 모드에서 position 트랙을 hips만 남기는 것이 중요 (전체 적용 시 아바타 늘어남).

## 9. 다음 단계 - VLibras CASA 번들 재생

파이프라인: CASA(Unity AssetBundle) → vlibras2slmb → .slmb.xz → decode-json → player
핵심: VLibras 84본 → SLMB 46조인트 리타겟팅 + 좌표계 변환
