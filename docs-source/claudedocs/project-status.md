# 프로젝트 현황 (2026-04-08)

다음 세션에서 참조할 수 있는 프로젝트 전체 현황 문서.

## 프로젝트 개요

브라질 수어(Libras) 3D 아바타 플레이어 생태계. ABNT NBR 25606 표준과 VLibras 레거시 포맷을 지원하는 웹 기반 플레이어.

- **배포**: https://sls-brazil-player.vercel.app/
- **GitHub**: https://github.com/hyunia69/sls_brazil_player
- **기술 스택**: Three.js v0.170.0 (CDN), 단일 HTML, Python 변환 도구
- **배포 방식**: Vercel 정적 사이트, Git push 시 자동 배포

---

## 완료된 작업

### 1. ABNT 표준 분석 (완료)
- ABNT NBR 25606 전체 분석 (46조인트 스켈레톤, 268 블렌드셰이프, 양자화 공식)
- SBTVD OG-06 운영 가이드라인 분석
- Annex A~D 전송 방식 분석
- 분석 문서: `docs-source/standards/` 디렉토리

### 2. SLMB 인코더/디코더 (완료)
- BVH → SLMB → BVH/glTF/JSON roundtrip 검증 완료
- Type-2/3 Qr 역변환 버그 수정 완료
- 코드: `tools/slmb_converter/`

### 3. ABNT 플레이어 (완료)
- **BVH Player** (`public/players/bvh/`): BVH 파일 직접 파싱 및 재생
- **SLMB Pipeline Player** (`public/players/slmb/`): JSON/BVH/glTF 3소스 동시 재생 비교
- ABNT 46조인트 avatarModel 로딩, scale 0.01 적용, 본 매핑 정상

### 4. VLibras 플레이어 (부분 완료)
- **VLibras Player** (`public/players/vlibras/`): Padrao/CASA/Icaro 모델 선택, CASA 애니메이션 재생
- **VLibras Player v3** (`public/players/vlibras-v3/`): Three.js 포맷 애니메이션
- **Model Viewer** (`public/players/viewer/`): 5개 모델 인터랙티브 뷰어
- 상체 재생 성공, **하체 좌표계 보정 미완**

### 5. VLibras→SLMB 변환기 (진행중)
- 스켈레톤 매핑 완료 (84본 VLibras → 46조인트 ABNT)
- 블렌드셰이프 매핑 정의
- 코드: `tools/vlibras2slmb/`
- **전체 파이프라인 미완성**

### 6. 프로젝트 통합 (2026-04-08 완료)
- `slmb/`, `vlibras/` 두 개 독립 프로젝트를 단일 구조로 통합
- 아바타 모델 공유 폴더 (`public/avatars/`) 구성
- 애니메이션 데이터 공유 폴더 (`public/animations/`) 구성
- 메인 랜딩 페이지 생성 (5개 플레이어 + 문서 링크)
- Git 저장소 생성, Vercel 배포 완료
- 원본 `slmb/`, `vlibras/` 디렉토리 삭제 (마이그레이션 검증 후)

---

## 현재 상태

| 컴포넌트 | 상태 | 위치 |
|---|---|---|
| SLMB 인코더/디코더 | ✅ 완료 | `tools/slmb_converter/` |
| BVH Player (ABNT) | ✅ 완료 | `public/players/bvh/` |
| SLMB Pipeline Player (ABNT) | ✅ 완료 | `public/players/slmb/` |
| VLibras Player | 🔄 상체 완료, 하체 미완 | `public/players/vlibras/` |
| VLibras Player v3 | 🔄 상체 완료, 하체 미완 | `public/players/vlibras-v3/` |
| Model Viewer | ✅ 완료 | `public/players/viewer/` |
| VLibras→SLMB 변환기 | 🔄 매핑 완료, 파이프라인 미완 | `tools/vlibras2slmb/` |
| 랜딩 페이지 | ✅ 완료 | `public/index.html` |
| 문서 페이지 | ✅ 완료 | `public/docs/` |
| Vercel 배포 | ✅ 완료 | Git push 자동 배포 |

