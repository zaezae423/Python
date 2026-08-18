"""주조 불량 레이블 생성 유틸리티."""
from __future__ import annotations

import numpy as np
import pandas as pd

# 수업에서는 자주 발생하는 네 불량을 주요 클래스로 따로 구분합니다.
MAJOR_DEFECTS = ["Short_Shot", "Bubble", "Exfoliation", "Blow_Hole"]

# 원본 데이터에서 확인할 전체 불량 이름입니다.
ALL_DEFECTS = [
    "Short_Shot", "Bubble", "Exfoliation", "Blow_Hole", "Stain", "Dent",
    "Deformation", "Contamination", "Impurity", "Crack", "Scratch",
    "Burning_Mark", "Inclusion",
]

# 모델이 사용하는 숫자 레이블과 사람이 읽는 클래스 이름을 연결합니다.
LABEL_NAMES = {0: "Good", 1: "Short_Shot", 2: "Bubble", 3: "Exfoliation", 4: "Blow_Hole", 5: "Etc"}


def _defect_columns(df: pd.DataFrame, cavity: str) -> list[str]:
    """지정한 캐비티에 실제로 존재하는 불량 열 이름만 반환합니다."""
    # 앞의 밑줄(_)은 이 함수가 모듈 내부에서 사용하는 보조 함수라는 관례입니다.
    return [f"Defects__{name}_{cavity}" for name in ALL_DEFECTS if f"Defects__{name}_{cavity}" in df.columns]


def create_cavity_label(df: pd.DataFrame, cavity: str) -> pd.Series:
    """cavity 1 또는 2의 불량 유형을 6개 클래스로 정리합니다.

    0: Good, 1~4: 주요 불량, 5: 기타 불량
    """
    # 현재 캐비티의 불량 원-핫 열을 찾습니다.
    cols = _defect_columns(df, cavity)
    if not cols:
        raise ValueError(f"cavity {cavity}에 해당하는 불량 컬럼을 찾지 못했습니다.")

    # 결측치는 불량 없음인 0으로 채우고 비교하기 쉬운 정수형으로 바꿉니다.
    defect_matrix = df[cols].fillna(0).astype(int)
    labels = []

    # iterrows()로 제품 한 행씩 확인하여 대표 불량 클래스를 결정합니다.
    for _, row in defect_matrix.iterrows():
        # 값이 1인 열에서 Defects__ 접두사와 _캐비티번호 접미사를 제거합니다.
        active = [c.replace("Defects__", "").rsplit("_", 1)[0] for c, v in row.items() if v == 1]
        if len(active) == 0:
            # 활성화된 불량이 하나도 없으면 양품(0)입니다.
            labels.append(0)
        else:
            # 여러 불량이 있으면 원본 열 순서에서 첫 번째 불량을 대표값으로 사용합니다.
            first = active[0]
            if first == "Short_Shot": labels.append(1)
            elif first == "Bubble": labels.append(2)
            elif first == "Exfoliation": labels.append(3)
            elif first == "Blow_Hole": labels.append(4)
            else: labels.append(5)
    # 원본 행 인덱스를 유지한 Series로 반환해야 df에 안전하게 붙일 수 있습니다.
    return pd.Series(labels, index=df.index, name=f"target_cavity{cavity}")


def make_training_table(df: pd.DataFrame) -> pd.DataFrame:
    """cavity1과 cavity2를 행 방향으로 합쳐 ML 학습용 테이블을 만듭니다."""
    # Defects 열은 정답을 만드는 데만 사용하고 모델 입력에서는 제외합니다.
    base_cols = [c for c in df.columns if not c.startswith("Defects__")]
    tables = []

    # 같은 공정 조건에서 나온 두 캐비티를 제품별 두 행으로 만듭니다.
    for cavity in ["1", "2"]:
        tmp = df[base_cols].copy()
        tmp["cavity"] = int(cavity)
        tmp["target"] = create_cavity_label(df, cavity)
        tables.append(tmp)

    # 두 캐비티 테이블을 세로로 연결하고 완전히 같은 행은 한 번만 남깁니다.
    train_df = pd.concat(tables, ignore_index=True)
    train_df = train_df.drop_duplicates().reset_index(drop=True)
    return train_df
