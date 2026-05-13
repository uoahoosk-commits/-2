import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import mne
import os
from scipy import signal

# ─────────────────────────────────────────────
# 1. 파일 경로 설정
# ─────────────────────────────────────────────
PSG_FILE = "data/SC4001E0-PSG.edf"          # 생체신호 파일
HYPNO_FILE = "data/SC4001EC-Hypnogram.edf"  # 수면단계 라벨 파일

# ─────────────────────────────────────────────
# 2. EDF 파일 불러오기
# ─────────────────────────────────────────────
print("📂 데이터 불러오는 중...")
raw = mne.io.read_raw_edf(PSG_FILE, preload=True, verbose=False)

# 사용 가능한 채널 확인
print("사용 가능한 채널:", raw.ch_names)

# 산소포화도 채널 자동 탐색
spo2_candidates = [ch for ch in raw.ch_names if "SpO2" in ch or "spo2" in ch.lower() or "SaO2" in ch]
if spo2_candidates:
    spo2_ch = spo2_candidates[0]
else:
    # 없으면 첫 번째 채널 사용 (테스트용)
    spo2_ch = raw.ch_names[0]
    print(f"⚠️  SpO2 채널을 찾지 못해 '{spo2_ch}' 채널을 사용합니다.")

print(f"✅ 사용할 채널: {spo2_ch}")

# ─────────────────────────────────────────────
# 3. SpO2 시계열 추출
# ─────────────────────────────────────────────
data, times = raw[spo2_ch, :]
spo2 = data[0]  # (n_samples,)
sfreq = raw.info["sfreq"]  # 샘플링 주파수 (Hz)

# 시간 단위를 분(minute)으로 변환
times_min = times / 60.0

print(f"📊 총 데이터 길이: {len(spo2):,} 샘플 ({times[-1]/60:.1f} 분)")
print(f"📡 샘플링 주파수: {sfreq} Hz")
print(f"💧 SpO2 범위: {spo2.min():.1f}% ~ {spo2.max():.1f}%")

# ─────────────────────────────────────────────
# 4. 데이터 전처리 (노이즈 필터링)
# ─────────────────────────────────────────────
# 이동 평균으로 노이즈 제거
window = max(1, int(sfreq * 5))  # 5초 윈도우
spo2_smooth = pd.Series(spo2).rolling(window=window, center=True, min_periods=1).mean().values

print(f"🔧 전처리 완료 (평활화 윈도우: {window} 샘플)")

# ─────────────────────────────────────────────
# 5. 정상/이상 구간 정의
# ─────────────────────────────────────────────
THRESHOLD_NORMAL = 95.0         # 정상 기준: 95% 이상
THRESHOLD_DROP = 3.0            # 급감 기준: 3% 이상 급감
THRESHOLD_SEVERE = 4.0          # 심각: 4% 이상 급감

# 절대값 기준: SpO2 < 95% = 비정상
is_abnormal = spo2_smooth < THRESHOLD_NORMAL

# 변화량 기준: 이전 값보다 3% 이상 급감
diff = np.diff(spo2_smooth, prepend=spo2_smooth[0])
is_drop = diff < -THRESHOLD_DROP
is_severe_drop = diff < -THRESHOLD_SEVERE

# 최종 이상 마스크 (절대값 or 급감)
is_anomaly = is_abnormal | is_drop

print(f"\n🔍 이상 탐지 결과:")
print(f"   - SpO2 < {THRESHOLD_NORMAL}% 구간: {is_abnormal.sum():,} 샘플 ({is_abnormal.mean()*100:.2f}%)")
print(f"   - 급감(>{THRESHOLD_DROP}%) 구간: {is_drop.sum():,} 샘플 ({is_drop.mean()*100:.2f}%)")
print(f"   - 심각(>{THRESHOLD_SEVERE}%) 구간: {is_severe_drop.sum():,} 샘플 ({is_severe_drop.mean()*100:.2f}%)")
print(f"   - 전체 이상 구간: {is_anomaly.sum():,} 샘플 ({is_anomaly.mean()*100:.2f}%)")

