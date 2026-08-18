# 기계부품 품질보증 AI 데이터셋

## 1. 데이터셋 개요

이 데이터셋은 **냉간단조 설비의 상태 및 공정 데이터를 이용하여 설비 품질보증 AI를 실습**하기 위한 제조 데이터셋입니다.

- 제조 분야: 기계부품
- 제조 공정: 냉간단조
- 수집 장비: 냉간단조기
- 가이드북의 수집 기간: 2022년 1월 ~ 7월
- 제공된 실습 파일의 실제 시각 범위: **2022-05-02 06:32:33 ~ 2022-05-14 04:34:46**
- 데이터 형식: CSV, 테이블형(Tabular)
- 분석 대상: 설비 상태(`STATUS`) 분류
- 가이드북 주요 알고리즘: XGBoost Classifier

냉간단조 설비에서 이상 상태를 조기에 탐지하지 못하면 금형 파손, 불량품 대량 생산, 긴 복구 시간 등의 문제가 발생할 수 있습니다. 이 데이터는 설비 센서와 제어 데이터를 바탕으로 정상/비정상 상태를 구분하고 주요 영향 변수를 분석하는 교육용 실습에 적합합니다.

## 2. 제공 파일

### `raw_total_data.csv`

원본에 가까운 데이터입니다.

- 실제 첨부 파일 크기: 약 80.9 MB
- 실제 행 수: 579,297
- 실제 열 수: 58
- 이 중 `Unnamed: 0`은 CSV 저장 과정에서 생성된 인덱스 열이므로 분석 시 제거합니다.
- `Unnamed: 0` 제거 후에는 가이드북 설명과 동일한 **57개 열**이 됩니다.
- 많은 센서 값이 결측치로 존재합니다. 이는 값이 변하지 않았을 때 추가 기록하지 않는 수집 방식의 영향이 큽니다.

### `실습데이터.csv`

가이드북 실습용으로 정리된 데이터입니다.

- 실제 첨부 파일 크기: 약 188.8 MB
- 행 수: 579,297
- 열 수: 57
- 결측치: 0
- `Timestamp` 1개 + 수치형 변수 56개
- 가이드북 설명에 따라 결측값을 이전 시점 값으로 채운 형태의 실습 데이터입니다.

## 3. 타깃 변수 `STATUS`

실습 데이터의 실제 클래스 분포는 다음과 같습니다.

| 원래 STATUS 값 | 개수 | 비율 | 가이드북 해석 |
|---:|---:|---:|---|
| 0.0 | 99,700 | 17.211% | 정상/비정상 사이의 별도 상태 |
| 0.5 | 2,295 | 0.396% | 비정상 상태 |
| 1.0 | 4,075 | 0.703% | 정상/비정상 사이의 별도 상태 |
| 2.0 | 473,227 | 81.690% | 정상 상태 |

가이드북에서는 `LabelEncoder` 적용 후 다음과 같이 범주화합니다.

- `0.0 → 0`
- `0.5 → 1`
- `1.0 → 2`
- `2.0 → 3`

따라서 레이블 1은 비정상 상태, 레이블 3은 정상 상태에 해당합니다. 클래스 비율이 크게 다르므로 단순 정확도만으로 모델을 평가하지 말고 **Macro F1-score, 클래스별 Precision/Recall/F1-score, Confusion Matrix**를 함께 확인하는 것이 중요합니다.

## 4. 주요 변수

아래 표는 실제 `실습데이터.csv`의 컬럼명을 기준으로 `.xlsx` 확장자를 제거한 이름입니다.

