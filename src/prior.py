import numpy as np
import json
import osmnx as ox
from scipy.spatial import cKDTree

def compute_prior(city):
    with open(f"../data/cities/{city}_grid.json", "r", encoding="utf-8") as f:
        grid_data = json.load(f)
    
    G = ox.load_graphml(f"../data/environment/{city}_roads.graphml")
    
    road_coords = []
    for node, data in G.nodes(data=True):
        road_coords.append([data["y"], data["x"]])
    road_coords = np.array(road_coords)
    
    print(f"{city}: 도로 노드 {len(road_coords)}개")
    
    tree = cKDTree(road_coords)
    
    cells = grid_data["cells"]
    priors = []
    
    for cell in cells:
        dist_deg, _ = tree.query([cell["lat"], cell["lon"]])
        dist_m = dist_deg * 111000
        
        if dist_m < 200:
            prior = 1.0
        elif dist_m < 500:
            prior = 0.7
        elif dist_m < 1000:
            prior = 0.5
        elif dist_m < 2000:
            prior = 0.3
        else:
            prior = 0.15
        
        priors.append(prior)
    
    total = sum(priors)
    priors = [p / total for p in priors]
    
    result = {
        "city": city,
        "rows": grid_data["rows"],
        "cols": grid_data["cols"],
        "bounds": grid_data["bounds"],
        "cells": [
            {"id": c["id"], "lat": c["lat"], "lon": c["lon"], "prior": p}
            for c, p in zip(cells, priors)
        ]
    }
    
    with open(f"../data/distance_matrix/{city}_prior.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    
    max_p = max(priors)
    min_p = min(priors)
    print(f"  사전확률 저장 완료 (max={max_p:.5f}, min={min_p:.5f})")

if __name__ == "__main__":
    for city in ["hwaseong", "daejeon", "seoul_sw", "jeonju"]:
        compute_prior(city)