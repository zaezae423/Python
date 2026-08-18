"""week08 Streamlit 앱을 week09 다이캐스팅 원본 데이터에 맞춘 예제입니다.

실행 방법:
    streamlit run app_week09_casting.py

기존 app.py와 달라진 핵심은 다음과 같습니다.
1. 1행 헤더 CSV 대신 Process/Sensor/Defects로 구성된 2행 헤더를 읽습니다.
2. 기존 센서 데이터용 utils 함수는 컬럼 구조가 맞지 않아 이 파일에서 전처리합니다.
3. status 대신 26개 Defects 컬럼의 합으로 OK/NG 품질 레이블을 만듭니다.
4. 설비/제품 필터 대신 Product_Type, Shot, 품질 필터를 사용합니다.
"""

# Path는 운영체제에 맞는 파일 경로를 안전하게 만드는 도구입니다.
from pathlib import Path

# pandas는 CSV처럼 표 형태로 된 데이터를 DataFrame으로 다룰 때 사용합니다.
import pandas as pd
# plotly.express는 막대그래프, 히스토그램, 산점도를 간단히 만듭니다.
import plotly.express as px
# streamlit은 Python 코드만으로 웹 화면과 입력 위젯을 만들 수 있게 해 줍니다.
import streamlit as st


# 기존 앱 폴더의 형제 폴더에 있는 week09 데이터를 가리킵니다.
# __file__ 기준 경로이므로 어느 작업 폴더에서 실행해도 같은 파일을 찾습니다.
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_FILE = (
    BASE_DIR.parent
    / "week09_Reference_data"
    / "data"
    / "DieCasting_Quality_Raw_Data.csv"
)


# Streamlit은 사용자가 위젯을 조작할 때마다 이 파일을 처음부터 다시 실행합니다.
# cache_data를 붙이면 같은 파일은 매번 다시 읽지 않고 이전 결과를 재사용합니다.
@st.cache_data
def load_casting_data(file_source):
    """2행 헤더 CSV를 읽고 분석하기 쉬운 단일 헤더로 변환합니다."""
    # 이 CSV의 첫 번째 행은 Process/Sensor/Defects 그룹이고,
    # 두 번째 행은 실제 변수명입니다. 따라서 header=[0, 1]이 필요합니다.
    raw_df = pd.read_csv(file_source, header=[0, 1], encoding="utf-8-sig")

    # 평탄화하기 전에 그룹별 컬럼명을 저장하면 화면에서 공정 변수와
    # 센서 변수, 불량 변수를 구분해 선택 상자에 사용할 수 있습니다.
    column_groups = {}

    # get_level_values(0)는 첫 번째 헤더 행만 가져옵니다.
    # unique()를 사용하여 Process, Sensor, Defects를 한 번씩만 꺼냅니다.
    group_names = raw_df.columns.get_level_values(0).unique()

    for group_name in group_names:
        # 현재 그룹에 속한 컬럼 이름을 담을 빈 리스트입니다.
        columns_in_group = []

        # raw_df.columns의 각 값은 (첫 번째 헤더, 두 번째 헤더) 튜플입니다.
        for group, column_name in raw_df.columns:
            if group == group_name:
                # strip()은 컬럼 이름 앞뒤의 불필요한 공백을 지웁니다.
                columns_in_group.append(str(column_name).strip())

        # 예: column_groups["Sensor"] = ["Air_Pressure", ...]
        clean_group_name = str(group_name).strip()
        column_groups[clean_group_name] = columns_in_group

    # 실제 분석에서는 두 번째 헤더의 변수명만 사용합니다.
    df = raw_df.copy()
    flat_column_names = []
    for _, column_name in df.columns:
        flat_column_names.append(str(column_name).strip())
    df.columns = flat_column_names

    # CSV 값은 모두 수치형이어야 합니다. 변환할 수 없는 값은 NaN으로 바꾼 뒤
    # 중앙값으로 채워 그래프와 집계가 중단되지 않게 합니다.
    for column in df.columns:
        # errors="coerce"는 숫자로 바꿀 수 없는 값을 NaN(결측값)으로 만듭니다.
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # select_dtypes()로 숫자 컬럼만 선택합니다.
    numeric_columns = df.select_dtypes(include="number").columns

    # median()은 각 컬럼의 중앙값을 계산합니다.
    # fillna()는 비어 있는 값을 해당 컬럼의 중앙값으로 채웁니다.
    df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())

    defect_columns = column_groups.get("Defects", [])
    if not defect_columns:
        raise ValueError("Defects 그룹을 찾을 수 없습니다. 2행 헤더를 확인하세요.")

    # 어느 cavity에서든 불량 항목이 하나 이상이면 해당 Shot을 NG로 판정합니다.
    # defect_count는 한 Shot에서 발생한 불량 항목의 총개수입니다.
    # axis=1은 세로(컬럼)가 아니라 가로(한 행)를 기준으로 더한다는 뜻입니다.
    df["defect_count"] = df[defect_columns].sum(axis=1)

    # gt(0)은 값이 0보다 큰지 검사하여 True 또는 False를 만듭니다.
    has_defect = df["defect_count"].gt(0)
    # map()으로 True는 NG, False는 OK라는 문자로 바꿉니다.
    df["quality"] = has_defect.map({True: "NG", False: "OK"})

    return df, column_groups


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """한글 Excel에서도 열기 쉽도록 UTF-8 BOM을 포함한 CSV를 만듭니다."""
    # index=False를 지정하면 DataFrame의 왼쪽 행 번호는 파일에 저장하지 않습니다.
    csv_text = df.to_csv(index=False)
    return csv_text.encode("utf-8-sig")


