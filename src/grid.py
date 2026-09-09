import numpy as np
import json
import os

def create_grid(min_lat, max_lat, min_lon, max_lon, cell_size_m=500):
    lat_step = cell_size_m / 111000
    lon_step = cell_size_m / (111000 * np.cos(np.radians(min_lat)))
    
    lats = np.arange(min_lat, max_lat, lat_step)
    lons = np.arange(min_lon, max_lon, lon_step)
    
    grid = []
    idx = 0
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            grid.append({
                "id": idx,
                "row": i,
                "col": j,
                "lat": float(lat + lat_step/2),
                "lon": float(lon + lon_step/2)
            })
            idx += 1
    
    return grid, len(lats), len(lons)

city_bounds = {
    "seoul_sw": {"min_lat": 37.45, "max_lat": 37.55, "min_lon": 126.80, "max_lon": 126.95},
    "daejeon":  {"min_lat": 36.28, "max_lat": 36.40, "min_lon": 127.30, "max_lon": 127.45},
    "jeonju":   {"min_lat": 35.78, "max_lat": 35.86, "min_lon": 127.08, "max_lon": 127.18},
    "hwaseong": {"min_lat": 37.10, "max_lat": 37.25, "min_lon": 126.90, "max_lon": 127.10}
}

os.makedirs("../data/cities", exist_ok=True)

for city, bounds in city_bounds.items():
    grid, rows, cols = create_grid(**bounds)
    
    output = {
        "city": city,
        "bounds": bounds,
        "rows": rows,
        "cols": cols,
        "cell_size_m": 500,
        "total_cells": len(grid),
        "cells": grid
    }
    
    with open(f"../data/cities/{city}_grid.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)
    
    print(f"{city}: {rows}x{cols} = {len(grid)}개 격자")

print("\n모든 도시 격자 생성 완료")