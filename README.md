# 🌙 Sleep SpO2 Anomaly Detection System (수면 산소포화도 이상탐지)

A Python-based anomaly detection system for sleep SpO2 (oxygen saturation) data using PhysioNet EDF files.

## 📋 Project Overview

이 프로젝트는 수면 중 산소포화도(SpO2) 데이터를 분석하여 수면무호흡 등 이상 구간을 자동으로 탐지하고 시각화합니다.

**주요 목표:**
- PhysioNet Sleep-EDF 데이터셋에서 SpO2 시계열 데이터 추출
- 절대 기준값(90%) 및 급격한 수치 변화(3% 이상 급감) 기반 이상 탐지
- 이상 이벤트 구간 자동 집계 및 CSV 저장
- 전문적 데이터 시각화

---

## 🎯 Project Structure

```
.
├── data/
│   ├── SC4001E0-PSG.edf          # 생체신호 데이터 (PhysioNet에서 다운로드)
│   └── SC4001EC-Hypnogram.edf    # 수면 단계 라벨
├── main.py                        # 메인 실행 파일 (데이터 로드 + 탐지 + 시각화)
├── requirements.txt               # 파이썬 패키지 의존성
├── anomaly_events.csv             # 이상 이벤트 결과 (자동 생성)
└── sleep_anomaly_result.png       # 시각화 그래프 (자동 생성)
```

---

## 📦 Installation

### 1. Python 설치 확인
```bash
python --version  # Python 3.8 이상 필요
```

### 2. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

**필요한 패키지:**
- `numpy` - 수치 계산
- `pandas` - 데이터 처리 및 CSV 저장
- `matplotlib` - 그래프 시각화
- `mne` - EDF 생체신호 파일 읽기
- `pyedflib` - EDF 파일 보조 라이브러리

---

## 📥 데이터 다운로드

### PhysioNet Sleep-EDF Database
1. https://physionet.org/register/ 에서 회원가입
2. https://physionet.org/content/sleep-edfx/1.0.0/ 접속
3. 로그인 후 **Files** 탭 → `sleep-cassette/` 폴더에서 아래 파일 다운로드:
   - `SC4001E0-PSG.edf` (생체신호 데이터)
   - `SC4001EC-Hypnogram.edf` (수면 단계 라벨)
4. 다운로드한 파일을 프로젝트의 `data/` 폴더에 저장

---

## 🚀 Quick Start

### 실행
```bash
python main.py
```

**출력 예시:**
```
📂 데이터 불러오는 중...
사용 가능한 채널: ['EEG Fpz-Cz', 'EEG Pz-Oz', 'EOG horizontal', 'SpO2', ...]
✅ 사용할 채널: SpO2
📊 총 데이터 길이: 2,030,400 샘플 (508.0 분)
📡 샘플링 주파수: 100.0 Hz

🔍 이상 탐지 결과:
   - SpO2 < 90%  구간: 3,210 샘플
   - 급감(>3%) 구간: 1,540 샘플
   - 전체 이상 구간: 4,320 샘플 (0.21%)

📋 총 이상 이벤트: 47 건
✅ 그래프 저장 완료: sleep_anomaly_result.png
✅ 이상 이벤트 저장 완료: anomaly_events.csv

===== 최종 요약 =====
총 수면 시간       : 508.0 분
이상 이벤트 횟수   : 47 건
평균 이상 지속시간 : 12.3 초
최저 SpO2          : 82.1 %
```

---

## 📊 Data Files

### SC4001E0-PSG.edf (입력)
PhysioNet에서 제공하는 수면다원검사(PSG) 원본 EDF 파일입니다.
수면 중 뇌파(EEG), 안구운동(EOG), 산소포화도(SpO2), 심박수 등 다양한 채널 포함.

### anomaly_events.csv (출력)
```csv
start_min,end_min,duration_sec,min_spo2
12.3,12.5,12.0,88.5
45.1,45.4,18.0,86.2
...
```

| 컬럼 | 설명 |
|------|------|
| `start_min` | 이상 구간 시작 시간 (분) |
| `end_min` | 이상 구간 종료 시간 (분) |
| `duration_sec` | 이상 지속 시간 (초) |
| `min_spo2` | 해당 구간 최저 산소포화도 (%) |

