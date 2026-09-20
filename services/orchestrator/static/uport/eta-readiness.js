/* Show the collector's aggregate ETA data status on the main dashboard.
 * The endpoint contains counts and gates only; no vessel identity, position,
 * training sample or model prediction is rendered from this response. */
(() => {
  "use strict";

  const target = document.getElementById("eta-readiness");
  if (!target) return;

  async function loadReadiness() {
    try {
      const response = await fetch("/api/v1/uport/predictions/eta-readiness", {
        headers: { "Accept": "application/json" }, cache: "no-store"
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      const quality = result.quality || {};
      const number = value => Number.isSafeInteger(value) && value >= 0
        ? value.toLocaleString("ko-KR") : "-";
      const counts = `위치 갱신 ${number(quality.stored_positions)}건 · ` +
        `입항 전 갱신 ${number(quality.voyages_with_prearrival_update)}항차 · ` +
        `학습/보류 ${number(quality.train_voyages)}/${number(quality.holdout_voyages)}`;
      // The public position clock is an update timestamp. A positive count
      // alone must never be presented as a trained ETA model or live AIS.
      target.textContent = quality.export_ready
        ? `ETA 학습 데이터 준비 완료 · ${counts}`
        : `ETA 학습 데이터 미확보 · ${counts}. 입항 전 AIS 관측시각, 시간대와 실제 입항 기준 확인이 필요합니다.`;
    } catch (_) {
      // An absent report is a visible unavailable state, never zero training
      // samples or a fabricated prediction.
      target.textContent = "ETA 학습 데이터 상태를 확인할 수 없습니다.";
    }
  }

  loadReadiness();
})();
