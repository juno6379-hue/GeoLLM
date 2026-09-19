(function () {
    "use strict";

    const featureId = row => String(row?.feature_id ?? row?.feature_instance_id ?? row?.event_id ?? row?.id ?? row?.source_id ?? "");
    const evidenceData = item => {
        const data = item && typeof item.data === "object" ? item.data : item;
        if (!data || typeof data !== "object") return data;
        const props = data.properties && typeof data.properties === "object" ? data.properties : {};
        return { ...props, ...data };
    };
    const numberText = value => typeof value === "number" && Number.isFinite(value)
        ? value.toLocaleString("ko-KR") : "-";
    const yesNo = value => value ? "사용" : "미사용";

    function coordinatePairFromWkt(wkt) {
        const match = String(wkt || "").match(/POINT\s*\(\s*([0-9.+-]+)\s+([0-9.+-]+)\s*\)/i);
        if (!match) return null;
        const lon = Number(match[1]);
        const lat = Number(match[2]);
        return Number.isFinite(lon) && Number.isFinite(lat) ? [lon, lat] : null;
    }

    function coordinateTextFromPair(coordinates) {
        if (!Array.isArray(coordinates) || coordinates.length < 2) return "";
        const lon = Number(coordinates[0]);
        const lat = Number(coordinates[1]);
        if (!Number.isFinite(lon) || !Number.isFinite(lat)) return "";
        return `경도 ${lon.toFixed(6)}, 위도 ${lat.toFixed(6)} · EPSG:4326`;
    }

    function coordinateTextFromFeature(feature, fallback) {
        const props = feature?.properties || {};
        if (props.coordinate_text) return props.coordinate_text;
        if (props.longitude != null && props.latitude != null) return coordinateTextFromPair([props.longitude, props.latitude]);
        const coordinates = feature?.geometry?.type === "Point" ? feature.geometry.coordinates : null;
        return coordinateTextFromPair(coordinates) || fallback || "";
    }

    function compactJson(value) {
        if (value === undefined || value === null || value === "") return "-";
        if (typeof value === "string") return value;
        try { return JSON.stringify(value); } catch (_err) { return String(value); }
    }

    function element(tag, text, className) {
        const node = document.createElement(tag);
        if (text !== undefined) node.textContent = String(text);
        if (className) node.className = className;
        return node;
    }

    function technicalEvidence(row, evidenceId, source) {
        const details = element("details", undefined, "evidence-technical");
        details.append(element("summary", "원본 식별 정보"));
        details.append(element("div", `객체 ID: ${featureId(row) || "-"}`));
        if (evidenceId) details.append(element("div", `근거 ID: ${evidenceId}`));
        if (source) details.append(element("div", `원본 출처: ${source}`));
        return details;
    }

    function addClass(node, className) {
        if (!node) return;
        if (node.classList?.add) node.classList.add(className);
        else if (!String(node.className || "").split(/\s+/).includes(className)) node.className = `${node.className || ""} ${className}`.trim();
    }

    function removeClass(node, className) {
        if (!node) return;
        if (node.classList?.remove) node.classList.remove(className);
        else node.className = String(node.className || "").split(/\s+/).filter(name => name && name !== className).join(" ");
    }

    function scaleState(map) {
        const zoom = typeof map?.getZoom === "function" ? map.getZoom() : 13;
        if (zoom >= 15) return { className: "s101-scale-detail", weight: 3, opacity: 0.95, fillOpacity: 0.36 };
        if (zoom >= 12) return { className: "s101-scale-harbor", weight: 2, opacity: 0.86, fillOpacity: 0.22 };
        return { className: "s101-scale-overview", weight: 1, opacity: 0.72, fillOpacity: 0.1 };
    }

    function applyScaleClass(map) {
        const container = typeof map?.getContainer === "function" ? map.getContainer() : null;
        if (!container) return;
        container.classList.remove("s101-scale-overview", "s101-scale-harbor", "s101-scale-detail");
        container.classList.add(scaleState(map).className);
    }

    function featureSymbol(row) {
        const portrayal = row?.portrayal || {};
        const symbol = portrayal.symbol || row?.portrayal_symbol;
        const asset = portrayal.asset || row?.portrayal_symbol_asset;
        if (symbol && asset) {
            return {
                key: String(symbol).toLowerCase(),
                label: `${row.feature_name || "S-101 feature"} (${symbol})`,
                asset,
            };
        }
        return null;
    }

    function fallbackSymbol(row) {
        const name = row?.feature_name || row?.feature_type_name || "";
        const symbols = {
            Berth: { glyph: "⚓", label: "선석 (Berth)", className: "s101-fallback-berth" },
            Obstruction: { glyph: "◇", label: "장애물 (Obstruction)", className: "s101-fallback-obstruction" },
            Wreck: { glyph: "✕", label: "침선 (Wreck)", className: "s101-fallback-wreck" },
            UnderwaterAwashRock: { glyph: "▲", label: "수중/간출암", className: "s101-fallback-rock" },
            IsolatedDangerBuoy: { glyph: "!", label: "고립위험 부표", className: "s101-fallback-danger-mark" },
            IsolatedDangerBeacon: { glyph: "!", label: "고립위험 표지", className: "s101-fallback-danger-mark" },
            EmergencyWreckMarkingBuoy: { glyph: "W", label: "응급 침선표지 부표", className: "s101-fallback-wreck-mark" },
            LateralBuoy: { glyph: "B", label: "측방 부표", className: "s101-fallback-aid" },
            LateralBeacon: { glyph: "B", label: "측방 표지", className: "s101-fallback-aid" },
            CardinalBuoy: { glyph: "C", label: "방위표지 부표", className: "s101-fallback-aid" },
            CardinalBeacon: { glyph: "C", label: "방위표지", className: "s101-fallback-aid" },
            SpecialPurposeGeneralBuoy: { glyph: "S", label: "특수목적 부표", className: "s101-fallback-aid" },
            SpecialPurposeGeneralBeacon: { glyph: "S", label: "특수목적 표지", className: "s101-fallback-aid" },
            LightAllAround: { glyph: "L", label: "전방위등", className: "s101-fallback-light" },
            LightSectored: { glyph: "L", label: "섹터등", className: "s101-fallback-light" },
        };
        return symbols[name] || null;
    }

    function featureDisplayName(value) {
        const names = {
            Obstruction: "장애물",
            Wreck: "침선",
            UnderwaterAwashRock: "수중/간출암",
            BuoyIsolatedDanger: "고립위험 부표",
            BeaconIsolatedDanger: "고립위험 표지",
            IsolatedDangerBuoy: "고립위험 부표",
            IsolatedDangerBeacon: "고립위험 표지",
            EmergencyWreckMarkingBuoy: "응급 침선표지 부표",
            LateralBuoy: "측방 부표",
            LateralBeacon: "측방 표지",
            CardinalBuoy: "방위표지 부표",
            CardinalBeacon: "방위표지",
            SpecialPurposeGeneralBuoy: "특수목적 부표",
            SpecialPurposeGeneralBeacon: "특수목적 표지",
            LightAllAround: "전방위등",
            LightSectored: "섹터등",
        };
        return names[value] || window.QuerySummary?.featureName?.(value) || value || "공간 객체";
    }

    function rowDisplayName(row) {
        if (row?.layer_role === "accident_event") {
            return row?.label || [row?.authority, row?.cause, row?.accident_type].filter(Boolean).join(" ") || "Accident event";
        }
        return row?.display_name || row?.feature_display_name || row?.name || row?.feature_name || row?.feature_type_name || "공간 객체";
    }

    function featureStyle(row) {
        if (row?.layer_role === "accident_event") {
            const cause = String(row?.cause || "");
            if (cause.includes("정비") || cause.toLowerCase().includes("maintenance")) {
                return { color: "#b45309", fillColor: "#fbbf24", label: "Accident event" };
            }
            return { color: "#be123c", fillColor: "#fb7185", label: "Accident event" };
        }
        const name = row?.feature_name || row?.feature_type_name || "";
        if (name === "Obstruction") return { color: "#f97316", fillColor: "#fed7aa", label: "장애물" };
        if (name === "Wreck") return { color: "#dc2626", fillColor: "#fecaca", label: "침선" };
        if (name === "UnderwaterAwashRock") return { color: "#7c3aed", fillColor: "#ddd6fe", label: "수중/간출암" };
        if (name === "IsolatedDangerBuoy" || name === "IsolatedDangerBeacon") return { color: "#eab308", fillColor: "#fef3c7", label: "고립위험 표지" };
        if (name === "EmergencyWreckMarkingBuoy") return { color: "#dc2626", fillColor: "#fee2e2", label: "응급 침선표지 부표" };
        if (name.includes("Buoy") || name.includes("Beacon") || name.includes("Light")) return { color: "#2563eb", fillColor: "#dbeafe", label: "항로표지" };
        return { color: "#0f766e", fillColor: "#99f6e4", label: featureDisplayName(name) };
    }

    function symbolClass(row) {
        const name = String(row?.feature_name || row?.feature_type_name || "").toLowerCase();
        if (name === "obstruction") return "s101-symbol-obstruction";
        if (name === "wreck") return "s101-symbol-wreck";
        if (name === "underwaterawashrock") return "s101-symbol-rock";
        if (name === "isolateddangerbuoy" || name === "isolateddangerbeacon") return "s101-symbol-danger-mark";
        if (name === "emergencywreckmarkingbuoy") return "s101-symbol-wreck";
        if (name.includes("buoy") || name.includes("beacon") || name.includes("light")) return "s101-symbol-aid";
        return "";
    }

    function obstructionCategoryLabel(value) {
        const labels = {
            1: "snag/stump",
            2: "wellhead",
            3: "diffuser",
            4: "crib",
            5: "fish haven",
            6: "foul area",
            7: "foul ground",
            8: "ice boom",
            9: "ground tackle",
            10: "boom",
            14: "pile",
            17: "wreckage",
            21: "volcanic activity",
            23: "vegetation",
        };
        const code = Number(value);
        return Number.isFinite(code) && labels[code] ? `${labels[code]} (${code})` : value ? `분류 코드 ${value}` : "-";
    }

    function waterLevelLabel(value) {
        const labels = {
            1: "partly submerged at high water",
            2: "always dry",
            3: "always underwater/submerged",
            4: "covers and uncovers",
            5: "awash",
            6: "subject to inundation",
            7: "floating",
        };
        const code = Number(value);
        return Number.isFinite(code) && labels[code] ? `${labels[code]} (${code})` : value ? `수면 상태 코드 ${value}` : "-";
    }

    function featureExplanation(row) {
        const attrs = row?.attributes || {};
        const geometryType = row?.geometry_type || "-";
        if (row?.feature_name === "Obstruction") {
            return [
                `이 객체는 S-101 Obstruction(장애물) Feature입니다.`,
                `geometry_type=${geometryType}이므로 ${geometryType === "POLYGON" ? "점이 아니라 실제 면형 장애물로 지도에 폴리곤을 그립니다." : "해당 도형 타입으로 지도에 표시합니다."}`,
                `categoryOfObstruction=${obstructionCategoryLabel(attrs.categoryOfObstruction)} / waterLevelEffect=${waterLevelLabel(attrs.waterLevelEffect)}.`,
            ].join(" ");
        }
        if (row?.feature_name === "Wreck") {
            return `이 객체는 S-101 Wreck(침선) Feature입니다. geometry_type=${geometryType}이므로 원천 데이터의 도형 타입 그대로 표시합니다.`;
        }
        if (row?.feature_name === "UnderwaterAwashRock") {
            return `이 객체는 S-101 Underwater/Awash Rock(수중암/간출암) Feature입니다. geometry_type=${geometryType}이므로 원천 데이터의 도형 타입 그대로 표시합니다.`;
        }
        if (row?.feature_name === "IsolatedDangerBuoy" || row?.feature_name === "IsolatedDangerBeacon") {
            return `이 객체는 S-101 고립위험 항로표지 Feature입니다. 실제 장애물 자체가 아니라, 전자해도에서 고립위험을 지시하는 부표/표지 위치입니다. geometry_type=${geometryType}으로 표시합니다.`;
        }
        if (row?.feature_name === "EmergencyWreckMarkingBuoy") {
            return `이 객체는 S-101 Emergency Wreck Marking Buoy Feature입니다. 침선 또는 신규 위험을 알리는 표지 위치이므로 위험객체 분석에 포함합니다. geometry_type=${geometryType}으로 표시합니다.`;
        }
        if (/Buoy|Beacon|Light/.test(row?.feature_name || "")) {
            return `이 객체는 S-101 항로표지/등화 Feature입니다. 물리적 장애물 자체라기보다 항행자가 위험을 회피하거나 항로를 식별하는 데 쓰는 전자해도 표지 위치입니다. geometry_type=${geometryType}으로 표시합니다.`;
        }
        return `원천 데이터의 geometry_type=${geometryType} 도형으로 표시합니다.`;
    }

    function attributeEntries(attributes) {
        if (!attributes || typeof attributes !== "object" || Array.isArray(attributes)) return [];
        const priority = [
            "objectName", "OBJNAM", "name", "categoryOfObstruction", "categoryOfWreck",
            "waterLevelEffect", "valueOfSounding", "depthRangeMinimumValue",
            "depthRangeMaximumValue", "qualityOfVerticalMeasurement", "status",
        ];
        const seen = new Set();
        const entries = [];
        for (const key of priority) {
            if (Object.prototype.hasOwnProperty.call(attributes, key)) {
                entries.push([key, attributes[key]]);
                seen.add(key);
            }
        }
        for (const [key, value] of Object.entries(attributes)) {
            if (seen.has(key)) continue;
            entries.push([key, value]);
            if (entries.length >= 10) break;
        }
        return entries.filter(([, value]) => value !== null && value !== undefined && value !== "");
    }

    function appendFeatureDetails(container, row, referenceLabel) {
        if (row?.layer_role === "accident_event") {
            container.append(element("strong", rowDisplayName(row)));
            container.append(element("div", `Event ID: ${featureId(row) || "-"}`));
            container.append(element("div", `기준점: ${referenceLabel}`));
            container.append(element("div", `기준점에서 ${window.QuerySummary.distanceText(row.distance_m)}`));
            container.append(element("div", `발생시각: ${row.occurred_at || "-"}`));
            container.append(element("div", `관할: ${row.authority || "-"} / 해역: ${row.sea_area || "-"}`));
            container.append(element("div", `원인: ${row.cause || "-"} / 유형: ${row.accident_type || "-"}`));
            container.append(element("div", `선종: ${row.vessel_type || "-"} / 톤수: ${row.tonnage ?? "-"}`));
            container.append(element("div", `인원: ${row.people_count ?? "-"} / 구조 ${row.rescued ?? "-"} / 사망 ${row.dead ?? "-"} / 실종 ${row.missing ?? "-"}`));
            container.append(element("div", `좌표: ${row.latitude ?? "-"}, ${row.longitude ?? "-"} (WGS84)`, "radius-meta"));
            container.append(element("div", `Source: ${row.source_ref || "serving.accident_events"}`, "radius-meta"));
            return;
        }
        container.append(element("strong", rowDisplayName(row)));
        container.append(element("div", `객체 ID: ${featureId(row) || "-"}`));
        container.append(element("div", `기준점: ${referenceLabel}`));
        container.append(element("div", `기준점에서 ${window.QuerySummary.distanceText(row.distance_m)}`));
        container.append(element("div", `S-101 Feature: ${row.feature_name || "-"} / 코드 ${row.feature_type_code ?? "-"}`, "radius-meta"));
        container.append(element("div", `Geometry: ${row.geometry_type || "-"}`, "radius-meta"));
        container.append(element("div", `Dataset: ${row.source_dataset_id || row.dataset_id || "-"} / ${row.dataset_version_id || "-"}`, "radius-meta"));
        container.append(element("div", featureExplanation(row), "radius-meta"));
        if (row.portrayal?.selection_reason) {
            container.append(element("div", `Portrayal: ${row.portrayal.symbol || "-"} · ${row.portrayal.selection_reason}`, "radius-meta"));
        }
        const entries = attributeEntries(row.attributes);
        if (entries.length) {
            const details = element("details", undefined, "evidence-technical");
            details.open = true;
            details.append(element("summary", "Feature 속성"));
            for (const [key, value] of entries) {
                details.append(element("div", `${key}: ${compactJson(value)}`));
            }
            container.append(details);
        }
    }

    function symbolMarker(feature, latlng, searchArea) {
        if (searchArea || !L.divIcon || !L.marker) {
            const style = featureStyle(feature.properties || {});
            return L.circleMarker(latlng, {
                radius: searchArea ? 4 : 7,
                color: searchArea ? "#0284c7" : style.color,
                fillColor: searchArea ? "#38bdf8" : style.fillColor,
                fillOpacity: searchArea ? 0.45 : 0.95,
                weight: 2,
            });
        }
        const row = feature.properties || {};
        if (row.layer_role === "accident_event") {
            const style = featureStyle(row);
            return L.circleMarker(latlng, {
                radius: 7,
                color: style.color,
                fillColor: style.fillColor,
                fillOpacity: 0.9,
                opacity: 0.95,
                weight: 2,
            });
        }
        const symbol = featureSymbol(row);
        if (!symbol) {
            const fallback = fallbackSymbol(row);
            if (fallback) {
                const html = `<span class="s101-fallback-symbol ${fallback.className}" title="${fallback.label}">${fallback.glyph}</span>`;
                return L.marker(latlng, {
                    icon: L.divIcon({
                        className: "s101-portrayal-marker",
                        html,
                        iconSize: [32, 32],
                        iconAnchor: [16, 16],
                        popupAnchor: [0, -14],
                    }),
                });
            }
            const style = featureStyle(row);
            return L.circleMarker(latlng, {
                radius: 7, color: style.color, fillColor: style.fillColor, fillOpacity: 0.95, weight: 2,
            });
        }
        const html = `<img class="s101-portrayal-symbol ${symbolClass(row)}" src="${symbol.asset}" alt="${symbol.label}" title="${symbol.label}">`;
        return L.marker(latlng, {
            icon: L.divIcon({
                className: "s101-portrayal-marker",
                html,
                iconSize: [32, 32],
                iconAnchor: [16, 16],
                popupAnchor: [0, -14],
            }),
        });
    }

    function isRadiusAnalysis(result) {
        const structured = result?.structured_result || {};
        return structured.analysis_type === "feature_search_by_radius"
            || structured.analysis_type === "traffic_search_by_time_space"
            || structured.analysis_type === "accident_spatial_history_lookup"
            || structured.analysis_type === "accident_event_lookup"
            || result?.orchestrator_v2?.route_plan?.analysis_type === "feature_search_by_radius"
            || result?.orchestrator_v2?.route_plan?.analysis_type === "traffic_search_by_time_space"
            || result?.orchestrator_v2?.route_plan?.analysis_type === "accident_spatial_history_lookup"
            || result?.orchestrator_v2?.route_plan?.analysis_type === "accident_event_lookup";
    }

    function isTrafficAnalysis(result) {
        const structured = result?.structured_result || {};
        return structured.analysis_type === "traffic_search_by_time_space"
            || result?.orchestrator_v2?.route_plan?.analysis_type === "traffic_search_by_time_space";
    }

    function isRadius(result) {
        const structured = result?.structured_result || {};
        const analysis = structured.analysis_type || result?.orchestrator_v2?.route_plan?.analysis_type;
        const needsInput = [result?.status, structured.status].some(status => ["NEEDS_CLARIFICATION", "NEEDS_USER_INPUT"].includes(status));
        const blocked = [result?.status, structured.status].some(status => ["BLOCKED", "BLOCKED_DATA", "BLOCKED_CONFIG"].includes(status));
        const hasRadiusLayers = Array.isArray(result?.map_layers) && result.map_layers.some(layer =>
            ["matched_features", "search_area", "accident_event", "accident_overlay"].includes(layer?.role || layer?.metadata?.role || layer?.metadata?.layer_role)
            || layer?.inline_geojson?.features?.some(feature => feature?.properties?.layer_role === "accident_event")
        );
        const hasSpatialGeojson = Array.isArray(structured.geojson?.features) || Array.isArray(result?.features?.features);
        return isRadiusAnalysis(result) || analysis === "place_lookup"
            || hasRadiusLayers
            || hasSpatialGeojson && ["accident_spatial_history_lookup", "accident_event_lookup"].includes(analysis)
            || analysis === "nearest_feature" && (blocked || needsInput && Array.isArray(structured.location_candidates));
    }

    function reset() {
        window.QuerySummary.reset();
        const details = document.getElementById("radiusDetails");
        details.replaceChildren();
        details.hidden = true;
        delete details.dataset.resultId;
        delete details.dataset.queryExecutionId;
        delete details.dataset.placeId;
        delete details.dataset.placeVersion;
        document.getElementById("returnedCount").textContent = "";
    }

    function withoutPlaceSelection(spatial) {
        const values = { ...(spatial || {}) };
        delete values.place_id;
        delete values.place_version;
        delete values.location_resolution;
        return values;
    }

    function renderCandidates(result, originalQuery, submit) {
        const structured = result.structured_result || {};
        const originalSpatial = structured.spatial_context || {};
        const container = document.getElementById("radiusDetails");
        for (const candidate of structured.location_candidates || []) {
            const section = element("div", undefined, "location-candidate");
            section.dataset.placeId = candidate.place_id || "";
            section.dataset.placeVersion = candidate.place_version || "";
            section.append(element("strong", candidate.label || candidate.base_location || candidate.place_id));
            const candidateCoordinates = coordinatePairFromWkt(candidate.geometry);
            const candidateCoordinateText = coordinateTextFromPair(candidateCoordinates);
            section.append(element("div", candidateCoordinateText || `${candidate.geometry || "좌표 미확정"} · ${candidate.crs || "좌표계 미확정"}`, "radius-meta"));
            const candidateStatus = candidate.status === "curated" ? "로컬 등록 후보" : candidate.status === "test" ? "테스트 후보" : candidate.status;
            const candidateSource = candidate.source_ref === "local_curated_binding" ? "로컬 등록 정보" : candidate.source_ref;
            if (candidateStatus) section.append(element("div", candidateStatus, "radius-meta"));
            if (candidateSource) section.append(element("div", candidateSource, "radius-meta"));
            if (candidate.evidence_summary) section.append(element("div", `근거: ${candidate.evidence_summary}`, "radius-meta"));
            if (candidate.place_id || candidate.place_version || candidate.source_records?.length) {
                const sourceDetails = element("details", undefined, "evidence-technical");
                sourceDetails.append(element("summary", "지명 출처 상세"));
                if (candidate.place_id) sourceDetails.append(element("div", `지명 ID: ${candidate.place_id}`));
                if (candidate.place_version) sourceDetails.append(element("div", `데이터 버전: ${candidate.place_version}`));
                for (const record of candidate.source_records || []) sourceDetails.append(element("div", compactJson(record), "radius-meta"));
                section.append(sourceDetails);
            }
            const button = element("button", "이 위치로 조회", "location-confirm");
            button.type = "button";
            button.disabled = !candidate.geometry || !candidate.crs;
            button.addEventListener("click", () => {
                button.disabled = true;
                submit({
                    query: structured.original_query || originalQuery,
                    fresh: true,
                    spatialContext: {
                        ...withoutPlaceSelection(originalSpatial),
                        place_id: candidate.place_id,
                        place_version: candidate.place_version,
                        base_location: candidate.base_location || candidate.label,
                        geometry: candidate.geometry,
                        crs: candidate.crs,
                        ...(structured.distance_m != null ? { buffer_distance: structured.distance_m } : {}),
                    },
                });
            });
            section.append(button);
            container.append(section);
        }
    }

    function renderPointForm(result, originalQuery, submit, radiusRequired) {
        const structured = result.structured_result || {};
        const spatial = structured.spatial_context || {};
        const form = element("form", undefined, "radius-point-form");
        form.noValidate = true;
        form.append(element("div", "기준 좌표 (EPSG:4326)", "section-title"));
        const fields = element("div", undefined, "radius-point-fields");
        const inputs = {};
        const fieldSpecs = [["longitude", "경도", -180, 180], ["latitude", "위도", -90, 90]];
        if (radiusRequired) fieldSpecs.push(["radius", "반경 (m)", 0, 50000]);
        for (const [name, title, min, max] of fieldSpecs) {
            const label = element("label", title);
            const input = element("input");
            Object.assign(input, { type: "number", name, min: String(min), max: String(max), step: "any", required: true, value: "" });
            input.inputMode = "decimal";
            label.append(input);
            fields.append(label);
            inputs[name] = input;
        }
        const knownRadius = structured.distance_m ?? spatial.buffer_distance;
        if (inputs.radius && typeof knownRadius === "number" && Number.isFinite(knownRadius)) inputs.radius.value = String(knownRadius);
        const point = spatial.crs === "EPSG:4326" && typeof spatial.geometry === "string"
            ? spatial.geometry.match(/^\s*POINT\s*\(\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?)\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?)\s*\)\s*$/i) : null;
        if (point && Number.isFinite(Number(point[1])) && Number.isFinite(Number(point[2])) && Math.abs(Number(point[1])) <= 180 && Math.abs(Number(point[2])) <= 90) {
            inputs.longitude.value = point[1];
            inputs.latitude.value = point[2];
        }
        const button = element("button", "이 좌표로 조회", "location-confirm");
        button.type = "submit";
        const error = element("div", "", "radius-warning");
        error.setAttribute("role", "alert");
        form.append(fields, button, error);
        form.addEventListener("submit", event => {
            event.preventDefault();
            const values = Object.fromEntries(Object.entries(inputs).map(([name, input]) => [name, input.value.trim() === "" ? NaN : Number(input.value)]));
            const valid = {
                longitude: Number.isFinite(values.longitude) && Math.abs(values.longitude) <= 180,
                latitude: Number.isFinite(values.latitude) && Math.abs(values.latitude) <= 90,
                ...(radiusRequired ? { radius: Number.isFinite(values.radius) && values.radius > 0 && values.radius <= 50000 } : {}),
            };
            for (const [name, input] of Object.entries(inputs)) input.setAttribute("aria-invalid", String(!valid[name]));
            if (!Object.values(valid).every(Boolean)) {
                error.textContent = radiusRequired ? "경도 -180~180, 위도 -90~90, 반경 0 초과~50,000 m를 입력해 주세요." : "경도 -180~180, 위도 -90~90을 입력해 주세요.";
                return;
            }
            error.textContent = "";
            button.disabled = true;
            submit({
                query: structured.original_query || originalQuery,
                fresh: true,
                spatialContext: {
                    ...withoutPlaceSelection(spatial),
                    base_location: structured.location_text || spatial.base_location || "사용자 지정 좌표",
                    geometry: `POINT(${values.longitude} ${values.latitude})`,
                    crs: "EPSG:4326",
                    ...(radiusRequired ? { buffer_distance: values.radius } : {}),
                },
            });
        });
        document.getElementById("radiusDetails").append(form);
    }

    function renderSurface(details, result, structured) {
        const surface = structured.result_surface || {};
        const sourceLayer = surface.source_layer || structured.source_layer || {};
        const usage = surface.web_rag_usage || structured.web_rag_usage || {};
        const evidenceCounts = surface.evidence_bundle || structured.evidence_bundle_counts || {};
        const geojsonInfo = surface.geojson || {};
        const mapLayerInfo = surface.map_layers || {};
        const mapLayerCount = mapLayerInfo.count ?? structured.map_layer_count ?? (Array.isArray(result.map_layers) ? result.map_layers.length : 0);
        const geojsonCount = geojsonInfo.feature_count ?? structured.geojson_feature_count ?? structured.geojson?.features?.length ?? 0;
        const rows = [
            ["전체 위험객체 수", numberText(surface.total_hazard_count ?? structured.total_count ?? structured.count)],
            ["nearest 반환 개수", numberText(surface.nearest_returned_count ?? structured.nearest_returned_count ?? structured.returned_count)],
            ["feature type breakdown", compactJson(surface.feature_type_breakdown || structured.feature_type_breakdown || structured.total_counts_by_type)],
            ["source layer", compactJson(sourceLayer.physical_table || sourceLayer.layer_id || sourceLayer)],
            ["reference geometry", compactJson(surface.reference_geometry || structured.reference_geometry)],
            ["GeoJSON/map layer", `GeoJSON ${numberText(geojsonCount)}개 / map layer ${numberText(mapLayerCount)}개`],
            ["evidence bundle", compactJson(evidenceCounts)],
            ["web/RAG 사용 여부", `web ${yesNo(usage.web_used)} / RAG ${yesNo(usage.rag_used)} / LLM ${yesNo(usage.llm_used)}`],
        ];
        const section = element("div", undefined, "radius-surface");
        for (const [label, value] of rows) {
            const row = element("div", undefined, "radius-surface-row");
            row.append(element("div", label, "radius-surface-label"));
            row.append(element("div", value, "radius-surface-value"));
            section.append(row);
        }
        details.append(section);
    }

    function placeProvenance(place, resolution) {
        const details = element("details", undefined, "evidence-technical");
        details.append(element("summary", "지명 출처 상세"));
        if (place.place_id) details.append(element("div", `지명 ID: ${place.place_id}`));
        if (place.place_version) details.append(element("div", `데이터 버전: ${place.place_version}`));
        if (resolution.source_ref) details.append(element("div", `원본 출처: ${resolution.source_ref}`));
        for (const record of resolution.source_records || []) details.append(element("div", compactJson(record), "radius-meta"));
        return details;
    }

    function renderPlaceResult(result, options) {
        const structured = result.structured_result || {};
        const collection = structured.geojson || result.map_layers?.find(layer => layer.inline_geojson)?.inline_geojson;
        const pointFeatures = Array.isArray(collection?.features)
            ? collection.features.filter(feature => {
                const coordinates = feature?.geometry?.coordinates;
                return feature?.geometry?.type === "Point" && Array.isArray(coordinates) && coordinates.length === 2
                    && coordinates.every(Number.isFinite) && Math.abs(coordinates[0]) <= 180 && Math.abs(coordinates[1]) <= 90;
            })
            : [];
        const feature = pointFeatures.length === 1 ? pointFeatures[0] : null;
        const coordinates = feature?.geometry?.coordinates;
        const valid = pointFeatures.length > 0;
        const query = structured.original_query || options.originalQuery;
        const details = document.getElementById("radiusDetails");
        const evidence = document.getElementById("answerEvidence");
        document.getElementById("intentResult").textContent = "지명 조회";
        document.getElementById("dangerCount").textContent = "-";
        if (!valid) {
            document.getElementById("answerStatus").textContent = "결과 확인 필요";
            window.QuerySummary.show("결과 확인 필요", "확인된 위치의 지도 좌표를 확인할 수 없습니다.", query);
            evidence.append(element("div", "유효한 기준점이 반환되지 않았습니다.", "radius-warning"));
            return;
        }
        if (!feature) {
            document.getElementById("answerStatus").textContent = "후보 확인 필요";
            document.getElementById("returnedCount").textContent = `후보 위치 ${pointFeatures.length}곳`;
            window.QuerySummary.show("후보 확인 필요", result.answer_text || result.summary || `후보 위치 ${pointFeatures.length}곳을 지도에 표시했습니다.`, query);
            details.append(element("strong", `후보 위치 ${pointFeatures.length}곳`), element("div", "지도 마커를 클릭하면 각 후보의 경도/위도와 근거를 확인할 수 있습니다.", "radius-meta"));
            const candidateCollection = { type: "FeatureCollection", features: pointFeatures };
            const layer = L.geoJSON(candidateCollection, {
                pointToLayer: (_feature, latlng) => L.circleMarker(latlng, { radius: 7, color: "#0f766e", fillColor: "#14b8a6", fillOpacity: 0.9, weight: 2 }),
                onEachFeature: (candidateFeature, marker) => {
                    const props = candidateFeature.properties || {};
                    const label = props.name || props.label || "후보 위치";
                    const coordinateText = coordinateTextFromFeature(candidateFeature);
                    const popup = element("div", undefined, "radius-popup");
                    popup.dataset.placeId = props.place_id || "";
                    popup.append(element("strong", label));
                    if (coordinateText) popup.append(element("div", coordinateText, "radius-meta"));
                    if (props.evidence_summary) popup.append(element("div", `근거: ${props.evidence_summary}`, "radius-meta"));
                    if (props.source_url) popup.append(element("div", `출처: ${props.source_url}`, "radius-meta"));
                    marker.bindPopup(popup, { maxWidth: 340 });
                    const entry = element("div", undefined, "evidence-item");
                    entry.dataset.placeId = props.place_id || "";
                    entry.dataset.evidenceId = props.evidence_id || "";
                    entry.append(element("strong", label));
                    if (coordinateText) entry.append(element("div", coordinateText, "radius-meta"));
                    if (props.evidence_summary) entry.append(element("div", `근거: ${props.evidence_summary}`, "radius-meta"));
                    evidence.append(entry);
                },
            }).addTo(options.map);
            options.activeLayers.push(layer);
            if (layer.getBounds().isValid()) options.map.fitBounds(layer.getBounds(), { padding: [24, 24], maxZoom: 16 });
            return;
        }
        const place = { ...feature.properties, place_id: structured.place_id || feature.properties?.place_id, place_version: structured.place_version || feature.properties?.place_version };
        const resolution = structured.location_resolution || {};
        const label = structured.location_text || place.name || "확인된 위치";
        const coordinateText = coordinateTextFromPair(coordinates);
        document.getElementById("answerStatus").textContent = "위치 확인 완료";
        document.getElementById("returnedCount").textContent = "확인된 위치 1곳";
        details.dataset.placeId = place.place_id || "";
        details.dataset.placeVersion = place.place_version || "";
        details.append(element("strong", label), element("div", coordinateText, "radius-meta"));
        window.QuerySummary.show("위치 확인 완료", result.answer_text || result.summary || `${label}: ${coordinateText}`, query);
        const entry = element("div", undefined, "evidence-item");
        entry.dataset.placeId = place.place_id || "";
        entry.dataset.evidenceId = place.evidence_id || "";
        entry.append(element("strong", label), placeProvenance(place, resolution));
        evidence.append(entry);
        const layer = L.geoJSON(collection, {
            pointToLayer: (_feature, latlng) => L.circleMarker(latlng, { radius: 7, color: "#0f766e", fillColor: "#14b8a6", fillOpacity: 0.9, weight: 2 }),
            onEachFeature: (_feature, marker) => {
                const popup = element("div", undefined, "radius-popup");
                popup.dataset.placeId = place.place_id || "";
                popup.append(element("strong", label), element("div", coordinateText, "radius-meta"), placeProvenance(place, resolution));
                marker.bindPopup(popup, { maxWidth: 340 });
            },
        }).addTo(options.map);
        options.activeLayers.push(layer);
        if (layer.getBounds().isValid()) options.map.fitBounds(layer.getBounds(), { padding: [24, 24], maxZoom: 16 });
    }

    function trafficCellColor(value, maxValue) {
        const ratio = maxValue > 0 ? Math.max(0, Math.min(1, value / maxValue)) : 0;
        if (ratio > 0.75) return "#7f1d1d";
        if (ratio > 0.5) return "#dc2626";
        if (ratio > 0.25) return "#f97316";
        return "#facc15";
    }

    function trafficSourceText(row, source) {
        const counts = row?.source_counts || {};
        const value = counts[source] || {};
        return `${source}: ${numberText(Number(value.vessel_count_total || 0))}건`;
    }

    function ensureTrafficLegend(map, activeLayers, maxTraffic) {
        if (!L.control) return;
        const legend = L.control({ position: "bottomright" });
        legend.onAdd = function () {
            const box = L.DomUtil.create("div", "traffic-legend");
            box.innerHTML = `
                <div class="traffic-legend-title">AIS/V-PASS 통항량</div>
                <div><span style="background:#7f1d1d"></span>상위 밀도</div>
                <div><span style="background:#dc2626"></span>높음</div>
                <div><span style="background:#f97316"></span>보통</div>
                <div><span style="background:#facc15"></span>낮음</div>
                <div class="traffic-legend-note">최대 셀 ${numberText(Number(maxTraffic || 0))}건 기준</div>
            `;
            return box;
        };
        legend.addTo(map);
        activeLayers.push({ remove: () => legend.remove() });
    }

    function renderTrafficResult(result, options) {
        const { map, activeLayers, originalQuery } = options;
        const structured = result.structured_result || {};
        const details = document.getElementById("radiusDetails");
        const evidence = document.getElementById("answerEvidence");
        const rows = Array.isArray(structured.features) ? structured.features : [];
        const layers = result.map_layers?.length ? result.map_layers : [{ role: "traffic_volume", inline_geojson: structured.geojson }];
        const total = structured.total_traffic_count ?? 0;
        const maxTraffic = rows.reduce((max, row) => Math.max(max, Number(row.vessel_count_total || 0)), 0);
        const months = structured.effective_temporal_window?.available_months || [];

        function updateTrafficSummary(row) {
            const selected = row && typeof row === "object";
            const source = selected ? row.layer_source || "AIS/V-PASS" : "AIS/V-PASS";
            const month = selected ? row.observed_month || "-" : `${months[0] || "-"}-${months[months.length - 1] || "-"}`;
            const traffic = selected ? Number(row.vessel_count_total || 0) : Number(total || 0);
            const counts = selected ? row.source_counts || {} : {};
            const sourceDetail = selected
                ? `AIS ${numberText(Number(counts.AIS?.vessel_count_total || 0))} / V-PASS ${numberText(Number(counts["V-PASS"]?.vessel_count_total || 0))}`
                : `지도 표시 ${numberText(rows.length)}개 셀`;
            document.getElementById("dangerCount").textContent = `${numberText(traffic)}건`;
            document.getElementById("returnedCount").textContent = selected
                ? `${month} 선택 셀 · ${sourceDetail}`
                : sourceDetail;
            document.getElementById("intentResult").textContent = selected
                ? `${source} ${month}`
                : "AIS/V-PASS 통항량";
            document.getElementById("similarityScore").textContent = "100%";
            document.getElementById("accuracyScore").textContent = "DB";
        }

        document.getElementById("answerStatus").textContent = "통항량 조회 완료";
        updateTrafficSummary(null);
        details.append(element("div", `${months[0] || "-"} - ${months[months.length - 1] || "-"} / AIS,V-PASS`, "radius-meta"));
        renderSurface(details, result, structured);
        ensureTrafficLegend(map, activeLayers, maxTraffic);

        const bounds = L.latLngBounds();
        for (const descriptor of layers) {
            const collection = descriptor.inline_geojson;
            if (!collection || !Array.isArray(collection.features)) continue;
            const leafletLayer = L.geoJSON(collection, {
                interactive: !searchArea,
                style: feature => {
                    const value = Number(feature.properties?.vessel_count_total || 0);
                    const color = trafficCellColor(value, maxTraffic);
                    return { color, fillColor: color, weight: 1, opacity: 0.65, fillOpacity: 0.12 };
                },
                onEachFeature: (feature, layer) => {
                    const row = feature.properties || {};
                    const popup = element("div", undefined, "radius-popup");
                    popup.append(element("strong", "AIS/V-PASS 통항량 셀"));
                    popup.append(element("div", `월: ${row.observed_month || "-"}`));
                    popup.append(element("div", `합계: ${numberText(Number(row.vessel_count_total || 0))}건`));
                    popup.append(element("div", trafficSourceText(row, "AIS")));
                    popup.append(element("div", trafficSourceText(row, "V-PASS")));
                    popup.append(element("div", `주간: ${numberText(Number(row.vessel_count_day || 0))} / 야간: ${numberText(Number(row.vessel_count_night || 0))}`));
                    popup.append(element("div", `grid_id: ${row.grid_id || row.source_id || "-"}`, "radius-meta"));
                    layer.bindPopup(popup, { maxWidth: 320 });
                    if (layer.on) {
                        layer.on("click", () => updateTrafficSummary(row));
                    }
                },
            }).addTo(map);
            if (searchArea && leafletLayer.bringToBack) leafletLayer.bringToBack();
            if (!searchArea && leafletLayer.bringToFront) leafletLayer.bringToFront();
            activeLayers.push(leafletLayer);
            if (leafletLayer.getBounds().isValid()) bounds.extend(leafletLayer.getBounds());
        }
        if (bounds.isValid()) map.fitBounds(bounds, { padding: [24, 24], maxZoom: 12 });

        const table = element("table", undefined, "radius-table");
        table.setAttribute("aria-label", "AIS/V-PASS 통항량 상위 셀");
        const head = table.createTHead().insertRow();
        for (const title of ["Source", "Month", "Traffic"]) head.append(element("th", title));
        const body = table.createTBody();
        for (const row of rows.slice(0, 30)) {
            const tr = body.insertRow();
            tr.insertCell().textContent = row.layer_source || "AIS/V-PASS";
            tr.insertCell().textContent = row.observed_month || "-";
            tr.insertCell().textContent = numberText(Number(row.vessel_count_total || 0));
        }
        details.append(table);

        for (const item of result.evidence_bundle?.spatial_layer_evidence || []) {
            const row = evidenceData(item) || {};
            evidence.append(element("div", item.summary || item.source_ref || row.relation || "AIS/V-PASS traffic layer", "evidence-item"));
        }
        if (!evidence.children.length) evidence.append(element("div", "AIS/V-PASS dynamic traffic layer", "evidence-item"));
        window.QuerySummary.show("AIS/V-PASS 통항량 분석", result.answer_text || result.summary || "", structured.original_query || originalQuery);
    }

    function render(result, options) {
        const { map, activeLayers, originalQuery, submit } = options;
        const structured = result.structured_result || {};
        const radiusAnalysis = isRadiusAnalysis(result);
        const status = result.status || structured.status;
        const needsInput = ["NEEDS_CLARIFICATION", "NEEDS_USER_INPUT"].includes(status)
            || ["NEEDS_CLARIFICATION", "NEEDS_USER_INPUT"].includes(structured.status);
        const details = document.getElementById("radiusDetails");
        reset();
        details.hidden = false;
        if (radiusAnalysis) window.QuerySummary.renderRadius(result, originalQuery);
        else window.QuerySummary.show(needsInput ? "입력 확인 필요" : status === "FAILED" ? "조회 실패" : "조회 차단", result.summary || result.answer_text || "기준 위치를 확인해 주세요.", structured.original_query || originalQuery);
        const evidence = document.getElementById("answerEvidence");
        evidence.replaceChildren();
        document.getElementById("intentResult").textContent = "공간 검색";
        document.getElementById("similarityScore").textContent = "-";
        document.getElementById("accuracyScore").textContent = "-";
        document.getElementById("answerText").textContent = result.answer_text || result.summary || "";

        if (needsInput || !["COMPLETED", "SUCCESS", "SUCCESS_EMPTY"].includes(status)) {
            document.getElementById("answerStatus").textContent = needsInput ? "입력 확인 필요" : status === "FAILED" ? "조회 실패" : "조회 차단";
            document.getElementById("dangerCount").textContent = "-";
            const questions = result.clarification_questions || [];
            if (questions.length) details.append(element("p", questions.join("\n"), "radius-message"));
            if (radiusAnalysis) renderSurface(details, result, structured);
            renderCandidates(result, originalQuery, submit);
            if (needsInput) renderPointForm(result, originalQuery, submit, radiusAnalysis);
            const blockers = structured.blockers || result.orchestrator_v2?.query_execution_context?.blockers || [];
            for (const blocker of blockers) evidence.append(element("div", blocker, "evidence-item"));
            if (!evidence.children.length) evidence.append(element("div", "공간 조회 결과 없음", "evidence-item"));
            return;
        }
        if (!radiusAnalysis) {
            renderPlaceResult(result, options);
            return;
        }
        if (isTrafficAnalysis(result)) {
            renderTrafficResult(result, options);
            return;
        }

        const rows = Array.isArray(structured.features)
            ? structured.features
            : Array.isArray(structured.events) ? structured.events : [];
        const evidenceItems = result.evidence_bundle?.spatial_feature_evidence || [];
        const total = structured.total_count ?? structured.count;
        const returned = structured.returned_count;
        document.getElementById("answerStatus").textContent = total === 0 ? "조회 완료 · 결과 없음" : "조회 완료";
        document.getElementById("dangerCount").textContent = `${numberText(total)}건`;
        document.getElementById("returnedCount").textContent = `표시 ${numberText(returned)}건 / 전체 ${numberText(total)}건`;
        document.getElementById("similarityScore").textContent = "100%";
        document.getElementById("accuracyScore").textContent = total === 0 ? "N/A" : "100%";
        details.dataset.resultId = structured.result_id || "";
        details.dataset.queryExecutionId = structured.query_execution_id || "";
        const referenceLabel = structured.location_text || structured.location_resolution?.label || structured.location_resolution?.base_location || "선택 위치";
        details.append(element("div", `기준점: ${referenceLabel} · 검색 반경 ${numberText(structured.distance_m)} m`, "radius-meta"));
        renderSurface(details, result, structured);
        if (structured.truncated) details.append(element("div", `가까운 순서로 ${numberText(returned)}건 표시`, "radius-meta"));

        const featureLayers = new Map();
        const tableRows = new Map();
        const evidenceRows = new Map();
        const mappedFeatures = [];
        const hazardLayers = [];
        const bounds = L.latLngBounds();
        const layers = result.map_layers?.length ? result.map_layers : [{ role: "matched_features", inline_geojson: structured.geojson }];
        function clearHighlights() {
            for (const node of tableRows.values()) removeClass(node, "radius-selected");
            for (const node of evidenceRows.values()) removeClass(node, "radius-selected");
        }
        function highlightFeature(id) {
            if (!id) return;
            clearHighlights();
            const row = tableRows.get(String(id));
            const evidenceNode = evidenceRows.get(String(id));
            addClass(row, "radius-selected");
            addClass(evidenceNode, "radius-selected");
            if (row?.scrollIntoView) row.scrollIntoView({ block: "nearest" });
            if (evidenceNode?.scrollIntoView) evidenceNode.scrollIntoView({ block: "nearest" });
        }
        for (const descriptor of layers) {
            const collection = descriptor.inline_geojson;
            if (!collection || !Array.isArray(collection.features)) continue;
            const searchArea = (descriptor.role || descriptor.metadata?.role) === "search_area";
            const layerTitle = descriptor.title || (searchArea ? "검색 범위" : "검색된 객체");
            const isSearchAreaFeature = feature => searchArea || feature?.properties?.role === "search_area";
            const hazardPathStyle = feature => {
                if (isSearchAreaFeature(feature)) {
                    return { color: "#0284c7", weight: 1, fillColor: "#38bdf8", fillOpacity: 0.035, opacity: 0.65, dashArray: "6,6" };
                }
                const base = featureStyle(feature.properties || {});
                const scaled = scaleState(map);
                return { color: base.color, fillColor: base.fillColor, weight: scaled.weight, opacity: scaled.opacity, fillOpacity: scaled.fillOpacity };
            };
            if (!searchArea) mappedFeatures.push(...collection.features.filter(feature => !isSearchAreaFeature(feature)));
            const leafletLayer = L.geoJSON(collection, {
                interactive: !searchArea,
                style: hazardPathStyle,
                pointToLayer: (feature, latlng) => symbolMarker(feature, latlng, isSearchAreaFeature(feature)),
                onEachFeature: (feature, layer) => {
                    if (isSearchAreaFeature(feature)) {
                        if (layer.options) layer.options.interactive = false;
                        return;
                        const row = feature.properties || {};
                        const popup = element("div", undefined, "radius-popup");
                        popup.append(element("strong", layerTitle));
                        popup.append(element("div", `기준점 반경 ${numberText(row.distance_m ?? structured.distance_m)} m`));
                        popup.append(element("div", "분석 대상이 아니라 질의 조건을 나타내는 검색 범위입니다.", "radius-meta"));
                        popup.replaceChildren();
                        popup.append(element("strong", "검색 범위 (분석 대상 아님)"));
                        popup.append(element("div", `기준점: ${referenceLabel}`));
                        popup.append(element("div", `반경: ${numberText(row.distance_m ?? structured.distance_m)} m`));
                        popup.append(element("div", "이 폴리곤은 질의 조건을 보여주는 범위 레이어입니다. 위험객체 자체가 아니며, 객체 정보는 내부 심볼/도형을 클릭해 확인합니다.", "radius-meta"));
                        layer.bindPopup(popup, { maxWidth: 300 });
                        return;
                    }
                    const row = feature.properties || {};
                    const id = featureId(row);
                    featureLayers.set(id, layer);
                    const popup = element("div", undefined, "radius-popup");
                    popup.dataset.featureId = id;
                    popup.append(element("strong", rowDisplayName(row)));
                    popup.append(element("div", `기준점에서 ${window.QuerySummary.distanceText(row.distance_m)}`));
                    popup.replaceChildren();
                    appendFeatureDetails(popup, row, referenceLabel);
                    const featureCoordinateText = coordinateTextFromFeature(feature);
                    if (featureCoordinateText) popup.append(element("div", featureCoordinateText, "radius-meta"));
                    popup.append(technicalEvidence(row, row.evidence_id, row.source || row.dataset_id));
                    layer.bindPopup(popup, { maxWidth: 340 });
                    if (layer.on) {
                        layer.on("click", () => {
                            highlightFeature(id);
                            if (layer.openPopup) layer.openPopup();
                        });
                    }
                },
            }).addTo(map);
            if (searchArea && leafletLayer.bringToBack) leafletLayer.bringToBack();
            if (!searchArea && leafletLayer.bringToFront) leafletLayer.bringToFront();
            if (!searchArea && leafletLayer.setStyle) hazardLayers.push([leafletLayer, hazardPathStyle]);
            activeLayers.push(leafletLayer);
            if (leafletLayer.getBounds().isValid()) bounds.extend(leafletLayer.getBounds());
        }
        applyScaleClass(map);
        if (map.off && map.__s101ScaleHandler) map.off("zoomend", map.__s101ScaleHandler);
        map.__s101ScaleHandler = () => {
            applyScaleClass(map);
            for (const [layer, style] of hazardLayers) layer.setStyle(style);
        };
        if (map.on) map.on("zoomend", map.__s101ScaleHandler);
        if (bounds.isValid()) map.fitBounds(bounds, { padding: [24, 24], maxZoom: 16 });

        function focusFeature(id) {
            const layer = featureLayers.get(id);
            if (!layer) return;
            if (layer.getLatLng) map.panTo(layer.getLatLng());
            else if (layer.getBounds) map.fitBounds(layer.getBounds(), { maxZoom: 16 });
            layer.openPopup();
        }

        const table = element("table", undefined, "radius-table");
        table.setAttribute("aria-label", "반환된 공간 객체");
        const head = table.createTHead().insertRow();
        for (const title of ["객체 ID", "종류", "거리 (m)"]) head.append(element("th", title));
        const body = table.createTBody();
        for (const row of rows) {
            const id = featureId(row);
            const tr = body.insertRow();
            tr.dataset.featureId = id;
            tr.dataset.evidenceId = row.evidence_id || "";
            tr.dataset.resultId = row.result_id || "";
            tableRows.set(id, tr);
            const button = element("button", id, "feature-focus");
            button.type = "button";
            button.title = "지도에서 객체 보기";
            button.addEventListener("click", () => {
                highlightFeature(id);
                focusFeature(id);
            });
            tr.insertCell().append(button);
            tr.insertCell().textContent = rowDisplayName(row);
            tr.insertCell().textContent = numberText(row.distance_m);
        }
        details.append(table);
        if (!rows.length) details.append(element("p", total === 0 ? "이 반경에 해당하는 객체가 없습니다." : "이 페이지에 표시할 객체가 없습니다.", "radius-message"));
        const offset = structured.offset || 0;
        const limit = structured.result_limit;
        if (Number.isInteger(limit) && limit > 0 && (total > limit || offset > 0)) {
            const navigation = element("nav", undefined, "radius-pagination");
            navigation.setAttribute("aria-label", "공간 결과 페이지");
            const previous = element("button", "이전 결과");
            const next = element("button", "다음 결과");
            previous.type = next.type = "button";
            previous.disabled = offset === 0;
            next.disabled = offset + returned >= total;
            function showPage(nextOffset) {
                previous.disabled = next.disabled = true;
                const slots = result.orchestrator_v2?.route_plan?.slots || {};
                submit({
                    query: structured.original_query || originalQuery,
                    fresh: true,
                    spatialContext: {
                        place_id: structured.place_id,
                        place_version: structured.place_version,
                        location_resolution: structured.location_resolution,
                        base_location: structured.location_text,
                        geometry: structured.reference_geometry,
                        crs: structured.crs || "EPSG:4326",
                        buffer_distance: structured.distance_m,
                        result_limit: limit,
                        offset: nextOffset,
                        target_features: structured.target_features || slots.target_features || [],
                        exclusions: structured.exclusions || slots.exclusions || [],
                    },
                });
            }
            previous.addEventListener("click", () => showPage(Math.max(0, offset - limit)));
            next.addEventListener("click", () => showPage(offset + limit));
            navigation.append(previous, element("span", `${numberText(returned ? offset + 1 : offset)}-${numberText(offset + returned)} / ${numberText(total)}`), next);
            details.append(navigation);
        }

        for (const item of evidenceItems) {
            const row = evidenceData(item) || {};
            const id = featureId(row);
            const entry = element("details", undefined, "evidence-item");
            entry.dataset.featureId = id;
            entry.dataset.evidenceId = item.evidence_id || row.evidence_id || "";
            entry.dataset.resultId = row.result_id || "";
            evidenceRows.set(id, entry);
            entry.append(element("summary", `${featureDisplayName(row.feature_name)} · ${referenceLabel}에서 ${window.QuerySummary.distanceText(row.distance_m)}`));
            entry.append(element("div", `기준점(${referenceLabel})과 이 객체 사이의 거리가 검색 반경 이내입니다.`, "radius-meta"));
            const attrs = attributeEntries(row.attributes);
            if (attrs.length) {
                const attrDetails = element("details", undefined, "evidence-technical");
                attrDetails.append(element("summary", "Feature 속성"));
                for (const [key, value] of attrs) attrDetails.append(element("div", `${key}: ${compactJson(value)}`));
                entry.append(attrDetails);
            }
            entry.append(technicalEvidence(row, item.evidence_id || row.evidence_id, item.source_ref || row.source || row.dataset_id));
            evidence.append(entry);
        }
        for (const item of result.evidence_bundle?.spatial_layer_evidence || []) {
            const row = evidenceData(item) || {};
            evidence.append(element("div", item.summary || item.source_ref || row.relation || "공간 레이어", "evidence-item"));
        }
        if (!evidence.children.length) evidence.append(element("div", "반환된 객체 근거 0건", "evidence-item"));

        const expected = Array.isArray(structured.feature_ids) ? structured.feature_ids.map(String).sort() : [];
        const surfaces = [rows.map(featureId), mappedFeatures.map(f => featureId(f.properties || {})), evidenceItems.map(item => featureId(evidenceData(item) || {}))];
        const mismatch = expected.length > 0
            && (expected.length !== returned || surfaces.some(ids => ids.length !== returned || JSON.stringify(ids.sort()) !== JSON.stringify(expected)));
        if (mismatch) {
            document.getElementById("answerStatus").textContent = "결과 확인 필요";
            window.QuerySummary.show("결과 확인 필요", "지도·목록·근거의 객체 목록이 일치하지 않아 검색 결과를 확인해야 합니다.", structured.original_query || originalQuery);
            evidence.prepend(element("div", "지도·표·근거의 객체 목록이 일치하지 않습니다.", "radius-warning"));
        }
    }

    window.RadiusResults = { isRadius, render, reset };
})();
