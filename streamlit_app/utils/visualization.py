"""Plotly를 사용해 센서 분석용 그래프를 만드는 함수 모음입니다.

각 함수는 그래프를 화면에 직접 출력하지 않고 Figure 객체를 반환합니다.
따라서 Streamlit 화면에서 원하는 위치에 st.plotly_chart()로 표시할 수 있습니다.
"""

import pandas as pd
import plotly.express as px


def make_time_series(df: pd.DataFrame, y_column: str):
    """시간에 따른 센서값을 설비별 선그래프로 만듭니다."""
    # 시간순으로 정렬해야 선이 실제 측정 순서대로 연결됩니다.
    # color에 machine_id를 지정하면 설비마다 다른 색상의 선이 만들어집니다.
    return px.line(
        df.sort_values("timestamp"),
        x="timestamp",
        y=y_column,
        color="machine_id",
        markers=True,
        title=f"{y_column} 시간 추세",
    )


def make_histogram(df: pd.DataFrame, column: str):
    """센서값 분포를 히스토그램으로 만듭니다."""
    # quality 컬럼이 있으면 OK/NG별 색을 사용하고, 없으면 단일 색으로 표시합니다.
    # barmode="overlay"는 여러 그룹의 막대를 겹쳐서 분포를 비교하게 합니다.
    return px.histogram(
        df,
        x=column,
        color="quality" if "quality" in df.columns else None,
        barmode="overlay",
        title=f"{column} 분포",
    )


def make_scatter(df: pd.DataFrame, x_column: str, y_column: str):
    """두 센서 변수의 관계를 산점도로 만듭니다."""
    # 판정 결과가 있으면 품질별로, 없으면 설비별로 점의 색을 구분합니다.
    # hover_data는 마우스를 점 위에 올렸을 때 보여 줄 추가 정보입니다.
    return px.scatter(
        df,
        x=x_column,
        y=y_column,
        color="quality" if "quality" in df.columns else "machine_id",
        hover_data=["timestamp", "machine_id", "product_id"],
        title=f"{x_column} vs {y_column}",
    )


def make_quality_bar(df: pd.DataFrame):
    """OK/NG 개수를 막대그래프로 만듭니다."""
    # value_counts()로 quality별 행 개수를 세고, 그래프에 넣기 좋은 표로 변환합니다.
    count_df = (
        df["quality"]
        .value_counts()
        .rename_axis("quality")
        .reset_index(name="count")
    )
    return px.bar(count_df, x="quality", y="count", title="OK / NG 판정 결과")
