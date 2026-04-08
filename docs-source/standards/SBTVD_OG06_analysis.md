# SBTVD TV 3.0 OG-06 운영 가이드라인 기술 분석 보고서

**문서**: TV 3.0 Operational Guidelines - Closed Signing (January 2026)
**상태**: NO NORMATIVE VALUE (비규범적 가이드라인)
**분석일**: 2026-02-12

---

## 1. 문서 개요

### 1.1 목적 및 범위

이 문서는 TV 3.0 Closed Signing에 대한 권장 실무 가이드라인을 제시한다. 규범적 표준인 ABNT NBR 25606 (TV 3.0 - Closed Signing)에 정의된 기술 사양을 실제 구현하기 위한 운영 절차, 변환 알고리즘, 워크플로우를 상세히 기술한다.

### 1.2 ABNT NBR 25606과의 관계

| 구분 | ABNT NBR 25606 | OG-06 (본 문서) |
|------|----------------|-----------------|
| 성격 | 규범적 표준 (Normative) | 운영 가이드라인 (No Normative Value) |
| 내용 | 기술 사양, 데이터 구조 정의 | 구현 방법, 변환 알고리즘, 워크플로우 |
| 역할 | **무엇**을 정의 | **어떻게** 구현하는지 안내 |
| 참조 | - | ABNT NBR 25606의 테이블 D.1~D.13을 지속적으로 참조 |

### 1.3 약어

| 약어 | 전체명 |
|------|--------|
| BVH | BioVision Hierarchy |
| DASH | Dynamic Adaptive Streaming over HTTP |
| DTT | Digital Terrestrial Television |
| glTF | graphics library Transmission Format |
| IMSC | Internet Media Subtitles and Captions |
| ISOBMFF | ISO Base Media File Format |
| JSON | JavaScript Object Notation |

### 1.4 가이드라인 구성

본 가이드라인은 수어 전송을 위한 **4가지 전략**을 다루며, 다음 부속서로 구성된다:

| 부속서 | 내용 | 상태 |
|--------|------|------|
| Annex R | 수어 표현 규칙 (공통 참조) | 완성 |
| Annex A | 수어 비디오 스트림 | **개발 중** (placeholder) |
| Annex B | 수어 글로스 스트림 | 완성 |
| Annex C | 자막 스트리밍 (자동 번역) | 완성 |
| Annex D | 수어 모션 스트림 | 완성 (가장 상세) |

> Annex B와 Annex C는 언어적/구조적 사양을 Annex R에서 공통으로 참조하여 문서 중복을 방지한다.

---

## 2. 수어 표현 규칙 (Annex R) - 상세 분석

Annex R은 TV 3.0 생태계에서 수어 데이터의 디지털 표현 및 구조화를 위한 표준화된 프레임워크를 정의한다. 글로스(gloss)와 메타데이터에 대한 통일된 구문을 수립하여 서로 다른 플랫폼과 디코딩 장치 간의 상호운용성을 보장한다.

> **핵심**: 이 규칙들은 브라질 수어(Libras)를 위해 개발되었으나, 다른 수어에도 쉽게 적용 가능하도록 설계되었다.

### 2.1 글로스 표기 규칙 체계

글로스 표현의 전체 규칙 체계는 다음과 같은 8개 규칙으로 구성된다:

| 규칙 | 섹션 | 구문 요소 | 목적 |
|------|------|-----------|------|
| 동음이의어 | R.1.1 | `&` | 의미 중의성 해소 |
| 구두점 | R.1.2 | `[PONTO]`, `[EXCLAMACAO]`, `[INTERROGACAO]` | 구두점 표현 |
| 형용사 | R.1.3 | 남성형 통일 | 성별 단순화 |
| 숫자 | R.1.4 | 기수, 서수, 수량, 시간, 분수, 통화 등 | 숫자 체계 표현 |
| 복합어 | R.1.5 | `_` (밑줄) | 단일 수어 표시로 연결 |
| 인칭-수 일치 | R.1.6 | `*S`, `*P` 접미사 | 동사 방향 표현 |
| 부정 통합 | R.1.7 | `NAO_` 접두사 | 부정 동시 수행 표현 |
| 강도 증감 | R.1.8 | `(+)`, `(-)` 접미사 | 강도 부사 표현 |

### 2.2 동음이의어 처리 (R.1.1)

**규칙**: 문어에서 철자가 동일하지만 수어에서 다른 수어를 갖는 단어(동음이의어)는 글로스 끝에 `&` 문자를 사용하여 문맥을 나타내는 명명법을 추가해야 한다.

**구문**: `글로스&문맥설명`

#### 예시 테이블: COLAR의 변형

| 동음이의어 | 글로스 표현 | 의미 |
|-----------|------------|------|
| COLAR | COLAR&ACESSORIO | 목걸이 (액세서리) |
| COLAR | COLAR&GRUDAR | 붙이다 (접착) |
| COLAR | COLAR&FILAR | 커닝하다 (시험에서) |
| COLAR | COLAR&INFORMATICA | 붙여넣기 (컴퓨터) |

#### 예시 테이블: APAGAR의 변형

| 동음이의어 | 글로스 표현 | 의미 |
|-----------|------------|------|
| APAGAR | APAGAR&EXTINGUIR | 삭제/소멸 |
| APAGAR | APAGAR&FOGO | 불 끄기 |
| APAGAR | APAGAR&INFORMATICA | 삭제 (컴퓨터) |
| APAGAR | APAGAR&ESCREVER | 지우기 (필기) |
| APAGAR | APAGAR&LOUSA | 칠판 지우기 |
| APAGAR | APAGAR&LUZ | 불 끄기 (조명) |
| APAGAR | APAGAR&VELA | 초 끄기 |

#### 사용 예시: COLAR 변형 적용

| 입력 문장 | 글로스 변환 결과 |
|-----------|----------------|
| Ganhei um colar da minha vo. (할머니에게 목걸이를 받았다.) | `GANHAR COLAR&ACESSORIO MEU VO [PONTO]` |
| E errado colar na prova. (시험에서 커닝은 나쁘다.) | `ERRADO COLAR&FILAR PROVA [PONTO]` |
| O papel esta todo colado. (종이가 모두 붙었다.) | `PAPEL COLAR&GRUDAR [PONTO]` |
| Copie e cole o texto. (텍스트를 복사하여 붙여넣기하라.) | `COPIAR COLAR&INFORMATICA TEXTO [PONTO]` |

#### 사용 예시: APAGAR 변형 적용

| 입력 문장 | 글로스 변환 결과 |
|-----------|----------------|
| Cuidado, apague o fogo! (조심, 불 꺼!) | `CUIDADO APAGAR&FOGO [EXCLAMACAO]` |
| Apague essa sentenca. (이 문장을 삭제하라.) | `APAGAR&INFORMATICA SENTENCA [PONTO]` |
| Apague meu nome da lista. (목록에서 내 이름을 지워라.) | `APAGAR&ESCREVER NOME LISTA [PONTO]` |
| Posso apagar o quadro? (칠판을 지워도 되나요?) | `EU PODER APAGAR&LOUSA [INTERROGACAO]` |
| Entre e apague a luz. (들어와서 불 꺼라.) | `ENTRAR APAGAR&LUZ [PONTO]` |
| Apague as velas e faca um pedido. (초를 끄고 소원을 빌어라.) | `APAGAR&VELA FAZER PEDIDO&PEDIR [PONTO]` |

> **파서 구현 참고**: 이 규칙은 번역 과정에서 수어의 의미론(semantics)과 화용론(pragmatics)을 고려하여, 문어의 어휘 항목에 대응하는 수어 어휘 항목의 의미를 반영한 정확한 번역을 가능하게 한다.

### 2.3 구두점 규칙 (R.1.2)

**규칙**: 구두점 문자(`"."`, `"!"`, `"?"`)는 대괄호 안에 전체 명칭으로 대체해야 한다.

| 구두점 | 글로스 표현 (포르투갈어) | 글로스 표현 (영어 대안) |
|--------|------------------------|----------------------|
| `.` (마침표) | `[PONTO]` | `[PERIOD]` |
| `!` (느낌표) | `[EXCLAMACAO]` | `[EXCLAMATION]` |
| `?` (물음표) | `[INTERROGACAO]` | `[INTERROGATION]` |

> **파서 구현 참고**: 포르투갈어와 영어 두 가지 표현 모두 허용된다. 파서는 양쪽 모두를 인식할 수 있어야 한다.

### 2.4 형용사 처리 (R.1.3)

**규칙**: 수어에서 형용사는 일반적으로 중성형이며, 성(남성/여성)이나 수(단수/복수)에 대한 표시가 없다. 따라서 이 글로스 표현에서 형용사는 **남성형으로 통일**하여 계산 처리를 단순화한다.

| 입력 문장 | 글로스 변환 결과 |
|-----------|----------------|
| Essa flor e cheiros**a**! (이 꽃은 향기롭다!) | `ESSE FLOR CHEIROS**O** [EXCLAMACAO]` |

> **파서 구현 참고**: 여성형 형용사(-a 어미)를 남성형(-o 어미)으로 변환하는 전처리 단계가 필요하다.

### 2.5 숫자 표현 체계 (R.1.4)

수어에서의 숫자 표현은 문맥에 따라 다양한 방식으로 구분된다.

#### 2.5.1 기수 (Cardinal Numbers)

**규칙**: 항상 아라비아 숫자를 참조로 사용한다. 수어 수행 시 해당 숫자에 대응하는 수어 기호를 사용하며, 철자를 손가락으로 나타내지 않는다.

| 입력 문장 | 글로스 변환 결과 |
|-----------|----------------|
| Eu preciso comprar 4 cadernos. (나는 공책 4권을 사야 한다.) | `EU PRECISAR COMPRAR 4 CADERNO [PONTO]` |

#### 2.5.2 서수 (Ordinal Numbers)

