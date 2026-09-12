const CITY_CONFIG = {
    hwaseong: { center: [37.175, 127.00], zoom: 12 },
    daejeon: { center: [36.34, 127.375], zoom: 12 },
    seoul_sw: { center: [37.50, 126.875], zoom: 12 },
    jeonju: { center: [35.82, 127.13], zoom: 12 }
};

const MODE_DESC = {
    investigation: "사건 발생지점으로 범인 거주지를 예측합니다.",
    prevention: "범죄자 거주지 + 안전 시설 정보로 위험 지역과 안전 귀갓길을 안내합니다."
};

const FEATURE_STYLE = {
    police: { color: '#e03131', emoji: '🚓', name: '경찰서' },
    convenience: { color: '#228be6', emoji: '🏪', name: '편의점' },
    fuel: { color: '#fd7e14', emoji: '⛽', name: '주유소' },
    lamp: { color: '#ffe066', emoji: '💡', name: '가로등' }
};

let map = null;
let heatLayer = null;
let pointMarkers = [];
let predictMarker = null;
let homeMarker = null;
let safetyMarkers = { convenience: [], police: [], fuel: [], lamp: [] };
let currentCity = "hwaseong";
let currentAlgo = "road";
let currentMode = "investigation";
let points = [];
let cityData = { cells: null, priors: null, roadDists: null, home: null, safety: null, rows: 0, cols: 0 };

let routeStart = null;
let routeEnd = null;
let routeStartMarker = null;
let routeEndMarker = null;
let shortestLine = null;
let safeLine = null;

function smoothPath(coords) {
    if (coords.length < 3) return coords;
    const smoothed = [coords[0]];
    for (let i = 1; i < coords.length - 1; i++) {
        const prev = coords[i-1];
        const cur = coords[i];
        const next = coords[i+1];
        smoothed.push([
            (prev[0] * 0.25 + cur[0] * 0.5 + next[0] * 0.25),
            (prev[1] * 0.25 + cur[1] * 0.5 + next[1] * 0.25)
        ]);
    }
    smoothed.push(coords[coords.length - 1]);
    return smoothed;
}

function getCityBounds(city) {
    const b = {
        hwaseong: { min_lat: 37.10, max_lat: 37.25, min_lon: 126.90, max_lon: 127.10 },
        daejeon:  { min_lat: 36.28, max_lat: 36.40, min_lon: 127.30, max_lon: 127.45 },
        jeonju:   { min_lat: 35.78, max_lat: 35.86, min_lon: 127.08, max_lon: 127.18 },
        seoul_sw: { min_lat: 37.45, max_lat: 37.55, min_lon: 126.80, max_lon: 126.95 }
    };
    return b[city];
}

