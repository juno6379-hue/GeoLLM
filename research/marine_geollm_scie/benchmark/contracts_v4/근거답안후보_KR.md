# FC 원문 기반 9문항 근거·답안 후보

원문 추출은 XML 및 판·파일 hash를 검증했다. 답안 선택과 완결성 판단은 AI 초안이며 기존 GOLD를 확대하지 않는다.

| 사례 | 주요 원문 객체 | 검증 레코드 수 | 승인 원문 답안 | 남은 검토 |
|---|---|---|---|---|
| PILOT_Q1_01 | Landmark, Building, LightAllAround, LightSectored, function | 69 | ‘등대’는 단일 S-101 Geo Feature로 확정하지 않는다. 구조물은 문맥·형상에 따라 Landmark 또는 Building, 등화는 LightAllAround/LightSectored 등 별도 Light Feature로 표현한다. 로컬 항로표지 명칭만으로 S-101 Feature를 확정하지 않는다. | 최종 GOLD에서 ‘등대 구조물’과 ‘등화’를 별도 정답 범위로 명시하고, function/category binding은 FC 2.0.0로 최종 확인. |
| PILOT_Q1_02 | AnchorageArea | 24 | 일반적인 ‘정박지’는 AnchorageArea(ACHARE)로 해석한다. Point/Surface가 허용된다. 다만 문맥이 AnchorBerth·Mooring 등 특정 시설을 가리키면 별도 개념으로 재해석할 수 있다. | GOLD 승인 시 이 질의의 ‘정박지’가 일반 정박구역을 뜻한다는 범위를 명시. |
| PILOT_Q1_03 | Wreck | 26 | 정답 개념은 Wreck(WRECKS)이며 정의와 허용 기하(Point/Surface)를 설명한다. Obstruction 등 다른 hazard 개념을 자동 포함하지 않는다. | 추가 쟁점 없음. 표준 정의·feature code·기하를 최종 확인. |
| PILOT_Q2_01 | Landmark, Building, LightAllAround, LightSectored, colour | 69 | ‘등대 색상’은 구조물 표면색과 등화색을 분리한다. Landmark의 colour는 1~13이 허용되지만 LightAllAround의 colour는 FC binding상 1,3,4,5,6,9,10,11만 허용된다. LightSectored는 sectorCharacteristics→lightSector의 colour를 검토한다. 따라서 공통 colour enumeration 전체를 모든 등대 관련 Feature에 그대로 적용하지 않는다. | 이 항목은 기존 합의안의 실질 수정사항. 최종 GOLD에서 Feature별 permitted_values를 FC binding 기준으로 확정. |
| PILOT_Q2_02 | RestrictedArea, restriction, categoryOfRestrictedArea | 23 | 행위 제한은 restriction(RESTRN), 제한구역의 법적/분류상 종류는 categoryOfRestrictedArea(CATREA)로 분리한다. 두 enumeration을 혼용하지 않는다. 로컬 진입제한 코드도 승인된 매핑 없이는 S-101 RESTRN으로 자동 치환하지 않는다. | 최종 답안은 질의의 ‘제한 종류’가 두 의미 중 무엇인지 짧게 구분 설명하는 것이 적절. |
| PILOT_Q2_03 | Wreck | 26 | Wreck의 정답 속성은 FC 2.0.0의 attributeBinding을 기준으로 한다. categoryOfWreck, defaultClearanceDepth, expositionOfSounding, featureName, height, qualityOfVerticalMeasurement, status, valueOfSounding, waterLevelEffect 등 허용 속성을 대상으로 하며 featureBinding·informationBinding은 별도 관계로 취급한다. | 최종 GOLD에는 필수/선택, 다중도, permitted_values까지 필요한 수준을 결정하고 DB projection 컬럼과 표준 attribute를 구분. |
| PILOT_Q6_01 | Wreck | 26 | Wreck 정의는 FC 2.0.0의 Wreck 레코드와 공식 XML/DCEG 원문으로 추적한다. 한국어 설명은 번역/해설임을 구분하고 KG 요약이나 mapsToProduct 간선을 원문 정의의 권위 출처로 대체하지 않는다. | Evidence GOLD에는 edition, feature code, source file, locator/section을 필수 저장. |
| PILOT_Q6_02 | Landmark, Building, LightAllAround, LightSectored, LateralBuoy, CardinalBuoy, IsolatedDangerBuoy, SafeWaterBuoy, SpecialPurposeGeneralBuoy, EmergencyWreckMarkingBuoy, InstallationBuoy, MooringBuoy | 88 | 등대는 Landmark/Building 등의 고정 구조물과 별도 Light equipment의 구성으로 설명하고, 부표는 LateralBuoy·CardinalBuoy·SafeWaterBuoy 등 전용 부유 표지 Feature로 설명한다. 부표에도 등화가 결합될 수 있으므로 Light 존재 여부 자체를 등대/부표 판별 규칙으로 사용하지 않는다. 제시하는 Buoy classes는 대표 예시로 표현한다. | 최종 GOLD에서 비교 기준을 ‘고정 구조물 vs 부유 표지의 Feature 모델링 및 equipment composition’으로 명시. |
| PILOT_Q6_03 | AnchorageArea | 24 | AnchorageArea 정의는 FC 2.0.0/원 XML 및 DCEG §16.3을 권위근거로 사용한다. KG relation은 검색 보조 provenance로만 사용하며 정의의 권위 출처를 대체하지 않는다. | Evidence GOLD에 source file/version/locator와 Feature code를 저장. |

## 원문 확인값

- `Landmark → colour`: binding 허용코드 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 다중도 0..*.
- `Building → colour`: binding 허용코드 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 다중도 0..*.
- `LightAllAround → colour`: binding 허용코드 1, 3, 4, 5, 6, 9, 10, 11, 다중도 1..*.
- `lightSector → colour`: binding 허용코드 1, 3, 4, 5, 6, 9, 10, 11, 다중도 1..*.

각 객체의 정확한 definition, 전체 직접 binding, 재귀 attribute 의존성, allowed code와 label, 판, XPath, 원문 hash는 JSONL에 있다. 전역 colour 코드목록 13개를 LightAllAround의 8개 허용값으로 대신하지 않는다. LightSectored는 복합 attribute 경로를 따라간다.
