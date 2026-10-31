# 반복 실험과 독립 GOLD 검수 절차

사용자 요청의 후속 연구 실행이다. 운영 서비스는 연구 모듈을 import하지 않는다. 모델·원천·평가계약과 소스를 동결하고 기존 K1 및 실패 원본을 보존한다. 독립 검수자는 사용자가 선정했다고 확인했지만 아직 검수 결과를 받지 않았으므로 완료 건수는 0이다.

## K5 실행

새 `repeat_experiment`는 graph 18문항 첫 회 → B0–B4 18×5×5=450조건 → graph 나머지 4회 → 반복 보고서 순서로 직렬 실행한다. 총 540개 관측이며 540개 독립 사례가 아니다. baseline은 seed42~46, temperature0.2를 사용하고 P는 기존 운영 생성 옵션을 바꾸지 않는다. P의 각 새 프로세스 원본 `repeat=0`은 보존하며 보고서에만 `external_repeat=0..4`를 추가한다.

```powershell
.venv/Scripts/python.exe -u -m research.marine_geollm_scie.runners.repeat_experiment --output research/marine_geollm_scie/runs/<새_K5_폴더> --baseline-profile research/marine_geollm_scie/runs/20261030_full_execution_v5/baseline_profile.json --model-profile research/marine_geollm_scie/runs/20261031_graph_timeout180_v2/model_profile.json --snapshot outputs/scie_model_snapshot_20261030_v3/snapshot_manifest.json --contracts research/marine_geollm_scie/benchmark/frozen_v5/answer_contracts.jsonl --execute
```

실행 전 운영 수정과 테스트/API검증을 끝내야 한다. 실행 중 source freeze에 포함된 파일은 수정하지 않는다. 기존 K1 baseline 약3,691초를 단순 환산하면 baseline K5만 약5.1시간이며 graph와 환경 변동을 포함해 5~7시간 이상 걸릴 수 있다. 이는 추정이며 완료 약속이 아니다.

`status.json`은5초마다 stage/child PID/시간을 갱신한다. 원본 실행기 로그는 stage별파일, 문항 진행은 baseline의execution_rows 및 graph의current_case에 기록한다. 모델 해시와 소스는 각 stage 전후에 확인한다. **stage 도중 변경되면 사후 gate가 전체 실행을 무효화**하므로 실행 중 수정하지 않는다. 코드 변경 후에는 새 출력 폴더를 사용한다. 운영 UI HTML과 런타임 feedback은 freeze대상이 아니다.

프로세스 전역 lock(`outputs/scie_repeat_active.lock`), 실행 중 연구 Python/컨테이너 검사를 사용한다. 다른 수동 모델작업까지 강제 차단하는 시스템 전역 스케줄러는 아니므로 연구 동안 다른 Ollama 작업을 시작하지 않는다. 기존 graph 이름충돌도 하위launcher가 거부한다.

baseline 완료는exit0만으로 판정하지 않는다. status/450행/정확한18×5×5키집합/원본hash/source integrity/snapshot unchanged를 검사한다. graph는18개고유원문사례/EXECUTION_OBSERVED/source unchanged/warmup무오류 gate를 적용한다. 모델 실패행은 원본 관측에 포함하며 성공으로 재시도·교체하지 않는다.

`STOP_AFTER_STAGE` 파일을 출력폴더에 만들면 진행중stage를 완료한 경계에서 멈춘다. 이는 즉시중지가 아니다. 사용자가 즉시중단을 요청하면 상위·하위PID 및 연구worker/proxy를 확인해 중단하고 원본을보존한다. 강제중단 시 남은lock을 자동삭제하지 않는다. 실제프로세스 종료확인 후 수동인계한다. 중단/실패run은 덮지 않으며 새run 또는 원래하위실행기의 검증된resume을별도계획한다.

## 통계와 해석

`repeat_analysis`는 동일사례의5회관측을 먼저 평균하고 동등표현군집으로 묶는다. Q4세문항은한군집이다. 미측정반복이있는사례는완전측정평균null, 완전측정이아닌군집도null로유지한다. 측정분만의평균에는분모와미측정수를함께표시한다. 모델별측정범위가다르면평균만으로우열을주장하지않는다.

사례별검사결과변동·상태분포·지연평균/표준편차/최소/최대를보존한다. 이는개발18문항에대한기술통계다. 독립human GOLD/holdout이없으므로 전체의미정확도·유의확률·신뢰구간을생성하지않는다. 반복5회는표본수를늘리는대신동일입력의변동을관측한다. 연구순서는무작위가아니며cache·시간순서영향도제한으로남긴다.

## 독립 검수 자료

최신자료는 `review/20261031_independent_gold_v3/`의한글A/B/합의빈양식,기계가독JSONL,질문과출처,별도AI후보다. v1은CSV원본경로추가전, v2는AI가선택한객체별locator제거전기록으로보존하며독립초기검수에는v3만사용한다. A/B는먼저모델출력·상대방판단·AI정답후보없이원천을확인한다. 초기양식의문서출처는전체원천의판·경로·해시만제공하고객체별locator/claim플래그를제거했다. 공간원본ID정답목록은초기양식에포함하지않고사용자가고정한동도기준점·반경·CSV입력조건만제공한다. 독립초기답안작성과이후AI후보사후검증은서로다른절차로기록한다.

검수결과를받으면서명/일시/독립성/원천확인/불일치합의와파일hash를보존하고새참조버전으로재채점한다. 기존AI참조를인간GOLD로소급변경하지않는다. 개발에노출된18문항은독립검수후에도holdout이아니다. 새로운항만·표현·질의family의미노출검증은별도필요하다.
