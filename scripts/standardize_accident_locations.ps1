param(
    [string]$InputCsv,
    [string]$OutputDir = "outputs/standardized",
    [string]$InventoryPath = "outputs/inventories/accident_inventory.csv",
    [string]$ReportPath = "outputs/reports/22_accident_geocoding_standardization.md"
)

$ErrorActionPreference = "Stop"

function Convert-DmsToDecimal {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }

    $matches = [regex]::Matches($Value, "-?\d+(?:\.\d+)?")
    if ($matches.Count -eq 0) {
        return $null
    }

    $degrees = [double]$matches[0].Value
    $minutes = if ($matches.Count -gt 1) { [double]$matches[1].Value } else { 0.0 }
    $seconds = if ($matches.Count -gt 2) { [double]$matches[2].Value } else { 0.0 }
    $sign = if ($degrees -lt 0) { -1.0 } else { 1.0 }
    return $sign * ([math]::Abs($degrees) + ($minutes / 60.0) + ($seconds / 3600.0))
}

function Convert-Number {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }
    $parsed = 0.0
    if ([double]::TryParse($Value.Replace(",", ""), [ref]$parsed)) {
        return $parsed
    }
    return $null
}

function New-StableId {
    param([string]$Seed)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Seed)
    $hash = $sha.ComputeHash($bytes)
    $hex = -join ($hash[0..7] | ForEach-Object { $_.ToString("x2") })
    return "accident-event:coastguard-2025-$hex"
}

if ([string]::IsNullOrWhiteSpace($InputCsv)) {
    $InputCsv = $null
    foreach ($candidate in Get-ChildItem -Path "Dataset" -Filter "*.csv") {
        try {
            $sample = Import-Csv -LiteralPath $candidate.FullName | Select-Object -First 1
            if ($null -eq $sample) {
                continue
            }
            $candidateHeaders = @($sample.PSObject.Properties | ForEach-Object { $_.Name })
            if ($candidateHeaders.Count -lt 18) {
                continue
            }
            $latSample = $sample.($candidateHeaders[5])
            $lonSample = $sample.($candidateHeaders[6])
            if ((Convert-DmsToDecimal $latSample) -ne $null -and (Convert-DmsToDecimal $lonSample) -ne $null) {
                $InputCsv = $candidate.FullName
                break
            }
        } catch {
            continue
        }
    }
}

if ([string]::IsNullOrWhiteSpace($InputCsv) -or -not (Test-Path -LiteralPath $InputCsv)) {
    throw "Accident detail CSV was not found. Pass -InputCsv or place it under Dataset."
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $InventoryPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ReportPath) | Out-Null

$rows = Import-Csv -LiteralPath $InputCsv
$headers = @()
if ($rows.Count -gt 0) {
    $headers = @($rows[0].PSObject.Properties | ForEach-Object { $_.Name })
}

function Get-Cell {
    param(
        [object]$Row,
        [int]$Index
    )
    if ($headers.Count -le $Index) {
        return $null
    }
    return $Row.($headers[$Index])
}

$standardRows = New-Object System.Collections.Generic.List[object]
$features = New-Object System.Collections.Generic.List[object]
$missingCoordinates = 0
$outOfRange = 0

for ($i = 0; $i -lt $rows.Count; $i++) {
    $row = $rows[$i]
    $occurredAt = Get-Cell $row 0
    $monthValue = Get-Cell $row 1
    $timeSlotValue = Get-Cell $row 2
    $authority = Get-Cell $row 3
    $seaArea = Get-Cell $row 4
    $sourceLatitude = Get-Cell $row 5
    $sourceLongitude = Get-Cell $row 6
    $weather = Get-Cell $row 7
    $cause = Get-Cell $row 8
    $accidentType = Get-Cell $row 9
    $vesselCount = Get-Cell $row 10
    $peopleCount = Get-Cell $row 11
    $rescued = Get-Cell $row 12
    $injured = Get-Cell $row 13
    $dead = Get-Cell $row 14
    $missing = Get-Cell $row 15
    $vesselType = Get-Cell $row 16
    $tonnage = Get-Cell $row 17

    $latitude = Convert-DmsToDecimal $sourceLatitude
    $longitude = Convert-DmsToDecimal $sourceLongitude
    $hasGeometry = $false
    $geocodeStatus = "GEOCODED_FROM_SOURCE_DMS"

    if ($null -eq $latitude -or $null -eq $longitude) {
        $missingCoordinates += 1
        $geocodeStatus = "MISSING_SOURCE_COORDINATES"
    } elseif ($latitude -lt -90 -or $latitude -gt 90 -or $longitude -lt -180 -or $longitude -gt 180) {
        $outOfRange += 1
        $geocodeStatus = "OUT_OF_RANGE_COORDINATES"
    } else {
        $hasGeometry = $true
    }

    $seed = "{0}|{1}|{2}|{3}|{4}|{5}" -f $occurredAt, $authority, $seaArea, $sourceLatitude, $sourceLongitude, ($i + 1)
    $eventId = New-StableId $seed
    $standard = [ordered]@{
        event_id = $eventId
        source_row_number = $i + 1
        occurred_at = $occurredAt
        month = Convert-Number $monthValue
        time_slot = Convert-Number $timeSlotValue
        authority = $authority
        sea_area = $seaArea
        latitude = $latitude
        longitude = $longitude
        source_latitude_dms = $sourceLatitude
        source_longitude_dms = $sourceLongitude
        geocode_status = $geocodeStatus
        crs = "EPSG:4326"
        weather = $weather
        cause = $cause
        accident_type = $accidentType
        vessel_count = Convert-Number $vesselCount
        people_count = Convert-Number $peopleCount
        rescued = Convert-Number $rescued
        injured = Convert-Number $injured
        dead = Convert-Number $dead
        missing = Convert-Number $missing
        vessel_type = $vesselType
        tonnage = Convert-Number $tonnage
    }
    $standardRows.Add([pscustomobject]$standard) | Out-Null

    if ($hasGeometry) {
        $features.Add([ordered]@{
            type = "Feature"
            id = $eventId
            geometry = [ordered]@{
                type = "Point"
                coordinates = @($longitude, $latitude)
            }
            properties = $standard
        }) | Out-Null
    }
}

