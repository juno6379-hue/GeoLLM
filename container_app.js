// 1. Register Projection EPSG:5179 using Proj4
proj4.defs('EPSG:5179', '+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +units=m +no_defs');
ol.proj.proj4.register(proj4);

// 2. Constants matching system defaults
const tileExtent = [-200000.0, -28024123.62, 31824123.62, 4000000.0];
const viewExtent = [-200000.0, -500000.0, 2500000.0, 3500000.0];
const origin = [-200000.0, 4000000.0];
const tileSize = 256;
const renderPixelRatio = 2;

const resolutions = [
  125094.232896,
  62547.116448,
  31273.558224,
  15636.779112,
  7818.389556,
  3909.194778,
  1954.597389,
  977.2986945,
  488.6493472,
  244.3246736,
  122.1623368,
  61.08116841,
  30.5405842,
  15.2702921,
  7.635146051,
  3.817573025,
  1.908786513,
];

// Slice to 16 zoom levels for cache alignment
const cacheAlignedResolutions = resolutions.slice(0, 16);
const projection = ol.proj.get('EPSG:5179');

// 3. Setup Layers
let wmsSource;
let tileLayer;
let debugGridLayer;
let measureLayer;
let measureSource;
let map;
let drawInteraction;

// Initial parameters
const serverUrlInput = document.getElementById('server-url');
const configuredBackendUrl = window.ENC_VIEWER_CONFIG?.backendUrl;
if (configuredBackendUrl) {
  serverUrlInput.value = configuredBackendUrl;
}
let currentServerUrl = serverUrlInput.value.trim();
let currentStyle = 'simplified';
let currentPalette = 'DAY';
const selectedDisplayModes = new Set(['base', 'standard', 'others']);

function displayModeParameter() {
  return ['base', 'standard', 'others']
    .filter(mode => selectedDisplayModes.has(mode))
    .join(',');
}

