import folium
from folium.plugins import HeatMap
import json
import os

city_centers = {
    "hwaseong": [37.175, 127.00],
    "daejeon": [36.34, 127.375],
    "seoul_sw": [37.50, 126.875],
    "jeonju": [35.82, 127.13]
}

os.makedirs("../data/maps/bayesian", exist_ok=True)

for city, center in city_centers.items():
    with open(f"../data/distance_matrix/{city}_bayesian.json", "r", encoding="utf-8") as f:
        bayesian = json.load(f)
    with open(f"../data/crimes/{city}_crimes.json", "r", encoding="utf-8") as f:
        crime_data = json.load(f)
    
    cells_meta = bayesian["cells_meta"]
    home = crime_data["actual_offender_home"]
    crimes = crime_data["crimes"]
    
    for snapshot in bayesian["snapshots"]:
        step = snapshot["step"]
        probs = snapshot["probabilities"]
        
        m = folium.Map(location=center, zoom_start=12)
        
        max_p = max(probs) if max(probs) > 0 else 1
        heat_data = [
            [cells_meta[i]["lat"], cells_meta[i]["lon"], probs[i] / max_p]
            for i in range(len(probs)) if probs[i] > 0
        ]
        HeatMap(heat_data, radius=15, blur=20, min_opacity=0.3).add_to(m)
        
        for i, crime in enumerate(crimes[:step]):
            folium.CircleMarker(
                location=[crime["lat"], crime["lon"]],
                radius=6,
                color="blue",
                fill=True,
                fillColor="blue",
                fillOpacity=0.8,
                popup=f"{crime['id']}차"
            ).add_to(m)
        
        folium.Marker(
            location=[home["lat"], home["lon"]],
            popup=f"실제 거주지",
            icon=folium.Icon(color="black", icon="home")
        ).add_to(m)
        
        max_idx = probs.index(max(probs))
        top = cells_meta[max_idx]
        folium.Marker(
            location=[top["lat"], top["lon"]],
            popup=f"예측 최고 지점",
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(m)
        
        title_html = f'''
        <div style="position: fixed; top: 10px; left: 50px; z-index:9999; 
        background: white; padding: 10px; border: 2px solid black; font-size: 16px;">
        {city.upper()} - 사건 {step}개 반영
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        m.save(f"../data/maps/bayesian/{city}_step_{step:02d}.html")
    
    print(f"{city}: {len(bayesian['snapshots'])}개 스냅샷 저장")

print("\n완료. data/maps/bayesian/ 폴더 확인")