import folium
from folium.plugins import HeatMap
import json

city_centers = {
    "hwaseong": [37.175, 127.00],
    "daejeon": [36.34, 127.375],
    "seoul_sw": [37.50, 126.875],
    "jeonju": [35.82, 127.13]
}

for city, center in city_centers.items():
    with open(f"../data/distance_matrix/{city}_rossmo.json", "r", encoding="utf-8") as f:
        rossmo = json.load(f)
    
    with open(f"../data/crimes/{city}_crimes.json", "r", encoding="utf-8") as f:
        crime_data = json.load(f)
    
    m = folium.Map(location=center, zoom_start=12)
    
    max_prob = max(c["probability"] for c in rossmo["cells"])
    heat_data = [
        [c["lat"], c["lon"], c["probability"] / max_prob]
        for c in rossmo["cells"] if c["probability"] > 0
    ]
    
    HeatMap(heat_data, radius=15, blur=20, min_opacity=0.3).add_to(m)
    
    for crime in crime_data["crimes"]:
        folium.CircleMarker(
            location=[crime["lat"], crime["lon"]],
            radius=6,
            color="blue",
            fill=True,
            fillColor="blue",
            fillOpacity=0.8,
            popup=f"{crime['id']}차 - {crime['location']}"
        ).add_to(m)
    
    home = crime_data["actual_offender_home"]
    folium.Marker(
        location=[home["lat"], home["lon"]],
        popup=f"실제 거주지: {home['location']}",
        icon=folium.Icon(color="black", icon="home")
    ).add_to(m)
    
    sorted_cells = sorted(rossmo["cells"], key=lambda c: c["probability"], reverse=True)
    top_cell = sorted_cells[0]
    folium.Marker(
        location=[top_cell["lat"], top_cell["lon"]],
        popup=f"알고리즘 예측 최고 확률 지점",
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(m)
    
    m.save(f"../data/maps/{city}_rossmo.html")
    print(f"{city}: ../data/maps/{city}_rossmo.html")

print("\n지도 저장 완료. 브라우저로 확인하세요.")