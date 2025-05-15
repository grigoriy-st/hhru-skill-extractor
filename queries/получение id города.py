import requests


def get_city_id(city_name):
    url = "https://api.hh.ru/areas"
    response = requests.get(url)
    areas = response.json()
    
    for area in areas:
        for region in area['areas']:
            if city_name.lower() in region['name'].lower():
                print(f"{region['name']}: ID = {region['id']}")
                return region['id']
    
    print(f"Город '{city_name}' не найден")
    return None

city_name = 'Омск'
get_city_id(city_name)