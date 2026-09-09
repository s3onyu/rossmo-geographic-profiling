import networkx as nx
import osmnx as ox
import json
import numpy as np
from scipy.spatial import cKDTree

def snap_to_road(lat, lon, tree, node_ids):
    dist, idx = tree.query([lat, lon])
    return node_ids[idx]

def compute_road_distances(city):
    print(f"\n=== {city} 도로망 거리 계산 ===")
    
    with open(f"../data/cities/{city}_grid.json", "r", encoding="utf-8") as f:
        grid_data = json.load(f)
    with open(f"../data/crimes/{city}_crimes.json", "r", encoding="utf-8") as f:
        crime_data = json.load(f)
    
    G = ox.load_graphml(f"../data/environment/{city}_roads.graphml")
    print(f"도로 노드: {len(G.nodes)}, 간선: {len(G.edges)}")
    
    node_ids = list(G.nodes)
    coords = np.array([[G.nodes[n]["y"], G.nodes[n]["x"]] for n in node_ids])
    tree = cKDTree(coords)
    
    G_undirected = G.to_undirected()
    
    cells = grid_data["cells"]
    crimes = crime_data["crimes"]
    
    cell_nodes = []
    for cell in cells:
        node = snap_to_road(cell["lat"], cell["lon"], tree, node_ids)
        cell_nodes.append(node)
    
    print(f"격자 {len(cells)}개 도로 노드 매칭 완료")
    
    distance_matrix = []
    
    for i, crime in enumerate(crimes):
        crime_node = snap_to_road(crime["lat"], crime["lon"], tree, node_ids)
        
        lengths = nx.single_source_dijkstra_path_length(
            G_undirected, crime_node, weight="length"
        )
        
        row = []
        for cell_node in cell_nodes:
            if cell_node in lengths:
                row.append(lengths[cell_node])
            else:
                row.append(-1)
        
        distance_matrix.append(row)
        print(f"  {i+1}/{len(crimes)}차 사건 다익스트라 완료")
    
    result = {
        "city": city,
        "num_crimes": len(crimes),
        "num_cells": len(cells),
        "distances": distance_matrix
    }
    
    with open(f"../data/distance_matrix/{city}_road_dist.json", "w") as f:
        json.dump(result, f)
    
    print(f"저장 완료: {city}_road_dist.json")
    
    unreachable = sum(1 for row in distance_matrix for d in row if d == -1)
    total = len(distance_matrix) * len(distance_matrix[0])
    print(f"연결 안 됨: {unreachable}/{total} ({unreachable/total*100:.1f}%)")

if __name__ == "__main__":
    for city in ["hwaseong", "daejeon", "seoul_sw", "jeonju"]:
        compute_road_distances(city)