---

## 알려진 이슈

### 1. VLibras 하체 좌표계 보정
- **문제**: Unity 좌표계(LH)와 glTF/Blender 좌표계(RH) 차이로 하체 애니메이션이 부정확
- **원인**: position `[x,y,z]→[x,y,-z]`, quaternion `[x,y,z,w]→[-x,-y,z,w]` 변환이 하체에 완전히 적용되지 않음
- **영향 범위**: `public/players/vlibras/`, `public/players/vlibras-v3/`
- **참고 문서**: `docs-source/claudedocs/technical-findings.md`

### 2. VLibras→SLMB 파이프라인 미완성
- 스켈레톤 매핑(84→46)은 정의됨 (`tools/vlibras2slmb/data/skeleton_map.py`)
- 전체 변환 파이프라인 (VLibras AssetBundle → SLMB .xz) 아직 end-to-end 검증 안됨
- CASA 단어만 테스트됨, 다른 수어 번들 테스트 필요

---

## 다음 작업 (우선순위 순)

### P1: 문장 번역 → 글로스 번들 → 애니메이션 재생 파이프라인 구축
- **목표**: 포르투갈어 문장을 수어로 변환하고 플레이어에서 재생하는 end-to-end 파이프라인
- **파이프라인 흐름**:
  1. 대표 포르투갈어 문장을 VLibras 번역 API로 수어문(글로스 시퀀스) 요청
     - API: `traducao2.vlibras.gov.br/translate`
  2. 수어문에 포함된 각 글로스의 번들 에셋을 VLibras CDN에서 다운로드
     - CDN: `dicionario2.vlibras.gov.br/bundles`
  3. 다운로드한 번들을 파싱하여 애니메이션 데이터로 변환
  4. 변환된 애니메이션을 VLibras 플레이어에 적용하여 재생
- **검증**: 문장 입력 → 수어 애니메이션 연속 재생이 자연스러운지 확인

### P2: SLMB 아바타에 VLibras 애니메이션 적용
- **목표**: ABNT 표준 아바타(46조인트)에서 VLibras CASA 애니메이션 재생
- 스켈레톤 리타겟팅 필요: VLibras 84본 → ABNT 46조인트 매핑 (`tools/vlibras2slmb/data/skeleton_map.py`)
- 변환 흐름: CASA (VLibras) → vlibras2slmb → .slmb.xz → slmb_converter decode → JSON → SLMB Pipeline Player
- 좌표계 변환 포함: Unity LH → glTF RH

### P3: VLibras 하체 좌표계 보정
- `public/players/vlibras/index.html`에서 하체 본의 좌표 변환 로직 수정
- Unity LH → glTF RH 변환을 하체 관절(hip, leg, foot)에 정확히 적용
- 검증: CASA 애니메이션 재생 시 하체 동작이 자연스러운지 확인

---

## 다음 세션 시작 가이드

```
이전 세션에서 브라질 수어(Libras) 플레이어 프로젝트를 진행했다.

프로젝트 현황: docs-source/claudedocs/project-status.md 참조
배포: https://sls-brazil-player.vercel.app/
GitHub: https://github.com/hyunia69/sls_brazil_player

이번 세션에서 할 것:
[여기에 작업 내용 기입]
```

---

## 핵심 파일 참조

| 목적 | 파일 |
|---|---|
| 프로젝트 설정 | `CLAUDE.md` |
| ABNT 아바타 모델 | `public/avatars/abnt/avatarModel/model_external.gltf` |
| VLibras 아바타 | `public/avatars/vlibras/{padrao,casa,icaro}/export/*.glb` |
| CASA 애니메이션 | `public/animations/vlibras/CASA_full.json` |
| ABNT 레퍼런스 BVH | `public/animations/abnt/avatarModel.bvh` |
| 스켈레톤 매핑 | `tools/vlibras2slmb/data/skeleton_map.py` |
| 좌표 변환 유틸 | `tools/vlibras2slmb/math_utils/coordinate.py` |
| 기술 검증 결과 | `docs-source/claudedocs/technical-findings.md` |