# ─────────────────────────────────────────────
# 6. 무호흡 이벤트 감지 (연속 구간 묶기)
# ─────────────────────────────────────────────
def find_apnea_events(mask, times_min, spo2_values, min_duration_sec=10):
    """
    연속 이상 구간을 무호흡 이벤트 단위로 묶음
    min_duration_sec: 최소 지속 시간 (초) - 노이즈 제거용
    """
    events = []
    in_event = False
    start_idx = 0
    
    for i, val in enumerate(mask):
        if val and not in_event:
            start_idx = i
            in_event = True
        elif not val and in_event:
            duration_sec = (times_min[i - 1] - times_min[start_idx]) * 60
            
            # 최소 지속 시간 이상인 것만 기록
            if duration_sec >= min_duration_sec:
                min_spo2 = spo2_values[start_idx:i].min()
                drop_magnitude = spo2_values[start_idx] - min_spo2
                
                events.append({
                    "이벤트번호": len(events) + 1,
                    "시작시간(분)": round(times_min[start_idx], 2),
                    "종료시간(분)": round(times_min[i - 1], 2),
                    "지속시간(초)": round(duration_sec, 1),
                    "최저SpO2(%)": round(min_spo2, 1),
                    "하강폭(%)": round(drop_magnitude, 1),
                })
            in_event = False
    
    # 마지막 구간이 이벤트 중인 경우
    if in_event:
        duration_sec = (times_min[-1] - times_min[start_idx]) * 60
        if duration_sec >= min_duration_sec:
            min_spo2 = spo2_values[start_idx:].min()
            drop_magnitude = spo2_values[start_idx] - min_spo2
            
            events.append({
                "이벤트번호": len(events) + 1,
                "시작시간(분)": round(times_min[start_idx], 2),
                "종료시간(분)": round(times_min[-1], 2),
                "지속시간(초)": round(duration_sec, 1),
                "최저SpO2(%)": round(min_spo2, 1),
                "하강폭(%)": round(drop_magnitude, 1),
            })
    
    return pd.DataFrame(events)

events_df = find_apnea_events(is_anomaly, times_min, spo2_smooth, min_duration_sec=10)

print(f"\n📋 무호흡 이벤트 감지 결과:")
print(f"   - 총 이벤트 건수: {len(events_df)} 건")

if not events_df.empty:
    print("\n🩺 상세 이벤트 정보 (최대 15개):")
    print(events_df.head(15).to_string(index=False))
else:
    print("   ⚠️  이상 이벤트가 발견되지 않았습니다.")

# ─────────────────────────────────────────────
# 7. 심각도 분류
# ─────────────────────────────────────────────
def classify_severity(min_spo2):
    """SpO2 최저값에 따른 심각도 분류"""
    if min_spo2 >= 90:
        return "경미"
    elif min_spo2 >= 80:
        return "중등"
    else:
        return "심각"

if not events_df.empty:
    events_df["심각도"] = events_df["최저SpO2(%)"].apply(classify_severity)
    severity_counts = events_df["심각도"].value_counts()
    
    print(f"\n⚠️  심각도 분류:")
    for severity in ["경미", "중등", "심각"]:
        count = severity_counts.get(severity, 0)
        print(f"   - {severity}: {count} 건")

# ─────────────────────────────────────────────
# 8. 시각화 (원본 + 평활화 데이터)
# ─────────────────────────────────────────────
fig = plt.figure(figsize=(18, 12), facecolor="#0d1117")
gs = GridSpec(4, 1, figure=fig, hspace=0.35)

ax1 = fig.add_subplot(gs[0:2, 0])  # 원본 + 평활화
ax2 = fig.add_subplot(gs[2, 0])    # 변화량
ax3 = fig.add_subplot(gs[3, 0])    # 이상 여부

# ── 상단: SpO2 시계열 (원본 + 평활화) ──
ax1.set_facecolor("#0d1117")

# 원본 데이터 (연한 색)
ax1.plot(times_min, spo2, color="#7fc3f7", linewidth=0.4, alpha=0.4, label="원본 SpO2")
ax1.fill_between(times_min, spo2, alpha=0.1, color="#7fc3f7")

# 평활화 데이터
ax1.plot(times_min, spo2_smooth, color="#4fc3f7", linewidth=1.2, alpha=0.9, label="평활화 SpO2")
ax1.fill_between(times_min, spo2_smooth, alpha=0.2, color="#4fc3f7")

# 이상 구간 빨간색 표시
ax1.fill_between(times_min, spo2_smooth, where=is_anomaly,
                 color="#ff4444", alpha=0.6, label="이상 구간")

# 기준선들
ax1.axhline(THRESHOLD_NORMAL, color="#ffaa00", linewidth=1.5,
            linestyle="--", alpha=0.8, label=f"정상 기준선 ({THRESHOLD_NORMAL}%)")
