"""센서 데이터를 읽고, 정리하고, 품질을 판정하는 공통 함수 모음입니다.

Streamlit 화면 파일에서 데이터 처리 코드를 분리하면 같은 기능을 여러 화면에서
재사용할 수 있고, 화면 코드도 더 짧고 읽기 쉬워집니다.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd


# 분석을 시작하기 전에 반드시 존재해야 하는 컬럼입니다.
# 리스트로 한곳에 모아 두면 컬럼 검증 규칙을 수정하기 쉽습니다.
REQUIRED_COLUMNS = [
    "timestamp",
    "machine_id",
    "product_id",
    "temperature",
    "pressure",
    "speed",
    "humidity",
    "vibration",
    "current",
    "status",
]

# 숫자로 변환하거나 통계 계산에 사용할 센서 컬럼만 따로 관리합니다.
NUMERIC_COLUMNS = [
    "temperature",
    "pressure",
    "speed",
    "humidity",
    "vibration",
    "current",
]

# 7주차 5일차 실습에서 사용한 센서 유효 범위
VALID_RANGES = {
    "temperature": (0, 100),
    "pressure": (0, 10),
    "speed": (0, 20),
    "humidity": (0, 100),
    "vibration": (0, 10),
    "current": (0, 20),
}

# 7주차 5일차 Rule 기반 판정 기준
DEFAULT_THRESHOLDS = {
    "temperature_max": 30.0,
    "pressure_max": 3.2,
    "speed_min": 4.0,
    "humidity_max": 70.0,
    "vibration_max": 2.5,
    "current_max": 10.0,
}


def load_table(file_source) -> pd.DataFrame:
    """CSV 또는 Excel 파일을 DataFrame으로 읽습니다."""
    # 파일이 없을 때 pandas에서 복잡한 오류가 발생하기 전에 명확한 안내를 줍니다.
    if file_source is None:
        raise ValueError("읽을 파일이 없습니다.")

    # Streamlit UploadedFile 또는 일반 파일 경로를 모두 지원합니다.
    file_name = getattr(file_source, "name", str(file_source))
    suffix = Path(file_name).suffix.lower()

    # 확장자에 따라 알맞은 pandas 읽기 함수를 선택합니다.
    if suffix == ".csv":
        return pd.read_csv(file_source, encoding="utf-8-sig")
    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(file_source)

    raise ValueError("CSV 또는 Excel 파일만 사용할 수 있습니다.")


def validate_columns(df: pd.DataFrame) -> list[str]:
    """필수 컬럼 중 누락된 컬럼 이름을 반환합니다."""
    # 리스트 컴프리헨션: REQUIRED_COLUMNS를 순회하며 없는 컬럼만 새 리스트에 담습니다.
    return [col for col in REQUIRED_COLUMNS if col not in df.columns]


def basic_profile(df: pd.DataFrame) -> dict:
    """화면 KPI에 사용할 기본 정보를 계산합니다."""
    # isna()는 결측치 여부를, duplicated()는 중복 행 여부를 True/False로 표시합니다.
    # True는 합계 계산에서 1로 취급되므로 전체 개수를 구할 수 있습니다.
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing": int(df.isna().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
    }


def clean_sensor_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    7주차에서 학습한 흐름으로 데이터를 정리합니다.
    시간 변환 → 문자 정리 → 중복 제거 → 결측치 처리 → 유효 범위 확인
    """
    missing_columns = validate_columns(df)
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {missing_columns}")

    # 원본 DataFrame을 직접 바꾸지 않도록 복사본에서 전처리를 진행합니다.
    work = df.copy()
    # 처리 전 값을 저장해 두면 처리 후 얼마나 달라졌는지 보고서를 만들 수 있습니다.
    before_rows = len(work)
    before_missing = int(work.isna().sum().sum())
    duplicate_count = int(work.duplicated().sum())

    # 1. 시간 변환
    # 변환할 수 없는 값은 errors="coerce"에 의해 NaT(시간 데이터의 결측치)가 됩니다.
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce")

    # 2. 문자 데이터 정리
    # astype(str)로 문자열화하고, strip()으로 앞뒤 공백을 제거합니다.
    work["machine_id"] = work["machine_id"].astype(str).str.strip()
    work["product_id"] = work["product_id"].astype(str).str.strip()
    work["status"] = work["status"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
    work.loc[~work["status"].isin(["OK", "NG"]), "status"] = "UNKNOWN"

    # 3. 중복 제거
    # 인덱스를 다시 0부터 붙이면 삭제된 행 때문에 생긴 인덱스 빈칸도 정리됩니다.
    work = work.drop_duplicates().reset_index(drop=True)

    # 4. 숫자 결측치는 중앙값으로 대체
    for col in NUMERIC_COLUMNS:
        # 숫자로 바꿀 수 없는 문자는 NaN으로 만든 뒤, 이상치에 비교적 강한 중앙값으로 채웁니다.
        work[col] = pd.to_numeric(work[col], errors="coerce")
        median_value = work[col].median()
        work[col] = work[col].fillna(median_value)

    # 시간 변환 실패 행은 분석에서 제외
    bad_time = work["timestamp"].isna()

    # 5. 센서 유효 범위를 벗어난 행 찾기
    # 처음에는 시간이 정상인 행을 True로 두고, 각 센서 범위 조건을 & 연산으로 누적합니다.
    valid_condition = ~bad_time
    for col, (low, high) in VALID_RANGES.items():
        valid_condition &= work[col].between(low, high, inclusive="both")

    # Boolean 인덱싱으로 유효하지 않은 행과 정상 행을 서로 분리합니다.
    outlier_df = work.loc[~valid_condition].copy()
    clean_df = work.loc[valid_condition].copy().reset_index(drop=True)

    # 화면에서 전처리 결과를 KPI로 보여주기 위한 요약 정보입니다.
    report = {
        "before_rows": before_rows,
        "after_rows": len(clean_df),
        "removed_rows": before_rows - len(clean_df),
        "before_missing": before_missing,
        "after_missing": int(clean_df.isna().sum().sum()),
        "duplicate_count": duplicate_count,
        "outlier_count": len(outlier_df),
    }
    return clean_df, outlier_df, report


def find_ng_reason(row: pd.Series, thresholds: dict) -> str:
    """한 행의 NG 원인을 사람이 읽을 수 있는 문장으로 만듭니다."""
    # 한 행에서 여러 기준을 동시에 위반할 수 있으므로 원인을 리스트에 차례로 모읍니다.
    reasons = []

    if row["temperature"] > thresholds["temperature_max"]:
        reasons.append("온도 높음")
    if row["pressure"] > thresholds["pressure_max"]:
        reasons.append("압력 높음")
    if row["speed"] < thresholds["speed_min"]:
        reasons.append("속도 낮음")
    if row["humidity"] > thresholds["humidity_max"]:
        reasons.append("습도 높음")
    if row["vibration"] > thresholds["vibration_max"]:
        reasons.append("진동 높음")
    if row["current"] > thresholds["current_max"]:
        reasons.append("전류 높음")
    if row["status"] != "OK":
        reasons.append("설비 상태 비정상")

    # 원인이 하나도 없으면 '정상', 있으면 쉼표로 연결된 설명을 반환합니다.
    return "정상" if not reasons else ", ".join(reasons)


def add_rule_quality(
    df: pd.DataFrame,
    thresholds: dict | None = None,
) -> pd.DataFrame:
    """사용자가 조절한 기준으로 OK/NG를 판정합니다."""
    # 사용자가 기준을 전달하지 않으면 미리 정의한 기본 판정 기준을 사용합니다.
    thresholds = thresholds or DEFAULT_THRESHOLDS
    # 원본 데이터 보존을 위해 판정 결과는 복사본에 새 컬럼으로 추가합니다.
    result = df.copy()
    result["quality"] = "OK"

    # | 연산자는 pandas에서 '조건 중 하나라도 참'인 행을 선택하는 OR 역할을 합니다.
    ng_condition = (
        (result["temperature"] > thresholds["temperature_max"])
        | (result["pressure"] > thresholds["pressure_max"])
        | (result["speed"] < thresholds["speed_min"])
        | (result["humidity"] > thresholds["humidity_max"])
        | (result["vibration"] > thresholds["vibration_max"])
        | (result["current"] > thresholds["current_max"])
        | (result["status"] != "OK")
    )

    result.loc[ng_condition, "quality"] = "NG"
    # axis=1은 DataFrame을 행 방향으로 순회하며 각 행에 함수를 적용한다는 뜻입니다.
    result["ng_reason"] = result.apply(
        lambda row: find_ng_reason(row, thresholds),
        axis=1,
    )
    return result


def apply_filters(
    df: pd.DataFrame,
    machine_id: str = "전체",
    product_id: str = "전체",
) -> pd.DataFrame:
    """사이드바에서 선택한 설비와 제품 조건을 적용합니다."""
    result = df.copy()

    # '전체'를 선택한 경우에는 필터링하지 않고 모든 행을 유지합니다.
    if machine_id != "전체":
        result = result[result["machine_id"] == machine_id]
    if product_id != "전체":
        result = result[result["product_id"] == product_id]

    return result.reset_index(drop=True)


def make_summary_report(result_df: pd.DataFrame) -> pd.DataFrame:
    """전체 품질 요약표를 만듭니다."""
    total_count = len(result_df)
    ok_count = int((result_df["quality"] == "OK").sum())
    ng_count = int((result_df["quality"] == "NG").sum())
    # 데이터가 0행일 때 0으로 나누는 오류가 생기지 않도록 조건식을 사용합니다.
    ng_ratio = round(ng_count / total_count * 100, 2) if total_count else 0.0

    # 값 하나도 리스트로 감싸면 1행짜리 DataFrame을 만들 수 있습니다.
    return pd.DataFrame(
        {
            "total_count": [total_count],
            "ok_count": [ok_count],
            "ng_count": [ng_count],
            "ng_ratio_percent": [ng_ratio],
        }
    )


def make_machine_report(result_df: pd.DataFrame) -> pd.DataFrame:
    """설비별 품질과 평균 센서값을 요약합니다."""
    # 빈 데이터는 groupby로 계산할 내용이 없으므로 빈 DataFrame을 즉시 반환합니다.
    if result_df.empty:
        return pd.DataFrame()

    # groupby로 같은 machine_id를 묶고, agg로 묶음마다 개수와 평균을 계산합니다.
    # (새 컬럼 이름)=(대상 컬럼, 집계 방법) 형식의 이름 있는 집계를 사용합니다.
    report = (
        result_df.groupby("machine_id")
        .agg(
            total_count=("quality", "count"),
            ok_count=("quality", lambda x: int((x == "OK").sum())),
            ng_count=("quality", lambda x: int((x == "NG").sum())),
            avg_temperature=("temperature", "mean"),
            avg_pressure=("pressure", "mean"),
            avg_vibration=("vibration", "mean"),
            avg_current=("current", "mean"),
        )
        .reset_index()
    )
    report["ng_ratio_percent"] = (
        report["ng_count"] / report["total_count"] * 100
    ).round(2)
    return report


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Streamlit 다운로드 버튼에 사용할 CSV 바이트를 만듭니다."""
    # utf-8-sig는 Excel에서도 한글이 깨질 가능성을 줄여 주는 인코딩입니다.
    # Streamlit 다운로드 버튼에는 문자열 대신 bytes 데이터를 전달합니다.
    return df.to_csv(index=False).encode("utf-8-sig")
