"""주조 품질 데이터 EDA 함수."""
from __future__ import annotations

import pandas as pd


def target_distribution(df: pd.DataFrame, target_col: str = "target") -> pd.DataFrame:
    """클래스별 데이터 개수와 전체에서 차지하는 비율을 계산합니다."""
    # value_counts()로 클래스 빈도를 세고, sort_index()로 0, 1, 2... 순서로 정렬합니다.
    result = df[target_col].value_counts().sort_index().rename_axis(target_col).reset_index(name="count")

    # 각 클래스 개수를 전체 개수로 나누면 클래스 비율을 구할 수 있습니다.
    result["ratio"] = (result["count"] / result["count"].sum()).round(4)
    return result


def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    """수치형 열의 평균, 표준편차, 사분위수 등을 요약합니다."""
    # 문자열 열을 제외하고 숫자로 된 열 이름만 선택합니다.
    num_cols = df.select_dtypes(include="number").columns

    # describe() 결과를 전치(T)하여 변수 하나가 한 행에 나타나도록 바꿉니다.
    return df[num_cols].describe().T.reset_index(names="column")


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """결측치가 있는 열만 골라 개수와 비율을 반환합니다."""
    # isna().sum()은 결측치 개수, isna().mean()은 결측치 비율을 계산합니다.
    return pd.DataFrame({
        "missing_count": df.isna().sum(),
        "missing_rate": df.isna().mean(),
    # query()로 결측치가 1개 이상인 행만 남기고 비율이 큰 순서로 정렬합니다.
    }).query("missing_count > 0").sort_values("missing_rate", ascending=False).reset_index(names="column")
