# 메인 캔버스 vs. VLibras 위젯 — 아바타 손잡이(chirality) 차이 분석

작성일: 2026-04-14
관련 컴포넌트: `public/players/sentence/index.html`, `tools/vlibras2slmb/batch/precompute_threejs.py`, VLibras 공식 위젯 (`vlibras.gov.br/app/vlibras-plugin.js`)
관련 작업: `1b89be4` (VLibras 공식 위젯 통합)

## 요약

Sentence Player에 VLibras 공식 위젯을 통합한 뒤 같은 문장을 동시 재생시키면 두 아바타의 주 조작 손이 서로 반대로 보인다.

| | 메인 캔버스 (Sentence Player) | VLibras 위젯 (모든 공식 채널) |
|---|---|---|
| signer의 dominant hand | **오른손** | **왼손** |
| LIBRAS 학술 문서화 컨벤션 (right hand 기술) | 부합 | 미부합 |
| LIBRAS 자체 valid 여부 (양손 자유 원칙) | valid | valid |
| 인구통계 dominance (≈90% 오른손잡이) | 부합 | 미부합 |
| 결정 출처 | precompute의 X-mirror가 우연히 학술 컨벤션과 일치 | VLibras 공식 팀의 일관된 베이크 정책 |

**핵심 결론**: 두 표현 모두 LIBRAS 측면에서 valid. 어느 쪽도 "오류"가 아니다. 메인이 더 "전형적"이고 위젯이 모든 공식 VLibras 채널에서 일관된 형태다. 우리 메인 코드의 결함이 아니며, 위젯 측에 dominant-hand 옵션이 없으므로 위젯도 우리가 손댈 수 없다. 별도 수정 작업 없음.

---

## 1. 관찰 사실

- **메인**: `public/players/sentence/index.html`, Three.js r170, Padrao/CASA/Icaro GLB + 사전 변환 `.threejs.json` 번들 큐잉 재생. 카메라 `(0,1.5,4)→(0,1,0)`, 기본 up, 모델에 `scale`/`rotation` 변경 없음(센터링만). **씬 레벨 chirality 변환 없음**.
- **위젯**: Unity WebGL, `vlibras.gov.br/app/vlibras-plugin.js`. sentence 페이지에서는 `avatar` 미지정(기본 랜덤 선택).
- 동일 글로스(`Casa`, `OLA`, `Sim bom dia` 등)에서 메인은 signer 오른팔로, 위젯은 signer 왼팔로 같은 동작 수행.
- **gov.br 공식 사이트**(`https://www.gov.br/governodigital/pt-br/acessibilidade-e-usuario/vlibras`)의 위젯도 동일하게 왼손 사용. 즉 random pick의 변동성이 아니라 VLibras 공식 자산 자체가 왼손으로 베이크돼 있음.

---

## 2. LIBRAS 손잡이 컨벤션

LIBRAS의 dominant hand 관행을 학술/공식 자료로 검토한 결과:

### 2.1 LIBRAS 자체 — 양손 자유 원칙

`libras.com.br` "Os Cinco Parâmetros da Libras":
> "Cada configuração pode ser feita pela mão dominante (mão direita para os destros, mão esquerda para os canhotos), ou pelas duas mãos dependendo do sinal."

→ 한 손 사인은 **signer 본인의 dominance에 따른다**. 단일 표준 없음. 오른손잡이는 오른손으로, 왼손잡이는 왼손으로 한다.

### 2.2 학술 문서화 컨벤션 — 오른손이 기술 표준

웹 검색으로 확인:
> "The signs in Libras are the same whether one performs using the right or the left hand, although the literature specifies the use of the right hand when describing a sign."

→ 사인 자체는 양손 모두 valid이지만 **학술 논문/사전·교재는 오른손으로 기술하는 것이 표준**. 즉 "right hand"는 "language convention"이 아닌 "documentation convention".

### 2.3 수어 학습 연구 — right/left가 아니라 dominant/non-dominant

Frontiers in Psychology 2018 "Learning an Embodied Visual Language: Four Imitation Strategies Available to Sign Learners":
> "Children must learn that signs are not specified for the right or left hand but for dominant and non-dominant. Importantly, learners must monitor the handedness of the signer and compare it to their own; if hand dominance is discordant, learners may correctly deploy the mirroring strategy."

