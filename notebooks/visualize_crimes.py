import folium
import json
import os

city_centers = {
    "hwaseong": [37.175, 127.00],
    "daejeon": [36.34, 127.375],
    "seoul_sw": [37.50, 126.875],
    "jeonju": [35.82, 127.13]
}

os.makedirs("../data/maps", exist_ok=True)

for city, center in city_centers.items():
    with open(f"../data/crimes/{city}_crimes.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    with open(f"../data/cities/{city}_grid.json", "r", encoding="utf-8") as f:
        grid = json.load(f)
    
    m = folium.Map(location=center, zoom_start=12)
    
    bounds = grid["bounds"]
    folium.Rectangle(
        bounds=[[bounds["min_lat"], bounds["min_lon"]], 
                [bounds["max_lat"], bounds["max_lon"]]],
        color="blue",
        fill=False,
        weight=2
    ).add_to(m)
    
    for crime in data["crimes"]:
        folium.CircleMarker(
            location=[crime["lat"], crime["lon"]],
            radius=8,
            color="red",
            fill=True,
            fillColor="red",
            fillOpacity=0.7,
            popup=f"{crime['id']}차 - {crime['location']} ({crime['date']})"
        ).add_to(m)
    
    home = data["actual_offender_home"]
    folium.Marker(
        location=[home["lat"], home["lon"]],
        popup=f"범인 거주지: {home['location']}",
        icon=folium.Icon(color="black", icon="home")
    ).add_to(m)
    
    output_path = f"../data/maps/{city}_map.html"
    m.save(output_path)
    print(f"{city}: {output_path}")

print("\n모든 지도 저장 완료. 브라우저로 열어서 확인하세요.")