import numpy as np
import json

def manhattan_distance(lat1, lon1, lat2, lon2):
    lat_m = abs(lat1 - lat2) * 111000
    lon_m = abs(lon1 - lon2) * 111000 * np.cos(np.radians((lat1+lat2)/2))
    return lat_m + lon_m

def rossmo_probability(grid_cell, crimes, buffer_radius=1000, f=1.2, g=1.2, phi=0.5):
    total = 0
    for crime in crimes:
        d = manhattan_distance(
            grid_cell["lat"], grid_cell["lon"],
            crime["lat"], crime["lon"]
        )
        
        if d == 0:
            continue
        
        if d > buffer_radius:
            term = phi / (d ** f)
        else:
            denominator = (2 * buffer_radius - d) ** g
            if denominator == 0:
                continue
            term = (1 - phi) * (buffer_radius ** (g - f)) / denominator
        
        total += term
    
    return total

def compute_rossmo_map(city, buffer_radius=1000, f=1.2, g=1.2):
    with open(f"../data/cities/{city}_grid.json", "r", encoding="utf-8") as f_in:
        grid_data = json.load(f_in)
    
    with open(f"../data/crimes/{city}_crimes.json", "r", encoding="utf-8") as f_in:
        crime_data = json.load(f_in)
    
    cells = grid_data["cells"]
    crimes = crime_data["crimes"]
    
    probabilities = []
    for cell in cells:
        p = rossmo_probability(cell, crimes, buffer_radius, f, g)
        probabilities.append(p)
    
    total = sum(probabilities)
    if total > 0:
        probabilities = [p / total for p in probabilities]
    
    result = {
        "city": city,
        "rows": grid_data["rows"],
        "cols": grid_data["cols"],
        "bounds": grid_data["bounds"],
        "parameters": {
            "buffer_radius": buffer_radius,
            "f": f,
            "g": g
        },
        "cells": [
            {"id": c["id"], "lat": c["lat"], "lon": c["lon"], "probability": p}
            for c, p in zip(cells, probabilities)
        ]
    }
    
    with open(f"../data/distance_matrix/{city}_rossmo.json", "w", encoding="utf-8") as f_out:
        json.dump(result, f_out, ensure_ascii=False)
    
    max_p = max(probabilities)
    max_idx = probabilities.index(max_p)
    top_cell = cells[max_idx]
    
    home = crime_data["actual_offender_home"]
    error_m = manhattan_distance(top_cell["lat"], top_cell["lon"], home["lat"], home["lon"])
    
    sorted_probs = sorted(probabilities, reverse=True)
    home_prob = rossmo_probability(
        {"lat": home["lat"], "lon": home["lon"]},
        crimes, buffer_radius, f, g
    )
    home_prob_normalized = home_prob / (sum(probabilities) * total) if total > 0 else 0
    rank = sum(1 for p in probabilities if p > home_prob_normalized) + 1
    percentile = rank / len(probabilities) * 100
    
    print(f"\n=== {city} 결과 ===")
    print(f"격자 수: {len(cells)}")
    print(f"최고 확률 지점: 위도 {top_cell['lat']:.4f}, 경도 {top_cell['lon']:.4f}")
    print(f"실제 거주지: 위도 {home['lat']:.4f}, 경도 {home['lon']:.4f}")
    print(f"오차: {error_m:.0f}m")
    print(f"실제 거주지가 상위 {percentile:.1f}% 안에 있음")

if __name__ == "__main__":
    for city in ["hwaseong", "daejeon", "seoul_sw", "jeonju"]:
        compute_rossmo_map(city)