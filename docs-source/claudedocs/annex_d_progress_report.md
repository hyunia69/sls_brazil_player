# ABNT NBR 25606 Annex D - Sign Language Motion Stream 개발 진행 보고서

**작성일**: 2026-04-06  
**프로젝트**: Brazil Sign Language (Libras) 3D Avatar Player  
**표준**: ABNT NBR 25606:2025 - TV 3.0 Closed Signing  
**범위**: Annex D - Sign Language Motion Stream (SLMB) 파이프라인 구현

---

## 1. 프로젝트 개요

본 프로젝트는 브라질 디지털 TV 3.0 표준(ABNT NBR 25606:2025)의 Annex D에 정의된 수어 모션 스트림(Sign Language Motion Stream) 재생 시스템을 구현한다. 브라질 수어(Libras)를 3D 아바타로 렌더링하여 청각장애인의 방송 접근성을 보장하는 Closed Signing 기술이다.

**핵심 목표:**

- SLMB(Sign Language Motion Bundle) 바이너리 포맷의 인코딩/디코딩 구현
- BVH 원본 모션에서 SLMB 압축 바이너리까지의 변환 파이프라인 구축
- SLMB에서 JSON, BVH, glTF 2.0 포맷으로의 역변환 구현
- Three.js 기반 웹 플레이어에서 ABNT 공식 아바타를 통한 모션 재생 검증

---

## 2. 파이프라인 구성

### 전체 흐름

```
BVH (원본 모션) → SLMB Encoder → .slmb.xz (압축 바이너리)
                                       |
                              SLMB Decoder → JSON / BVH / glTF
                                       |
                              Three.js Player → 아바타 렌더링
```

### SLMB Converter (Python, 총 2,845줄, 외부 의존성 없음)

| 모듈 | 파일명 | 줄 수 | 역할 |
|-------|--------|-------|------|
| 상수 정의 | constants.py | 432 | ABNT Table D.9 조인트/블렌드셰이프 정의 |
| 인코더 | slmb_encoder.py | 387 | BVH to SLMB 바이너리 인코딩 + LZMA/xz 압축 |
| 디코더 | slmb_decoder.py | 329 | SLMB to BodyMotionBlock + FaceMotionBlock 파싱 |
| BVH 파서 | bvh_parser.py | 269 | BVH 텍스트 포맷 파서 |
| BVH 출력 | bvh_writer.py | 166 | SLMB to BVH 재구성 |
| glTF 출력 | gltf_writer.py | 304 | SLMB to glTF 2.0 애니메이션 출력 |
| JSON 출력 | json_writer.py | 111 | SLMB to JSON 웹 플레이어 포맷 출력 |
| 수학 유틸 | math_utils.py | 316 | 쿼터니언/오일러 변환, 좌표 변환 |
| 얼굴 데이터 | face_data.py | 256 | 블렌드셰이프 데이터 생성 |
| CLI | main.py | 266 | 명령행 인터페이스 |

**설계 원칙:** Python 표준 라이브러리만 사용하며 외부 의존성이 전혀 없다. `struct`, `lzma`, `json`, `math` 등 내장 모듈만으로 전체 파이프라인을 구현했다.

---

## 3. SLMB 바이너리 포맷 (ABNT Annex D)

### 파일 구조

```
.slmb.xz → LZMA 해제 → MotionBundle
  +-- SLMB_TITLE_KEY (0x534C4D42 = "SLMB")
  +-- BodyMotionBlock (46 조인트 x N 프레임)
  +-- FaceMotionBlock (268 블렌드셰이프)
```

### 46 조인트 구성 (Table D.9)

| 타입 | 개수 | 인코딩 방식 | 비트/프레임 | 용도 |
|------|------|------------|-----------|------|
| Type-0 | 1 | Translation(uint16x3) + Quaternion(int16x3) | 144 | 루트(hips_JNT) |
| Type-1 | 15 | Quaternion(int16x3) | 48 | 주요 골격 |
| Type-2 | 8 | Euler 3축 패킹(10+10+12 bits) | 32 | 손바닥 |
| Type-3 | 20 | Z축 Euler(8 bits) | 8 | 손가락 |
| Type-4 | 2 | X/Y Euler(8+8 bits) | 16 | 눈 |

**총 46 조인트**: 1(Type-0) + 15(Type-1) + 8(Type-2) + 20(Type-3) + 2(Type-4)

### 양자화 정밀도

| 데이터 유형 | 범위 | 양자화 단위 | 정밀도 |
|------------|------|-----------|--------|
| Translation | [-0.5m, 0.5m] | uint16 | ±0.015mm |
| Quaternion (Type-0/1) | [-1, 1] | int16 | ±0.000061 |
| Type-2 Euler | 3축 패킹(10+10+12 bits) | 혼합 | ±0.176° |
| Type-3 Euler | Z축 단일(8 bits) | uint8 | ±1.41° |

