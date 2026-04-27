# Stroke 검출 6 Method

- Method A — Cumulative %  (누적 비율)
  1. 전체 회전 변화량을 100%로 놓고, 처음 12%가 채워지는 지점부터 마지막 12%가 시작되는 지점까지를 stroke로 친다. 간단·예측 가능해서 현재 운영 중인 baseline.
  2. 임계
     1) head 12% / tail 12% (조정 가능)
     2) ±50ms padding
  3. 안전망: stroke 길이가 전체의 40% 미만이면 중심 기준 확장 (MIN_STROKE_RATIO = 0.40)
  4. 약점: prep과 stroke가 비슷한 속도로 이어지면 경계를 잘못 짚는다.

- Method B — Peak-hold window  (속도 임계 첫/마지막)
  1. 가장 빠른 순간의 속도를 peakVel이라 하고, 속도가 peakVel × 45% 이상인 가장 이른 sample부터 가장 늦은 sample까지 전부 stroke로 본다. 빠른 동작이 여러 번 있어도 다 감싸 안는다.
  2. 임계: 속도 ≥ peakVel × 45% (조정 가능)
  3. 약점: 임계를 낮추면 prep까지 빨려 들어가고, 높이면 멈춤(hold) 구간이 잘린다.

- Method C — Rest-pose distance asymmetric + plateau  (차렷 거리 비대칭, 멈춤 끝 인식)
  1. 손이 차렷(t=0 자세)에서 얼마나 멀어졌는지를 restDist라 하고, peak를 기준으로 좌우를 다르게 본다.
  2. strokeStart: peak에서 왼쪽으로 스캔, restDist < maxRest × 30% 지점 다음 (prep 배제)
  3. strokeEnd: peak에서 오른쪽으로 스캔, restDist < maxRest × 90% 지점 직전 (= 다시 내려오기 시작하는 순간)
  4. 수어학적 의미: stroke는 hold(유지)가 끝나는 지점에 종료되어야 한다는 직관. recovery 차렷 왕복을 가장 깔끔하게 잘라낸다.

- Method D — Peak drop centered  (피크 좌우 속도 drop)
  1. 가장 빠른 순간(peak)을 중심으로 좌우 스캔, 속도가 peakVel × (1 − 40%) = 60% 아래로 떨어지는 지점에서 자른다. 격렬한 burst만 콕 집어내는 좁은 방식.
  2. 임계: drop 40% (조정 가능)
  3. 약점: hold 구간이나 multi-peak를 잘라내서 결과가 너무 짧다.

- Method E — Movement-Hold model (Liddell & Johnson 1989) ⭐ PR 신규
  1. 수어 음운론의 M-H 모델을 직접 코드화: 수어의 의미 단위는 "움직임"이 아니라 그 사이에 끼어 있는 "유지(hold) 자세"에 있다는 관점.
  2. hold 조건 (3개 동시)
     1) 속도 ≤ peakVel × 15%
     2) restDist ≥ maxRest × 80%
     3) 100ms 이상 지속
  3. stroke: 첫 hold 시작 − 50ms ~ 마지막 hold 끝 + 50ms
  4. fallback: hold가 0개면 methodA(0.12, 0.12) — BOM 같은 단일 ballistic 동작 호환
  5. 강점: hold-dominant 글로스(TER, CASA, FAMILIA)에서 의미적 경계를 정확히 잡는다.

- Method G — Bimanual separated R/L union  (양손 분리 후 합집합) ⭐ PR 신규
  1. 지금까지 5개는 양손을 합쳐 하나의 motion profile로 봤지만, 오른손(STROKE_BONES_R 3본) / 왼손(STROKE_BONES_L 3본)을 분리해서 각각 Method A를 적용한 뒤 union한다.
  2. strokeStart = min(R, L), strokeEnd = max(R, L)
  3. 단측 fallback: 한쪽 손 motion이 거의 0이면 운동측만 사용
  4. 강점: 한 손이 멈췄는데 다른 손이 계속 움직이는 양손 비대칭 글로스(FAMILIA, AGUA)에서 한쪽이 일찍 잘리는 문제를 직접 해소.
  5. 참고: 이 방법은 다른 method와 직교 — 이론상 R에 E, L에 A를 거는 hybrid도 가능.