**규칙**: 1~5번째까지는 기수와 동음이의어이므로 `&ORDINAL` 접미사로 구분한다. 10번째부터는 기수와 동일하게 표현한다.

| 기호 | 글로스 표현 | 비고 |
|------|-----------|------|
| 1o | `PRIMEIRO&ORDINAL` | 동음이의어 구분 필요 |
| 2o | `SEGUNDO&ORDINAL` | 동음이의어 구분 필요 |
| 3o | `TERCEIRO&ORDINAL` | 동음이의어 구분 필요 |
| 4o | `QUARTO&ORDINAL` | 동음이의어 구분 필요 |
| 5o | `QUINTO&ORDINAL` | 동음이의어 구분 필요 |
| 6o | `SEXTO` | 구분 불필요 |
| 7o | `SETIMO` | 구분 불필요 |
| 8o | `OITAVO` | 구분 불필요 |
| 9o | `NONO` | 구분 불필요 |
| 10o | `10` | 기수와 동일 |
| 11o | `11` | 기수와 동일 |
| 12o | `12` | 기수와 동일 |
| 20o | `20` | 기수와 동일 |

#### 2.5.3 수량 (Quantity)

**규칙**: 수량을 나타내는 숫자에는 특정 수어 기호를 사용해야 한다. `_` (밑줄)로 단위와 결합한다.

| 입력 | 글로스 표현 |
|------|-----------|
| 1 hora (1시간) | `UM_HORA` |
| 1 pessoa (1명) | `UM_PESSOA` |

#### 2.5.4 시간 (Time)

**규칙**: 시간 약어는 전체 명칭으로 풀어쓴다: `HORA`(시), `MINUTO`(분), `SEGUNDO`(초), `MANHA`(아침), `TARDE`(오후), `NOITE`(밤).

| 입력 문장 | 글로스 변환 결과 |
|-----------|----------------|
| Sao 3h30. (오전 3시 30분이다.) | `3 HORA 30 MINUTO MANHA [PONTO]` |
| A reuniao sera as 14h30. (회의는 오후 2시 30분이다.) | `REUNIAO 2 HORA 30 MINUTO TARDE [PONTO]` |

> **참고**: 14시는 오후 2시로 변환되어 `TARDE`(오후) 글로스와 함께 표현된다.

#### 2.5.5 분수, 백분율, 경기점수, 통화

| 유형 | 기호 | 글로스 대체 |
|------|------|-----------|
| 분수 | 분수 기호 | `FRACAO` |
| 백분율 | `%` | `PORCENTAGEM` |
| 경기/대결 | `X` | `VERSUS` |
| 통화 (R$) | `R$` | `REAL&MOEDA` |
| 통화 (US$) | `US$` | `DOLLAR` |
| 소수점 | `,` | `VIRGULA` |
| 센트 | - | `CENTAVOS` |

#### 사용 예시

| 입력 문장 | 글로스 변환 결과 |
|-----------|----------------|
| Temos 2/3 de aprovacao. (우리는 2/3 승인률을 갖고 있다.) | `TER 2 FRACAO 3 APROVAR [PONTO]` |
| A musica teve 25,5% de rejeicao. (그 노래는 25.5% 거부율이었다.) | `MUSICA TER 25 VIRGULA 5 PORCENTAGEM REJEICAO [PONTO]` |
| Fluminense ganhou de 4x2 do Vasco. (Fluminense가 Vasco를 4:2로 이겼다.) | `FLUMINENSE GANHAR 4 VERSUS 2 VASCO [PONTO]` |
| Eu preciso de R$ 4,99. (나는 R$4.99가 필요하다.) | `EU PRECISAR 4 REAL&MOEDA 99 CENTAVOS [PONTO]` |

### 2.6 복합어 처리 (R.1.5)

**규칙**: 단일 수어 기호로 표현되는 복합어나 표현은 `_` (밑줄)로 연결한다. 인사말도 이 규칙을 적용한다.

| 입력 문장 | 글로스 변환 결과 |
|-----------|----------------|
| Comprei um novo guarda-roupa. (새 옷장을 샀다.) | `COMPRAR GUARDA_ROUPA NOVO [PONTO]` |
| Bom dia! (좋은 아침!) | `BOM_DIA [EXCLAMACAO]` |
| Boa tarde! (좋은 오후!) | `BOA_TARDE [EXCLAMACAO]` |
| Boa noite! (좋은 저녁!) | `BOA_NOITE [EXCLAMACAO]` |

> **파서 구현 참고**: `_`로 연결된 토큰들은 단일 수어 사전 항목으로 처리해야 한다.

### 2.7 동사 인칭-수 일치 (R.1.6)

**규칙**: 방향 동사(directional verbs)에서 화자와 수신자 간의 일치를 표현하기 위해 `*S`(단수)와 `*P`(복수) 접미사를 사용한다. 동사는 부정사(infinitive) 형태로 표기하고, 인칭 표시로 방향을 나타낸다.

#### 인칭 대명사 코드

| 대명사 | 코드 | 유형 |
|--------|------|------|
| EU (나) | `1S` | 1인칭 단수 |
| TU/VOCE (너) | `2S` | 2인칭 단수 |
| ELE/ELA (그/그녀) | `3S` | 3인칭 단수 |
| NOS (우리) | `1P` | 1인칭 복수 |
| VOS/VOCES (너희들) | `2P` | 2인칭 복수 |
| ELES/ELAS (그들) | `3P` | 3인칭 복수 |

#### 구문 형식: `발신자코드_동사_수신자코드`

| 입력 문장 | 글로스 변환 결과 |
|-----------|----------------|
| Eu perguntei a sua idade. (나는 네 나이를 물었다.) | `1S_PERGUNTAR_2S IDADE [PONTO]` |
| O que voce me perguntou? (네가 나에게 뭘 물었니?) | `2S_PERGUNTAR_1S QUE [INTERROGACAO]` |
| Ela perguntou meu nome. (그녀가 내 이름을 물었다.) | `3S_PERGUNTAR_1S NOME [PONTO]` |
| Ele perguntou a ela sua idade. (그가 그녀에게 나이를 물었다.) | `3S_PERGUNTAR_3S IDADE [PONTO]` |
| Nos perguntamos a sua idade. (우리가 네 나이를 물었다.) | `1P_PERGUNTAR_2S IDADE [PONTO]` |
| Voces perguntam a minha idade. (너희들이 내 나이를 물었다.) | `2P_PERGUNTAR_1S IDADE [PONTO]` |
| Eles perguntaram a sua idade. (그들이 네 나이를 물었다.) | `3P_PERGUNTAR_2S IDADE [PONTO]` |

> **파서 구현 참고**: `_`로 연결된 동사 패턴에서 인칭 코드(1S~3P)를 인식하여 수어 방향 애니메이션에 반영해야 한다.

### 2.8 부정 표현 (R.1.7)

**규칙**: 부정 부사가 동사와 동시에 수행될 수 있는 경우, 접두사 `NAO_`(NOT_)를 동사 앞에 결합한다. 부정문에서 머리 움직임(부정)과 표정은 문법적으로 필수적이다.

| 입력 문장 | 글로스 변환 결과 |
|-----------|----------------|
| Eu nao posso mais esperar. (더 이상 기다릴 수 없다.) | `EU NAO_PODER ESPERAR [PONTO]` |
| Ele nao consegue ganhar. (그는 이길 수 없다.) | `ELE NAO_CONSEGUIR GANHAR [PONTO]` |

> **파서 구현 참고**: `NAO_` 접두사가 붙은 동사는 부정 수어와 해당 동사 수어를 동시에 수행해야 한다. 아바타 구현 시 머리 흔들기와 부정 표정이 동반되어야 한다.

### 2.9 강도 표현 (R.1.8)

**규칙**: 강도 부사("muito", "mais", "muitissimo" 등)는 `(+)` 마커로, 감소 부사("pouco", "menos", "pouquissimo" 등)는 `(-)` 마커로 대체한다. 마커는 해당 단어 끝에 삽입한다.

강도는 수어 기호의 **지속 시간, 에너지, 분산, 평균 속도**로 특성화된다.

| 마커 | 적용 부사 | 효과 |
|------|-----------|------|
| `(+)` | muito(매우), mais(더), muitissimo(매우 많이) | 수어 동작 확대/강화 |
| `(-)` | pouco(약간), menos(덜), pouquissimo(매우 적게) | 수어 동작 축소/약화 |

#### 사용 예시

| 입력 문장 | 글로스 변환 결과 |
|-----------|----------------|
| Ele esta muito deprimido. (그는 매우 우울하다.) | `ELE DEPRIMIDO(+) [PONTO]` |
| Ela e tao bonita! (그녀는 참 아름답다!) | `ELE BONITO(+) [EXCLAMACAO]` |
| Voce esta nervoso demais. (너는 너무 긴장했다.) | `VOCE NERVOSO(+) [PONTO]` |
| Estou um pouco doente. (나는 조금 아프다.) | `EU DOENTE(-) [PONTO]` |

> **파서 구현 참고**: `(+)`/`(-)` 마커는 아바타 엔진에서 수어 동작의 속도와 크기를 조절하는 매개변수로 사용해야 한다. 형용사 성별 통일 규칙(R.1.3)도 함께 적용됨에 유의 (예: "bonita" -> "BONITO").

### 2.10 수어 애니메이션 접근 - URL/사전 (R.2)

수어 애니메이션은 공공 사전을 통해 URL로 접근하고 다운로드할 수 있다.

#### URL 형식

```
https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/{글로스명}
```

**예시**:
- `CASA` 글로스의 애니메이션: `https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/CASA`

#### 사전 목록 접근

- 전체 사인 목록: `https://dicionario2.vlibras.gov.br/bundles`

> **구현 참고**: 응용 프로그램은 글로스의 고유 이름을 사용하여 프로그래밍적으로 올바른 애니메이션 파일을 검색할 수 있다.