이 양자화 설계는 방송 스트리밍 대역폭을 최소화하면서도 수어 인식에 충분한 정밀도를 유지한다. 손가락 관절(Type-3)의 낮은 정밀도(±1.41°)는 굴곡/신전 단일 축만 사용하므로 시각적 품질에 영향이 없다.

---

## 4. 사용 데이터

### 레퍼런스 애니메이션

| 항목 | 내용 |
|------|------|
| 파일 | `data/avatarModel.bvh` |
| 프레임 수 | 142 (30fps, 4.73초) |
| 출처 | SBTVD OG-06 운영 가이드라인 참조 애니메이션 |
| 조인트 수 | 46 (ABNT NBR 25606 Table D.9 준수) |

### 라운드트립 검증 파일 (SLMB 파이프라인 생성)

| 파일 | 크기 | 설명 |
|------|------|------|
| `avatarModel.slmb.xz` | 10 KB | LZMA/xz 압축 SLMB 바이너리 |
| `avatarModel_roundtrip.bvh` | 375 KB | SLMB에서 복원한 BVH |
| `avatarModel_roundtrip.gltf` + `.bin` | 35 KB + 164 KB | SLMB에서 생성한 glTF 2.0 |
| `avatarModel_roundtrip_slmb.json` | 267 KB | 웹 플레이어용 JSON |

**압축 성능:**

- 원본 합계: 약 545 KB (BVH 텍스트 기준)
- 압축 결과: 10 KB (.slmb.xz)
- **압축률: 18배** (약 5.5%)
- **방송 비트레이트: 약 17 kbps** (30fps 기준, 실시간 스트리밍 가능)

---

## 5. 아바타 모델

### Samsung MyEmoji (ABNT 공식 레퍼런스 아바타)

| 항목 | 내용 |
|------|------|
| 경로 | `data/avatarModel/model_external.gltf` |
| 포맷 | glTF 2.0 (.gltf + .bin + 29 PNG 텍스처) |
| 소스 | Samsung MyEmoji v3.1 |
| 스켈레톤 | ABNT 46 조인트와 100% 명칭 매칭 |
| 블렌드셰이프 | ABNT Table D.11과 완전 호환 (268개) |

**스케일 이슈 및 해결:**

Samsung MyEmoji 모델의 `RootNode`에 `scale=[100, 100, 100]`이 설정되어 있다. 이로 인해 Three.js에서 로드 시 아바타가 100배 크기로 렌더링되는 문제가 발생한다.

- **해결**: Three.js에서 `model.scale.set(0.01, 0.01, 0.01)` 적용
- **검증**: BVH offset 값(cm 단위) x 100 = glTF translation 값(m 단위) 정확 대응 확인

---

## 6. 플레이어 구현

### player_bvh (BVH 전용 플레이어)

| 항목 | 내용 |
|------|------|
| 경로 | `slmb-player/player_bvh/index.html` |
| 기능 | 드래그앤드롭 BVH 로딩, 스켈레톤 시각화, 재생 제어 |
| 렌더링 | Three.js v0.170.0 (WebGL) |
| 구조 | 단일 HTML 파일 |
| 상태 | **완료** |

### player_bvh_slmb (SLMB 파이프라인 검증 플레이어)

| 항목 | 내용 |
|------|------|
| 경로 | `slmb-player/player_bvh_slmb/index.html` |
| 입력 소스 | SLMB JSON / Roundtrip BVH / Roundtrip glTF (3개 동시) |
| 아바타 | Samsung MyEmoji glTF 자동 로드 |
| 구조 | 단일 HTML 파일 |
| 상태 | **완료 및 검증** |

**UI 기능:**

- 재생/정지/속도 조절
- 타임라인 스크러빙
- 스켈레톤 오버레이 토글
- 카메라 리셋
- 3개 소스 간 전환

**검증 결과:** 3개 입력 소스(JSON, BVH, glTF) 모두 동일 아바타에서 동일 모션을 렌더링함을 확인했다. 이는 SLMB 인코딩/디코딩 파이프라인의 무결성을 입증한다.

---

## 7. 핵심 기술 이슈 해결

### Bug #1: Type-2/3 Qr 역변환 누락

| 항목 | 내용 |
|------|------|
| 증상 | 오른손 조인트 약 180° 오회전 |
| 원인 | 인코더에서 `Q_enc = Q_bvh x Qr` 적용 후, 디코더에서 `Qr` inverse 미적용 |
| 해결 | 디코더에 `Q_bvh = Q_enc x inv(Qr)` 역변환 적용 |

**오차 개선:**

| 지표 | 수정 전 | 수정 후 |
|------|---------|---------|
| 최대 오차 | 180.53° | 0.71° |
| 평균 오차 | 18.65° | 0.13° |

