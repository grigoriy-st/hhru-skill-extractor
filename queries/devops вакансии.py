import requests

def search_devops_vacancies_omsk():
    base_url = "https://api.hh.ru/vacancies"
    
    params = {
        "text": "DevOps инженер",
        "area": 1249,              
        "per_page": 100,         
        "page": 0,               
        "search_field": "name"   
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"Найдено вакансий: {data['found']}")
        for vacancy in data['items']:
            print(f"\n{vacancy['name']}")
            print(f"Компания: {vacancy['employer']['name']}")
            print(f"Зарплата: {vacancy.get('salary')}")
            print(f"Ссылка: {vacancy['alternate_url']}")
    
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")

search_devops_vacancies_omsk()