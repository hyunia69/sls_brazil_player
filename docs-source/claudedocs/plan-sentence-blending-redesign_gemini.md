# 수어 문장 블렌딩 로직 전면 재검토 계획 리뷰

**문서:** `docs-source/claudedocs/plan-sentence-blending-redesign.md`
**리뷰어:** Gemini CLI
**날짜:** 2026-04-20

## 1. 계획의 타당성 및 강점 (Pros)

*   **정량적 메트릭 도입 (핵심 강점):** "어색하다"는 정성적 느낌을 **Jerk RMS(부드러움), Hold Preservation(의미 보존)** 등의 수치로 변환하여 객관적 의사결정 근거를 마련한 점이 매우 탁월합니다.
*   **학술적 근거 (M-H Model):** 단순 제스처 단위를 넘어 수어학의 핵심인 **Movement-Hold 모델**을 도입하여 품질 한계를 돌파하려는 방향이 올바릅니다.
*   **단계적 리스크 관리:** Production(`sentence/`)에는 저위험(상수 조정)만 선반영하고, 구조 변경은 실험대(`sentence-stroke-test/`)에서 검증 후 이식하는 전략이 실무적으로 안정적입니다.
*   **사용자 중심 평가:** 기술 지표에 매몰되지 않고 **Deaf User 평가(P6.5)**를 최종 게이트로 둔 점은 실제 사용성을 보장하는 핵심 요소입니다.

## 2. 잠재적 문제점 및 우려사항 (Cons)

*   **SQUAD 구현 복잡도:** Three.js `AnimationMixer`의 기본 `slerp`를 우회하여 커스텀 `SQUAD` 보간을 주입하는 과정에서 **성능(60fps) 유지**나 **본(Bone) 변형 오버라이드** 간의 기술적 충돌 가능성이 있습니다.
*   **M-H 검출의 신뢰도:** 원본 데이터에 Phase Marker가 없는 상태에서 속도와 정지만으로 Hold를 검출할 때, **모션 노이즈**로 인해 Hold 구간을 놓치거나 잘못 식별할 위험이 있습니다.
*   **확장성(Scalability):** 27개 글로스에서 도출된 최적 파라미터가 100개 이상의 대규모 글로스셋에서도 일관된 품질을 보장할지에 대한 조기 확인이 필요합니다.

## 3. 개선 제언 및 보안책 (Suggestions)

*   **SQUAD 대안 검토:** SQUAD 구현이 지나치게 무겁거나 불안정할 경우, 보간 계수(Alpha)에 **Cubic Bezier나 Easing 함수**를 적용한 'Ease-in/out Slerp'만으로도 Jerk RMS를 상당히 개선할 수 있습니다.
*   **모션 데이터 Smoothing:** `computeMotionProfile` 실행 전, 데이터에 **Low-pass filter**를 적용하여 미세한 떨림을 제거하면 Method E(M-H)의 검출 안정성이 비약적으로 향상됩니다.
*   **Transition Profile 메타데이터화:** P5.2 실험 결과를 바탕으로 각 글로스의 종단 특성(Static 여부 등)을 **JSON DB화**하여 런타임 계산 부하를 줄이고 정확도를 높이는 방식을 권장합니다.
*   **디버깅 시각화 강화:** `sentence-stroke-test` 차트에서 **Jerk Spike 지점을 클릭하면 해당 타임라인으로 점프**하는 기능을 추가하여 문제 구간 분석 속도를 높일 수 있습니다.

## 4. 최종 의견 및 실행 권고

본 계획은 **"데이터 기반의 점진적 개선(Data-driven Iterative Improvement)"**의 정석을 따르고 있으며, 매우 견고합니다.

**추천 실행 순서:**
1.  **Metric Baseline 확보 (최우선):** Jerk RMS / Hold Preservation 메트릭을 즉시 구현하여 현재(Method A)의 수치를 확정하십시오.
2.  **Low-risk 개선 적용:** `FADE_MIN` 0.2s 상향을 Production에 반영하여 즉각적인 체감 품질을 개선하십시오.
3.  **Method E 실험:** 노이즈 필터링이 포함된 M-H 검출 로직을 실험대에서 검증하십시오.
