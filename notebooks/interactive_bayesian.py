import json
import os

city_config = {
    "hwaseong": {"center": [37.175, 127.00], "zoom": 12},
    "daejeon": {"center": [36.34, 127.375], "zoom": 12},
    "seoul_sw": {"center": [37.50, 126.875], "zoom": 12},
    "jeonju": {"center": [35.82, 127.13], "zoom": 12}
}

os.makedirs("../data/maps/interactive", exist_ok=True)

for city, config in city_config.items():
    with open(f"../data/distance_matrix/{city}_bayesian.json", "r", encoding="utf-8") as f:
        bayesian = json.load(f)
    with open(f"../data/crimes/{city}_crimes.json", "r", encoding="utf-8") as f:
        crime_data = json.load(f)
    
    cells_meta = bayesian["cells_meta"]
    snapshots = bayesian["snapshots"]
    home = crime_data["actual_offender_home"]
    crimes = crime_data["crimes"]
    
    snapshots_js = []
    for snap in snapshots:
        max_p = max(snap["probabilities"]) if max(snap["probabilities"]) > 0 else 1
        heat_data = []
        for i, p in enumerate(snap["probabilities"]):
            if p > 0:
                heat_data.append([cells_meta[i]["lat"], cells_meta[i]["lon"], p / max_p])
        
        max_idx = snap["probabilities"].index(max(snap["probabilities"]))
        top = cells_meta[max_idx]
        
        snapshots_js.append({
            "step": snap["step"],
            "heat": heat_data,
            "top": {"lat": top["lat"], "lon": top["lon"]}
        })
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>{city.upper()} - Bayesian Rossmo</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
    <style>
        body {{ margin: 0; font-family: sans-serif; }}
        #map {{ height: 100vh; width: 100%; }}
        #control {{
            position: absolute; top: 10px; left: 50px; z-index: 1000;
            background: white; padding: 15px; border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3); min-width: 300px;
        }}
        #slider {{ width: 100%; }}
        h3 {{ margin: 0 0 10px 0; }}
        .info {{ font-size: 14px; margin-top: 8px; }}
    </style>
</head>
<body>
    <div id="control">
        <h3>{city.upper()}</h3>
        <div>사건 수: <span id="stepLabel">0</span> / {len(snapshots)-1}</div>
        <input type="range" id="slider" min="0" max="{len(snapshots)-1}" value="0" step="1"/>
        <div class="info">🔴 예측 최고 지점 | ⚫ 실제 거주지 | 🔵 사건</div>
    </div>
    <div id="map"></div>
    <script>
        const snapshots = {json.dumps(snapshots_js, ensure_ascii=False)};
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
        
        let heatLayer = null;
        let crimeMarkers = [];
        let topMarker = null;
        
        function render(step) {{
            const snap = snapshots[step];
            
            if (heatLayer) map.removeLayer(heatLayer);
            heatLayer = L.heatLayer(snap.heat, {{radius: 20, blur: 25, minOpacity: 0.4}}).addTo(map);
            
            crimeMarkers.forEach(m => map.removeLayer(m));
            crimeMarkers = [];
            
            const posGroups = {{}};
            for (let i = 0; i < step; i++) {{
                const c = crimes[i];
                const key = `${{c.lat.toFixed(4)}},${{c.lon.toFixed(4)}}`;
                if (!posGroups[key]) posGroups[key] = [];
                posGroups[key].push(c);
            }}
            
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
                    const m = L.circleMarker([lat, lon], {{
                        radius: 7, color: 'blue', fillColor: 'blue', fillOpacity: 0.8, weight: 2
                    }}).addTo(map).bindPopup(`${{c.id}}차 - ${{c.location}}`);
                    crimeMarkers.push(m);
                }});
            }}
            
            if (topMarker) map.removeLayer(topMarker);
            if (step > 0) {{
                topMarker = L.marker([snap.top.lat, snap.top.lon], {{
                    icon: L.divIcon({{
                        html: '<div style="background:red;color:white;padding:4px 8px;border-radius:4px;font-weight:bold;">PREDICT</div>',
                        iconSize: [60, 24]
                    }})
                }}).addTo(map).bindPopup('알고리즘 예측 최고 지점');
            }}
            
            document.getElementById('stepLabel').textContent = step;
        }}
        
        document.getElementById('slider').addEventListener('input', (e) => {{
            render(parseInt(e.target.value));
        }});
        
        render(0);
    </script>
</body>
</html>"""
    
    with open(f"../data/maps/interactive/{city}.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{city}: ../data/maps/interactive/{city}.html")

print("\n브라우저로 열어서 슬라이더 조작해보세요.")