→ 사인은 right/left가 아니라 dominant/non-dominant로 명시되며, 학습자는 자기 dominance에 맞게 mirroring strategy로 따라할 수 있다. lateral movement가 있는 사인의 mirroring은 movement reversal 오류 가능.

### 2.4 결론 — 메인은 학술 컨벤션, 위젯은 비표준 컨벤션

두 표현 모두 LIBRAS 측면에서 valid. 다만 학술/문서화/인구통계 다수 기준으로는 **메인이 더 전형적**이다. 위젯의 왼손 dominance는 LIBRAS 언어학적 오류는 아니지만 학술 컨벤션과 어긋나 있다.

---

## 3. 메인 캔버스 chirality 추적 (코드 레벨)

### 3.1 `precompute_threejs.py` 레거시 retarget의 X-축 미러

`tools/vlibras2slmb/batch/precompute_threejs.py:_clip_to_threejs_legacy()` (line 424-536). 이 함수는 Unity AssetBundle → Three.js JSON 사전 변환의 기본 경로(`--legacy` 기본).

- **line 494-495**: body bone 회전에 `yz sign flip`:
  ```python
  for qv in curve.values:  # qv = [x, y, z, w] raw Unity
      flat.extend((qv[0], -qv[1], -qv[2], qv[3]))  # yz sign flip
  ```
  이 변환 `(x, y, z, w) → (x, -y, -z, w)`은 수학적으로 **YZ 평면 반사 = X-축 미러**다. 회전 관점에서는 "로컬 X 축에 대한 회전 방향 반사" — 결과적으로 signing chirality가 반전된다.

- **line 478-490**: 7개 helper bone (`BnBacia001`, `BnMaoOrientR/L`, `BnPolyVR/L`, `ik_FKR/L`)은 Unity curve 대신 Icaro bind pose 값으로 정적 override.

- **line 508-522**: 모든 rotation track bone에 대해 position을 Icaro bind pose 로컬 position 그대로 2-keyframe static으로 고정. **좌표 변환 미적용**. Unity position curve는 사용하지 않음.

- **docstring (line 428-429, 중요)**:
  > "The reference file `public/animations/vlibras/CASA_threejs.json` was produced by a three-step pipeline that we replicate here"

  즉 이 변환은 Unity 공식 LH→RH 변환이 아니라 **과거 누군가가 만든 X-mirror 관례를 역공학해 재현한 것**. P1 Playwright 검증(≤6mm bone delta)도 이 레거시 reference와의 일치를 본 것이지 위젯 Unity-native 출력과의 일치를 본 게 아니다.

### 3.2 `coordinate.py`는 다른 변환을 정의하지만 호출되지 않는다

`tools/vlibras2slmb/math_utils/coordinate.py`:
- `unity_quat_to_abnt(w,x,y,z) → (w,-x,y,-z)` (line 38-55): `x`와 `z` imaginary 반전 = XZ 평면 반사.
- `unity_position_to_abnt(x,y,z) → (-x,y,-z)` (line 81-95): 180° Y 회전과 동등.

**precompute_threejs.py는 이 함수들을 import/호출하지 않는다.** 두 개의 서로 다른 Unity→glTF 관례가 레포 안에 공존하며 실제 사용되는 것은 precompute의 `(x,-y,-z,w)`다.

### 3.3 Icaro bind pose의 R/L bone 배치 — X-mirror와 정합

`tools/vlibras2slmb/data/icaro_bind_pose.json`:

| bone | x | y | z |
|---|---|---|---|
| `BnMaoOrientR` | **-8.498** | 2.669 | -0.244 |
| `BnMaoOrientL` | **+8.498** | 2.669 | -0.244 |
| `ik_FKR` | **-5.466** | 2.669 | -0.261 |
| `ik_FKL` | **+5.466** | 2.669 | -0.261 |
| `BnPolyVR` | **-3.376** | 2.724 | -3.394 |
| `BnPolyVL` | **+3.376** | 2.724 | -3.394 |

모든 "R" bone이 `x < 0`, "L" bone이 `x > 0`. **Icaro 스켈레톤 자체가 Unity→glTF 변환 과정에서 이미 X-축으로 mirror된 구조**다. precompute의 회전 미러와 축 방향이 정합해서, "Unity → (X-mirror 1회) → glTF"의 self-consistent한 변환을 형성한다. 그래서 legacy reference와의 bone-delta 검증은 통과한다.

