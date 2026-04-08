# 다음 세션 입력 프롬프트

아래 프롬프트를 다음 세션 시작 시 입력하세요.

---

```
이전 세션에서 브라질 수어(Libras) SLMB 플레이어 프로젝트를 진행했다.

완료된 것:
1. ABNT NBR 25606 표준 분석 완료
2. avatarModel.bvh(레퍼런스 BVH) + model_external.gltf(Samsung MyEmoji 아바타) 분석/검증 완료
3. slmb_converter의 BVH→SLMB→BVH/glTF/JSON roundtrip 검증 및 버그 수정 완료 (Type-2/3 Qr 역변환)
4. player_bvh (BVH 전용 플레이어) 구현 완료
5. player_bvh_slmb (JSON/BVH/glTF 3소스 플레이어) 구현 완료 - 3가지 모두 정상 재생 확인

이번 세션에서 할 것:
VLibras에서 제공하는 CASA(집) 수어 애니메이션 번들을 재생하는 것이 목표다.

CASA 데이터 위치: data/CASA/ (Unity AssetBundle + JSON 추출본)
변환기: slmb-player/vlibras2slmb/ (VLibras 84본 → SLMB 46조인트 리타겟팅)
플레이어: slmb-player/player_bvh_slmb/

파이프라인:
CASA (VLibras AnimationClip) → vlibras2slmb convert → .slmb.xz → slmb_converter decode-json → .json → player_bvh_slmb 재생

우선 vlibras2slmb로 CASA를 변환할 수 있는지 확인하고, 변환 후 player에서 재생해줘.
CASA_animation.json이나 CASA_full.json을 입력으로 사용할 수 있는지도 확인해라.
```
