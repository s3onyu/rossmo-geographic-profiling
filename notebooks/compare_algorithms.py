import json
import os

city_config = {
    "hwaseong": {"center": [37.175, 127.00], "zoom": 12},
    "daejeon": {"center": [36.34, 127.375], "zoom": 12},
    "seoul_sw": {"center": [37.50, 126.875], "zoom": 12},
    "jeonju": {"center": [35.82, 127.13], "zoom": 12}
}

os.makedirs("../data/maps/compare", exist_ok=True)

for city, config in city_config.items():
    with open(f"../data/distance_matrix/{city}_rossmo.json", "r", encoding="utf-8") as f:
        original = json.load(f)
    with open(f"../data/distance_matrix/{city}_improved.json", "r", encoding="utf-8") as f:
        improved = json.load(f)
    with open(f"../data/distance_matrix/{city}_road_rossmo.json", "r", encoding="utf-8") as f:
        road = json.load(f)
    with open(f"../data/crimes/{city}_crimes.json", "r", encoding="utf-8") as f:
        crime_data = json.load(f)
    
    home = crime_data["actual_offender_home"]
    crimes = crime_data["crimes"]
    
    def make_heat_and_top(data):
        cells = data["cells"]
        probs = [c["probability"] for c in cells]
        max_p = max(probs) if max(probs) > 0 else 1
        heat = [[c["lat"], c["lon"], c["probability"] / max_p] for c in cells if c["probability"] > 0]
        max_idx = probs.index(max(probs))
        top = {"lat": cells[max_idx]["lat"], "lon": cells[max_idx]["lon"]}
        return heat, top
    
    original_heat, original_top = make_heat_and_top(original)
    improved_heat, improved_top = make_heat_and_top(improved)
    road_heat, road_top = make_heat_and_top(road)
    
    versions = {
        "original": {"name": "원본 Rossmo", "heat": original_heat, "top": original_top, "color": "#888"},
        "improved": {"name": "환경가중 (베이지안)", "heat": improved_heat, "top": improved_top, "color": "#f80"},
        "road": {"name": "도로망 거리 (최종)", "heat": road_heat, "top": road_top, "color": "#f00"}
    }
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>{city.upper()} - 알고리즘 비교</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
    <style>
        body {{ margin: 0; font-family: sans-serif; }}
        #map {{ height: 100vh; width: 100%; }}
        #control {{
            position: absolute; top: 10px; left: 50px; z-index: 1000;
            background: white; padding: 15px; border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3); min-width: 320px;
        }}
        h3 {{ margin: 0 0 12px 0; }}
        .btn-group {{ display: flex; gap: 5px; margin-bottom: 10px; }}
        .btn {{
            flex: 1; padding: 8px; border: 2px solid #ddd; background: #f5f5f5;
            cursor: pointer; border-radius: 4px; font-size: 13px;
        }}
        .btn.active {{ background: #333; color: white; border-color: #333; }}
        .info {{ font-size: 13px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee; }}
        .legend {{ font-size: 12px; color: #666; margin-top: 8px; }}
    </style>
</head>
<body>
    <div id="control">
        <h3>{city.upper()} - 알고리즘 비교</h3>
        <div class="btn-group">
            <button class="btn active" data-v="original">원본</button>
            <button class="btn" data-v="improved">환경가중</button>
            <button class="btn" data-v="road">도로망</button>
        </div>
        <div id="versionInfo" class="info"></div>
        <div class="legend">⚫ 실제 거주지 | 🚩 예측 최고 지점 | 🔵 사건</div>
    </div>
    <div id="map"></div>
    <script>
        const versions = {json.dumps(versions, ensure_ascii=False)};
        const crimes = {json.dumps(crimes, ensure_ascii=False)};
        const home = {json.dumps(home, ensure_ascii=False)};
        
        const map = L.map('map').setView({config['center']}, {config['zoom']});
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap'
        }}).addTo(map);
        
        L.marker([home.lat, home.lon], {{
            icon: L.divIcon({{
                html: '<div style="background:black;color:white;padding:4px 8px;border-radius:4px;font-weight:bold;">HOME</div>',
                iconSize: [50, 24]
            }})
        }}).addTo(map).bindPopup('실제 거주지');
        
        const posGroups = {{}};
        crimes.forEach(c => {{
            const key = `${{c.lat.toFixed(4)}},${{c.lon.toFixed(4)}}`;
            if (!posGroups[key]) posGroups[key] = [];
            posGroups[key].push(c);
        }});
        
        for (const key in posGroups) {{
            const group = posGroups[key];
            const n = group.length;
            group.forEach((c, idx) => {{
                let lat = c.lat, lon = c.lon;
                if (n > 1) {{
                    const angle = (2 * Math.PI * idx) / n;
                    const offset = 0.0008;
                    lat = c.lat + offset * Math.cos(angle);
                    lon = c.lon + offset * Math.sin(angle);
                }}
                L.circleMarker([lat, lon], {{
                    radius: 7, color: 'blue', fillColor: 'blue', fillOpacity: 0.8, weight: 2
                }}).addTo(map).bindPopup(`${{c.id}}차 - ${{c.location}}`);
            }});
        }}
        
        let heatLayer = null;
        let topMarker = null;
        
        function haversine(lat1, lon1, lat2, lon2) {{
            const R = 6371000;
            const dLat = (lat2-lat1) * Math.PI/180;
            const dLon = (lon2-lon1) * Math.PI/180;
            const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
            return 2 * R * Math.asin(Math.sqrt(a));
        }}
        
        function render(vkey) {{
            const v = versions[vkey];
            
            if (heatLayer) map.removeLayer(heatLayer);
            heatLayer = L.heatLayer(v.heat, {{radius: 20, blur: 25, minOpacity: 0.4}}).addTo(map);
            
            if (topMarker) map.removeLayer(topMarker);
            topMarker = L.marker([v.top.lat, v.top.lon], {{
                icon: L.divIcon({{
                    html: `<div style="background:${{v.color}};color:white;padding:4px 8px;border-radius:4px;font-weight:bold;">PREDICT</div>`,
                    iconSize: [60, 24]
                }})
            }}).addTo(map).bindPopup(v.name);
            
            const error = haversine(v.top.lat, v.top.lon, home.lat, home.lon);
            document.getElementById('versionInfo').innerHTML = `
                <b>${{v.name}}</b><br/>
                예측: ${{v.top.lat.toFixed(4)}}, ${{v.top.lon.toFixed(4)}}<br/>
                실제와 오차: ${{Math.round(error)}}m
            `;
        }}
        
        document.querySelectorAll('.btn').forEach(btn => {{
            btn.addEventListener('click', (e) => {{
                document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                render(e.target.dataset.v);
            }});
        }});
        
        render('original');
    </script>
</body>
</html>"""
    
    with open(f"../data/maps/compare/{city}.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{city}: ../data/maps/compare/{city}.html")

print("\n완료. 브라우저로 열어서 3가지 버튼 눌러가며 비교하세요.")