import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import mne
import os

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

# ─────────────────────────────────────────────
# 4. 이상 탐지
# ─────────────────────────────────────────────
# 기준: SpO2 < 90% 이거나, 이전 값보다 3% 이상 급감한 경우
THRESHOLD_ABS = 90.0       # 절대 기준: 90% 미만
THRESHOLD_DROP = 3.0       # 변화량 기준: 3% 이상 급감

# 절대값 기준
is_low = spo2 < THRESHOLD_ABS

# 변화량 기준 (급감 구간)
diff = np.diff(spo2, prepend=spo2[0])
is_drop = diff < -THRESHOLD_DROP

# 최종 이상 마스크
is_anomaly = is_low | is_drop

print(f"\n🔍 이상 탐지 결과:")
print(f"   - SpO2 < {THRESHOLD_ABS}%  구간: {is_low.sum():,} 샘플")
print(f"   - 급감(>{THRESHOLD_DROP}%) 구간: {is_drop.sum():,} 샘플")
print(f"   - 전체 이상 구간: {is_anomaly.sum():,} 샘플 ({is_anomaly.mean()*100:.2f}%)")

# ─────────────────────────────────────────────
# 5. 이상 이벤트 집계 (연속 구간 묶기)
# ─────────────────────────────────────────────
def find_events(mask, times_min):
    """연속 이상 구간을 이벤트 단위로 묶음"""
    events = []
    in_event = False
    start = 0
    for i, val in enumerate(mask):
        if val and not in_event:
            start = i
            in_event = True
        elif not val and in_event:
            events.append({
                "start_min": times_min[start],
                "end_min": times_min[i - 1],
                "duration_sec": (times_min[i - 1] - times_min[start]) * 60,
                "min_spo2": spo2[start:i].min()
            })
            in_event = False
    if in_event:
        events.append({
            "start_min": times_min[start],
            "end_min": times_min[-1],
            "duration_sec": (times_min[-1] - times_min[start]) * 60,
            "min_spo2": spo2[start:].min()
        })
    return pd.DataFrame(events)

events_df = find_events(is_anomaly, times_min)
print(f"\n📋 총 이상 이벤트: {len(events_df)} 건")
if not events_df.empty:
    print(events_df.head(10).to_string(index=False))

# ─────────────────────────────────────────────
# 6. 시각화
# ─────────────────────────────────────────────
fig = plt.figure(figsize=(16, 10), facecolor="#0d1117")
gs = GridSpec(3, 1, figure=fig, hspace=0.45)

ax1 = fig.add_subplot(gs[0:2, 0])
ax2 = fig.add_subplot(gs[2, 0])

# ── 상단: SpO2 시계열 ──
ax1.set_facecolor("#0d1117")
ax1.plot(times_min, spo2, color="#4fc3f7", linewidth=0.6, alpha=0.9, label="SpO2 (%)")
ax1.fill_between(times_min, spo2, alpha=0.15, color="#4fc3f7")

# 이상 구간 빨간색 표시
ax1.fill_between(times_min, spo2, where=is_anomaly,
                 color="#ff4444", alpha=0.5, label="이상 구간")
ax1.axhline(THRESHOLD_ABS, color="#ffaa00", linewidth=1.2,
            linestyle="--", alpha=0.8, label=f"기준선 ({THRESHOLD_ABS}%)")

ax1.set_ylabel("SpO2 (%)", color="white", fontsize=12)
ax1.set_title("🌙 수면 중 산소포화도(SpO2) 이상탐지", color="white", fontsize=15, pad=12)
ax1.tick_params(colors="white")
ax1.spines[:].set_color("#333")
ax1.set_ylim([75, 105])
legend = ax1.legend(facecolor="#1e2530", edgecolor="#444", labelcolor="white", fontsize=10)
ax1.set_xlabel("시간 (분)", color="white", fontsize=11)

# ── 하단: 이상 여부 바 ──
ax2.set_facecolor("#0d1117")
ax2.fill_between(times_min, is_anomaly.astype(int),
                 color="#ff4444", alpha=0.7, step="post")
ax2.set_ylabel("이상 여부", color="white", fontsize=11)
ax2.set_xlabel("시간 (분)", color="white", fontsize=11)
ax2.set_yticks([0, 1])
ax2.set_yticklabels(["정상", "이상"], color="white")
ax2.tick_params(colors="white")
ax2.spines[:].set_color("#333")
ax2.set_ylim([-0.1, 1.3])

plt.savefig("sleep_anomaly_result.png", dpi=150,
            bbox_inches="tight", facecolor="#0d1117")
print("\n✅ 그래프 저장 완료: sleep_anomaly_result.png")
plt.show()

# ─────────────────────────────────────────────
# 7. 결과 요약 저장
# ─────────────────────────────────────────────
if not events_df.empty:
    events_df.to_csv("anomaly_events.csv", index=False, encoding="utf-8-sig")
    print("✅ 이상 이벤트 저장 완료: anomaly_events.csv")

    print("\n===== 최종 요약 =====")
    print(f"총 수면 시간       : {times_min[-1]:.1f} 분")
    print(f"이상 이벤트 횟수   : {len(events_df)} 건")
    print(f"평균 이상 지속시간 : {events_df['duration_sec'].mean():.1f} 초")
    print(f"최저 SpO2          : {events_df['min_spo2'].min():.1f} %")
else:
    print("이상 이벤트가 발견되지 않았습니다.")