function initMap() {
  // Tile Grid matching S-101 server specification
  const tileGrid = new ol.tilegrid.TileGrid({
    extent: tileExtent,
    tileSize,
    resolutions: cacheAlignedResolutions,
    origin,
  });

  // WMS Source
  wmsSource = new ol.source.TileWMS({
    url: currentServerUrl,
    params: {
      LAYERS: 'enc101',
      STYLES: '',
      colorPalette: currentPalette,
      EPSG: 5179,
      simplifiedPoint: currentStyle === 'simplified',
      showTeText: document.getElementById('chk-te-text').checked,
      displayMode: displayModeParameter(),
      logicalWidth: tileSize,
      logicalHeight: tileSize,
      renderPixelRatio,
    },
    projection,
    tileGrid,
    hidpi: true,
    wrapX: false,
    transition: 0,
  });

  // Tile loading events to update status HUD
  wmsSource.on('tileloadstart', () => {
    updateStatusHUD('loading', '타일 불러오는 중...');
  });
  wmsSource.on('tileloadend', () => {
    updateStatusHUD('ok', '연결 및 로드 완료');
  });
  wmsSource.on('tileloaderror', () => {
    updateStatusHUD('error', '타일 로드 오류');
  });

  // Primary Tile Layer
  tileLayer = new ol.layer.Tile({
    source: wmsSource,
    preload: 0,
  });

  // Optional Debug Grid overlay
  debugGridLayer = new ol.layer.Tile({
    source: new ol.source.TileDebug({
      projection,
      tileGrid,
    }),
    visible: document.getElementById('chk-grid').checked,
  });

  // Vector Layer for measurements
  measureSource = new ol.source.Vector();
  measureLayer = new ol.layer.Vector({
    source: measureSource,
    style: new ol.style.Style({
      fill: new ol.style.Fill({
        color: 'rgba(30, 111, 253, 0.15)',
      }),
      stroke: new ol.style.Stroke({
        color: '#1e6ffd',
        width: 3,
        lineDash: [4, 8],
      }),
      image: new ol.style.Circle({
        radius: 6,
        fill: new ol.style.Fill({
          color: '#4d8cff',
        }),
        stroke: new ol.style.Stroke({
          color: '#ffffff',
          width: 2,
        }),
      }),
    }),
  });

  // Assemble Map viewport
  map = new ol.Map({
    target: 'map',
    pixelRatio: renderPixelRatio,
    layers: [tileLayer, debugGridLayer, measureLayer],
    view: new ol.View({
      projection,
      center: [(viewExtent[0] + viewExtent[2]) / 2, (viewExtent[1] + viewExtent[3]) / 2],
      resolutions: cacheAlignedResolutions,
      zoom: 2,
      extent: viewExtent,
      constrainResolution: true,
    }),
  });

  // Track map status events
  map.on('moveend', () => {
    const zoom = map.getView().getZoom();
    document.getElementById('zoom-value').textContent = Number(zoom).toFixed(1);
  });

  // Real-time Coordinate tracking HUD
  map.on('pointermove', (evt) => {
    if (evt.dragging) return;
    
    const coords = evt.coordinate;
    if (coords && coords.length === 2) {
      // EPSG:5179 (E/N) formatting
      document.getElementById('coord-5179').textContent = 
        `${Number(coords[0]).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}, ` +
        `${Number(coords[1]).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

      // Convert EPSG:5179 coordinate to WGS84 (Lon/Lat)
      try {
        const wgs84Coords = ol.proj.transform(coords, 'EPSG:5179', 'EPSG:4326');
        const lon = wgs84Coords[0];
        const lat = wgs84Coords[1];
        document.getElementById('coord-84').textContent = 
          `${Math.abs(lon).toFixed(6)}°${lon >= 0 ? 'E' : 'W'}, ` +
          `${Math.abs(lat).toFixed(6)}°${lat >= 0 ? 'N' : 'S'}`;
      } catch (err) {
        document.getElementById('coord-84').textContent = '좌표 변환 오류';
      }
    }
  });
}

// 4. Update HUD helper
function updateStatusHUD(status, text) {
  const widget = document.getElementById('status-widget');
  const label = document.getElementById('status-text');
  
  widget.className = 'widget status-widget'; // reset classes
  label.textContent = text;
  
  if (status === 'loading') {
    widget.classList.add('status-loading');
  } else if (status === 'error') {
    widget.classList.add('status-error');
  } else {
    widget.classList.add('status-ok');
  }
}

// 5. Setup Action Handlers and UI Events
document.getElementById('btn-reconnect').addEventListener('click', () => {
  const newUrl = document.getElementById('server-url').value.trim();
  if (newUrl) {
    currentServerUrl = newUrl;
    wmsSource.setUrl(newUrl);
    wmsSource.refresh();
    updateStatusHUD('ok', '타일 소스가 업데이트됨');
  }
});

// Symbol Style switching
document.querySelectorAll('[id^="style-"]').forEach((btn) => {
  btn.addEventListener('click', (e) => {
    document.querySelectorAll('[id^="style-"]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentStyle = btn.getAttribute('data-style');
    wmsSource.updateParams({
      simplifiedPoint: currentStyle === 'simplified'
    });
  });
});

// Color Palette switching
document.getElementById('select-palette').addEventListener('change', (e) => {
  currentPalette = e.target.value;
  wmsSource.updateParams({
    colorPalette: currentPalette
  });
});

// Base is locked on; Standard and Others are independent optional additions.
document.querySelectorAll('.mode-btn').forEach((button) => {
  button.addEventListener('click', () => {
    const mode = button.dataset.displayMode;
    if (mode === 'base') return;

    if (selectedDisplayModes.has(mode)) selectedDisplayModes.delete(mode);
    else selectedDisplayModes.add(mode);

    document.querySelectorAll('.mode-btn').forEach((candidate) => {
      const active = selectedDisplayModes.has(candidate.dataset.displayMode);
      candidate.classList.toggle('active', active);
      candidate.setAttribute('aria-pressed', String(active));
    });

    wmsSource.updateParams({ displayMode: displayModeParameter() });
  });
});

// Baseline Grid toggle
document.getElementById('chk-grid').addEventListener('change', (e) => {
  debugGridLayer.setVisible(e.target.checked);
});

document.getElementById('chk-te-text').addEventListener('change', (e) => {
  wmsSource.updateParams({ showTeText: e.target.checked });
});

// 6. Measurement Tools Logic
function setTool(toolName) {
  // Reset previous draw interaction
  if (drawInteraction) {
    map.removeInteraction(drawInteraction);
    drawInteraction = null;
  }

  // Set active class
  document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById(`tool-${toolName === 'None' ? 'pan' : toolName.toLowerCase()}`).classList.add('active');

  if (toolName === 'None') {
    document.getElementById('measure-result').classList.add('hidden');
    return;
  }

  // Prepare draw type
  let drawType = 'LineString';
  if (toolName === 'Area') {
    drawType = 'Polygon';
  }

  drawInteraction = new ol.interaction.Draw({
    source: measureSource,
    type: drawType,
    style: new ol.style.Style({
      fill: new ol.style.Fill({
        color: 'rgba(255, 255, 255, 0.2)',
      }),
      stroke: new ol.style.Stroke({
        color: 'rgba(30, 111, 253, 0.8)',
        lineDash: [4, 8],
        width: 2,
      }),
      image: new ol.style.Circle({
        radius: 5,
        stroke: new ol.style.Stroke({
          color: 'rgba(30, 111, 253, 0.7)',
          width: 2,
        }),
        fill: new ol.style.Fill({
          color: 'rgba(255, 255, 255, 0.8)',
        }),
      }),
    }),
  });

  map.addInteraction(drawInteraction);

  // Show result elements
  document.getElementById('measure-result').classList.remove('hidden');
  document.getElementById('btn-clear-measure').classList.remove('hidden');

  drawInteraction.on('drawstart', (evt) => {
    measureSource.clear(); // Clear previous measurement drawings
    const sketch = evt.feature;
    let listener = sketch.getGeometry().on('change', (evt) => {
      const geom = evt.target;
      let output;
      if (geom instanceof ol.geom.Polygon) {
        // Area measurement in sq kilometers
        const area = geom.getArea();
        if (area > 1000000) {
          output = `${(area / 1000000).toFixed(2)} km²`;
        } else {
          output = `${area.toFixed(0)} m²`;
        }
      } else if (geom instanceof ol.geom.LineString) {
        // Distance measurement in kilometers / nautical miles
        const length = geom.getLength();
        if (length > 1000) {
          const km = length / 1000;
          const nm = km * 0.539957; // Kilometers to Nautical Miles
          output = `${km.toFixed(2)} km (${nm.toFixed(2)} NM)`;
        } else {
          output = `${length.toFixed(1)} m`;
        }
      }
      document.getElementById('measure-value').textContent = output;
    });
  });
}

// Set up UI Event listeners for measurements
document.getElementById('tool-pan').addEventListener('click', () => setTool('None'));
document.getElementById('tool-distance').addEventListener('click', () => setTool('Distance'));
document.getElementById('tool-area').addEventListener('click', () => setTool('Area'));

document.getElementById('btn-clear-measure').addEventListener('click', () => {
  measureSource.clear();
  document.getElementById('measure-value').textContent = '-';
  document.getElementById('btn-clear-measure').classList.add('hidden');
});

// Initialize on page load
window.addEventListener('load', initMap);
