import numpy as np
import json

def manhattan_distance(lat1, lon1, lat2, lon2):
    lat_m = abs(lat1 - lat2) * 111000
    lon_m = abs(lon1 - lon2) * 111000 * np.cos(np.radians((lat1+lat2)/2))
    return lat_m + lon_m

def single_crime_likelihood(cell_lat, cell_lon, crime, buffer_radius=1000, f=1.2, g=1.2, phi=0.5):
    d = manhattan_distance(cell_lat, cell_lon, crime["lat"], crime["lon"])
    if d == 0:
        return 0
    if d > buffer_radius:
        return phi / (d ** f)
    else:
        denominator = (2 * buffer_radius - d) ** g
        if denominator == 0:
            return 0
        return (1 - phi) * (buffer_radius ** (g - f)) / denominator

def bayesian_sequential(city, buffer_radius=1000, f=1.2, g=1.2):
    with open(f"../data/cities/{city}_grid.json", "r", encoding="utf-8") as f_in:
        grid_data = json.load(f_in)
    with open(f"../data/crimes/{city}_crimes.json", "r", encoding="utf-8") as f_in:
        crime_data = json.load(f_in)
    with open(f"../data/distance_matrix/{city}_prior.json", "r", encoding="utf-8") as f_in:
        prior_data = json.load(f_in)
    
    cells = grid_data["cells"]
    crimes = crime_data["crimes"]
    priors = {c["id"]: c["prior"] for c in prior_data["cells"]}
    
    current = [priors[c["id"]] for c in cells]
    
    home = crime_data["actual_offender_home"]
    
    snapshots = []
    
    initial = list(current)
    total = sum(initial)
    initial = [p / total for p in initial]
    snapshots.append({
        "step": 0,
        "num_crimes": 0,
        "probabilities": initial
    })
    
    for i, crime in enumerate(crimes):
        likelihoods = []
        for cell in cells:
            l = single_crime_likelihood(cell["lat"], cell["lon"], crime, buffer_radius, f, g)
            likelihoods.append(l)
        
        new_posterior = [c * l for c, l in zip(current, likelihoods)]
        total = sum(new_posterior)
        if total > 0:
            new_posterior = [p / total for p in new_posterior]
        current = new_posterior
        
        max_p = max(current)
        max_idx = current.index(max_p)
        top_cell = cells[max_idx]
        error_m = manhattan_distance(top_cell["lat"], top_cell["lon"], home["lat"], home["lon"])
        
        home_dist_min = float('inf')
        home_idx = 0
        for j, c in enumerate(cells):
            d = manhattan_distance(c["lat"], c["lon"], home["lat"], home["lon"])
            if d < home_dist_min:
                home_dist_min = d
                home_idx = j
        home_prob = current[home_idx]
        rank = sum(1 for p in current if p > home_prob) + 1
        percentile = rank / len(current) * 100
        
        snapshots.append({
            "step": i + 1,
            "num_crimes": i + 1,
            "probabilities": list(current)
        })
        
        print(f"{city} - {i+1}차 사건 반영: 오차 {error_m:.0f}m, 상위 {percentile:.1f}%")
    
    result = {
        "city": city,
        "rows": grid_data["rows"],
        "cols": grid_data["cols"],
        "bounds": grid_data["bounds"],
        "cells_meta": [{"id": c["id"], "lat": c["lat"], "lon": c["lon"]} for c in cells],
        "snapshots": snapshots
    }
    
    with open(f"../data/distance_matrix/{city}_bayesian.json", "w", encoding="utf-8") as f_out:
        json.dump(result, f_out, ensure_ascii=False)
    
    print(f"  스냅샷 {len(snapshots)}개 저장 완료\n")

if __name__ == "__main__":
    for city in ["hwaseong", "daejeon", "seoul_sw", "jeonju"]:
        bayesian_sequential(city)