ax1.axhline(90, color="#ff6666", linewidth=1, linestyle=":", alpha=0.7, label="심각 기준 (90%)")

ax1.set_ylabel("SpO2 (%)", color="white", fontsize=13, fontweight="bold")
ax1.set_title("🌙 수면 중 산소포화도(SpO2) 이상탐지", color="white", fontsize=16, pad=15, fontweight="bold")
ax1.tick_params(colors="white", labelsize=10)
ax1.spines[:].set_color("#333")
ax1.set_ylim([70, 105])
legend = ax1.legend(facecolor="#1e2530", edgecolor="#444", labelcolor="white", fontsize=10, loc="lower left")
ax1.grid(True, alpha=0.1, color="white")

# ── 중단 상: 변화량 ──
ax2.set_facecolor("#0d1117")
ax2.bar(times_min, diff, width=0.01, color="#66bb6a", alpha=0.6, label="SpO2 변화량")
ax2.axhline(-THRESHOLD_DROP, color="#ff6666", linewidth=1.2, linestyle="--", 
            alpha=0.8, label=f"급감 기준 ({-THRESHOLD_DROP}%)")
ax2.axhline(0, color="white", linewidth=0.8, alpha=0.3)

ax2.set_ylabel("변화량 (%)", color="white", fontsize=12, fontweight="bold")
ax2.tick_params(colors="white", labelsize=10)
ax2.spines[:].set_color("#333")
ax2.legend(facecolor="#1e2530", edgecolor="#444", labelcolor="white", fontsize=9)
ax2.grid(True, alpha=0.1, color="white")

# ── 하단: 이상 여부 ──
ax3.set_facecolor("#0d1117")
ax3.fill_between(times_min, is_anomaly.astype(int),
                 color="#ff4444", alpha=0.8, step="post", label="이상")
ax3.set_ylabel("상태", color="white", fontsize=12, fontweight="bold")
ax3.set_xlabel("시간 (분)", color="white", fontsize=12, fontweight="bold")
ax3.set_yticks([0, 1])
ax3.set_yticklabels(["정상", "이상"], color="white", fontsize=10)
ax3.tick_params(colors="white", labelsize=10)
ax3.spines[:].set_color("#333")
ax3.set_ylim([-0.15, 1.3])
ax3.grid(True, alpha=0.1, color="white", axis="x")

plt.savefig("sleep_anomaly_result.png", dpi=150,
            bbox_inches="tight", facecolor="#0d1117")
print("\n✅ 그래프 저장 완료: sleep_anomaly_result.png")
plt.show()

# ─────────────────────────────────────────────
# 9. 결과 저장 및 요약
# ─────────────────────────────────────────────
if not events_df.empty:
    # CSV 저장
    events_df.to_csv("anomaly_events.csv", index=False, encoding="utf-8-sig")
    print("\n✅ 이상 이벤트 저장 완료: anomaly_events.csv")
    
    # 최종 요약
    total_sleep_min = times_min[-1]
    total_anomaly_sec = (is_anomaly.sum() / sfreq)
    total_anomaly_min = total_anomaly_sec / 60
    
    print("\n" + "="*50)
    print("📊 최종 분석 요약")
    print("="*50)
    print(f"✓ 총 수면 시간        : {total_sleep_min:.1f} 분 ({total_sleep_min/60:.1f} 시간)")
    print(f"✓ 이상 이벤트 횟수    : {len(events_df)} 건")
    print(f"✓ 총 이상 지속시간    : {total_anomaly_min:.1f} 분 ({total_anomaly_sec:.0f} 초)")
    print(f"✓ 이상 비율          : {is_anomaly.mean()*100:.2f}%")
    print(f"✓ 평균 이벤트 지속시간: {events_df['지속시간(초)'].mean():.1f} 초")
    print(f"✓ 최장 이벤트 시간    : {events_df['지속시간(초)'].max():.1f} 초")
    print(f"✓ 최저 SpO2          : {events_df['최저SpO2(%)'].min():.1f}%")
    print(f"✓ 평균 최저 SpO2     : {events_df['최저SpO2(%)'].mean():.1f}%")
    print(f"✓ 평균 하강폭        : {events_df['하강폭(%)'].mean():.1f}%")
    print("="*50)
    
    # 시간대별 분석
    events_df["시간대"] = events_df["시작시간(분)"].apply(
        lambda x: f"{int(x//60):02d}:{int(x%60):02d}"
    )
    
else:
    print("\n⚠️  이상 이벤트가 발견되지 않았습니다.")
    print("="*50)