---

## 3. 수어 비디오 스트림 (Annex A)

**상태: 별도 문서에서 개발 중**

Annex A는 수어 비디오 스트림 가이드라인을 포함할 예정이나, 현재 placeholder만 존재한다. 이 부속서의 내용은 별도 문서에서 완성될 때 추가될 예정이다.

---

## 4. 글로스 스트림 워크플로우 (Annex B)

### 4.1 범위 (Scope)

이 문서는 번역이 **전송 전**(송신측, Source-side)에 수행되는 경우의 수어 통합 워크플로우를 규정한다. 수어 글로스 콘텐츠는 방송국에서 생성되고 패키징된다.

### 4.2 수어 표현

이 기술에서 사용되는 수어 표현과 글로싱 규칙은 Annex R의 사양을 따른다.

### 4.3 운영 워크플로우

#### 4.3.1 송신측 프로세스

1. 방송국이 오디오, 비디오, 수어 글로스 시퀀스를 **IMSC1 포맷**으로 다중화(multiplex)
2. OTT(Over-the-Top) 또는 OTA(Over-the-Air) 신호로 전송

#### 4.3.2 수신측 프로세스

1. 등록된 애플리케이션이 **ABNT NBR 25608, Annex C**에 규정된 API 메커니즘을 통해 스트림에 접근
2. 애플리케이션은 `<span>` 태그 내의 각 글로스 문장에 대해 렌더링 수행
3. 글로스 문장은 `xml:lang="bzs"` 속성으로 식별

#### 4.3.3 IMSC1 통합

- 수어 사전 및 수어 플레이어 컴포넌트가 애플리케이션 내에 완전히 내장되어 실행
- TV 3.0 수신기 또는 연결된 컴패니언 디바이스에서 실행

```
[방송국] ──> 오디오 + 비디오 + 글로스(IMSC1) ──> [다중화/전송]
                                                      │
                                                      ▼
[수신기] ──> API 접근 ──> <span xml:lang="bzs"> 파싱 ──> [수어 플레이어 렌더링]
```

---

## 5. 자막 스트리밍 워크플로우 (Annex C)

### 5.1 범위 (Scope)

이 문서는 번역이 **수신 후**(수신측, Receiver-side)에 수행되는 경우의 수어 생성 워크플로우를 규정한다. 번역 프로세스는 디지털 TV 수신기 또는 연결된 세컨드 스크린 디바이스에서 직접 실행된다.

### 5.2 수어 표현

Annex R의 사양을 따른다 (Annex B와 동일).

### 5.3 운영 워크플로우

#### 5.3.1 자동 번역 프로세스

| 단계 | 설명 |
|------|------|
| 1 | 방송국이 오디오, 비디오, **문어(written-language) 자막**을 다중화하여 전송 |
| 2 | 수신측 애플리케이션이 ABNT NBR 25608에 규정된 API로 자막 스트림에 접근 |
| 3 | 애플리케이션이 **로컬에서 수어로 자동 번역** 수행 |
| 4 | 번역 후 각 생성된 문장에 대해 렌더링 처리 |

#### 5.3.2 수신측 처리

- 수어 번역기, 수어 사전, 수어 플레이어 컴포넌트가 모두 애플리케이션 내에 내장
- TV 3.0 수신기 또는 컴패니언 디바이스에서 실행

```
[방송국] ──> 오디오 + 비디오 + 자막(문어) ──> [다중화/전송]
                                                   │
                                                   ▼
[수신기] ──> 자막 추출 ──> [수어 자동 번역] ──> [수어 플레이어 렌더링]
                              │
                              └── 수어 번역기 + 사전 + 플레이어 (모두 내장)
```

#### Annex B와 Annex C의 핵심 차이

| 구분 | Annex B (글로스 스트림) | Annex C (자막 스트리밍) |
|------|----------------------|----------------------|
| 번역 위치 | 송신측 (방송국) | 수신측 (수신기) |
| 전송 데이터 | 수어 글로스 (IMSC1) | 문어 자막 |
| 번역 필요 여부 | 사전 번역 완료 | 수신기에서 자동 번역 |
| 추가 컴포넌트 | 사전 + 플레이어 | **번역기** + 사전 + 플레이어 |

---

## 6. 모션 스트림 가이드라인 (Annex D)

Annex D는 3D 휴머노이드 아바타를 사용하여 DTT 수신기에서 수어 해석을 제공하기 위한 수어 모션 스트림의 전송을 위한 운영 가이드라인을 정의한다.

### 6.1 모션 파일 포맷 변환 (D.2)

ABNT NBR 25606에 정의된 SLMB(Sign Language Motion Bundle) 포맷은 현재 시장의 애니메이션 소프트웨어에서 직접 지원되지 않으므로, SLMB 파일을 알려진 모션 파일 포맷으로 변환하는 방법을 상세히 기술한다.

#### 6.1.1 매개변수 규약 (D.2.2)

| 접두사 | 출처 | 참조 |
|--------|------|------|
| `geo.` | 바디 지오메트리 | ABNT NBR 25606, Table D.3, D.5 |
| `bmb.` | BodyMotionBlock 구조체 | ABNT NBR 25606, Table D.8 |
| `fmb.` | FaceMotionBlock 구조체 | ABNT NBR 25606, Table D.10 |
| `bvh.` | BVH 파일 포맷 | Tables D.1, D.2 (본 문서) |
| `json.` | JSON 파일 포맷 | Tables D.3, D.4 (본 문서) |
| `glTF.` | glTF 파일 포맷 | D.2.6.1 (본 문서) |

지오메트리 벡터:
- `geo.refpose_from_parent`: 참조 포즈에서 부모로부터의 관절 위치 (x/y/z)
- `geo.refpose_end`: 참조 포즈에서 관절 끝 위치 (x/y/z)
- `geo.RX`, `geo.RY`, `geo.RZ`: Type-2, Type-3 관절의 회전 축 좌표 (x/y/z)

### 6.2 회전 변환 알고리즘 (D.2.3)

SLMB 파일은 일부 관절에 쿼터니언을, 다른 관절에 오일러 각도(x/y/z 시퀀스)를 사용한다. 포맷 간 변환을 위해 오일러-쿼터니언 상호 변환이 필요하다.

#### 전제 함수: 회전 축에서 쿼터니언으로 변환

```
rotationaxisToquaternion(Rx, Ry, Rz)
{
    qw = sqrt(1 + Rx.x + Ry.y + Rz.z) / 2
    qx = (Ry.z - Rz.y) / (4*qw)
    qy = (Rz.x - Rx.z) / (4*qw)
    qz = (Rx.y - Ry.z) / (4*qw)
    return (qw, qx, qy, qz)
}
```

> 한글 설명: 회전 축의 좌표계(Rx, Ry, Rz 행렬)에서 쿼터니언 표현을 계산한다. 회전 행렬의 대각 요소 합으로 qw를 구하고, 비대각 요소 차이로 qx, qy, qz를 구한다.

#### 오일러(y/x/z) -> 쿼터니언 변환

```
euler2quaternion_yxz(Ex, Ey, Ez, RX, RY, RZ)
{
    Qr = rotationaxisToquaternion(Rx, Ry, Rz)
    Qex = (cos(Ex/2), sin(Ex/2), 0, 0)
    Qey = (cos(Ey/2), 0, sin(Ey/2), 0)
    Qez = (cos(Ez/2), 0, 0, sin(Ez/2))
    (qw, qx, qy, qz) = Qez * Qex * Qey * Qr
    return (qw, qx, qy, qz)
}
```

> 한글 설명: BVH 포맷에서 사용하는 y/x/z 순서 오일러 회전을 쿼터니언으로 변환한다. 각 축별 회전을 개별 쿼터니언으로 변환한 후, z, x, y 순서로 곱하고 축 보정 쿼터니언(Qr)을 적용한다.

#### 오일러(x/y/z) -> 쿼터니언 변환

```
euler2quaternion_xyz(Ex, Ey, Ez, RX, RY, RZ)
{
    Qr = rotationaxisToquaternion(Rx, Ry, Rz)
    Qex = (cos(Ex/2), sin(Ex/2), 0, 0)
    Qey = (cos(Ey/2), 0, sin(Ey/2), 0)
    Qez = (cos(Ez/2), 0, 0, sin(Ez/2))
    (qw, qx, qy, qz) = Qez * Qey * Qex * Qr
    return (qw, qx, qy, qz)
}
```

> 한글 설명: SLMB 포맷에서 사용하는 x/y/z 순서 오일러 회전을 쿼터니언으로 변환한다. y/x/z 변환과의 차이는 곱셈 순서가 `Qez * Qey * Qex`인 점이다.

#### 쿼터니언 -> 오일러(y/x/z) 변환

```
quaternion2euler_yxz(qw, qx, qy, qz, RX, RY, RZ)
{
    Q = (qw, qx, qy, qz)
    Qr = rotationaxisToquaternion(Rx, Ry, Rz)
    (qRw, qRx, qRy, qRz) = Q * inverse(Qr)
    a = qRw - qRx
    b = qRy - qRz
    c = qRx + qRw
    d = -qRz - qRy
    th_plus = atan2(b, a)
    if (d==0 && c==0) {
        th_minus = th_plus
    } else {
        th_minus = atan2(d, c)
    }
    th1 = th_plus - th_minus
    th2 = acos(2 * (a^2 + b^2) / (a^2 + b^2 + c^2 + d^2) - 1)
    th3 = th_plus + th_minus
    Ex = wrap_to_degree(th2 - pi/2);
    Ey = wrap_to_degree(th1);
    Ez = wrap_to_degree(-th3);
    return (Ex, Ey, Ez)
}
```

> 한글 설명: Bernardes & Viollet의 논문에 기반한 직접적이고 효율적인 쿼터니언-오일러 변환 알고리즘이다. 축 보정 쿼터니언의 역수를 적용한 후, 4개의 중간 변수(a,b,c,d)를 통해 세 오일러 각도를 계산한다. `wrap_to_degree()` 함수는 각도를 도 단위로 변환하고 (-180, 180] 범위에 유지한다.