async function geocodeAddress(query, cityHint) {
    const bounds = getCityBounds(cityHint);
    const viewbox = `${bounds.min_lon},${bounds.max_lat},${bounds.max_lon},${bounds.min_lat}`;
    
    const urls = [
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1&countrycodes=kr&viewbox=${viewbox}&bounded=1`,
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1&countrycodes=kr`,
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query + ' 대한민국')}&format=json&limit=1`
    ];
    
    for (const url of urls) {
        try {
            const res = await fetch(url);
            const data = await res.json();
            if (data.length > 0) {
                return { lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon), name: data[0].display_name };
            }
        } catch (e) {
            console.error("geocoding failed", e);
        }
        await new Promise(r => setTimeout(r, 300));
    }
    return null;
}

async function loadCity(city) {
    const grid = await fetch(`data/${city}_grid.json`).then(r => r.json());
    const crimeData = await fetch(`data/${city}_crimes.json`).then(r => r.json());
    const priorData = await fetch(`data/${city}_prior.json`).then(r => r.json());
    
    let roadData = null;
    try {
        roadData = await fetch(`data/${city}_road_dist.json`).then(r => r.json());
    } catch (e) {}
    
    let safetyData = null;
    try {
        safetyData = await fetch(`data/${city}_safety.json`).then(r => r.json());
    } catch (e) {}
    
    cityData.cells = grid.cells;
    cityData.rows = grid.rows;
    cityData.cols = grid.cols;
    cityData.priors = priorData.cells.map(c => c.prior);
    cityData.roadDists = roadData ? roadData.distances : null;
    cityData.home = crimeData.actual_offender_home;
    cityData.defaultCrimes = crimeData.crimes;
    cityData.safety = safetyData ? safetyData.features : [];
}

function initMap(city) {
    const config = CITY_CONFIG[city];
    
    if (map) {
        map.remove();
    }
    
    map = L.map('map').setView(config.center, config.zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);
    
    map.on('click', (e) => {
        addPoint(e.latlng.lat, e.latlng.lng);
    });
    
    map.on('contextmenu', (e) => {
        e.originalEvent.preventDefault();
        if (currentMode === 'prevention') {
            setRoutePoint(e.latlng.lat, e.latlng.lng);
        }
    });
    
    if (cityData.home && currentCity === 'hwaseong' && currentMode === 'investigation') {
        homeMarker = L.marker([cityData.home.lat, cityData.home.lon], {
            icon: L.divIcon({
                html: '<div style="background:black;color:white;padding:4px 8px;border-radius:4px;font-weight:bold;">HOME</div>',
                iconSize: [50, 24]
            })
        }).addTo(map).bindPopup(`실제 거주지: ${cityData.home.location}`);
    }
    
    safetyMarkers = { convenience: [], police: [], fuel: [], lamp: [] };
    if (currentMode === 'prevention') {
        renderSafetyOverlays();
    }
    
    routeStart = null;
    routeEnd = null;
    routeStartMarker = null;
    routeEndMarker = null;
    shortestLine = null;
    safeLine = null;
}

function renderSafetyOverlays() {
    if (!cityData.safety) return;
    
    ['convenience', 'police', 'fuel', 'lamp'].forEach(type => {
        safetyMarkers[type].forEach(m => map.removeLayer(m));
        safetyMarkers[type] = [];
        
        const checkbox = document.getElementById(`show${type.charAt(0).toUpperCase() + type.slice(1)}`);
        if (!checkbox || !checkbox.checked) return;
        
        const style = FEATURE_STYLE[type];
        const items = cityData.safety.filter(f => f.type === type);
        
        items.forEach(f => {
            const m = L.circleMarker([f.lat, f.lon], {
                radius: type === 'lamp' ? 3 : (type === 'police' ? 7 : 5),
                color: style.color,
                fillColor: style.color,
                fillOpacity: 0.8,
                weight: type === 'police' ? 2 : 1
            }).addTo(map).bindPopup(`${style.emoji} ${style.name}`);
            safetyMarkers[type].push(m);
        });
    });
}

function setRoutePoint(lat, lon) {
    if (!routeStart) {
        routeStart = { lat, lon };
        routeStartMarker = L.marker([lat, lon], {
            icon: L.divIcon({
                html: '<div style="background:#40c057;color:white;padding:6px 10px;border-radius:20px;font-weight:bold;">🏃 출발</div>',
                iconSize: [70, 30]
            })
        }).addTo(map);
        document.getElementById('routeResult').innerHTML = '<span style="color:#40c057;">출발지 지정됨. 도착지를 우클릭하세요.</span>';
    } else if (!routeEnd) {
        routeEnd = { lat, lon };
        routeEndMarker = L.marker([lat, lon], {
            icon: L.divIcon({
                html: '<div style="background:#fa5252;color:white;padding:6px 10px;border-radius:20px;font-weight:bold;">🏠 도착</div>',
                iconSize: [70, 30]
            })
        }).addTo(map);
        computeRoute();
    } else {
        clearRoute();
        setRoutePoint(lat, lon);
    }
}

function clearRoute() {
    if (routeStartMarker) map.removeLayer(routeStartMarker);
    if (routeEndMarker) map.removeLayer(routeEndMarker);
    if (shortestLine) map.removeLayer(shortestLine);
    if (safeLine) map.removeLayer(safeLine);
    routeStart = null;
    routeEnd = null;
    routeStartMarker = null;
    routeEndMarker = null;
    shortestLine = null;
    safeLine = null;
    document.getElementById('routeResult').innerHTML = '';
    document.getElementById('startSearch').value = '';
    document.getElementById('endSearch').value = '';
}

async function searchRouteByAddress() {
    const startQuery = document.getElementById('startSearch').value.trim();
    const endQuery = document.getElementById('endSearch').value.trim();
    
    if (!startQuery || !endQuery) {
        document.getElementById('routeResult').innerHTML = '<span style="color:#fa5252;">출발지와 도착지를 모두 입력하세요.</span>';
        return;
    }
    
    document.getElementById('routeResult').innerHTML = '<span>주소 검색 중...</span>';
    
    clearRoute();
    document.getElementById('startSearch').value = startQuery;
    document.getElementById('endSearch').value = endQuery;
    
    const startRes = await geocodeAddress(startQuery, currentCity);
    if (!startRes) {
        document.getElementById('routeResult').innerHTML = `<span style="color:#fa5252;">출발지 "${startQuery}" 검색 실패</span>`;
        return;
    }
    
    const endRes = await geocodeAddress(endQuery, currentCity);
    if (!endRes) {
        document.getElementById('routeResult').innerHTML = `<span style="color:#fa5252;">도착지 "${endQuery}" 검색 실패</span>`;
        return;
    }
    
    setRoutePoint(startRes.lat, startRes.lon);
    setRoutePoint(endRes.lat, endRes.lon);
    
    map.fitBounds([[startRes.lat, startRes.lon], [endRes.lat, endRes.lon]], { padding: [50, 50] });
}

function computeRoute() {
    if (!routeStart || !routeEnd) return;
    
    document.getElementById('routeResult').innerHTML = '<span>경로 계산 중...</span>';
    
    setTimeout(() => {
        const startIdx = findNearestCell(cityData.cells, routeStart.lat, routeStart.lon);
        const endIdx = findNearestCell(cityData.cells, routeEnd.lat, routeEnd.lon);
        
        const buffer = parseInt(document.getElementById('bufferSlider').value);
        const safetyScores = computeSafetyScores(cityData.cells, points, cityData.safety, buffer);
        
        const shortest = findPath(cityData.cells, cityData.rows, cityData.cols, startIdx, endIdx, safetyScores, 0);
        const safetyWeight = parseFloat(document.getElementById('safetySlider').value);
        const safe = findPath(cityData.cells, cityData.rows, cityData.cols, startIdx, endIdx, safetyScores, safetyWeight);
        
        if (shortestLine) map.removeLayer(shortestLine);
        if (safeLine) map.removeLayer(safeLine);
        
        let shortestCoords = shortest.path.map(i => [cityData.cells[i].lat, cityData.cells[i].lon]);
        shortestCoords = smoothPath(smoothPath(shortestCoords));
        shortestLine = L.polyline(shortestCoords, { color: '#fa5252', weight: 4, opacity: 0.7, dashArray: '8, 8' }).addTo(map);
        
        let safeCoords = safe.path.map(i => [cityData.cells[i].lat, cityData.cells[i].lon]);
        safeCoords = smoothPath(smoothPath(safeCoords));
        safeLine = L.polyline(safeCoords, { color: '#40c057', weight: 5, opacity: 0.9 }).addTo(map);
        
        const extraDist = safe.distance - shortest.distance;
        const extraPercent = shortest.distance > 0 ? Math.round(extraDist / shortest.distance * 100) : 0;
        const walkingSpeed = 1.4;
        const shortestMin = Math.round(shortest.distance / walkingSpeed / 60);
        const safeMin = Math.round(safe.distance / walkingSpeed / 60);
        
        document.getElementById('routeResult').innerHTML = `
            <div style="background:white;padding:10px;border-radius:4px;">
                <div style="color:#fa5252;"><b>🔴 최단</b>: ${Math.round(shortest.distance)}m (${shortestMin}분)</div>
                <div style="color:#40c057;"><b>🟢 안전</b>: ${Math.round(safe.distance)}m (${safeMin}분)</div>
                <div style="margin-top:8px;font-size:12px;color:#666;">
                    +${Math.round(extraDist)}m 우회 (${extraPercent}% 증가)<br/>
                    <b>${safeMin - shortestMin}분 더</b> 걸리지만 위험 지역 피함
                </div>
            </div>
        `;
    }, 50);
}

function addPoint(lat, lon) {
    const id = points.length + 1;
    const label = currentMode === 'investigation' ? `사건 ${id}` : `범죄자 ${id}`;
    points.push({ id, lat, lon, location: label });
    renderPoints();
    recompute();
    if (routeStart && routeEnd) computeRoute();
}

function removePoint(idx) {
    points.splice(idx, 1);
    points.forEach((p, i) => {
        p.id = i + 1;
        p.location = currentMode === 'investigation' ? `사건 ${i+1}` : `범죄자 ${i+1}`;
    });
    renderPoints();
    recompute();
    if (routeStart && routeEnd) computeRoute();
}

function clearPoints() {
    points = [];
    renderPoints();
    recompute();
}

function loadDefaultCrimes() {
    if (currentMode !== 'investigation') return;
    points = cityData.defaultCrimes.map((c, i) => ({
        id: i + 1,
        lat: c.lat,
        lon: c.lon,
        location: c.location || `사건 ${i+1}`
    }));
    renderPoints();
    recompute();
}

function renderPoints() {
    const list = document.getElementById('pointList');
    if (points.length === 0) {
        list.innerHTML = '<div class="empty">아직 지점이 없습니다</div>';
    } else {
        list.innerHTML = points.map((p, i) => `
            <div class="point-item">
                <span>${p.id}. ${p.location}</span>
                <span class="del" onclick="removePoint(${i})">×</span>
            </div>
        `).join('');
    }
    
    pointMarkers.forEach(m => map.removeLayer(m));
    pointMarkers = [];
    
    const posGroups = {};
    points.forEach(p => {
        const key = `${p.lat.toFixed(4)},${p.lon.toFixed(4)}`;
        if (!posGroups[key]) posGroups[key] = [];
        posGroups[key].push(p);
    });
    
    for (const key in posGroups) {
        const group = posGroups[key];
        const n = group.length;
        group.forEach((p, idx) => {
            let lat = p.lat, lon = p.lon;
            if (n > 1) {
                const angle = (2 * Math.PI * idx) / n;
                const offset = 0.0008;
                lat = p.lat + offset * Math.cos(angle);
                lon = p.lon + offset * Math.sin(angle);
            }
            
            let m;
            if (currentMode === 'prevention') {
                m = L.marker([lat, lon], {
                    icon: L.divIcon({
                        html: `<div style="background:purple;color:white;padding:4px 8px;border-radius:4px;font-weight:bold;font-size:12px;">🏠 범죄자${p.id}</div>`,
                        iconSize: [80, 24]
                    })
                }).addTo(map).bindPopup(`${p.id}. ${p.location}`);
            } else {
                m = L.circleMarker([lat, lon], {
                    radius: 8, color: 'blue', fillColor: 'blue', fillOpacity: 0.8, weight: 2
                }).addTo(map).bindPopup(`${p.id}. ${p.location}`);
            }
            pointMarkers.push(m);
        });
    }
}

function getDistanceFunction() {
    if (currentAlgo === "road" && cityData.roadDists && points.length > 0) {
        const pointDists = points.map(p => {
            let minDist = Infinity;
            let closestIdx = 0;
            cityData.defaultCrimes.forEach((dc, di) => {
                const d = manhattanDistance(p.lat, p.lon, dc.lat, dc.lon);
                if (d < minDist) {
                    minDist = d;
                    closestIdx = di;
                }
            });
            
            if (minDist < 100) {
                return cityData.roadDists[closestIdx];
            }
            return null;
        });
        
        return (cellIdx, pointIdx) => {
            if (pointDists[pointIdx] !== null) {
                return pointDists[pointIdx][cellIdx];
            }
            const cell = cityData.cells[cellIdx];
            const point = points[pointIdx];
            return manhattanDistance(cell.lat, cell.lon, point.lat, point.lon);
        };
    }
    
    return (cellIdx, pointIdx) => {
        const cell = cityData.cells[cellIdx];
        const point = points[pointIdx];
        return manhattanDistance(cell.lat, cell.lon, point.lat, point.lon);
    };
}

function recompute() {
    if (heatLayer) {
        map.removeLayer(heatLayer);
        heatLayer = null;
    }
    if (predictMarker) {
        map.removeLayer(predictMarker);
        predictMarker = null;
    }
    
    if (points.length === 0) {
        document.getElementById('resultSection').style.display = 'none';
        return;
    }
    
    const buffer = parseInt(document.getElementById('bufferSlider').value);
    const f = parseFloat(document.getElementById('fSlider').value);
    const g = f;
    
    if (currentMode === 'investigation') {
        recomputeInvestigation(buffer, f, g);
    } else {
        recomputePrevention(buffer, f, g);
    }
}

function recomputeInvestigation(buffer, f, g) {
    const priors = currentAlgo === "original" ? null : cityData.priors;
    const distFn = getDistanceFunction();
    
    const probs = computeRossmo(cityData.cells, points, distFn, buffer, f, g, priors);
    
    const maxP = Math.max(...probs);
    const heatData = [];
    for (let i = 0; i < probs.length; i++) {
        if (probs[i] > 0) {
            heatData.push([cityData.cells[i].lat, cityData.cells[i].lon, probs[i] / maxP]);
        }
    }
    
    heatLayer = L.heatLayer(heatData, { 
        radius: 25, blur: 20, minOpacity: 0.3, max: 0.6,
        gradient: {0.0: 'blue', 0.3: 'cyan', 0.5: 'lime', 0.7: 'yellow', 1.0: 'red'}
    }).addTo(map);
    
    const { cell: topCell } = findMaxCell(probs, cityData.cells);
    predictMarker = L.marker([topCell.lat, topCell.lon], {
        icon: L.divIcon({
            html: '<div style="background:red;color:white;padding:4px 8px;border-radius:4px;font-weight:bold;">PREDICT</div>',
            iconSize: [60, 24]
        })
    }).addTo(map).bindPopup('알고리즘 예측 최고 지점');
    
    document.getElementById('resultSection').style.display = 'block';
    let resultHtml = `
        <strong>예측 지점</strong><br/>
        위도 ${topCell.lat.toFixed(4)}, 경도 ${topCell.lon.toFixed(4)}<br/>
    `;
    if (cityData.home && currentCity === 'hwaseong') {
        const error = haversineDistance(topCell.lat, topCell.lon, cityData.home.lat, cityData.home.lon);
        resultHtml += `<br/><strong>실제와 오차</strong>: ${Math.round(error)}m`;
    }
    document.getElementById('result').innerHTML = resultHtml;
}

function recomputePrevention(buffer, f, g) {
    const risks = computeRisk(cityData.cells, points, buffer, f, g);
    
    const heatData = [];
    for (let i = 0; i < risks.length; i++) {
        if (risks[i] > 0.05) {
            heatData.push([cityData.cells[i].lat, cityData.cells[i].lon, risks[i]]);
        }
    }
    
    heatLayer = L.heatLayer(heatData, { 
        radius: 30, blur: 20, minOpacity: 0.3, max: 1.0,
        gradient: {0.0: 'blue', 0.3: 'green', 0.5: 'yellow', 0.7: 'orange', 1.0: 'red'}
    }).addTo(map);
    
    let highRiskCount = 0;
    let mediumRiskCount = 0;
    for (const r of risks) {
        if (r > 0.7) highRiskCount++;
        else if (r > 0.4) mediumRiskCount++;
    }
    
    document.getElementById('resultSection').style.display = 'block';
    document.getElementById('result').innerHTML = `
        <strong>위험 지역 분석</strong><br/>
        범죄자 수: ${points.length}명<br/>
        고위험 격자 (>70%): <span style="color:red;font-weight:bold;">${highRiskCount}개</span><br/>
        중위험 격자 (40-70%): <span style="color:orange;font-weight:bold;">${mediumRiskCount}개</span><br/>
        <br/>
        <small style="color:#666;">※ 검색창 또는 지도 우클릭으로 안전 귀갓길 지정</small>
    `;
}

function switchMode(mode) {
    currentMode = mode;
    points = [];
    
    document.querySelectorAll('.mode-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.mode === mode);
    });
    
    document.getElementById('modeDesc').textContent = MODE_DESC[mode];
    
    if (mode === 'investigation') {
        document.getElementById('pointListLabel').textContent = '사건 지점 (지도 클릭으로 추가)';
        document.getElementById('loadDefaultBtn').style.display = 'block';
        document.getElementById('algoSection').style.display = 'block';
        document.getElementById('safetySection').style.display = 'none';
        document.getElementById('routeSection').style.display = 'none';
    } else {
        document.getElementById('pointListLabel').textContent = '범죄자 거주지 (지도 좌클릭으로 추가)';
        document.getElementById('loadDefaultBtn').style.display = 'none';
        document.getElementById('algoSection').style.display = 'none';
        document.getElementById('safetySection').style.display = 'block';
        document.getElementById('routeSection').style.display = 'block';
    }
    
    initMap(currentCity);
    renderPoints();
    recompute();
}

async function changeCity(city) {
    currentCity = city;
    points = [];
    await loadCity(city);
    initMap(city);
    renderPoints();
    recompute();
}

document.getElementById('citySelect').addEventListener('change', (e) => {
    changeCity(e.target.value);
});

document.getElementById('algoSelect').addEventListener('change', (e) => {
    currentAlgo = e.target.value;
    recompute();
});

document.getElementById('bufferSlider').addEventListener('input', (e) => {
    document.getElementById('bufferLabel').textContent = e.target.value;
    recompute();
});

document.getElementById('fSlider').addEventListener('input', (e) => {
    document.getElementById('fLabel').textContent = e.target.value;
    recompute();
});

document.getElementById('safetySlider').addEventListener('input', (e) => {
    document.getElementById('safetyLabel').textContent = e.target.value;
    if (routeStart && routeEnd) computeRoute();
});

document.getElementById('clearBtn').addEventListener('click', clearPoints);
document.getElementById('loadDefaultBtn').addEventListener('click', loadDefaultCrimes);
document.getElementById('clearRouteBtn').addEventListener('click', clearRoute);
document.getElementById('searchRouteBtn').addEventListener('click', searchRouteByAddress);

document.getElementById('startSearch').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchRouteByAddress();
});
document.getElementById('endSearch').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchRouteByAddress();
});

document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => switchMode(btn.dataset.mode));
});

['showConvenience', 'showPolice', 'showFuel', 'showLamp'].forEach(id => {
    document.getElementById(id).addEventListener('change', renderSafetyOverlays);
});

(async () => {
    await loadCity(currentCity);
    initMap(currentCity);
})();