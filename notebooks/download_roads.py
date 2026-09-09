import osmnx as ox
import os

city_bounds = {
    "seoul_sw": {"min_lat": 37.45, "max_lat": 37.55, "min_lon": 126.80, "max_lon": 126.95},
    "daejeon":  {"min_lat": 36.28, "max_lat": 36.40, "min_lon": 127.30, "max_lon": 127.45},
    "jeonju":   {"min_lat": 35.78, "max_lat": 35.86, "min_lon": 127.08, "max_lon": 127.18},
    "hwaseong": {"min_lat": 37.10, "max_lat": 37.25, "min_lon": 126.90, "max_lon": 127.10}
}

os.makedirs("../data/environment", exist_ok=True)

for city, bounds in city_bounds.items():
    path = f"../data/environment/{city}_roads.graphml"
    if os.path.exists(path):
        print(f"{city}: 이미 존재, 건너뜀")
        continue
    
    print(f"{city} 다운로드 중...")
    bbox = (bounds["min_lon"], bounds["min_lat"], bounds["max_lon"], bounds["max_lat"])
    G = ox.graph_from_bbox(bbox, network_type="drive")
    ox.save_graphml(G, path)
    print(f"  노드 {len(G.nodes)}, 간선 {len(G.edges)}")

print("\n모든 도시 도로망 준비 완료")