#### 쿼터니언 -> 오일러(x/y/z) 변환

```
quaternion2euler_xyz(qw, qx, qy, qz, RX, RY, RZ)
{
    Q = (qw, qx, qy, qz)
    Qr = rotationaxisToquaternion(Rx, Ry, Rz)
    (qRw, qRx, qRy, qRz) = Q * inverse(Qr)
    a = qRw - qRy
    b = qRx + qRz
    c = qRy + qRw
    d = qRz - qRx
    th_plus = atan2(b, a)
    if (d==0 && c==0) {
        th_minus = th_plus
    } else {
        th_minus = atan2(d, c)
    }
    th1 = th_plus - th_minus
    th2 = acos(2 * (a^2 + b^2) / (a^2 + b^2 + c^2 + d^2) - 1)
    th3 = th_plus + th_minus
    Ex = wrap_to_degree(th1);
    Ey = wrap_to_degree(th2 - pi/2);
    Ez = wrap_to_degree(th3);
    return (Ex, Ey, Ez)
}
```

> 한글 설명: x/y/z 순서 오일러 변환은 y/x/z 변환과 중간 변수(a,b,c,d) 계산식과 최종 각도 할당이 다르다. Ex에 th1, Ey에 th2-pi/2, Ez에 th3가 할당된다.

#### 회전 변환 알고리즘 요약

| 변환 | 용도 | 입력 시퀀스 | 곱셈 순서 |
|------|------|-----------|-----------|
| `euler2quaternion_yxz` | BVH -> SLMB | y/x/z (BVH) | Qez * Qex * Qey * Qr |
| `euler2quaternion_xyz` | SLMB -> BVH/glTF | x/y/z (SLMB) | Qez * Qey * Qex * Qr |
| `quaternion2euler_yxz` | SLMB -> BVH | 쿼터니언 | a=qRw-qRx, b=qRy-qRz |
| `quaternion2euler_xyz` | BVH -> SLMB | 쿼터니언 | a=qRw-qRy, b=qRx+qRz |

### 6.3 BVH 변환 상세 (D.2.4)

#### 6.3.1 BVH 파일 포맷 구조

BVH 파일은 두 섹션으로 구성된다:
- **HIERARCHY**: 참조 포즈에서의 스켈레톤 정의
- **MOTION**: 프레임별 관절 움직임 데이터

##### BVH 파일 포맷 구문 (Table D.1)

```
BodyMotionBVH () {
    HIERARCHY
    ROOT hips_JNT                    // 루트 관절 = hips_JNT
    {
        joint_declaration(root_joint)  // Table D.2에 정의된 재귀적 관절 선언
    }
    MOTION
    Frames: num_frames               // 총 프레임 수
    Frame Time: frame_time           // 프레임 간 시간(초, 부동소수점)
    // 프레임별 관절별 채널별 이동값
    for (i = 0; i < num_frames; i++) {
        for (j = 0; j < num_joints; j++) {
            for (k = 0; k < num_channels(j); k++) {
                <movement[i][j][k]>
            }
        }
    }
}
```

##### 관절 선언 구문 (Table D.2)

```
joint_declaration(joint) {
    OFFSET ref[joint].x ref[joint].y ref[joint].z   // 부모로부터의 참조 위치
    CHANNELS num_channels[joint] channel_name[0] channel_name[1] ...

    if (num_children[joint] == 0) {
        End Site
        {
            OFFSET refend[joint].x refend[joint].y refend[joint].z  // 뼈 끝 위치
        }
    } else {
        for (i = 0; i < num_children[joint]; i++) {
            child = child_joint[i][joint]
            JOINT child
            {
                joint_declaration(child)    // 재귀 호출
            }
        }
    }
}
```

##### 채널 유형

| 채널 | 설명 |
|------|------|
| Xposition, Yposition, Zposition | x/y/z 축의 관절 위치 |
| Xrotation, Yrotation, Zrotation | x/y/z 축 주위 오일러 각도 회전 |

> **핵심**: 회전 채널의 순서가 회전 적용의 역순을 정의한다.

##### SLMB 호환 BVH 파일 조건

1. HIERARCHY의 스켈레톤과 참조 포즈가 ABNT NBR 25606을 준수
2. 모든 관절의 채널 순서는 `Zrotation Xrotation Yrotation` (Y, X, Z 순서로 회전)
3. 관절 이동이 ABNT NBR 25606, Table D.4의 제한을 준수

#### 6.3.2 BVH -> SLMB 변환 의사코드 (D.2.4.3)

```
/** HIERARCHY 섹션에서 관절 정보 로드 */
joint_list = <HIERARCHY 섹션에서 선언된 순서대로 관절 목록>
for (j = 0; j < <size of joint_list>; j++) {
    joint_order[j] = <ABNT NBR 25606, Table D.9에 정의된 j번째 관절의 순서>
    joint_type[j] = <ABNT NBR 25606, Table D.9에 정의된 j번째 관절의 타입>
    channel_list[j] = <j번째 관절의 채널 목록, 선언 순서대로>
}

bmb.number_of_frames = bvh.num_frames
bmb.frame_time = bvh.frame_time

for (f = 0; f < bvh.num_frames; f++) {
    for (j = 0; j < <size of joint_list>; j++) {
        /** BVH MOTION 섹션에서 이동 정보 로드 */
        for (c = 0; c < <size of channel_list[j]>; c++) {
            if (channel_list[j][c] == "XPosition") XPosition = bvh.movement[f][j][c]
            if (channel_list[j][c] == "YPosition") YPosition = bvh.movement[f][j][c]
            if (channel_list[j][c] == "ZPosition") ZPosition = bvh.movement[f][j][c]
            if (channel_list[j][c] == "XRotation") XRotation = bvh.movement[f][j][c]
            if (channel_list[j][c] == "YRotation") YRotation = bvh.movement[f][j][c]
            if (channel_list[j][c] == "ZRotation") ZRotation = bvh.movement[f][j][c]
        }

        if (joint_type[j] == 0) {
            /** Type-0 관절의 이동(translation) 변환 */
            bmb.Tx[f][joint_order[j]] = (Xposition + 0.5) * 65535
            bmb.Ty[f][joint_order[j]] = (Yposition + 0.5) * 65535
            bmb.Tz[f][joint_order[j]] = (Zposition + 0.5) * 65535
        }

        if (joint_type[j] == 0 || joint_type[j] == 1) {
            /** Type-0, Type-1 관절의 회전 변환 (쿼터니언 저장) */
            (qw, qx, qy, qz) = euler2quaternion_yxz(
                Xrotation, Yrotation, Zrotation, (1,0,0), (0,1,0), (0,0,1))
            if (qw < 0) then qx = -qx, qy = -qy, qz = -qz
            bmb.Qx[f][joint_order[j]] = qx * 32767
            bmb.Qy[f][joint_order[j]] = qy * 32767
            bmb.Qz[f][joint_order[j]] = qz * 32767

        } else if (joint_type[j] == 2) {
            /** Type-2 관절의 회전 변환 (커스텀 축 오일러) */
            (qw, qx, qy, qz) = euler2quaternion_yxz(
                Xrotation, Yrotation, Zrotation, (1,0,0), (0,1,0), (0,0,1))
            (Ex, Ey, Ez) = quaternion2euler_xyz(
                qw, qx, qy, qz,
                geo.RX[joint_order[j]], geo.RY[joint_order[j]], geo.RZ[joint_order[j]])
            E2x = (Ex + 90) / 180 * 1023
            E2y = (Ey + 90) / 180 * 1023
            E2z = (Ez + 180) / 360 * 4095
            bmb.E2[f][joint_order[j]] = (E2x << 22) + (E2y << 12) + E2z

        } else if (type == 3) {
            /** Type-3 관절의 회전 변환 (단일 축) */
            (qw, qx, qy, qz) = euler2quaternion_yxz(
                Xrotation, Yrotation, Zrotation, (1,0,0), (0,1,0), (0,0,1))
            (Ex, Ey, Ez) = quaternion2euler_xyz(
                qw, qx, qy, qz,
                geo.RX[joint_order[j]], geo.RY[joint_order[j]], geo.RZ[joint_order[j]])
            bmb.E3[f][joint_order[j]] = (Ez + 180) / 360 * 255

        } else if (type == 4) {
            /** Type-4 관절의 회전 변환 (2축 직접) */
            E4x = (Xrotation + 90) / 180 * 255
            E4y = (Yrotation + 90) / 180 * 255
            bmb.E4[f][joint_order[j]] = (E4x << 8) + E4y
        }
    }
}
```

> 한글 설명: BVH에서 SLMB로의 변환 핵심은 관절 타입별 다른 인코딩을 적용하는 것이다. Type-0/1은 쿼터니언으로, Type-2는 커스텀 축 기준 3축 오일러 패킹(10+10+12=32비트), Type-3은 Z축만 8비트, Type-4는 X/Y축 각 8비트로 인코딩한다. BVH의 y/x/z 회전 순서를 먼저 쿼터니언으로 변환하고, 필요 시 SLMB의 x/y/z 커스텀 축 오일러로 재변환한다.

#### 6.3.3 SLMB -> BVH 변환 의사코드 (D.2.4.4)

HIERARCHY 섹션은 ABNT NBR 25606, Tables D.1/D.3에서 가져오거나, 제공된 `avatarModel.bvh` 파일에서 얻을 수 있다.