### sleep_anomaly_result.png (출력)
- 상단 그래프: SpO2 시계열 + 이상 구간(빨간색) + 기준선(주황 점선)
- 하단 그래프: 이상 여부 바 차트

---

## 🤖 Algorithm: Rule-Based Anomaly Detection

**탐지 기준 2가지:**

| 기준 | 설명 |
|------|------|
| 절대값 기준 | SpO2 < 90% → 임상적으로 저산소증 판단 기준 |
| 변화량 기준 | 이전 샘플 대비 3% 이상 급감 → 무호흡 발생 시 나타나는 급격한 패턴 |

**장점:**
- ✅ 임상 기준에 근거한 직관적인 탐지 로직
- ✅ 별도 학습 데이터 불필요 (비지도 방식)
- ✅ 결과 해석이 쉬움
- ✅ 연속 이상 구간을 이벤트 단위로 묶어 집계

---

## 🔧 Customization

### 1. 탐지 기준값 변경
`main.py` 수정:
```python
THRESHOLD_ABS = 90.0   # SpO2 절대 기준 (기본: 90%)
THRESHOLD_DROP = 3.0   # 급감 기준 (기본: 3%)
```

### 2. 다른 피험자 데이터 사용
`main.py` 수정:
```python
PSG_FILE = "data/SC4002E0-PSG.edf"       # 파일명 변경
HYPNO_FILE = "data/SC4002EC-Hypnogram.edf"
```

### 3. 다른 채널 분석
`main.py` 수정:
```python
# SpO2 대신 심박수 채널 분석 예시
spo2_ch = "Pulse"
```

---

## 📈 Output Examples

### 콘솔 출력
```
===== 최종 요약 =====
총 수면 시간       : 508.0 분
이상 이벤트 횟수   : 47 건
평균 이상 지속시간 : 12.3 초
최저 SpO2          : 82.1 %
```

### CSV 출력
이상 이벤트별 시작/종료 시간, 지속 시간, 최저 SpO2 저장

### 그래프 출력
- 고해상도(150 DPI) PNG 파일
- 어두운 배경 테마 (다크모드)
- 정상 구간: 파란선
- 이상 구간: 빨간색 음영
- 기준선: 주황 점선 (SpO2 90%)

---

## 🐛 Troubleshooting

### 1. "SpO2 채널을 찾지 못했습니다" 경고
**원인:** EDF 파일에 SpO2 채널명이 다르게 저장됨
**해결:** 출력된 채널 목록 확인 후 `main.py`에서 채널명 직접 지정
```python
spo2_ch = "SaO2"  # 실제 채널명으로 변경
```

### 2. "No module named 'mne'" 에러
**원인:** mne 패키지 미설치
**해결:**
```bash
pip install mne
```

### 3. EDF 파일을 읽지 못하는 경우
**원인:** 파일 경로 또는 파일명 오류
**해결:** `data/` 폴더 안에 파일이 올바르게 저장됐는지 확인

### 4. 그래프가 표시되지 않음
**원인:** matplotlib 백엔드 문제
**해결:**
```bash
pip install --upgrade matplotlib
```

---

## 📚 References

- **PhysioNet Sleep-EDF Database**: https://physionet.org/content/sleep-edfx/1.0.0/
- **MNE-Python Documentation**: https://mne.tools/stable/index.html
- **수면무호흡 SpO2 기준**: American Academy of Sleep Medicine (AASM)
- **Pandas Documentation**: https://pandas.pydata.org/
- **Matplotlib Documentation**: https://matplotlib.org/

---

## 📝 License

MIT License - 자유롭게 사용 및 수정 가능합니다.

---

## 👨‍💻 Author

작성일: 2026-05-13
Python 3.8+

---

## ✨ Features

- ✅ PhysioNet EDF 파일 자동 파싱 (MNE 라이브러리)
- ✅ 절대값 + 변화량 이중 기준 이상 탐지
- ✅ 연속 이상 구간 이벤트 단위 집계
- ✅ 전문적 데이터 시각화 (다크 테마)
- ✅ CSV 형식 결과 저장
- ✅ 상세한 통계 요약 출력
- ✅ 한글 지원
