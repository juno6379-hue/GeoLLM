# v4 보고 gate 중단과 v5 재실행

v4는 2026-11-01 21:28:57 KST에 144관측 수집 후 보고서 완료 gate에서 중단됐다. fault27은 실행되지 않았다. 17개 문항의 B4/H에서 SHARED_REVIEW_MISMATCH가 확인됐으며 완료된 비교로 인용하지 않는다. 418개 원본 파일의 hash는 `outputs/v4_stopped_audit_20261101/preserved_hashes.json`에 보존했다.

원인은 typed tool prompt로 교체한 뒤 reviewer가 이전 설명 marker를 split하던 코드가 남은 것이다. 모델 호출 전에 IndexError가 발생해 review_call_raw.json이 만들어지지 않았다. 초기 계획 무효1건을 제외한17건의 검토는 실제 호출되지 않았다. 이를 모델 검토 실패율로 해석해서는 안 된다.

수정은 연구 runner에 한정한다. public TOOL_INSTRUCTIONS를 직접 전달하며 callback 준비/호출 예외도 공유 실패 receipt로 남긴다. 실패를 정상 검토로 바꾸지 않고 완료 gate를 완화하지 않는다. v4 원본에 receipt를 사후 추가하거나 점수를 바꾸지 않는다.

새 run은 `runs/20261101_gold_v2_eight_k1_v5`, snapshot은 `outputs/scie_gold_v2_eight_snapshot_20261101_v5`다. v4 평가계약·immutable GOLD·모델digest·예산은 그대로 유지하고 수정된 소스를 새 동결한다. P1 포함8방법144와fault27을 처음부터 실행한다. 실행 중 소스 변경/중복worker/추가 모델·운영API 호출 금지. 최종 완료 여부는 실제 status와 raw hash·공유계획/검토·공통ESR·완료 gate를 검증한다. 인간GOLD/전체시스템완료는 여전히 미완료다.