```
/** BVH HIERARCHY 섹션에서 관절 정보 로드 */
joint_list = <BVH HIERARCHY 섹션에서 선언된 순서대로 관절 목록>
for (j = 0; j < <size of joint_list>; j++) {
    joint_order[j] = <ABNT NBR 25606, Table D.9에 정의된 순서>
    joint_type[j] = <ABNT NBR 25606, Table D.9에 정의된 타입>
    channel_list[j] = <채널 목록, 선언 순서대로>
}

bvh.num_frames = bmb.number_of_frames
bvh.frame_time = bmb.frame_time

for (f = 0; f < bmb.number_of_frames; f++) {
    for (j = 0; j < <size of joint_list>; j++) {

        if (joint_type[j] == 0) {
            /** Type-0 관절: 이동(translation) 역변환 */
            Xposition = bmb.Tx[f][joint_order[j]] / 65535 - 0.5
            Yposition = bmb.Ty[f][joint_order[j]] / 65535 - 0.5
            Zposition = bmb.Tz[f][joint_order[j]] / 65535 - 0.5
        } else {
            /** 비-Type-0 관절: 참조 포즈 위치 사용 */
            Xposition = geo.refpose_from_parent[joint_order[j]].x
            Yposition = geo.refpose_from_parent[joint_order[j]].y
            Zposition = geo.refpose_from_parent[joint_order[j]].z
        }

        if (joint_type[j] == 0 || joint_type[j] == 1) {
            /** Type-0/1: 쿼터니언 -> y/x/z 오일러 */
            qx = bmb.Qx[f][joint_order[j]] / 32767
            qy = bmb.Qy[f][joint_order[j]] / 32767
            qz = bmb.Qz[f][joint_order[j]] / 32767
            qw = sqrt(1 - qx^2 - qy^2 - qz^2)
            (Yrotation, Xrotation, Zrotation) = quaternion2euler_yxz(
                qw, qx, qy, qz, (1,0,0), (0,1,0), (0,0,1))

        } else if (joint_type[j] == 2) {
            /** Type-2: 패킹된 오일러 디코딩 -> 쿼터니언 -> y/x/z 오일러 */
            E2x = bmb.E2[f][joint_order[j]] >> 22
            E2y = (bmb.E2[f][joint_order[j]] >> 12) & 0x03FF
            E2z = bmb.E2[f][joint_order[j]] & 0x0FFF
            Ex = E2x * 180 / 1023 - 90
            Ey = E2y * 180 / 1023 - 90
            Ez = E2z * 360 / 4095 - 180
            (qw, qx, qy, qz) = euler2quaternion_xyz(
                Ex, Ey, Ez,
                geo.RX[joint_order[j]], geo.RY[joint_order[j]], geo.RZ[joint_order[j]])
            (Xrotation, Yrotation, Zrotation) = quaternion2euler_yxz(
                qw, qx, qy, qz, (1,0,0), (0,1,0), (0,0,1))

        } else if (joint_type[j] == 3) {
            /** Type-3: 단일축 디코딩 -> 쿼터니언 -> y/x/z 오일러 */
            Ez = bmb.E3[f][joint_order[j]] * 360 / 255 - 180
            (qw, qx, qy, qz) = euler2quaternion_xyz(
                0, 0, Ez,
                geo.RX[joint_order[j]], geo.RY[joint_order[j]], geo.RZ[joint_order[j]])
            (Xrotation, Yrotation, Zrotation) = quaternion2euler_yxz(
                qw, qx, qy, qz, (1,0,0), (0,1,0), (0,0,1))

        } else if (joint_type[j] == 4) {
            /** Type-4: 2축 직접 디코딩 */
            E4x = bmb.E4[f][joint_order[j]] >> 8;
            E4y = bmb.E4[f][joint_order[j]] & 0xFF
            Xrotation = E4x * 180 / 255 - 90
            Yrotation = E4y * 180 / 255 - 90
            Zrotation = 0
        }

        /** BVH MOTION 섹션에 이동 정보 채우기 */
        for (c = 0; c < <size of channel_list[j]>; c++) {
            if (channel_list[j][c] == "XPosition") bvh.movement[f][j][c] = XPosition
            if (channel_list[j][c] == "YPosition") bvh.movement[f][j][c] = YPosition
            if (channel_list[j][c] == "ZPosition") bvh.movement[f][j][c] = ZPosition
            if (channel_list[j][c] == "XRotation") bvh.movement[f][j][c] = XRotation
            if (channel_list[j][c] == "YRotation") bvh.movement[f][j][c] = YRotation
            if (channel_list[j][c] == "ZRotation") bvh.movement[f][j][c] = ZRotation
        }
    }
}
```

> 한글 설명: SLMB에서 BVH로의 역변환이다. 각 관절 타입별로 SLMB의 인코딩된 값을 디코딩하여 BVH의 y/x/z 오일러 각도 형식으로 변환한다. Type-2/3 관절은 SLMB의 커스텀 축 오일러를 쿼터니언으로 변환한 후 BVH의 표준 축 오일러로 다시 변환하는 2단계 과정이 필요하다.

#### 관절 타입별 인코딩 비교

| 타입 | 용도 | 이동 | 회전 형식 | 비트 할당 |
|------|------|------|-----------|-----------|
| Type-0 | 루트 관절 | 16비트 x3 (Tx,Ty,Tz) | 쿼터니언 (Qx,Qy,Qz: 16비트 x3) | 이동 48b + 회전 48b |
| Type-1 | 주요 관절 | 없음 | 쿼터니언 (Qx,Qy,Qz: 16비트 x3) | 회전 48b |
| Type-2 | 커스텀 축 관절 | 없음 | 오일러 패킹 (10+10+12=32비트) | 회전 32b |
| Type-3 | 단일 축 관절 | 없음 | Z축만 8비트 | 회전 8b |
| Type-4 | 2축 관절 | 없음 | X/Y 각 8비트 (8+8=16비트) | 회전 16b |

### 6.4 JSON 변환 상세 (D.2.5)

#### 6.4.1 JSON 파일 구조

JSON 파일은 AR Emoji SDK와 호환되는 얼굴 움직임 데이터를 저장한다.

##### JSON 파일 구문 (Table D.3)

```json
{
    "name": "MAL",
    "version": "1.2.3",
    "blendShapes": [
        {"name": "head_GEO", ...},
        {"name": "eyelash_GEO", ...},
        {"name": "mouth_GEO", ...},
        {"name": "eyebrow_l_GEO", ...},
        {"name": "eyebrow_r_GEO", ...}
    ],
    "shapesAmount": 5,
    "time": [0, 30, 60, 90, 120],
    "frames": 5
}
```

##### 메시 선언 구문 (Table D.4)

```json
{
    "name": "eyebrow_l_GEO",
    "fullName": "eyebrow_l_GEO",
    "blendShapeVersion": "3.1",
    "morphTarget": 9,
    "morphName": [
        "BrowsDown_Left", "BrowsDown_Right", "BrowsUp_Center",
        "BrowsUp_Left", "BrowsUp_Right", "Sneer",
        "HAPPY_51", "ANGRY_55", "SAD_58"
    ],
    "key": [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.00258091744, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...
    ]
}
```

#### 6.4.2 JSON -> SLMB 변환 의사코드 (D.2.5.3)

```
fmb.number_of_frames = json.frames
for (f = 0; f < json.frames; f++) {
    fmb.frame_time[f] = json.time[f]
}

/** JSON에서 블렌드셰이프 로드. FMB는 빈 상태에서 시작하여 JSON 파싱 중 채워짐 */
fmb.number_of_blend_shapes = 0
for (m = 0; m < json.shapesAmount; m++) {
    for (b = 0; b < json.blendShapes[m].morphTarget; b++) {
        hasWeight = false
        for (f = 0; f < json.frames; f++) {
            weight = json.blendShapes[m].key[b][f]
            if (weight != 0) {
                if (not hasWeight) {
                    hasWeight = true
                    fmb.number_of_blend_shapes++;
                    target_index = fmb.number_of_blend_shapes - 1
                    fmb.blend_shape_id[target_index] = <ABNT 25606, Table D.11에서
                        메시명과 블렌드셰이프명으로 ID 조회>
                    /** 가중치가 0이 아닌 프레임 목록 생성 */
                    number_of_frames = 0
                }
                number_of_frames++
                frame_index = number_of_frames - 1
                frame_list[frame_index] = f
                /** 블렌드셰이프 가중치 변환 공식 */
                fmb.blend_shape_weight[target_index][frame_index] = weight * 65535
            }
        }

        if (not hasWeight) {
            /** 프레임 목록을 프레임 범위 목록으로 변환 */
            current_frame_defined = false
            fmb.number_of_frame_ranges[target_index] = 0
            for (k = 0; k < number_of_frames; k++) {
                if (not current_frame_defined) {
                    current_frame_defined = true
                    first_frame = frame_list[k];
                } else if (frame_list[k] != current_frame + 1) {
                    last_frame = current_frame
                    fmb.number_of_frame_ranges[target_index]++
                    range_index = fmb.number_of_frame_ranges[target_index] - 1
                    fmb.frame_range_first[target_index][range_index] = first_frame
                    fmb.frame_range_size[target_index][range_index] =
                        last_frame - first_frame + 1
                    first_frame = frame_list[i];
                }
                current_frame = frame_list[k]
            }
            if (current_frame_defined) {
                last_frame = current_frame
                fmb.number_of_frame_ranges[target_index]++
                range_index = fmb.number_of_frame_ranges[target_index] - 1
                fmb.frame_range_first[target_index][range_index] = first_frame
                fmb.frame_range_size[target_index][range_index] =
                    last_frame - first_frame + 1
            }
        }
    }
}
```

> 한글 설명: JSON에서 SLMB FaceMotionBlock으로의 변환은 두 가지 핵심 작업을 수행한다. (1) 가중치가 0이 아닌 블렌드셰이프만 선택하여 SLMB에 등록 (스파스 인코딩), (2) 연속된 프레임을 프레임 범위(range)로 압축하여 저장 효율성 극대화. 가중치 변환은 부동소수점(0~1)을 16비트 정수(0~65535)로 스케일링한다.