| 변수명 | 구분 | 설명 |
|---|---|---|
| `Timestamp` | 시간 | 데이터 수집 시각 |
| `OUTPUT_COUNT_DAY_1` | 생산량 | 일일 생산량 #1 |
| `KO6_MOTOR_SET_FREQ` | KO#6 | KO#6 모터 설정 주파수 |
| `CUTTING_SET_FREQ` | 절단장 | 절단장 설정 주파수 |
| `STATUS` | 상태 | 설비 상태 |
| `KO5_MOTOR_SET_FREQ` | KO#5 | KO#5 모터 설정 주파수 |
| `METAL_OIL_SUPPLY_PRESS_CONTR` | 압력 | 어깨 메탈 오일공급 압력 조작측 |
| `KO4_MOTOR_SET_FREQ` | KO#4 | KO#4 모터 설정 주파수 |
| `KO2_MOTOR_SET_FREQ` | KO#2 | KO#2 모터 설정 주파수 |
| `MAIN_MOTOR_CURR` | 메인 모터 | 메인 모터 전류 |
| `KO3_MOTOR_SET_FREQ` | KO#3 | KO#3 모터 설정 주파수 |
| `TRANS_POS_UP_SET_H` | 트랜스퍼 설정 | 재료 트랜스퍼 Up 설정값 High |
| `TRANS_POS_RIGHT_SET_L` | 트랜스퍼 설정 | 재료 트랜스퍼 Right 설정값 Low |
| `TONGS_INVERTER_ALM_ERR_CD` | 집게틀 | 집게틀 인버터 알람 에러코드 |
| `KO1_MOTOR_SET_FREQ` | KO#1 | KO#1 모터 설정 주파수 |
| `KO3_MOTOR_INVERTER_ALM` | KO#3 | KO#3 인버터 알람 |
| `MAIN_MOTOR_RPM` | 메인 모터 | 메인 모터 회전수 |
| `TRANS_CURR` | 재료이송 | 재료이송 전류값 |
| `KO1_MOTOR_CURR` | KO#1 | KO#1 모터 전류값 |
| `TRANS_INVERTER_ALM_ERR_CD` | 재료이송 | 재료이송 인버터 알람 에러코드 |
| `TONGS_CAST_SET_FREQ` | 집게틀 | 집게틀 설정 주파수 |
| `TRANS_POS_LEFT_SET_H` | 트랜스퍼 설정 | 재료 트랜스퍼 Left 설정값 High |
| `KO4_MOTOR_INVERTER_ALM` | KO#4 | KO#4 인버터 알람 |
| `TRANS_POS_DOWN_SET_L` | 트랜스퍼 설정 | 재료 트랜스퍼 Down 설정값 Low |
| `KO6_MOTOR_CURR` | KO#6 | KO#6 모터 전류값 |
| `OIL_SUPPLY_PRESS` | 압력 | 윤활유 공급 압력 |
| `KO2_MOTOR_INVERTER_ALM` | KO#2 | KO#2 인버터 알람 |
| `KO3_MOTOR_CURR` | KO#3 | KO#3 모터 전류값 |
| `TRANS_POS_UP` | 트랜스퍼 변위 | 재료 트랜스퍼 변위 Up |
| `TONGS_POS` | 집게틀 | 집게틀 위치 |
| `WORK_OIL_SUPPLY_PRESS` | 압력 | 가공유 공급 압력 |
| `METAL_TEMP_CONTROL` | 온도 | 어깨 메탈 온도 조작측 |
| `TONGS_CAST_CURR` | 집게틀 | 집게틀 전류값 |
| `CUTTING_INVERTER_ALM_ERR_CD` | 절단장 | 절단장 인버터 알람 에러코드 |
| `KO6_MOTOR_INVERTER_ALM` | KO#6 | KO#6 인버터 알람 |
| `TRANS_POS_RIGHT_SET_H` | 트랜스퍼 설정 | 재료 트랜스퍼 Right 설정값 High |
| `TRANS_POS_UP_SET_L` | 트랜스퍼 설정 | 재료 트랜스퍼 Up 설정값 Low |
| `TRANS_POS_LEFT` | 트랜스퍼 변위 | 재료 트랜스퍼 변위 Left |
| `KO4_MOTOR_CURR` | KO#4 | KO#4 모터 전류값 |
| `METAL_OIL_SUPPLY_PRESS_CUT` | 압력 | 어깨 메탈 오일공급 압력 절단측 |
| `MAIN_AIR_PRESS` | 압력 | 메인 에어 압력 |
| `TRANS_POS_LEFT_SET_L` | 트랜스퍼 설정 | 재료 트랜스퍼 Left 설정값 Low |
| `TRANS_SET_FREQ` | 재료이송 | 재료이송 설정 주파수 |
| `METAL_TEMP_CUT` | 온도 | 어깨 메탈 온도 절단측 |
| `KO5_MOTOR_INVERTER_ALM` | KO#5 | KO#5 인버터 알람 |
| `MAIN_MOTOR_SET_FREQ` | 메인 모터 | 메인 모터 설정 주파수 |
| `OIL_PRESS_LEVEL_ALM` | 알람 | 유압 유니트 레벨 경고 |
| `CUTTING_CURR` | 절단장 | 절단장 전류값 |
| `KO5_MOTOR_CURR` | KO#5 | KO#5 모터 전류값 |
| `KO2_MOTOR_CURR` | KO#2 | KO#2 모터 전류값 |
| `KO1_MOTOR_INVERTER_ALM` | KO#1 | KO#1 인버터 알람 |
| `TRANS_POS_DOWN_SET_H` | 트랜스퍼 설정 | 재료 트랜스퍼 Down 설정값 High |
| `OUTPUT_COUNT_DAY_2` | 생산량 | 일일 생산량 #2 |
| `OUTPUT_COUNT_SUM` | 생산량 | 누적 생산량 |
| `TRANS_POS_DOWN` | 트랜스퍼 변위 | 재료 트랜스퍼 변위 Down |
| `TRANS_POS_RIGHT` | 트랜스퍼 변위 | 재료 트랜스퍼 변위 Right |
| `MAIN_MOTOR_ALM` | 메인 모터 | 메인 모터 알람 |

