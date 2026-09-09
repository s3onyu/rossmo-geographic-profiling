import numpy as np
import json

def manhattan_distance(lat1, lon1, lat2, lon2):
    lat_m = abs(lat1 - lat2) * 111000
    lon_m = abs(lon1 - lon2) * 111000 * np.cos(np.radians((lat1+lat2)/2))
    return lat_m + lon_m

def rossmo_likelihood(cell_lat, cell_lon, crimes, buffer_radius=1000, f=1.2, g=1.2, phi=0.5):
    total = 0
    for crime in crimes:
        d = manhattan_distance(cell_lat, cell_lon, crime["lat"], crime["lon"])
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

def compute_improved(city, buffer_radius=1000, f=1.2, g=1.2):
    with open(f"../data/cities/{city}_grid.json", "r", encoding="utf-8") as f_in:
        grid_data = json.load(f_in)
    with open(f"../data/crimes/{city}_crimes.json", "r", encoding="utf-8") as f_in:
        crime_data = json.load(f_in)
    with open(f"../data/distance_matrix/{city}_prior.json", "r", encoding="utf-8") as f_in:
        prior_data = json.load(f_in)
    
    cells = grid_data["cells"]
    crimes = crime_data["crimes"]
    priors = {c["id"]: c["prior"] for c in prior_data["cells"]}
    
    posteriors = []
    for cell in cells:
        likelihood = rossmo_likelihood(cell["lat"], cell["lon"], crimes, buffer_radius, f, g)
        prior = priors[cell["id"]]
        posterior = likelihood * prior
        posteriors.append(posterior)
    
    total = sum(posteriors)
    if total > 0:
        posteriors = [p / total for p in posteriors]
    
    home = crime_data["actual_offender_home"]
    home_likelihood = rossmo_likelihood(home["lat"], home["lon"], crimes, buffer_radius, f, g)
    
    home_dist_min = float('inf')
    home_prior = 0
    for c in prior_data["cells"]:
        d = manhattan_distance(c["lat"], c["lon"], home["lat"], home["lon"])
        if d < home_dist_min:
            home_dist_min = d
            home_prior = c["prior"]
    
    home_posterior_raw = home_likelihood * home_prior
    total_raw = sum(rossmo_likelihood(c["lat"], c["lon"], crimes, buffer_radius, f, g) * priors[c["id"]] for c in cells)
    home_posterior = home_posterior_raw / total_raw if total_raw > 0 else 0
    
    rank = sum(1 for p in posteriors if p > home_posterior) + 1
    percentile = rank / len(posteriors) * 100
    
    max_p = max(posteriors)
    max_idx = posteriors.index(max_p)
    top_cell = cells[max_idx]
    error_m = manhattan_distance(top_cell["lat"], top_cell["lon"], home["lat"], home["lon"])
    
    result = {
        "city": city,
        "rows": grid_data["rows"],
        "cols": grid_data["cols"],
        "bounds": grid_data["bounds"],
        "cells": [
            {"id": c["id"], "lat": c["lat"], "lon": c["lon"], "probability": p}
            for c, p in zip(cells, posteriors)
        ]
    }
    
    with open(f"../data/distance_matrix/{city}_improved.json", "w", encoding="utf-8") as f_out:
        json.dump(result, f_out, ensure_ascii=False)
    
    print(f"\n=== {city} 개선판 결과 ===")
    print(f"최고 확률 지점: 위도 {top_cell['lat']:.4f}, 경도 {top_cell['lon']:.4f}")
    print(f"실제 거주지: 위도 {home['lat']:.4f}, 경도 {home['lon']:.4f}")
    print(f"오차: {error_m:.0f}m")
    print(f"실제 거주지가 상위 {percentile:.1f}% 안에 있음")

if __name__ == "__main__":
    for city in ["hwaseong", "daejeon", "seoul_sw", "jeonju"]:
        compute_improved(city)