#### 6.4.3 SLMB -> JSON 변환 의사코드 (D.2.5.4)

```
json.frames = fmb.number_of_frames
for (f = 0; f < fmb.number_of_frames; f++) {
    json.time[f] = fmb.frame_time[f]
}

json.shapesAmount = 0
for (b = 0; b < fmb.number_of_blend_shapes; b++) {
    mesh_name, target_name = <fmb.blend_shape_id[b]에서
        ABNT 25606, Table D.11에 따라 메시명과 블렌드셰이프명 조회>

    /** 해당 메시가 이미 등록되었는지 확인, 없으면 생성 */
    mesh_index_defined = false
    for (m = 0; m < json.shapesAmount; m++) {
        if (json.blendShapes[m].name = mesh_name) {
            mesh_index = m
            mesh_index_defined = true
        }
    }
    if (not mesh_index_defined) {
        json.shapesAmount++
        mesh_index = json.shapesAmount - 1
        json.blendShapes[mesh_index].name = mesh_name
        json.blendShapes[mesh_index].morphTarget = 0
    }

    /** 블렌드셰이프 목록에 추가 */
    json.blendShapes[mesh_index].morphTarget++
    target_index = json.blendShapes[mesh_index].morphTarget - 1
    json.blendShapes[mesh_index].morphName[target_index] = target_name

    /** 모든 프레임의 가중치를 0으로 초기화 */
    for (f = 0; f < fmb.number_of_frames; f++) {
        json.blendShapes[mesh_index].key[target_index][f] = 0
    }

    /** FMB에서 수집된 데이터로 가중치 채우기 */
    frame_list_size = 0
    for (r = 0; r < fmb.number_of_frame_ranges[b]; r++) {
        for (f = 0; f < fmb.frame_ranges_size[b][r]; f++) {
            frame = fmb.frame_ranges_first[b][r] + f
            /** 블렌드셰이프 가중치 역변환 공식 */
            json.blendShapes[mesh_index].key[target_index][frame] =
                fmb.number_of_blend_shapes[i][j] / 65535
        }
    }
}
```

> 한글 설명: SLMB에서 JSON으로의 역변환이다. SLMB의 스파스 프레임 범위 데이터를 JSON의 밀집(dense) 배열 형식으로 변환한다. 가중치가 없는 프레임은 0으로 채워지고, 범위 내 프레임들만 실제 값(65535로 나눈 부동소수점)이 할당된다.

### 6.5 glTF 변환 상세 (D.2.6)

#### 6.5.1 glTF 파일 구조

glTF 2.0 사양에 따라 아바타 모델에 애니메이션 데이터를 추가한다. 제공된 `avatarModel.zip`에는 ABNT NBR 25606의 스켈레톤, 참조 포즈, 얼굴 메시, 블렌드셰이프가 포함된다.

> **참고**: 아바타가 전신으로 제공되지만, SLMB의 모션은 하체(다리, 발)에는 적용되지 않는다.

##### glTF 애니메이션 데이터 구조

```
glTF 파일
├── bufferViews[] ── 바이너리 버퍼 매핑 (offset, length)
├── accessors[] ── 버퍼뷰 인덱스 참조
├── animations[]
│   ├── samplers[] ── 각 샘플러:
│   │   ├── input: 프레임 시간 접근자
│   │   ├── interpolation: 보간 방법
│   │   └── output: 속성 값 접근자
│   └── channels[] ── 각 채널:
│       ├── sampler: 샘플러 인덱스
│       └── target:
│           ├── node: nodes[] 인덱스 (관절 또는 메시)
│           └── path: "translation" | "rotation" | "weights"
├── nodes[] ── 관절 및 메시 노드
└── meshes[] ── 메시 정의 (extras.targetNames 포함)
```

##### 속성 값 형식

| path | 값 형식 | 설명 |
|------|---------|------|
| `translation` | float x 3 (X/Y/Z) | 이동 벡터 |
| `rotation` | float x 4 (W/X/Y/Z) | 쿼터니언 |
| `weights` | float x N | 블렌드셰이프 가중치 배열 |

#### 6.5.2 SLMB -> glTF 변환 의사코드 (D.2.6.3)

```
number_of_channels = 0
number_of_samplers = 0

/** === 바디 모션 변환 === */
for (j = 0; j < bmb.number_of_joints; j++) {
    joint_type, joint_name = <ABNT 25606, Table D.9에서 순서 j에 해당하는 타입과 이름>

    if (joint_type == 0) {
        /** Type-0 관절: 이동(translation) 등록 */
        number_of_samplers++
        sampler_index = number_of_samplers - 1
        for (f = 0; f < bmb.number_of_frames; f++) {
            glTF.animations.samplers[sampler_index].input.time[f] = f * bmb.frame_time
            /** Type-0 이동 변환 공식 */
            tx = bmb.Tx[j][f] / 65535 - 0.5
            ty = bmb.Ty[j][f] / 65535 - 0.5
            tz = bmb.Tz[j][f] / 65535 - 0.5
            glTF.animations.samplers[sampler_index].output.translation[f][0] = tx
            glTF.animations.samplers[sampler_index].output.translation[f][1] = ty
            glTF.animations.samplers[sampler_index].output.translation[f][2] = tz
        }
        number_of_channels++
        channel_index = number_of_channels - 1
        glTF.animations.channels[channel_index].sampler = sampler_index
        glTF.animations.channels[channel_index].node = <joint_name에 해당하는 glTF.nodes 인덱스>
        glTF.animations.channels[channel_index].path = "translation"
    }

    /** 모든 관절: 회전(rotation) 등록 */
    number_of_samplers++
    sampler_index = number_of_samplers - 1
    for (f = 0; f < bmb.number_of_frames; f++) {
        glTF.animations.samplers[sampler_index].input.time[f] = f * bmb.frame_time

        if (joint_type == 0 || joint_type == 1) {
            /** Type-0/1: 쿼터니언 직접 사용 */
            qx = bmb.Qx[j][f] / 32767
            qy = bmb.Qy[j][f] / 32767
            qz = bmb.Qz[j][f] / 32767
            qw = sqrt(1 - qx^2 - qy^2 - qz^2)

        } else if (joint_type == 2) {
            /** Type-2: 패킹된 오일러 -> 쿼터니언 */
            E2x = bmb.E2[j][f] << 22
            E2y = (bmb.E2[j][f] << 12) & 0x3FF
            E2z = bmb.E2[j][f] & 0xFFF
            Ex = E2x * 180 / 1023 - 90
            Ey = E2y * 180 / 1023 - 90
            Ez = E2z * 360 / 4095 - 180
            (qx, qy, qz, qw) = euler2quaternion_xyz(Ex, Ey, Ez, geo.RX, geo.RY, geo.RZ)

        } else if (joint_type == 3) {
            /** Type-3: 단일축 -> 쿼터니언 */
            Ez = bmb.E3[j][f] * 360 / 255 - 180
            (qx, qy, qz, qw) = euler2quaternion_xyz(0, 0, Ez, geo.RX, geo.RY, geo.RZ)

        } else if (joint_type == 4) {
            /** Type-4: 2축 -> 쿼터니언 */
            E4x = bmb.E4[j][f] << 8
            E4y = bmb.E4[j][f] && 0xFF
            Ex = E4x * 180 / 255 - 90
            Ey = E4y * 180 / 255 - 90
            (qx, qy, qz, qw) = euler2quaternion_xyz(Ex, Ey, 0, (1,0,0), (0,1,0), (0,0,1))
        }

        glTF.animations.samplers[sampler_index].output.rotation[f][0] = qw
        glTF.animations.samplers[sampler_index].output.rotation[f][1] = qx
        glTF.animations.samplers[sampler_index].output.rotation[f][2] = qy
        glTF.animations.samplers[sampler_index].output.rotation[f][3] = qz
    }
    number_of_channels++
    channel_index = number_of_channels - 1
    glTF.animations.channels[channel_index].sampler = sampler_index
    glTF.animations.channels[channel_index].node = <joint_name에 해당하는 glTF.nodes 인덱스>
    glTF.animations.channels[channel_index].path = "rotation"
}

/** === 얼굴 모션 변환 === */
/** 메시, 블렌드셰이프, 프레임 목록 구성 */
number_of_meshes = 0
for (b = 0; b < fmb.number_of_blend_shapes; b++) {
    mesh_name, target_name = <fmb.blend_shape_id[b]에서 ABNT 25606, Table D.11 참조>

    /** 메시가 이미 등록되었는지 확인, 없으면 생성 */
    mesh_index_defined = false
    for (j = 0; j < number_of_meshes; j++) {
        if (mesh_list[j].name = mesh_name) {
            mesh_index = j
            mesh_index_defined = true
        }
    }
    if (not mesh_index_defined) {
        number_of_meshes++
        mesh_index = number_of_meshes - 1
        mesh_list[mesh_index].name = mesh_name
        mesh_list[mesh_index].index = <mesh_name에 해당하는 glTF.meshes 인덱스>
        mesh_list[mesh_index].number_of_targets = 0
    }

    /** 블렌드셰이프 항목 추가 */
    mesh_list[mesh_index].number_of_targets++
    target_index = mesh_list[mesh_index].number_of_targets - 1
    mesh_list[mesh_index].targets[target_index].name = target_name
    mesh_list[mesh_index].targets[target_index].number_of_frames = 0

    /** 가중치가 0이 아닌 프레임 목록 채우기 */
    for (r = 0; r < fmb.number_of_frame_ranges[b]; r++) {
        for (f = 0; f < fmb.frame_range_size[b][r]; f++) {
            mesh_list[mesh_index].targets[target_index].number_of_frames++
            frame_index = mesh_list[mesh_index].targets[target_index].number_of_frames - 1
            mesh_list[mesh_index].targets[target_index].frames[frame_index].frame =
                fmb.frame_range_first[b][r] + f
            mesh_list[mesh_index].targets[target_index].frames[frame_index].weight =
                fmb.blend_shape_weight[b][frame_index]
        }
    }
}

/** 얼굴 움직임 등록 */
for (m = 0; m < number_of_meshes; m++) {
    mesh_index = meshes_list[m].index
    mesh_name = meshes_list[m].name
    number_of_samplers++
    sampler_index = number_of_samplers - 1

    /** 가중치를 0으로 초기화 */
    for (f = 0; f < fmb.number_of_frames; f++) {
        glTF.animations.samplers[sampler_index].input.time[f] = f * fmb.frame_time
        for (b = 0; b < <glTF.meshes[mesh_index].extras.targetNames 크기>; b++) {
            glTF.animations.samplers[sampler_index].output.weights[f][b] = 0
        }
    }

    /** 메시 목록에서 수집된 정보로 가중치 채우기 */
    for (b = 0; b < meshes_list[m].number_of_targets; b++) {
        target_name = meshes_list[m].targets[b].name
        target_index = <target_name에 해당하는 glTF.meshes[mesh_index].extras.targetNames 인덱스>
        for (f = 0; f < meshes_list[m].targets[b].number_of_frames; f++) {
            frame = meshes_list[m].targets[b].frames[f].frame
            /** 블렌드셰이프 가중치 변환 공식 */
            weight = meshes_list[m].targets[b].frames[f].weight / 65535
            glTF.animations.samplers[sampler_index].output.weights[target_index][frame] = weight
        }
    }

    number_of_channels++
    channel_index = number_of_channels - 1
    glTF.animations.channels[channel_index].sampler = sampler_index
    glTF.animations.channels[channel_index].node = <mesh_name에 해당하는 glTF.nodes 인덱스>
    glTF.animations.channels[channel_index].path = "weights"
}
```

