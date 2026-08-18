"""제조 센서 데이터를 분석하는 Streamlit 통합 실습 앱입니다.

이 파일은 사용자의 입력과 화면 출력을 담당합니다. 실제 데이터 처리와 그래프 생성은
utils 폴더의 함수에 맡겨, 화면 코드와 처리 코드를 분리하는 구조를 연습합니다.

전체 흐름:
파일 선택 → 데이터 검증 → 전처리 → 조건별 탐색 → OK/NG 판정 → 결과 다운로드
"""

# pathlib.Path는 운영체제에 맞는 파일 경로를 안전하게 만들 때 사용합니다.
from pathlib import Path

# pandas는 표 형태의 데이터를 DataFrame으로 다루는 라이브러리입니다.
import pandas as pd
# streamlit은 Python 코드로 웹 화면과 입력 위젯을 만드는 라이브러리입니다.
import streamlit as st

# 데이터 처리에 필요한 값과 함수를 utils 모듈에서 가져옵니다.
# 기능을 별도 파일로 분리하면 여러 화면에서 같은 코드를 재사용할 수 있습니다.
from utils.data_processing import (
    DEFAULT_THRESHOLDS,
    NUMERIC_COLUMNS,
    add_rule_quality,
    apply_filters,
    basic_profile,
    clean_sensor_data,
    load_table,
    make_machine_report,
    make_summary_report,
    to_csv_bytes,
    validate_columns,
)
# 그래프 생성 함수도 별도 모듈에서 가져옵니다.
# 이 함수들은 Plotly Figure 객체를 만들고, 실제 출력은 이 파일에서 담당합니다.
from utils.visualization import (
    make_histogram,
    make_quality_bar,
    make_scatter,
    make_time_series,
)


# __file__은 현재 실행 중인 app.py의 경로입니다.
# resolve()는 절대 경로로 바꾸고, parent는 app.py가 들어 있는 프로젝트 폴더를 뜻합니다.
# 이렇게 하면 어느 폴더에서 실행해도 항상 같은 data 폴더를 찾을 수 있습니다.
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_FILE = BASE_DIR / "data" / "week07_sensor_sample_raw.csv"


# Streamlit은 위젯을 조작할 때마다 파일 전체를 위에서부터 다시 실행합니다.
# @st.cache_data를 사용하면 파일이 바뀌지 않은 동안 이전 읽기 결과를 재사용하므로
# 같은 CSV를 불필요하게 반복해서 읽지 않습니다.
@st.cache_data
def load_default_data() -> pd.DataFrame:
    """업로드 파일이 없을 때 사용할 기본 샘플 데이터를 읽습니다."""
    # utf-8-sig는 Windows Excel에서 저장한 한글 CSV도 비교적 안전하게 읽는 인코딩입니다.
    return pd.read_csv(DEFAULT_FILE, encoding="utf-8-sig")


def show_header() -> None:
    """앱 상단에 제목과 전체 학습 흐름을 표시합니다."""
    st.title("제조 센서 데이터 분석 앱")
    st.caption(
        "7주차 데이터 처리 결과를 Streamlit으로 연결합니다: "
        "업로드 → 확인 → 전처리 → 필터·EDA → 상태 판정 → 다운로드"
    )


