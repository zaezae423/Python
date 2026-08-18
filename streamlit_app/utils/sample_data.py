"""전처리 실습에 사용할 제조 센서 샘플 데이터를 만드는 모듈입니다.

정상 데이터뿐 아니라 결측치, 이상치, 문자 오류, 중복 행을 일부러 포함하여
학생들이 데이터 정제 과정을 직접 확인할 수 있게 합니다.
"""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def create_sample_sensor_data(row_count: int = 180, seed: int = 42) -> pd.DataFrame:
    """7주차 통합 실습과 같은 컬럼 구조의 제조 센서 샘플 데이터를 만듭니다."""
    # seed가 같으면 실행할 때마다 같은 난수가 생성되어 수업 결과를 재현할 수 있습니다.
    rng = np.random.default_rng(seed)
    # 첫 측정 시각을 정하고 이후 데이터는 10초 간격으로 생성합니다.
    start_time = datetime(2026, 7, 1, 9, 0, 0)
    rows = []

    for i in range(row_count):
        current_time = start_time + timedelta(seconds=10 * i)

        # 한 시점의 센서 데이터를 딕셔너리 한 개로 만든 뒤 rows 리스트에 추가합니다.
        # normal(평균, 표준편차)은 평균 근처에 값이 많이 모이는 정규분포 난수를 만듭니다.
        rows.append(
            {
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "machine_id": rng.choice(["M01", "M02", "M03"]),
                "product_id": rng.choice(["P-A", "P-B", "P-C"]),
                "temperature": round(rng.normal(26, 2.0), 2),
                "pressure": round(rng.normal(2.8, 0.25), 2),
                "speed": round(rng.normal(5.0, 0.7), 2),
                "humidity": round(rng.normal(60, 5.0), 2),
                "vibration": round(rng.normal(1.5, 0.4), 2),
                "current": round(rng.normal(8.0, 1.0), 2),
                "status": rng.choice(["OK", "OK", "OK", "NG"]),
            }
        )

    # 딕셔너리 리스트를 표 형태의 DataFrame으로 변환합니다.
    df = pd.DataFrame(rows)

    # 아래부터는 전처리 연습을 위해 의도적으로 잘못된 데이터를 넣습니다.

    # 결측치: np.nan은 숫자 데이터에서 값이 비어 있음을 나타냅니다.
    df.loc[5, "temperature"] = np.nan
    df.loc[12, "pressure"] = np.nan
    df.loc[20, "current"] = np.nan

    # 센서 이상치: 실제 센서의 유효 범위를 벗어난 값을 넣습니다.
    df.loc[30, "temperature"] = 999
    df.loc[40, "pressure"] = -3
    df.loc[50, "speed"] = -1
    df.loc[60, "humidity"] = 150
    df.loc[70, "vibration"] = 12
    df.loc[80, "current"] = 25

    # 문자 데이터 오류: 공백, 소문자, 허용되지 않은 상태값을 섞습니다.
    df.loc[90, "status"] = " ok "
    df.loc[100, "status"] = "ng"
    df.loc[110, "status"] = "ERROR"

    # 중복 행: 첫 번째 행을 한 번 더 붙여 중복 제거를 연습할 수 있게 합니다.
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    return df


def save_sample_files(output_dir: str | Path = "data") -> tuple[Path, Path]:
    """CSV와 Excel 샘플 파일을 저장합니다."""
    # 문자열 경로와 Path 객체를 모두 받을 수 있도록 Path로 통일합니다.
    output_dir = Path(output_dir)
    # parents=True는 상위 폴더도 함께 만들고, exist_ok=True는 이미 있어도 오류를 내지 않습니다.
    output_dir.mkdir(parents=True, exist_ok=True)

    df = create_sample_sensor_data()
    csv_path = output_dir / "week07_sensor_sample_raw.csv"
    xlsx_path = output_dir / "week07_sensor_sample_raw.xlsx"

    # index=False로 저장하면 DataFrame의 행 번호가 불필요한 CSV 컬럼으로 들어가지 않습니다.
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(xlsx_path, index=False)
    return csv_path, xlsx_path


if __name__ == "__main__":
    # 이 파일을 직접 실행할 때만 샘플 파일을 생성합니다.
    # 다른 파일에서 import할 때는 아래 코드가 실행되지 않습니다.
    csv_file, xlsx_file = save_sample_files()
    print("샘플 파일 생성 완료")
    print(csv_file)
    print(xlsx_file)