> 한글 설명: SLMB에서 glTF로의 변환은 가장 포괄적인 변환으로, 바디 모션(BodyMotionBlock)과 얼굴 모션(FaceMotionBlock)을 모두 하나의 glTF 애니메이션에 통합한다. 바디 모션은 관절별 translation과 rotation 채널로, 얼굴 모션은 메시별 weights 채널로 변환된다. glTF는 쿼터니언을 직접 지원하므로 BVH 변환과 달리 오일러 각도 변환 없이 쿼터니언을 직접 출력한다.

### 6.6 전송 프로세스 (D.3~D.4)

#### 전체 전송 프로세스

```
[방송국]
  글로스 시퀀스 정의 (예: "EU" + "CASA" + "VOLTAR")
      │
      ▼
  수어 사전에서 BVH/JSON 파일 검색
  (EU.bvh, EU.json, CASA.bvh, CASA.json, VOLTAR.bvh, VOLTAR.json)
      │
      ▼
  BVH/JSON 파일 연결
  (EU_CASA_VOLTAR.bvh, EU_CASA_VOLTAR.json)
      │
      ▼
  SLMB 인코딩
  (BVH -> BodyMotionBlock, JSON -> FaceMotionBlock -> MotionBundle -> LZMA 압축)
      │
      ▼
  IMSC1 문서 생성 (타임스탬프 동기화)
      │
      ▼
  MP4 세그멘테이션 및 캡슐화
      │
      ▼
  MPD 파일 선언
      │
      ▼
  다중화 및 전송 (OTT/OTA)
```

#### 수어 사전 구조

| 구성 요소 | 설명 | 파일 포맷 |
|-----------|------|-----------|
| 글로스 | 수어 단위 식별자 | 텍스트 |
| 바디 모션 파일 | 신체 움직임 데이터 | BVH |
| 얼굴 모션 파일 | 표정 데이터 | JSON |

#### MotionBundle 캡슐화 구조 (Table D.5)

| 바이트 수 | 요소 | 파라미터 | 값 | 설명 |
|-----------|------|---------|-----|------|
| 1 | Title header | header | 0x60 | (key_size=4, payload_size=0): (4-1)<<5 + 0 |
| 4 | key | - | 0x53 0x4C 0x4D 0x42 | "SLMB" 매직 넘버 |
| 1 | Body motion header | header | 0x3F | (key_size=2, payload_size>31): (2-1)<<5 + 0x1F |
| 2 | key | - | 0x01 0x01 | 바디 모션, 지오메트리 ID 1 |
| 4 | payload_size | bSize | - | BodyMotionBlock 크기 (바이트) |
| bSize | payload | - | BodyMotionBlock() | 바디 모션 데이터 |
| 1 | Face motion header | header | 0x3F | (key_size=2, payload_size>31): (2-1)<<5 + 0x1F |
| 2 | key | - | 0x02 0x01 | 얼굴 모션, 지오메트리 ID 1 |
| 4 | payload_size | fSize | - | FaceMotionBlock 크기 (바이트) |
| fSize | payload | - | FaceMotionBlock() | 얼굴 모션 데이터 |

#### LZMA 압축

```bash
# 압축 (xz 명령 사용)
xz EU_CASA_VOLTAR.slmb
# 결과: EU_CASA_VOLTAR.slmb.xz

# 해제
unxz EU_CASA_VOLTAR.slmb.xz
# 결과: EU_CASA_VOLTAR.slmb (MotionBundle 블록)
```

#### IMSC1 Sign Language Motion Profile

MPD 파일에서의 설정:
- `SupplementalProperty` schemeIdUri: `http://dashif.org/guidelines/dash-atsc-closedcaption`
- `value`: profile set to `2`
- `codecs`: `stpp.ttml.im1m`

##### 수어 창 위치 설정 (선택사항)

| 속성 | 설명 |
|------|------|
| `SL_Window_Presentation` | 수어 창 표시 여부 (true/false) |
| `SL_Window_Position_X/Y` | 수어 창 위치 |
| `SL_Window_Width/Height` | 수어 창 크기 |
| `Video_Window_Position_X/Y` | 메인 비디오 창 위치 |
| `Video_Window_Width/Height` | 메인 비디오 창 크기 |
| `SL_AvatarBodyGeometryIds` | 호환 바디 지오메트리 ID |
| `SL_AvatarFaceGeometryIds` | 호환 얼굴 지오메트리 ID |

### 6.7 수신 프로세스 (D.5)

```
[수신기]
  MPEG-DASH 플레이어 (AdaptationSet 해석)
      │
      ▼
  MP4 파서 (서브샘플 추출)
  ├── 서브샘플 0: TTML 파일 (텍스트)
  └── 서브샘플 1+: SLMB 파일 (바이너리)
      │
      ▼
  TTML 파서
  ├── SLMB 파일 (애니메이션 데이터)
  ├── 시작 타임스탬프
  ├── 종료 타임스탬프 (선택)
  ├── 대체 텍스트 (선택)
  └── 표시 창 정보 (선택)
      │
      ▼
  SLMB 디코딩
  ├── LZMA 압축 해제 -> MotionBundle
  ├── MotionBundle 파싱 (헤더별 블록 추출)
  │   ├── key {0x01, 0x01}: BodyMotionBlock
  │   └── key {0x02, 0x01}: FaceMotionBlock
  └── 파일 변환
      ├── BodyMotionBlock -> BVH 또는 glTF
      └── FaceMotionBlock -> JSON 또는 glTF
      │
      ▼
  3D 아바타 엔진 (Blender, Maya, AR Emoji SDK 등)
      │
      ▼
  수어 렌더링 출력
```

#### MotionBundle 파싱 의사코드 (D.5.2.2)

```
pos = 0
element_size = 0
while (pos < <MotionBundle 크기>) {
    element_size = element_size + 1
    index = element_size - 1
    key_size = (MotionBundle[pos] >> 5) + 1
    payload_size = MotionBundle[pos] & 0x1F
    pos = pos + 1
    element[index].key = MotionBundle[pos to pos + key_size - 1]
    pos = pos + element[index].key_size
    if (payload_size == 0x1F) {
        payload_size = MotionBundle[pos to pos + 3]
        pos = pos + 4
    }
    element[index].payload = MotionBundle[pos to pos + payload_size - 1]
    pos = pos + payload_size
}

for (index = 0; index < element_size; index++) {
    if (element[index].key == {0x01, 0x01}) {
        BodyMotionBlock = element[index].payload
    }
    if (element[index].key == {0x02, 0x01}) {
        FaceMotionBlock = element[index].payload
    }
}
```

> 한글 설명: MotionBundle의 각 블록 헤더를 순차적으로 파싱한다. 헤더의 상위 3비트(+1)가 키 크기, 하위 5비트가 페이로드 크기를 나타낸다. 페이로드 크기가 0x1F이면 다음 4바이트에 실제 크기가 저장된다. 키 값 {0x01, 0x01}은 바디 모션, {0x02, 0x01}은 얼굴 모션을 식별한다.

---

## 7. 코드 구현 참조사항

### 7.1 글로스 파서 구현 규칙

글로스 텍스트를 파싱하여 수어 재생 명령을 생성하기 위한 규칙 적용 순서와 체크리스트:

#### 파서 토큰 인식 우선순위

| 순서 | 패턴 | 규칙 | 예시 |
|------|------|------|------|
| 1 | `[PONTO]`, `[EXCLAMACAO]`, `[INTERROGACAO]` | 구두점 (R.1.2) | 문장 경계 인식 |
| 2 | `(+)`, `(-)` 접미사 | 강도 (R.1.8) | `BONITO(+)` -> 동작 확대 |
| 3 | `NAO_` 접두사 | 부정 (R.1.7) | `NAO_PODER` -> 동시 부정 |
| 4 | `숫자S_동사_숫자S` 패턴 | 인칭-수 (R.1.6) | `1S_PERGUNTAR_2S` |
| 5 | `단어&문맥` | 동음이의어 (R.1.1) | `COLAR&ACESSORIO` |
| 6 | `단어_단어` | 복합어 (R.1.5) | `BOM_DIA`, `UM_HORA` |
| 7 | 숫자 | 숫자 표현 (R.1.4) | `4`, `PRIMEIRO&ORDINAL` |
| 8 | 나머지 단어 | 사전 조회 | `CASA`, `COMPRAR` |

