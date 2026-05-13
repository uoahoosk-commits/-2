# 🌙 Sleep SpO2 Anomaly Detection System (수면 산소포화도 이상탐지)

A Python-based anomaly detection system for sleep SpO2 (oxygen saturation) data using PhysioNet EDF files.

## 📋 Project Overview

이 프로젝트는 수면 중 산소포화도(SpO2) 데이터를 분석하여 수면무호흡 등 이상 구간을 자동으로 탐지하고 시각화합니다.

**주요 목표:**
- PhysioNet Sleep-EDF 데이터셋에서 SpO2 시계열 데이터 추출
- 노이즈 필터링(이동 평균)을 통한 데이터 전처리
- 절대 기준값(95%) 및 급격한 수치 변화(3% 이상 급감) 기반 이상 탐지
- 무호흡 이벤트 집계 및 경미/중등/심각 심각도 분류
- 3단 전문적 데이터 시각화 (다크 테마)
- CSV 형식 결과 저장 및 상세 통계 요약 출력

---

## 🎯 Project Structure

```
.
├── data/
│   ├── SC4001E0-PSG.edf          # 생체신호 데이터 (PhysioNet에서 다운로드)
│   └── SC4001EC-Hypnogram.edf    # 수면 단계 라벨
├── main.py                        # 메인 실행 파일 (전처리 + 탐지 + 시각화)
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
- `scipy` - 신호 처리 (필터링)

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
💧 SpO2 범위: 82.1% ~ 99.5%
🔧 전처리 완료 (평활화 윈도우: 500 샘플)

🔍 이상 탐지 결과:
   - SpO2 < 95.0% 구간: 12,540 샘플 (0.62%)
   - 급감(>3%) 구간:     1,820 샘플 (0.09%)
   - 심각(>4%) 구간:       430 샘플 (0.02%)
   - 전체 이상 구간:    13,210 샘플 (0.65%)

📋 무호흡 이벤트 감지 결과:
   - 총 이벤트 건수: 47 건

⚠️  심각도 분류:
   - 경미: 30 건
   - 중등: 14 건
   - 심각:  3 건

✅ 그래프 저장 완료: sleep_anomaly_result.png
✅ 이상 이벤트 저장 완료: anomaly_events.csv

==================================================
📊 최종 분석 요약
==================================================
✓ 총 수면 시간        : 508.0 분 (8.5 시간)
✓ 이상 이벤트 횟수    : 47 건
✓ 총 이상 지속시간    : 22.0 분 (1320 초)
✓ 이상 비율           : 0.65%
✓ 평균 이벤트 지속시간: 28.1 초
✓ 최장 이벤트 시간    : 142.0 초
✓ 최저 SpO2           : 82.1%
✓ 평균 최저 SpO2      : 91.3%
✓ 평균 하강폭         : 4.2%
==================================================
```

---

## 📊 Data Files

### SC4001E0-PSG.edf (입력)
PhysioNet에서 제공하는 수면다원검사(PSG) 원본 EDF 파일입니다.
수면 중 뇌파(EEG), 안구운동(EOG), 산소포화도(SpO2), 심박수 등 다양한 채널을 포함합니다.

### anomaly_events.csv (출력)
```csv
이벤트번호,시작시간(분),종료시간(분),지속시간(초),최저SpO2(%),하강폭(%),심각도
1,12.30,12.52,13.2,92.3,3.1,경미
2,45.10,45.58,28.8,88.5,5.9,중등
3,98.22,100.15,113.0,81.4,9.2,심각
```

| 컬럼 | 설명 |
|------|------|
| `이벤트번호` | 탐지된 순서 |
| `시작시간(분)` | 이상 구간 시작 시간 |
| `종료시간(분)` | 이상 구간 종료 시간 |
| `지속시간(초)` | 이상 지속 시간 |
| `최저SpO2(%)` | 해당 구간 최저 산소포화도 |
| `하강폭(%)` | 구간 시작 대비 최저값의 하강 폭 |
| `심각도` | 경미 / 중등 / 심각 |

### sleep_anomaly_result.png (출력)
3단 구성의 다크 테마 그래프:

| 그래프 | 내용 |
|--------|------|
| 상단 | 원본 SpO2 + 평활화 SpO2 + 이상 구간(빨간 음영) + 기준선 |
| 중단 | 샘플 간 SpO2 변화량 바 차트 |
| 하단 | 시간대별 정상/이상 상태 바 |

---

## 🤖 Algorithm

### Step 1 — 전처리 (노이즈 제거)
측정 노이즈를 줄이기 위해 5초 윈도우 이동 평균으로 SpO2 신호를 평활화합니다.
```python
window = int(sfreq * 5)  # 5초
spo2_smooth = pd.Series(spo2).rolling(window=window, center=True, min_periods=1).mean()
```

### Step 2 — 이상 탐지 (2가지 기준)

| 기준 | 조건 | 의미 |
|------|------|------|
| 절대값 기준 | SpO2 < 95% | 정상 범위 이탈 |
| 변화량 기준 | 이전 샘플 대비 3% 이상 급감 | 무호흡 발생 패턴 |

두 기준 중 하나라도 해당되면 이상으로 판단합니다.

### Step 3 — 이벤트 집계
10초 이상 지속된 연속 이상 구간만 유효한 무호흡 이벤트로 집계합니다. (단기 노이즈 제거)

### Step 4 — 심각도 분류
이벤트별 최저 SpO2를 기준으로 3단계로 분류합니다.

| 심각도 | SpO2 기준 |
|--------|-----------|
| 경미 | 90% 이상 |
| 중등 | 80% 이상 ~ 90% 미만 |
| 심각 | 80% 미만 |

**장점:**
- ✅ 임상 기준에 근거한 직관적인 탐지 로직
- ✅ 이동 평균 전처리로 노이즈에 강건함
- ✅ 별도 학습 데이터 불필요 (비지도 방식)
- ✅ 결과 해석이 쉽고 발표 설명이 직관적

---

## 🔧 Customization

### 1. 탐지 기준값 변경
`main.py` 수정:
```python
THRESHOLD_NORMAL = 95.0   # 정상 기준 SpO2 (기본: 95%)
THRESHOLD_DROP = 3.0      # 급감 기준 (기본: 3%)
THRESHOLD_SEVERE = 4.0    # 심각 급감 기준 (기본: 4%)
```

### 2. 이벤트 최소 지속 시간 변경
```python
# 5초 이상 지속된 구간만 이벤트로 집계
events_df = find_apnea_events(is_anomaly, times_min, spo2_smooth, min_duration_sec=5)
```

### 3. 평활화 윈도우 변경
```python
window = int(sfreq * 10)  # 10초 윈도우로 변경
```

### 4. 다른 피험자 데이터 사용
```python
PSG_FILE = "data/SC4002E0-PSG.edf"
HYPNO_FILE = "data/SC4002EC-Hypnogram.edf"
```

---

## 🐛 Troubleshooting

### 1. "SpO2 채널을 찾지 못했습니다" 경고
**원인:** EDF 파일에 SpO2 채널명이 다르게 저장됨
**해결:** 출력된 채널 목록 확인 후 직접 지정
```python
spo2_ch = "SaO2"  # 실제 채널명으로 수정
```

### 2. "No module named 'mne'" 에러
**원인:** mne 패키지 미설치
**해결:**
```bash
pip install mne
```

### 3. "No module named 'scipy'" 에러
**원인:** scipy 패키지 미설치
**해결:**
```bash
pip install scipy
```

### 4. EDF 파일을 읽지 못하는 경우
**원인:** 파일 경로 또는 파일명 오류
**해결:** `data/` 폴더 안에 파일이 올바르게 저장됐는지 확인

### 5. 그래프가 표시되지 않음
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
- ✅ 이동 평균 기반 노이즈 전처리
- ✅ 절대값 + 변화량 이중 기준 이상 탐지
- ✅ 최소 지속 시간 필터로 노이즈성 이벤트 제거
- ✅ 경미 / 중등 / 심각 3단계 심각도 분류
- ✅ 3단 전문 시각화 (다크 테마)
- ✅ CSV 형식 결과 저장
- ✅ 상세한 통계 요약 출력
- ✅ 한글 지원
