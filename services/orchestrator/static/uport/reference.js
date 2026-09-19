/* Show only the scope and quality of an operator-configured berth CSV.
 * The dataset lacks occupancy, length and water depth, so this dashboard
 * summary must never translate a row count into available berth capacity. */
(() => {
  "use strict";

  const label = document.getElementById("berth-reference-status");
  if (!label) return;
  fetch("/api/v1/uport/operations/berth-reference")
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(data => {
      if (!Number.isSafeInteger(data.row_count) || data.row_count < 0 ||
          data.operational_status_available !== false) {
        throw new Error("Invalid berth reference response");
      }
      const reversed = Number(data.warning_counts?.TONNAGE_RANGE_REVERSED || 0);
      const zeroCapacity = Number(data.warning_counts?.CAPACITY_ZERO || 0);
      // textContent keeps source metadata and warnings as plain text.
      label.textContent = `선석 제원 참고 ${data.row_count}건 · 톤수 범위 확인 ${reversed}건 · 척수 0 ${zeroCapacity}건 · 실시간 점유 정보 없음`;
    })
    .catch(() => {
      label.textContent = "점유 데이터 연결 대기 중 · 선석 제원 CSV 미설정 또는 읽기 실패";
    });
})();
