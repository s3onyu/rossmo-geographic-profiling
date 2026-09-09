import osmnx as ox

print("대전 도로망 다운로드 중...")

bounds = {
    "min_lat": 36.28,
    "max_lat": 36.40,
    "min_lon": 127.30,
    "max_lon": 127.45
}

bbox = (bounds["min_lon"], bounds["min_lat"], bounds["max_lon"], bounds["max_lat"])

G = ox.graph_from_bbox(bbox, network_type="drive")

print(f"노드 수: {len(G.nodes)}")
print(f"간선 수: {len(G.edges)}")

ox.save_graphml(G, "../data/environment/daejeon_roads.graphml")
print("저장 완료: data/environment/daejeon_roads.graphml")