# RQ3 정상 공간 조회 복구와 wrong-but-executable 개발 검증

## 기존 v6 결론은 유지

P1 ESR=0/5, 실행·공간 공동 성공=0/5, raw 공간정답은 2/5 관측·3/5 미측정이다. 성공 실행 분모가 0이므로 **CGE와 SSFR는 측정 불가(null)**다. SSFR 0%나 silent failure가 없었다고 해석하지 않는다.

## 실제로 확인한 별도 개발 결과

| 확인 경로 | 반환/GOLD 객체 행 | 실행 E | 객체집합 정답 S |
|---|---:|---|---|
| 운영 GeoLLM Q4 API | 11건 반환 | true (네 실행 필드 확인) | API 관측만으로 별도 공간 정확도 확정하지 않음 |
| 연구DB Q4 원본 ID 연결 | 11/11 | true | true — 원본 CSV ID 집합 기준 |
| Q5_02 최소 기하 거리 2km | 24/24 | true | true |
| Q5_02 중심점 거리 2km 변이 | 0/24 | true | false — 24행 누락 |

기준 polygon은 기존 GOLD의 HarbourAreaAdministrative **1137770**으로 고정했다. 정상 정답은 AnchorageArea3 + RestrictedArea21 객체 행이다. 같은 실재 객체가 축척별로 중복될 수 있는 기존 feature-row 정책을 유지하며 24개 독립 시설이라고 부르지 않는다.

정상 predicate:

```sql
ST_DWithin(target::geography, reference::geography, 2000, true)
```

변이 predicate:

```sql
ST_DWithin(ST_Centroid(target)::geography,
           ST_Centroid(reference)::geography, 2000, true)
```

두 번째 predicate도 유효한 SQL이므로 정상 종료했다. 그러나 최소 geometry-to-geometry 거리라는 요청 의미를 centroid-to-centroid 거리로 바꾸어 정답 객체를 모두 누락했다. **E=true·S=false인 silent spatial failure 반례**가 실제로 성립한다. 실제로는 한 SELECT에서 두 predicate를 함께 평가한 paired SQL 개발 진단이며, 두 방법/모델을 별도로 실행한 논문 성능 비교가 아니다. 의도적으로 만든 단일 반례에서 계산 가능한 SSFR를 방법별 일반 성능으로 보고하지 않는다.

## 원천·실행 검증

기존 `marine-scie-pilot-db` 연구 label/DB identity를 확인하고 기존 컨테이너만 시작했다. 운영DB를 대체 원천으로 쓰거나 연구DB를 수정하지 않았다. 단일 READ ONLY·REPEATABLE READ 트랜잭션에서 S101 projection과 해양지명 두 관계를 CSV 추출하고, 실제 source hash가 v6의 동결 export와 일치함을 확인했다. 같은 트랜잭션에서 거리·포함 결과를 얻고 ROLLBACK했다. 기준 geometry SHA/CRS/유일행 및 기존 독립 GOLD 객체집합을 검증했다. 이것은 두 관계의 검증이지 6개 관계 전체 재동결이 아니다.

원본: `outputs/rq3_wrong_executable_20261102_v2/`의 protocol_before_execution.json, transaction.sql/stdout/stderr, spatial_rows.json, summary.json, manifest.json. SQL 성공은 서버 응답 확인 뒤에만 기록했다. 실제 모델/Recovery 호출이나 ExecutionValidator 권한 우회로 P0/P1의 성공을 만들어내지 않았다.

## 발견하고 수정한 평가 오류

첫 진단 v1은 Q4 DB의 해시 source_id와 GOLD의 원본 CSV 일련번호44–54를 직접 비교해 S=false로 잘못 판정했다. 검색이 실패한 것이 아니라 **ID namespace 평가 오류**였다. v1의 SQL·원시결과·manifest 및 원래 runner bytes를 보존했다. 원래 runner는 `outputs/rq3_parent_20261102/preserved_runner_v1.py`에 SHA 일치 확인 후 보존했다.

v2는 고정 원본 CSV bytes hash, 전체 properties, provenance source hash, ingestion hash ID 생성식을 대조해 원본 일련번호와 연결한다. 이름/근접거리만으로 객체를 같다고 추정하지 않는다. DB 해시 ID도 별도로 보존하고 Q4 11/11 일치를 재실행했다. DB geometry는 projected WKT 유래이고 기존 Q4 GOLD는 명시 DMS 좌표 정책이므로 이번 Q4 S는 **객체집합 일치**에 한정한다. 모든 좌표 정밀도·거리 오차가 검증됐다고 주장하지 않는다.

## UI·회귀와 남은 단계

RQ3 UI는 기존 v6 지표와 v2 개발 진단을 별도 표시한다. artifact 해시/네 실행 필드/객체집합·건수/S 판정 정합성을 검사하고, v1은 연결하지 않는다. 관련 연구·평가기 회귀21, UI회귀15, Node23 통과(중복합산하지 않음). 실제 HTTP와 기존 GOLD/v6 506파일·v1 불변 확인은 `outputs/rq3_parent_20261102/final_verification.json`에 기록한다. 브라우저 화면 조작 검증과 구분한다.

다음은 이 반례를 새 동결 benchmark의 method executor/post-validation 관측과 연결하고, 여러 독립 geometry·정상/오류 사례로 확장하는 것이다. 연구 ResearchBindingAdapter의 snapshot 권위 연결·정상 control 오차단 등 기존 선행 gate는 별도 남아 있다. 운영 Q4 복구와 direct SQL 반례를 새 8방법 전체 비교 완료로 대신하지 않는다. 홀드아웃은 사용하지 않았다.