$standardCsv = Join-Path $OutputDir "accident_events_coastguard_2025.csv"
$geojsonPath = Join-Path $OutputDir "accident_spatial_layers.geojson"

$standardRows | Export-Csv -LiteralPath $standardCsv -NoTypeInformation -Encoding UTF8

$geojson = [ordered]@{
    type = "FeatureCollection"
    name = "accident_events_coastguard_2025"
    crs = [ordered]@{ type = "name"; properties = [ordered]@{ name = "EPSG:4326" } }
    features = $features
}
$geojson | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $geojsonPath -Encoding UTF8

$geocoded = $features.Count
$total = $rows.Count
$bbox = if ($geocoded -gt 0) {
    $validRows = $standardRows | Where-Object { $_.geocode_status -eq "GEOCODED_FROM_SOURCE_DMS" }
    "{0},{1},{2},{3}" -f (($validRows | Measure-Object -Property longitude -Minimum).Minimum),
        (($validRows | Measure-Object -Property latitude -Minimum).Minimum),
        (($validRows | Measure-Object -Property longitude -Maximum).Maximum),
        (($validRows | Measure-Object -Property latitude -Maximum).Maximum)
} else {
    ""
}

[pscustomobject]@{
    dataset_id = "accident_events_coastguard_2025"
    source_path = $InputCsv
    standardized_csv = $standardCsv
    geojson_path = $geojsonPath
    source_rows = $total
    geocoded_rows = $geocoded
    missing_coordinates = $missingCoordinates
    out_of_range_coordinates = $outOfRange
    geometry_type = "Point"
    crs = "EPSG:4326"
    bbox = $bbox
    geocoding_method = "source_dms_to_decimal_degrees"
    status = if ($geocoded -eq $total) { "GEOCODED_STANDARDIZED" } else { "GEOCODED_WITH_GAPS" }
} | Export-Csv -LiteralPath $InventoryPath -NoTypeInformation -Encoding UTF8

$generatedAt = (Get-Date).ToUniversalTime().ToString("o")
$report = @(
    "# Accident Location Geocoding and Standardization",
    "",
    ("- generated_at: ``{0}``" -f $generatedAt),
    ("- source: ``{0}``" -f $InputCsv),
    ("- standardized_csv: ``{0}``" -f $standardCsv),
    ("- geojson: ``{0}``" -f $geojsonPath),
    ("- inventory: ``{0}``" -f $InventoryPath),
    ("- source_rows: ``{0}``" -f $total),
    ("- geocoded_rows: ``{0}``" -f $geocoded),
    ("- missing_coordinates: ``{0}``" -f $missingCoordinates),
    ("- out_of_range_coordinates: ``{0}``" -f $outOfRange),
    "- crs: ``EPSG:4326``",
    ("- bbox: ``{0}``" -f $bbox),
    "",
    "## Standard Fields",
    "",
    "- ``event_id``, ``occurred_at``, ``authority``, ``sea_area``, ``latitude``, ``longitude``, ``geocode_status``",
    "- ``weather``, ``cause``, ``accident_type``, ``vessel_count``, ``people_count``, ``rescued``, ``injured``, ``dead``, ``missing``, ``vessel_type``, ``tonnage``",
    "",
    "## Geocoding Policy",
    "",
    "Coordinates are converted from source DMS latitude/longitude fields into decimal degrees in EPSG:4326. Rows without parseable coordinates are retained in the standardized CSV and excluded from the GeoJSON point layer."
)
$report -join "`n" | Set-Content -LiteralPath $ReportPath -Encoding UTF8

Write-Output (@{
    source_rows = $total
    geocoded_rows = $geocoded
    missing_coordinates = $missingCoordinates
    out_of_range_coordinates = $outOfRange
    standardized_csv = $standardCsv
    geojson = $geojsonPath
    inventory = $InventoryPath
    report = $ReportPath
} | ConvertTo-Json -Compress)