### 3.4 `buildClipFromJson` + 모델 로딩 — 변환 추가 없음

`public/players/sentence/index.html:342-359`에서 JSON 값을 그대로 `THREE.QuaternionKeyframeTrack` / `VectorKeyframeTrack`에 전달한다. 모델 로딩(line 652-711)은 bounding-box 기준 센터링만 하고 `scale`/`rotation` 미설정. → **씬/런타임 레벨에서 chirality를 뒤집을 수 있는 지점 없음**. 모든 chirality 결정은 사전 변환된 bundle 데이터에 있다.

### 3.5 정합성 종합

```
Unity raw clip → [precompute X-mirror] → Three.js JSON
                                              ↓ 적용
                          Icaro skeleton (이미 X-mirror된 구조)
                                              ↓
                          메인 캔버스: signer 오른손
```

precompute의 X-mirror가 Icaro 스켈레톤의 X-mirror와 self-consistent하게 결합돼 LIBRAS 학술 컨벤션의 오른손 dominance를 만들어낸다. 의도였는지 우연이었는지는 레거시 코드 작성자만 알 수 있으나, 결과적으로는 가장 전형적인 LIBRAS 표현이 된다.

---

## 4. VLibras 위젯 조사 — dominant-hand 옵션 부재

### 4.1 위젯 생성자 옵션

`vlibras-portal/app/index.html:202-208`의 공식 포털 위젯 생성 예:
```js
new window.VLibras.Widget({
  rootPath: '',
  personalization: 'https://vlibras.gov.br/config/configs.json',
  opacity: 1,
  position: 'R',
  avatar: 'random'
});
```

가능한 옵션은 `rootPath`, `personalization`, `opacity`, `position`, `avatar`. **handedness 옵션 없음.**

### 4.2 personalization config

`https://vlibras.gov.br/config/configs.json` (실측):
```json
{
  "calca":"#0E0F18", "camisa":"#1C204F", "cabelo":"#000000",
  "avatar":"random", "corpo":"#C18471", "iris":"#000000",
  "olhos":"#FFFFFF", "sombrancelhas":"#000000", "pos":"center",
  "logo":"https://vlibras.gov.br/config/img/logo-lavid.png"
}
```

색상 + 아바타 + 위치만. **handedness 필드 없음**.

### 4.3 VLibras Widget 6.0.0 공식 docs

`vlibras.gov.br/doc/widget/functionalities/avatarchange.html`에 따르면:

> "Atualmente o VLibras possui dois avatares intérpretes (Ícaro e Hozana). No widget a mudança pode ser feita clicando no botão com o ícone do avatar, localizado no canto superior esquerdo da janela da ferramenta."

Widget 6.0.0의 전체 기능 목록: 텍스트 번역, 재생/일시정지, 속도 선택, 자막, 아바타 변경, 위치, 투명도, 지역 선택, 사전, 평가/리뷰, 아바타 개인화. **dominant-hand 토글은 없다.**

### 4.4 `vlibras-plugin.chunk.js` 정적 분석

`vlibras-portal/app/vlibras-plugin.chunk.js`(minified) 그렙: `dominant`, `canhoto`, `destro`, `mirror`, `reflect`, `flipX`, `swap`, `leftHand`, `rightHand` 모두 무결과. minified라 키워드 검출 한계는 있지만, 표준 영문/포어 키워드가 전혀 잡히지 않는 것은 강한 부정 신호.

### 4.5 결론

위젯은 Unity 아바타에 베이크된 chirality를 그대로 재생하며, **런타임 옵션으로 뒤집을 수 없다**. 위젯 측에서 chirality를 수정할 경로는 존재하지 않는다.

---

## 5. 왜 VLibras 공식 위젯은 왼손 dominance인가 — 가설

### 가설 A (가장 유력): 베이크 과정의 결과
Unity로 아바타를 import하거나 Blender→Unity 워크플로우에서 X-mirror가 한 번 적용됐고 그 상태가 공식 자산으로 굳어짐. 디자인 의도라기보단 **파이프라인 부산물**일 가능성.