### Bug #2: glTF RootNode Scale 100배

| 항목 | 내용 |
|------|------|
| 증상 | 아바타가 100배 크기로 렌더링 |
| 원인 | Samsung MyEmoji `RootNode` scale=[100, 100, 100] |
| 해결 | Three.js에서 `scale.set(0.01, 0.01, 0.01)` 적용 |

---

## 8. 참조 표준 및 웹사이트

### ABNT 표준

| 표준 | 설명 |
|------|------|
| ABNT NBR 25606:2025 | TV 3.0 Closed Signing (핵심 표준) |
| ABNT NBR 25601~25609 | TV 3.0 표준 프레임워크 |
| SBTVD OG-06 | 운영 가이드라인 (아바타 모델 스펙, 참조 구현) |

### 국제 표준

| 표준 | 설명 |
|------|------|
| ISO/IEC 14496-30:2018 | ISOBMFF Timed Text |
| ISO/IEC 23000-19:2024 | CMAF Streaming |
| IEEE 754 | 부동소수점 연산 |
| W3C IMSC1:2020 | TTML 프로파일 |
| RFC 5646 | 언어 태그 |

### 웹 기술

| 기술 | URL | 용도 |
|------|-----|------|
| Three.js v0.170.0 | https://threejs.org/ | 3D 렌더링 엔진 |
| glTF 2.0 | https://www.khronos.org/gltf/ | 3D 모델 포맷 |
| CDN | cdn.jsdelivr.net/npm/three@0.170.0 | Three.js 배포 |

### 참조 사이트

| 사이트 | URL | 설명 |
|--------|-----|------|
| SBTVD Forum | https://forumsbtvd.org.br/ | 브라질 디지털 TV 표준 기구 |
| VLibras | https://vlibras.gov.br/ | 브라질 수어 번역 서비스 (참조) |
| VLibras 번역 API | traducao2.vlibras.gov.br/translate | 수어 번역 엔드포인트 |
| VLibras 사전 CDN | dicionario2.vlibras.gov.br/bundles | 수어 모션 번들 CDN |

---

## 9. 실행 방법

### 로컬 서버 실행

```bash
cd D:/lg/work/SLS/brazil/code/player
python -m http.server 8080
```

### 플레이어 접속

| 플레이어 | URL |
|---------|-----|
| BVH 전용 플레이어 | http://localhost:8080/slmb-player/player_bvh/ |
| SLMB 검증 플레이어 | http://localhost:8080/slmb-player/player_bvh_slmb/ |

### SLMB 변환기 CLI

```bash
# BVH to SLMB 인코딩
python -m slmb_converter encode data/avatarModel.bvh data/avatarModel.slmb.xz

# 라운드트립 검증 (BVH → SLMB → BVH/glTF/JSON)
python -m slmb_converter roundtrip data/avatarModel.bvh

# SLMB 파일 정보 조회
python -m slmb_converter info data/avatarModel.slmb.xz
```

---

## 10. 현재 상태 요약

| 구성 요소 | 상태 | 설명 |
|-----------|------|------|
| SLMB Encoder/Decoder | 완료 | 인코딩/디코딩/라운드트립 전체 검증 |
| BVH Parser/Writer | 완료 | 양자화 손실 포함 양방향 변환 |
| glTF Writer | 완료 | glTF 2.0 애니메이션 출력 |
| JSON Writer | 완료 | 웹 플레이어용 JSON 출력 |
| player_bvh | 완료 | BVH 전용 플레이어 |
| player_bvh_slmb | 완료 | 3소스 파이프라인 검증 플레이어 |
| 얼굴 블렌드셰이프 | 매핑 완료 | 268개 ID 정의 완료, 실시간 재생 미구현 |

---

## 11. 향후 과제

1. **TTML/IMSC1 시간 동기화 계층 구현** - 방송 스트리밍 환경에서 수어 모션과 프로그램 타임라인 간 정밀 동기화
2. **DASH/CMAF 전송 계층 연동** - ISO/IEC 23000-19 기반 적응형 스트리밍 전송 구현
3. **얼굴 블렌드셰이프 실시간 재생 구현** - 268개 블렌드셰이프 ID 매핑은 완료, Three.js 모프타겟 렌더링 연동 필요
4. **VLibras to SLMB 변환 파이프라인 완성** - VLibras AssetBundle 모션 데이터를 ABNT 표준 SLMB 포맷으로 변환
5. **다양한 수어 단어/문장 테스트** - 현재 단일 레퍼런스 애니메이션(avatarModel.bvh) 외 추가 수어 데이터 검증

---

*본 보고서는 ABNT NBR 25606:2025 Annex D 구현 프로젝트의 기술적 진행 상황을 기록한다.*