## 5. 데이터 품질 관점

가이드북은 제조 데이터 품질을 다음 6가지 관점에서 확인합니다.

- **완전성(Completeness)**: 필수 값에 누락이 없는가
- **유일성(Uniqueness)**: 중복되거나 동일해야 하지 않는 데이터가 중복되지 않는가
- **유효성(Validity)**: 정의된 형식, 범위, 도메인을 만족하는가
- **일관성(Consistency)**: 데이터 구조, 타입, 표현이 일관적인가
- **정확성(Accuracy)**: 실제 현상과 데이터가 일치하는가
- **무결성(Integrity)**: 데이터 간 관계와 품질 조건이 유지되는가

이 데이터는 시계열 센서 데이터의 특성상 `raw_total_data.csv`에 결측치가 많습니다. 가이드북에서는 **이전 시점 값으로 Forward Fill(`ffill`)**하여 실습 데이터를 구성합니다.

또한 일부 변수는 특정 값에 매우 많이 몰려 있어 일반적인 IQR 기반 이상치 제거를 그대로 적용하기 어렵습니다. 따라서 이상치를 자동 삭제하기보다 먼저 변수 분포와 공정 특성을 확인하는 것이 중요합니다.

## 6. 실습 시 주의사항

1. `Timestamp`는 모델의 일반 수치 입력값에서 제외하고, 시계열 정렬 및 데이터 품질 확인에 사용합니다.
2. `STATUS`는 종속변수(Target)이며 나머지 수치 변수는 독립변수(Feature)로 사용합니다.
3. 클래스 불균형이 크므로 `train_test_split(..., stratify=y)`를 권장합니다.
4. 가이드북은 Min-Max 정규화를 실습하지만, XGBoost와 같은 트리 기반 모델은 일반적으로 정규화가 필수는 아닙니다.
5. 정규화를 사용하는 경우 데이터 누수를 피하기 위해 학습 데이터에 `fit()`하고 테스트 데이터에는 `transform()`만 적용하는 방식이 권장됩니다.
6. 공정 최적값은 정상 상태 데이터의 평균(centroid)을 참고값으로 계산할 수 있으나, 실제 현장 적용 전에는 공정 전문가의 검증이 필요합니다.

## 7. 출처 표기

연구 또는 공식 활용 시 KAMP 가이드북의 출처 표기 조건을 확인해야 합니다.

> 중소벤처기업부, Korea AI Manufacturing Platform(KAMP), 기계부품 품질보증 AI 데이터셋, 스마트제조혁신추진단(㈜임픽스), 2022.12.23., www.kamp-ai.kr

제공기관: 스마트제조혁신추진단 / 수행기관: ㈜임픽스  
운영기관: KAIST 제조AI빅데이터센터