def main() -> None:
    """Streamlit 화면을 순서대로 구성하고 사용자 선택에 맞는 메뉴를 실행합니다."""
    # 페이지 설정은 다른 Streamlit 명령보다 먼저 실행해야 합니다.
    # layout="wide"는 브라우저의 넓은 영역을 사용하여 표와 그래프를 보기 좋게 합니다.
    st.set_page_config(
        page_title="제조AX Streamlit 1일 통합 실습",
        layout="wide",
    )
    show_header()

    # ---------------------------------------------------------
    # 1. 파일 업로드
    # ---------------------------------------------------------
    # sidebar는 화면 왼쪽 영역입니다. type을 지정하면 선택 가능한 확장자를 제한합니다.
    # 업로드하지 않으면 uploaded_file에는 None이 저장됩니다.
    uploaded_file = st.sidebar.file_uploader(
        "CSV 또는 Excel 파일 업로드",
        type=["csv", "xlsx"],
    )

    # 조건 표현식: 업로드 파일이 있으면 해당 파일을, 없으면 기본 샘플을 읽습니다.
    # try/except는 잘못된 파일이나 읽기 오류로 앱 전체가 중단되는 것을 막습니다.
    try:
        raw_df = load_table(uploaded_file) if uploaded_file else load_default_data()
    except Exception as error:
        st.error(f"파일을 읽지 못했습니다: {error}")
        # st.stop()은 현재 실행만 안전하게 멈추고, 사용자가 새 파일을 선택할 수 있게 합니다.
        st.stop()

    # 분석에 꼭 필요한 컬럼이 모두 있는지 전처리 전에 먼저 검사합니다.
    missing_columns = validate_columns(raw_df)
    if missing_columns:
        st.error(f"필수 컬럼이 없습니다: {missing_columns}")
        st.info(
            "필수 컬럼: timestamp, machine_id, product_id, temperature, "
            "pressure, speed, humidity, vibration, current, status"
        )
        st.stop()

    # ---------------------------------------------------------
    # 2. 전처리
    # ---------------------------------------------------------
    # 하나의 함수가 튜플로 반환한 세 결과를 각각의 변수에 나누어 저장합니다.
    # clean_df: 분석 가능한 데이터, outlier_df: 범위 밖 데이터,
    # quality_report: 전처리 전후 행 수와 이상치 개수 등의 요약 딕셔너리입니다.
    clean_df, outlier_df, quality_report = clean_sensor_data(raw_df)

    # ---------------------------------------------------------
    # 3. 사이드바 메뉴와 필터
    # ---------------------------------------------------------
    # radio는 여러 메뉴 중 하나만 선택하는 위젯입니다.
    # 선택 결과 문자열이 page에 저장되며 아래 if/elif 분기의 기준이 됩니다.
    page = st.sidebar.radio(
        "수업 메뉴",
        [
            "1. 데이터 확인",
            "2. 전처리·품질 진단",
            "3. 필터·EDA",
            "4. Rule 기반 상태 판정",
            "5. 결과 다운로드",
        ],
    )

    st.sidebar.divider()
    st.sidebar.subheader("데이터 필터")

    # unique()로 중복 없는 값을 얻고, 리스트로 변환한 뒤 sorted()로 정렬합니다.
    # 앞에 '전체'를 추가하여 필터를 적용하지 않는 선택지도 제공합니다.
    machine_options = ["전체"] + sorted(clean_df["machine_id"].unique().tolist())
    product_options = ["전체"] + sorted(clean_df["product_id"].unique().tolist())

    # selectbox의 반환값은 사용자가 현재 선택한 항목입니다.
    selected_machine = st.sidebar.selectbox("설비", machine_options)
    selected_product = st.sidebar.selectbox("제품", product_options)

    # 두 선택 조건을 모두 적용한 새 DataFrame을 만듭니다.
    # 이후 EDA와 판정은 원본 전체가 아닌 이 필터 결과를 사용합니다.
    filtered_df = apply_filters(
        clean_df,
        machine_id=selected_machine,
        product_id=selected_product,
    )

    # ---------------------------------------------------------
    # 메뉴 1: 데이터 확인
    # ---------------------------------------------------------
    if page == "1. 데이터 확인":
        # 원본 데이터의 행·열·결측값·중복 개수를 딕셔너리로 계산합니다.
        profile = basic_profile(raw_df)

        # st.columns(4)는 화면을 같은 너비의 네 영역으로 나눕니다.
        # metric은 핵심 수치를 카드 형태로 강조하여 보여 줍니다.
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("행 수", f"{profile['rows']:,}")
        col2.metric("열 수", profile["columns"])
        col3.metric("결측값", profile["missing"])
        col4.metric("중복 행", profile["duplicates"])

        st.subheader("원본 데이터 미리보기")
        # head(100)은 데이터가 많아도 첫 100행만 빠르게 미리 보여 줍니다.
        st.dataframe(raw_df.head(100), use_container_width=True)

        st.subheader("컬럼과 자료형")
        # 컬럼별 이름, 자료형, 결측값 개수를 같은 길이의 리스트로 만든 뒤
        # 새로운 DataFrame으로 묶어 데이터 구조를 한눈에 확인합니다.
        column_info = pd.DataFrame(
            {
                "column": raw_df.columns,
                "dtype": [str(raw_df[col].dtype) for col in raw_df.columns],
                "missing": [int(raw_df[col].isna().sum()) for col in raw_df.columns],
            }
        )
        st.dataframe(column_info, use_container_width=True)

        st.subheader("숫자 데이터 요약")
        # describe()는 개수, 평균, 표준편차, 최솟값, 사분위수, 최댓값을 계산합니다.
        # .T는 행과 열을 바꾸어 센서 변수가 세로로 보이게 합니다.
        st.dataframe(raw_df[NUMERIC_COLUMNS].describe().T, use_container_width=True)

    # ---------------------------------------------------------
    # 메뉴 2: 전처리·품질 진단
    # ---------------------------------------------------------
    elif page == "2. 전처리·품질 진단":
        # quality_report는 clean_sensor_data()에서 만든 전처리 요약 딕셔너리입니다.
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("전처리 전", quality_report["before_rows"])
        col2.metric("전처리 후", quality_report["after_rows"])
        col3.metric("중복", quality_report["duplicate_count"])
        col4.metric("유효범위 밖", quality_report["outlier_count"])

        st.subheader("전처리 내용")
        # Markdown 문자열 끝의 공백 두 칸은 화면에서 줄바꿈을 의미합니다.
        st.markdown(
            """
            1. `timestamp`를 날짜/시간 형식으로 변환  
            2. 문자 공백과 대소문자 정리  
            3. 중복 행 제거  
            4. 숫자 결측치를 중앙값으로 대체  
            5. 센서 유효 범위를 벗어난 행 분리
            """
        )

        # with 블록 안의 요소는 해당 열 영역에 배치됩니다.
        left, right = st.columns(2)
        with left:
            st.write("전처리 후 데이터")
            st.dataframe(clean_df.head(100), use_container_width=True)
        with right:
            st.write("유효 범위를 벗어난 데이터")
            st.dataframe(outlier_df, use_container_width=True)

    # ---------------------------------------------------------
    # 메뉴 3: 필터·EDA
    # ---------------------------------------------------------
    elif page == "3. 필터·EDA":
        # EDA(Exploratory Data Analysis)는 그래프와 요약 통계로 데이터의 특징을
        # 탐색하는 과정입니다. 사이드바에서 고른 설비와 제품 데이터만 사용합니다.
        st.subheader("대화형 탐색적 데이터 분석")

        col1, col2, col3 = st.columns(3)
        col1.metric("필터 행 수", len(filtered_df))
        col2.metric("선택 설비", selected_machine)
        col3.metric("선택 제품", selected_product)

        # 사용자가 분석 목적에 맞는 그래프 종류를 직접 선택합니다.
        chart_type = st.selectbox(
            "차트 유형",
            ["시간 추세", "히스토그램", "산점도"],
        )

        # 선택한 차트에 필요한 추가 변수와 그래프 생성 함수를 결정합니다.
        if chart_type == "시간 추세":
            y_column = st.selectbox("센서 변수", NUMERIC_COLUMNS)
            fig = make_time_series(filtered_df, y_column)
        elif chart_type == "히스토그램":
            column = st.selectbox("센서 변수", NUMERIC_COLUMNS)
            fig = make_histogram(filtered_df, column)
        else:
            x_column = st.selectbox("X축", NUMERIC_COLUMNS, index=0)
            y_column = st.selectbox("Y축", NUMERIC_COLUMNS, index=4)
            fig = make_scatter(filtered_df, x_column, y_column)

        # utils의 함수가 반환한 Plotly Figure를 Streamlit 화면에 출력합니다.
        st.plotly_chart(fig, use_container_width=True)
        # 그래프 아래에는 현재 필터 결과의 기초 통계도 함께 제공합니다.
        st.dataframe(
            filtered_df[NUMERIC_COLUMNS].describe().T,
            use_container_width=True,
        )

    # ---------------------------------------------------------
    # 메뉴 4: Rule 기반 상태 판정
    # ---------------------------------------------------------
    elif page == "4. Rule 기반 상태 판정":
        # Rule 기반 판정은 사람이 정한 임계값과 센서값을 비교하는 단순한 기준입니다.
        # 학습 모델의 성능을 비교하기 위한 출발점(Baseline)으로 사용할 수 있습니다.
        st.subheader("Rule 기반 OK / NG 판정")

        st.info(
            "Rule 기반 판정은 9주차 머신러닝과 10주차 이상탐지 모델의 "
            "비교 기준선(Baseline)으로 사용합니다."
        )

        st.sidebar.divider()
        st.sidebar.subheader("판정 기준")

        # number_input으로 입력한 여섯 기준을 딕셔너리에 모읍니다.
        # value는 화면을 처음 열었을 때 표시할 기본값이며 float로 형식을 통일합니다.
        thresholds = {
            "temperature_max": st.sidebar.number_input(
                "온도 상한", value=float(DEFAULT_THRESHOLDS["temperature_max"])
            ),
            "pressure_max": st.sidebar.number_input(
                "압력 상한", value=float(DEFAULT_THRESHOLDS["pressure_max"])
            ),
            "speed_min": st.sidebar.number_input(
                "속도 하한", value=float(DEFAULT_THRESHOLDS["speed_min"])
            ),
            "humidity_max": st.sidebar.number_input(
                "습도 상한", value=float(DEFAULT_THRESHOLDS["humidity_max"])
            ),
            "vibration_max": st.sidebar.number_input(
                "진동 상한", value=float(DEFAULT_THRESHOLDS["vibration_max"])
            ),
            "current_max": st.sidebar.number_input(
                "전류 상한", value=float(DEFAULT_THRESHOLDS["current_max"])
            ),
        }

        # 각 행이 기준을 위반했는지 검사하여 quality와 ng_reason 컬럼을 추가합니다.
        result_df = add_rule_quality(filtered_df, thresholds)
        # session_state는 Streamlit이 파일을 다시 실행해도 값을 유지하는 저장 공간입니다.
        # 여기 저장해야 다음 '결과 다운로드' 메뉴에서도 방금 판정한 결과를 사용할 수 있습니다.
        st.session_state["result_df"] = result_df

        # 비교 결과는 True/False Series입니다. True를 합산하면 NG 행 수가 됩니다.
        total_count = len(result_df)
        ng_count = int((result_df["quality"] == "NG").sum())
        ok_count = total_count - ng_count
        # 행이 하나도 없을 때 0으로 나누는 오류가 발생하지 않도록 조건을 둡니다.
        ng_ratio = ng_count / total_count * 100 if total_count else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("전체", total_count)
        col2.metric("OK", ok_count)
        col3.metric("NG", ng_count)
        col4.metric("NG 비율", f"{ng_ratio:.1f}%")

        # 왼쪽에는 OK/NG 개수, 오른쪽에는 시간에 따른 온도 변화를 표시합니다.
        left, right = st.columns(2)
        with left:
            st.plotly_chart(make_quality_bar(result_df), use_container_width=True)
        with right:
            st.plotly_chart(
                make_time_series(result_df, "temperature"),
                use_container_width=True,
            )

        st.subheader("NG 알람 이력")
        # Boolean 인덱싱으로 quality 값이 NG인 행만 선택합니다.
        alarm_df = result_df[result_df["quality"] == "NG"]
        # 알람 확인에 필요한 컬럼만 정해진 순서로 보여 줍니다.
        st.dataframe(
            alarm_df[
                [
                    "timestamp",
                    "machine_id",
                    "product_id",
                    "quality",
                    "ng_reason",
                ]
            ],
            use_container_width=True,
        )

        st.subheader("설비별 품질 요약")
        st.dataframe(make_machine_report(result_df), use_container_width=True)

    # ---------------------------------------------------------
    # 메뉴 5: 결과 다운로드
    # ---------------------------------------------------------
    else:
        # 앞의 네 문자열에 해당하지 않는 마지막 메뉴가 선택되면 이 블록이 실행됩니다.
        st.subheader("분석 결과 다운로드")

        # 저장된 판정 결과가 있으면 가져오고, 아직 판정 메뉴를 방문하지 않았다면
        # 현재 필터 데이터와 기본 임계값으로 즉시 결과를 만들어 사용합니다.
        result_df = st.session_state.get(
            "result_df",
            add_rule_quality(filtered_df),
        )
        # 다운로드 목적에 맞게 전체 요약, 설비별 요약, NG 알람 표를 각각 준비합니다.
        summary_report = make_summary_report(result_df)
        machine_report = make_machine_report(result_df)
        alarm_df = result_df[result_df["quality"] == "NG"].copy()

        st.write("전체 요약")
        st.dataframe(summary_report, use_container_width=True)

        st.write("설비별 요약")
        st.dataframe(machine_report, use_container_width=True)

        # 다운로드 버튼을 세 열로 배치합니다.
        # pandas DataFrame은 to_csv_bytes()에서 CSV 바이트 데이터로 변환됩니다.
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                "판정 결과 CSV",
                data=to_csv_bytes(result_df),
                file_name="streamlit_quality_result.csv",
                mime="text/csv",
            )
        with col2:
            st.download_button(
                "설비별 리포트 CSV",
                data=to_csv_bytes(machine_report),
                file_name="streamlit_machine_report.csv",
                mime="text/csv",
            )
        with col3:
            st.download_button(
                "알람 이력 CSV",
                data=to_csv_bytes(alarm_df),
                file_name="streamlit_alarm_report.csv",
                mime="text/csv",
            )

        st.success(
            "7주차의 파일 처리·전처리·Rule 판정 코드가 "
            "Streamlit 웹 앱으로 연결되었습니다."
        )


if __name__ == "__main__":
    # 이 파일을 직접 실행할 때만 main()을 호출합니다.
    # 다른 Python 파일에서 app을 import할 때 화면 코드가 즉시 실행되는 것을 막습니다.
    main()
