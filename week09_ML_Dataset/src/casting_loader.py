"""주조 품질보증 데이터 로더

KAMP 원본처럼 header=[0,1] 형태의 MultiIndex CSV와
일반 1행 헤더 CSV를 모두 읽을 수 있도록 만든 교육용 코드입니다.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd


def load_casting_csv(path: str | Path, multi_header: bool = True) -> pd.DataFrame:
    """CSV 파일을 DataFrame으로 불러옵니다.

    Parameters
    ----------
    path : str | Path
        CSV 파일 경로
    multi_header : bool
        True이면 header=[0,1]로 읽어 MultiIndex 컬럼을 유지합니다.
    """
    # 문자열 경로를 Path 객체로 통일하면 운영체제에 안전하게 경로를 다룰 수 있습니다.
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

    # KAMP 원본은 첫 두 행이 그룹명과 변수명으로 구성된 2단 헤더입니다.
    if multi_header:
        return pd.read_csv(path, header=[0, 1])

    # 일반 CSV는 첫 번째 행만 컬럼명으로 사용합니다.
    return pd.read_csv(path)


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """MultiIndex 컬럼을 분석하기 쉬운 단일 컬럼명으로 변환합니다.

    예: (Process, Velocity_1) -> Process__Velocity_1
    """
    # 원본 데이터프레임의 컬럼을 직접 바꾸지 않도록 복사본을 만듭니다.
    copied = df.copy()
    if isinstance(copied.columns, pd.MultiIndex):
        # 각 헤더 단계를 __로 연결합니다. 예: Process__Velocity_1
        copied.columns = ["__".join([str(x) for x in col if str(x) != "nan"]) for col in copied.columns]
    return copied


def summarize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """컬럼별 자료형, 결측치, 고유값 수를 요약합니다."""
    # 서로 다른 품질 지표를 같은 컬럼 인덱스로 계산해 하나의 표로 묶습니다.
    return pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing_count": df.isna().sum(),
        "missing_rate": df.isna().mean().round(4),
        "unique_count": df.nunique(dropna=True),
    }).reset_index(names="column")