def main() -> None:
    """다이캐스팅 품질 데이터용 Streamlit 화면을 구성합니다."""
    # set_page_config는 다른 Streamlit 화면 명령보다 먼저 실행해야 합니다.
    # layout="wide"는 표와 그래프가 넓게 보이도록 화면 전체 폭을 사용합니다.
    st.set_page_config(page_title="다이캐스팅 품질 분석", layout="wide")
    st.title("다이캐스팅 품질 분석 앱")
    st.caption(
        "week09 원본 데이터의 공정·센서 변수와 cavity별 불량 발생 패턴을 탐색합니다."
    )

    # 업로드 파일이 없으면 week09 기본 CSV를 사용합니다.
    # 업로드하는 CSV도 같은 2행 헤더 구조여야 합니다.
    uploaded_file = st.sidebar.file_uploader("2행 헤더 CSV 업로드", type=["csv"])
    # 업로드 파일이 있으면 그것을 사용하고, 없으면 기본 파일 경로를 사용합니다.
    if uploaded_file is not None:
        file_source = uploaded_file
    else:
        file_source = DEFAULT_FILE

    try:
        df, column_groups = load_casting_data(file_source)
    except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
        st.error(f"데이터를 읽지 못했습니다: {error}")
        st.info(f"기본 데이터 경로: {DEFAULT_FILE}")
        st.stop()

    # get(키, 기본값)은 키가 없을 때 오류 대신 빈 리스트를 반환합니다.
    process_columns = column_groups.get("Process", [])
    sensor_columns = column_groups.get("Sensor", [])
    defect_columns = column_groups.get("Defects", [])

    # 원본 구조가 다른 파일을 잘못 선택했을 때 뒤의 코드에서 발생할
    # KeyError보다 이해하기 쉬운 안내를 먼저 표시합니다.
    required_columns = {"Product_Type", "Shot"}
    # 집합의 빼기 연산으로 필수 컬럼 중 실제 데이터에 없는 컬럼을 찾습니다.
    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        st.error(f"필수 컬럼이 없습니다: {missing_columns}")
        st.stop()

    # ------------------------------------------------------------------
    # 사이드바 메뉴와 필터: machine_id/product_id 대신 week09 변수를 사용합니다.
    # ------------------------------------------------------------------
    page = st.sidebar.radio(
        "분석 메뉴",
        ["1. 데이터 확인", "2. 품질 현황", "3. 공정·센서 EDA", "4. 결과 다운로드"],
    )
    st.sidebar.divider()
    st.sidebar.subheader("데이터 필터")

    # dropna()는 결측값 제거, unique()는 중복 제거, sorted()는 정렬입니다.
    product_values = df["Product_Type"].dropna().unique().tolist()
    product_values = sorted(product_values)
    product_options = ["전체"] + product_values
    selected_product = st.sidebar.selectbox("제품 유형", product_options)

    shot_min = int(df["Shot"].min())
    shot_max = int(df["Shot"].max())
    selected_shot_range = st.sidebar.slider(
        "Shot 범위", shot_min, shot_max, (shot_min, shot_max)
    )
    selected_quality = st.sidebar.multiselect(
        "품질", ["OK", "NG"], default=["OK", "NG"]
    )

    # 여러 필터 조건을 Boolean Series로 만든 뒤 한 번에 적용합니다.
    # slider가 반환한 (최솟값, 최댓값)을 두 변수에 나누어 저장합니다.
    selected_shot_min, selected_shot_max = selected_shot_range

    # between()은 Shot이 선택 범위 안에 있는 행을 True로 표시합니다.
    shot_condition = df["Shot"].between(selected_shot_min, selected_shot_max)
    # isin()은 quality가 사용자가 선택한 목록에 들어 있는지 검사합니다.
    quality_condition = df["quality"].isin(selected_quality)
    # & 연산자는 두 조건이 모두 True인 행만 선택합니다.
    mask = shot_condition & quality_condition

    # 제품 유형이 '전체'가 아닐 때만 제품 조건을 추가합니다.
    if selected_product != "전체":
        product_condition = df["Product_Type"].eq(selected_product)
        mask = mask & product_condition

    # loc[mask]로 조건에 맞는 행만 꺼냅니다.
    # copy()를 사용하면 이후 변경이 원본 df에 영향을 주지 않습니다.
    filtered_df = df.loc[mask].copy()

    if page == "1. 데이터 확인":
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("행 수", f"{len(df):,}")
        col2.metric("원본 열 수", len(process_columns + sensor_columns + defect_columns))
        col3.metric("결측값", f"{int(df.isna().sum().sum()):,}")
        col4.metric("중복 행", f"{int(df.duplicated().sum()):,}")

        st.subheader("원본 데이터 미리보기")
        st.dataframe(df.head(100), use_container_width=True)

        # 2행 헤더가 어떤 역할로 나뉘는지 별도 표로 보여 줍니다.
        st.subheader("컬럼 그룹")
        # 화면에 표시할 행들을 먼저 리스트에 하나씩 추가합니다.
        group_rows = []
        for group, columns in column_groups.items():
            group_rows.append(
                {
                    "그룹": group,
                    "컬럼 수": len(columns),
                    "컬럼": ", ".join(columns),
                }
            )
        # 딕셔너리 리스트를 표 형태의 DataFrame으로 바꿉니다.
        group_table = pd.DataFrame(group_rows)
        st.dataframe(group_table, use_container_width=True, hide_index=True)

    elif page == "2. 품질 현황":
        total_count = len(filtered_df)
        # quality가 NG이면 True입니다. Python에서는 True를 1처럼 더할 수 있으므로
        # sum() 결과가 NG 행의 개수가 됩니다.
        ng_count = int(filtered_df["quality"].eq("NG").sum())
        ok_count = total_count - ng_count
        # 데이터가 0행일 때 0으로 나누는 오류가 생기지 않도록 조건을 둡니다.
        ng_rate = ng_count / total_count * 100 if total_count else 0.0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("필터 행 수", f"{total_count:,}")
        col2.metric("OK", f"{ok_count:,}")
        col3.metric("NG", f"{ng_count:,}")
        col4.metric("NG 비율", f"{ng_rate:.2f}%")

        if filtered_df.empty:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
            st.stop()

        left, right = st.columns(2)
        with left:
            # value_counts()는 OK와 NG가 각각 몇 행인지 셉니다.
            quality_counts = filtered_df["quality"].value_counts()
            quality_counts = quality_counts.rename_axis("quality")
            quality_counts = quality_counts.reset_index(name="count")
            fig = px.bar(
                quality_counts,
                x="quality",
                y="count",
                color="quality",
                title="OK / NG 분포",
            )
            st.plotly_chart(fig, use_container_width=True)
        with right:
            # 각 불량 컬럼의 1 값을 합산하면 해당 불량의 총 발생 횟수입니다.
            defect_counts = filtered_df[defect_columns].sum()
            defect_counts = defect_counts.sort_values(ascending=False)
            # 한 번도 발생하지 않은 불량은 그래프에서 제외합니다.
            defect_counts = defect_counts[defect_counts.gt(0)]
            defect_counts = defect_counts.rename_axis("defect")
            defect_counts = defect_counts.reset_index(name="count")
            fig = px.bar(
                defect_counts,
                x="count",
                y="defect",
                orientation="h",
                title="불량 유형별 발생 횟수",
            )
            st.plotly_chart(fig, use_container_width=True)

    elif page == "3. 공정·센서 EDA":
        st.subheader("공정·센서 변수 탐색")
        # id, 제품 유형, Shot은 구분용 컬럼이므로 수치 분포 분석에서 제외합니다.
        excluded_columns = {"id", "Product_Type", "Shot"}
        analysis_columns = []
        for column in process_columns + sensor_columns:
            if column not in excluded_columns:
                analysis_columns.append(column)
        selected_column = st.selectbox("분석 변수", analysis_columns)

        if filtered_df.empty:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
            st.stop()

        left, right = st.columns(2)
        with left:
            fig = px.histogram(
                filtered_df,
                x=selected_column,
                color="quality",
                barmode="overlay",
                marginal="box",
                title=f"{selected_column} 분포",
            )
            st.plotly_chart(fig, use_container_width=True)
        with right:
            fig = px.scatter(
                filtered_df,
                x="Shot",
                y=selected_column,
                color="quality",
                hover_data=["Product_Type", "defect_count"],
                title=f"Shot별 {selected_column}",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("품질별 요약 통계")
        # groupby()로 OK와 NG를 나눈 뒤 선택 변수의 기초 통계를 계산합니다.
        summary = filtered_df.groupby("quality")[selected_column].describe().T
        st.dataframe(summary, use_container_width=True)

    else:
        st.subheader("필터 결과 다운로드")
        st.write(f"현재 조건에 해당하는 {len(filtered_df):,}행을 저장합니다.")
        st.dataframe(filtered_df.head(100), use_container_width=True)
        st.download_button(
            "다이캐스팅 분석 결과 CSV",
            data=to_csv_bytes(filtered_df),
            file_name="die_casting_quality_result.csv",
            mime="text/csv",
            disabled=filtered_df.empty,
        )


if __name__ == "__main__":
    main()
