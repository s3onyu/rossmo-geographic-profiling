import json
import os

hwaseong_data = {
    "city": "hwaseong",
    "type": "real",
    "description": "이춘재 연쇄살인 사건 (1986-1991) - 리 단위 근사 좌표",
    "crimes": [
        {"id": 1, "lat": 37.2018, "lon": 127.0125, "date": "1986-09-15", "location": "태안읍 안녕리"},
        {"id": 2, "lat": 37.2058, "lon": 127.0357, "date": "1986-10-20", "location": "태안읍 진안리"},
        {"id": 3, "lat": 37.2018, "lon": 127.0125, "date": "1986-12-12", "location": "태안읍 안녕리"},
        {"id": 4, "lat": 37.1602, "lon": 126.9847, "date": "1986-12-14", "location": "정남면 관항리"},
        {"id": 5, "lat": 37.1852, "lon": 127.0248, "date": "1987-01-10", "location": "태안읍 황계리"},
        {"id": 6, "lat": 37.2058, "lon": 127.0357, "date": "1987-05-02", "location": "태안읍 진안리"},
        {"id": 7, "lat": 37.1435, "lon": 126.9312, "date": "1988-09-07", "location": "팔탄면 가재리"},
        {"id": 8, "lat": 37.2058, "lon": 127.0357, "date": "1988-09-16", "location": "태안읍 진안리"},
        {"id": 9, "lat": 37.2015, "lon": 127.0524, "date": "1990-11-15", "location": "태안읍 병점리"},
        {"id": 10, "lat": 37.1897, "lon": 127.0774, "date": "1991-04-03", "location": "동탄면 반송리"}
    ],
    "actual_offender_home": {
        "lat": 37.2075,
        "lon": 127.0389,
        "location": "태안읍 진안1리 (이춘재 본적)"
    }
}

daejeon_data = {
    "city": "daejeon",
    "type": "simulated",
    "description": "대전 시뮬레이션 시나리오 - 갑천 양쪽 가상 사건",
    "crimes": [
        {"id": 1, "lat": 36.3612, "lon": 127.4023, "date": "2024-03-15", "location": "대덕구 오정동"},
        {"id": 2, "lat": 36.3389, "lon": 127.3712, "date": "2024-04-02", "location": "서구 갈마동"},
        {"id": 3, "lat": 36.3701, "lon": 127.3489, "date": "2024-04-20", "location": "유성구 궁동"},
        {"id": 4, "lat": 36.3245, "lon": 127.4102, "date": "2024-05-08", "location": "중구 문화동"},
        {"id": 5, "lat": 36.3512, "lon": 127.3823, "date": "2024-05-25", "location": "서구 둔산동"}
    ],
    "actual_offender_home": {
        "lat": 36.3567,
        "lon": 127.3745,
        "location": "가상 - 서구 만년동"
    }
}

seoul_data = {
    "city": "seoul_sw",
    "type": "simulated",
    "description": "서울 서남부 시뮬레이션 시나리오",
    "crimes": [
        {"id": 1, "lat": 37.4912, "lon": 126.8567, "date": "2024-01-10", "location": "구로구 개봉동"},
        {"id": 2, "lat": 37.4823, "lon": 126.8912, "date": "2024-02-03", "location": "관악구 신림동"},
        {"id": 3, "lat": 37.5089, "lon": 126.8734, "date": "2024-02-25", "location": "양천구 신월동"},
        {"id": 4, "lat": 37.4756, "lon": 126.8845, "date": "2024-03-18", "location": "관악구 봉천동"},
        {"id": 5, "lat": 37.4967, "lon": 126.8623, "date": "2024-04-12", "location": "구로구 오류동"}
    ],
    "actual_offender_home": {
        "lat": 37.4889,
        "lon": 126.8712,
        "location": "가상 - 구로구 항동"
    }
}

jeonju_data = {
    "city": "jeonju",
    "type": "simulated",
    "description": "전주 시뮬레이션 시나리오",
    "crimes": [
        {"id": 1, "lat": 35.8234, "lon": 127.1156, "date": "2024-06-05", "location": "완산구 서신동"},
        {"id": 2, "lat": 35.8156, "lon": 127.1487, "date": "2024-06-22", "location": "완산구 중앙동"},
        {"id": 3, "lat": 35.8412, "lon": 127.1289, "date": "2024-07-10", "location": "덕진구 인후동"},
        {"id": 4, "lat": 35.8098, "lon": 127.1345, "date": "2024-07-28", "location": "완산구 삼천동"}
    ],
    "actual_offender_home": {
        "lat": 35.8267,
        "lon": 127.1298,
        "location": "가상 - 완산구 효자동"
    }
}

os.makedirs("../data/crimes", exist_ok=True)

for city_data in [hwaseong_data, daejeon_data, seoul_data, jeonju_data]:
    city = city_data["city"]
    with open(f"../data/crimes/{city}_crimes.json", "w", encoding="utf-8") as f:
        json.dump(city_data, f, ensure_ascii=False, indent=2)
    print(f"{city}: {len(city_data['crimes'])}건 저장 완료 ({city_data['type']})")

print("\n모든 도시 사건 데이터 저장 완료")