- **근거**:
  - 두 아바타(Ícaro, Hozana) 모두 왼손이라면 캐릭터별 디자인이 아니라 공통 베이스 스켈레톤의 베이크 정책 때문일 가능성이 크다.
  - 우리 메인 캔버스는 이 X-mirror된 Unity 자산에 precompute에서 다시 X-mirror를 적용 → double mirror = 원래 right-handed Unity 데이터를 복원한 효과 → LIBRAS 학술 컨벤션과 일치.
- **검증 방법**: sentence 페이지 widget config에 `avatar: 'icaro'`, `'hozana'` 각각 설정해서 두 아바타가 같은 손을 쓰는지 확인. 같다면 가설 A 강화.

### 가설 B (약함): viewer-mirror 학습 친화 디자인
학습자가 따라할 때 viewer 자신의 오른손이 화면 오른쪽에 보이게 거울상으로 표시. 일반적으로 셀카 비디오에서 발생하지 컴퓨터 생성 아바타에선 의도적 mirror 적용이 필요하며, VLibras 공식 docs에 mirror 모드 언급이 없으므로 가설 약함.

### 가설 C (약함): 모델러/디자이너가 왼손잡이
아바타 모델링 단계에서 dominant pose를 자기 기준으로 잡았고 그게 굳어짐. 가능하지만 1차 자료 없이는 검증 불가.

### 가설 D (배제): random pick 부작용
사용자 보고로 공식 사이트도 동일하게 왼손이므로 random pick 변동성과 무관. Ícaro·Hozana 둘 다 왼손이거나, random이 사실상 결정적.

---

## 6. 평가 기준별 어느 쪽이 "더 옳은가"

| 기준 | 더 옳은 쪽 |
|---|---|
| 학술/문서화 표준 | 메인 (오른손) |
| VLibras 공식 채널 일관성 | 위젯 (왼손) |
| 인구통계학적 dominance | 메인 (대부분 오른손잡이) |
| LIBRAS 언어학적 valid | 동등 |
| 수어 학습 친화성 | 학습자 dominance에 따라 |

---

## 7. 결론과 권장 사항

1. **수정 작업 없음.** 메인은 학술 컨벤션에 부합하고 위젯은 우리 통제 밖이므로, 양쪽 모두 그대로 두는 것이 정답.
2. **사용자 안내 (선택)**: sentence 페이지 UI에 한 줄 안내를 넣어 "메인 = signer 오른손, 위젯 = signer 왼손이지만 둘 다 LIBRAS valid" 정도를 표시할 수 있음. 필수 아님.
3. **향후 조사**:
   - **가설 A 검증**: `avatar: 'icaro'` vs `'hozana'` 시도해서 두 아바타가 같은 손인지 분류.
   - **VLibras 다른 클라이언트** (desktop 앱, Android 앱)에 dominant-hand 토글이 있는지 확인. 위젯이 가장 제약이 많은 클라이언트일 수 있음.
   - **VLibras/LAVID/UFPB 학술 자료** 검색: 아바타 베이크 시점에 X-mirror가 의도적이었는지 부산물이었는지 1차 자료 확인.
   - **`precompute_threejs.py` docstring 보강**: "이 X-mirror가 결과적으로 학술 컨벤션 dominance를 만든다"는 분석 노트를 추가해서 P2 (VLibras→SLMB 리타겟팅) 작업자가 헷갈리지 않게 함.

---

## 참고 자료

### 코드
- `public/players/sentence/index.html:342-359, 652-711, 1044-1048` — 씬 설정·모델 로딩·위젯 임베드
- `tools/vlibras2slmb/batch/precompute_threejs.py:424-536` — 레거시 retarget 함수
- `tools/vlibras2slmb/math_utils/coordinate.py:38-95` — 사용되지 않는 표준 변환 함수
- `tools/vlibras2slmb/data/icaro_bind_pose.json` — Icaro 스켈레톤 bind pose

### 외부 자료
- VLibras Widget 6.0.0 공식 docs: https://vlibras.gov.br/doc/widget/functionalities/avatarchange.html
- LIBRAS 5 parameters (libras.com.br): https://www.libras.com.br/os-cinco-parametros-da-libras
- gov.br VLibras 페이지: https://www.gov.br/governodigital/pt-br/acessibilidade-e-usuario/vlibras
- Frontiers 2018 sign learning research: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.00811/full
- VLibras config endpoint: https://vlibras.gov.br/config/configs.json