#### 구현 체크리스트

- [ ] `&` 구분자로 동음이의어 분리 (글로스명 + 문맥)
- [ ] `[PONTO]`/`[PERIOD]` 양쪽 형식 지원
- [ ] `[EXCLAMACAO]`/`[EXCLAMATION]` 양쪽 형식 지원
- [ ] `[INTERROGACAO]`/`[INTERROGATION]` 양쪽 형식 지원
- [ ] 형용사 성별 통일 (여성형 -> 남성형) 전처리
- [ ] 서수 1~5번째 `&ORDINAL` 접미사 처리
- [ ] 서수 10번째 이후 기수와 동일 처리
- [ ] 수량 표현 `UM_HORA` 등 `_` 결합 처리
- [ ] 시간 약어 확장 (h -> HORA, min -> MINUTO 등)
- [ ] 분수, 백분율, 통화 기호 변환
- [ ] `_` 연결 복합어를 단일 사전 항목으로 처리
- [ ] 인칭 코드 `1S`~`3P` 파싱 및 방향 정보 추출
- [ ] `NAO_` 접두사 인식 및 동시 부정 플래그 설정
- [ ] `(+)`/`(-)` 마커 인식 및 강도 파라미터 추출
- [ ] VLibras 사전 URL 구성 및 애니메이션 다운로드

### 7.2 모션 포맷 변환기 구현 가이드

#### 변환 매트릭스

| 변환 방향 | 바디 모션 | 얼굴 모션 | 참조 섹션 |
|-----------|-----------|-----------|-----------|
| BVH -> SLMB | BodyMotionBlock 생성 | - | D.2.4.3 |
| SLMB -> BVH | BVH MOTION 생성 | - | D.2.4.4 |
| JSON -> SLMB | - | FaceMotionBlock 생성 | D.2.5.3 |
| SLMB -> JSON | - | JSON 파일 생성 | D.2.5.4 |
| SLMB -> glTF | glTF 바디 애니메이션 | glTF 얼굴 애니메이션 | D.2.6.3 |

#### 핵심 변환 공식 요약

##### 이동(Translation) 변환 (Type-0 관절만)

```
인코딩: bmb.Tx = (Xposition + 0.5) * 65535
디코딩: Xposition = bmb.Tx / 65535 - 0.5
범위: [-0.5, 0.5] <-> [0, 65535]
```

##### 회전(Rotation) 변환 - Type-0/1 (쿼터니언)

```
인코딩: bmb.Qx = qx * 32767 (qw >= 0 보장)
디코딩: qx = bmb.Qx / 32767, qw = sqrt(1 - qx^2 - qy^2 - qz^2)
범위: [-1, 1] <-> [-32767, 32767]
```

##### 회전 변환 - Type-2 (3축 오일러 패킹)

```
인코딩: E2x = (Ex + 90) / 180 * 1023      // 10비트
        E2y = (Ey + 90) / 180 * 1023      // 10비트
        E2z = (Ez + 180) / 360 * 4095     // 12비트
        bmb.E2 = (E2x << 22) + (E2y << 12) + E2z
디코딩: E2x = bmb.E2 >> 22
        E2y = (bmb.E2 >> 12) & 0x03FF
        E2z = bmb.E2 & 0x0FFF
        Ex = E2x * 180 / 1023 - 90
        Ey = E2y * 180 / 1023 - 90
        Ez = E2z * 360 / 4095 - 180
범위: Ex,Ey [-90,90], Ez [-180,180]
```

##### 회전 변환 - Type-3 (단일 축)

```
인코딩: bmb.E3 = (Ez + 180) / 360 * 255   // 8비트
디코딩: Ez = bmb.E3 * 360 / 255 - 180
범위: Ez [-180, 180] <-> [0, 255]
```

##### 회전 변환 - Type-4 (2축)

```
인코딩: E4x = (Xrotation + 90) / 180 * 255   // 8비트
        E4y = (Yrotation + 90) / 180 * 255   // 8비트
        bmb.E4 = (E4x << 8) + E4y
디코딩: E4x = bmb.E4 >> 8
        E4y = bmb.E4 & 0xFF
        Xrotation = E4x * 180 / 255 - 90
        Yrotation = E4y * 180 / 255 - 90
        Zrotation = 0
범위: X,Y [-90, 90] <-> [0, 255]
```

##### 블렌드셰이프 가중치

```
인코딩: fmb.weight = weight_float * 65535    // 16비트
디코딩: weight_float = fmb.weight / 65535
범위: [0, 1] <-> [0, 65535]
```

### 7.3 URL 기반 사전 접근 구현

```
기본 URL: https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/
사전 목록: https://dicionario2.vlibras.gov.br/bundles

접근 패턴: GET {기본 URL}{글로스명}
예시:      GET https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/CASA
```

#### 구현 체크리스트

- [ ] 사전 목록(`/bundles`)을 캐싱하여 존재하지 않는 글로스 사전 조회
- [ ] URL 인코딩 처리 (특수문자, 공백 등)
- [ ] `&` 구분자를 포함한 동음이의어 글로스의 URL 인코딩 확인
- [ ] 다운로드 실패 시 폴백 처리 (대체 텍스트 표시 등)
- [ ] 애니메이션 파일 로컬 캐싱 전략 구현

### 7.4 BVH/glTF 변환 구현 체크리스트

#### BVH 변환 구현

- [ ] BVH HIERARCHY 섹션 파서 구현 (재귀적 관절 선언)
- [ ] BVH MOTION 섹션 파서 구현 (프레임/관절/채널 순서)
- [ ] 채널 순서 검증 (Zrotation Xrotation Yrotation 필수)
- [ ] 관절 타입별 분기 처리 (Type 0~4)
- [ ] `euler2quaternion_yxz()` 함수 구현
- [ ] `euler2quaternion_xyz()` 함수 구현
- [ ] `quaternion2euler_yxz()` 함수 구현
- [ ] `quaternion2euler_xyz()` 함수 구현
- [ ] `rotationaxisToquaternion()` 함수 구현
- [ ] `wrap_to_degree()` 함수 구현 ((-180, 180] 범위)
- [ ] qw < 0 일 때 쿼터니언 부호 반전 처리
- [ ] 관절 이동 제한 값 검증 (ABNT NBR 25606, Table D.4)
- [ ] 참조 BVH 파일(`avatarModel.bvh`) 연동

#### glTF 변환 구현

- [ ] glTF 2.0 사양 준수 파서/생성기
- [ ] bufferViews/accessors 구조 생성
- [ ] animations/samplers/channels 구조 생성
- [ ] translation 채널 (Type-0 관절만)
- [ ] rotation 채널 (모든 관절, 쿼터니언 W/X/Y/Z 순서)
- [ ] weights 채널 (얼굴 메시별)
- [ ] 참조 아바타 모델(`avatarModel.zip`) 연동
- [ ] glTF.nodes 인덱스 매핑 (관절명/메시명 -> 인덱스)
- [ ] glTF.meshes.extras.targetNames 매핑
- [ ] 바이너리 버퍼 생성 및 bufferViews 오프셋 계산

#### JSON (얼굴 모션) 변환 구현

- [ ] JSON 파일 파서 (blendShapes 배열, key 행렬)
- [ ] 스파스 인코딩: 가중치 0이 아닌 블렌드셰이프만 선택
- [ ] 프레임 범위 압축 알고리즘 구현
- [ ] blend_shape_id 매핑 (ABNT NBR 25606, Table D.11)
- [ ] 메시/타겟 그룹핑 (JSON의 계층 구조 유지)

#### MotionBundle 처리 구현

- [ ] MotionBundle 헤더 파싱 (키 크기, 페이로드 크기)
- [ ] SLMB 매직 넘버 ("SLMB" = 0x53 0x4C 0x4D 0x42) 검증
- [ ] 블록 타입 식별 (0x01=바디, 0x02=얼굴, 두 번째 바이트=지오메트리 ID)
- [ ] LZMA 압축/해제 (XZ Utils 호환)
- [ ] 바디/얼굴 지오메트리 ID 호환성 확인

#### 전송/수신 통합 구현

- [ ] IMSC1 Sign Language Motion Profile TTML 문서 생성
- [ ] MP4 세그멘테이션 (서브샘플 포함)
- [ ] MPD 파일 AdaptationSet 설정 (codecs=stpp.ttml.im1m)
- [ ] sbtvd:signlanguagemotion 속성 처리 (urn:mpeg:14496-30:subs:N)
- [ ] 수어 창 위치/크기 설정 옵션 지원
- [ ] 아바타 지오메트리 ID 호환성 선택
- [ ] 사인 간 전환 부드러움 처리 (권장사항)
- [ ] 유휴 상태 전환 처리 (권장사항)

---

## 참고 문헌

| 번호 | 참고 자료 |
|------|----------|
| [1] | ABNT NBR 25606, TV 3.0 - Closed signing |
| [2] | Quaternion to Euler angles conversion (Bernardes & Viollet, PLOS ONE) |
| [3] | Motion Capture File Formats explained (Meredith & Maddock) |
| [4] | BVH Motion Capture Data Animated (CHAN Ka Chun et al.) |
| [5] | Biovision BVH |
| [6] | Galaxy AR Emoji SDK for Unity (Samsung) |
| [7] | glTF 2.0 Specification (Khronos Group, v2.0.1) |
| [8] | XZ Utils |
| [9] | Blender |
| [10] | Autodesk Maya |
| [11] | glTF Viewer |
| [12] | ISO/IEC 14496-30:2018 (Timed text in ISOBMFF) |

---

*본 보고서는 SBTVD TV 3.0 OG-06 Closed Signing 운영 가이드라인 (January 2026)의 기술 분석을 기반으로 작성되었습니다.*
