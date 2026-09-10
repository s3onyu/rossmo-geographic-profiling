import osmnx as ox
import json
import os

city_bounds = {
    "hwaseong": {"min_lat": 37.10, "max_lat": 37.25, "min_lon": 126.90, "max_lon": 127.10},
    "daejeon":  {"min_lat": 36.28, "max_lat": 36.40, "min_lon": 127.30, "max_lon": 127.45},
    "jeonju":   {"min_lat": 35.78, "max_lat": 35.86, "min_lon": 127.08, "max_lon": 127.18},
    "seoul_sw": {"min_lat": 37.45, "max_lat": 37.55, "min_lon": 126.80, "max_lon": 126.95}
}

os.makedirs("../data/safety", exist_ok=True)

for city, bounds in city_bounds.items():
    print(f"\n=== {city} ===")
    bbox = (bounds["min_lon"], bounds["min_lat"], bounds["max_lon"], bounds["max_lat"])
    
    tags = {
        "highway": "street_lamp",
        "amenity": ["police", "fuel"],
        "shop": "convenience"
    }
    
    try:
        features = ox.features_from_bbox(bbox, tags=tags)
        print(f"총 {len(features)} 개 시설")
        
        safety_data = {"city": city, "features": []}
        
        for idx, row in features.iterrows():
            geom = row.geometry
            if geom.geom_type == "Point":
                lat, lon = geom.y, geom.x
            else:
                lat, lon = geom.centroid.y, geom.centroid.x
            
            ftype = "unknown"
            if row.get("highway") == "street_lamp":
                ftype = "lamp"
            elif row.get("amenity") == "police":
                ftype = "police"
            elif row.get("amenity") == "fuel":
                ftype = "fuel"
            elif row.get("shop") == "convenience":
                ftype = "convenience"
            
            safety_data["features"].append({
                "type": ftype,
                "lat": float(lat),
                "lon": float(lon)
            })
        
        counts = {}
        for f in safety_data["features"]:
            counts[f["type"]] = counts.get(f["type"], 0) + 1
        print(f"내역: {counts}")
        
        with open(f"../data/safety/{city}_safety.json", "w", encoding="utf-8") as f:
            json.dump(safety_data, f, ensure_ascii=False)
        print(f"저장 완료")
        
    except Exception as e:
        print(f"에러: {e}")