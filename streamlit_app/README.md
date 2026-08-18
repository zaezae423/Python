# 제조AX Streamlit 1일 압축 교육 코드

7주차 교육 파일의 다음 내용을 그대로 이어서 사용합니다.

- CSV·Excel 파일 읽기
- `head`, `shape`, `info`, `describe`
- 조건 필터와 `groupby`
- 시간·문자·결측치·중복·이상치 처리
- Rule 기반 OK/NG 판정
- 설비별·알람 리포트 생성

## 최종 학습 흐름

```text
업로드 → 데이터 확인 → 전처리 → 필터·EDA
→ Rule 기반 상태 판정 → 리포트 다운로드
```

## 폴더 구성

```text
week08_day01_streamlit_one_day/
├─ app.py
├─ apps/
│  ├─ 01_hello_streamlit.py
│  ├─ 02_file_upload_profile.py
│  ├─ 03_filter_eda.py
│  ├─ 04_quality_status.py
│  └─ 05_final_integrated_app.py
├─ utils/
│  ├─ sample_data.py
│  ├─ data_processing.py
│  └─ visualization.py
├─ data/
├─ notebooks/
├─ docs/
├─ outputs/
├─ requirements.txt
└─ run_app_windows.bat
```

## 설치

VS Code 터미널에서 패키지 폴더로 이동한 후 실행합니다.

```bash
python -m pip install -r requirements.txt
```

`plotly` 또는 노트북 출력 오류를 줄이기 위해 `nbformat`도 포함했습니다.

## 작은 앱부터 실행

```bash
python -m streamlit run apps/01_hello_streamlit.py
python -m streamlit run apps/02_file_upload_profile.py
python -m streamlit run apps/03_filter_eda.py
python -m streamlit run apps/04_quality_status.py
```

## 최종 앱 실행

```bash
python -m streamlit run app.py
```

Windows에서는 `run_app_windows.bat`를 실행해도 됩니다.

## 수업 연결

- 7주차: 파일 처리·전처리·Rule 판정
- 오늘: Streamlit 웹 앱 구현
- 9주차: XGBoost 품질 예측 결과 연결
- 10주차: LSTM Autoencoder 이상 점수 연결
- 프로젝트: 조별 제조 데이터 분석 앱으로 확장
