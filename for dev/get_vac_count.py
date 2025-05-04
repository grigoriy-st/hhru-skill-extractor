import requests

query = "Python разработчик"
url = f"https://api.hh.ru/vacancies?text={query}"
response = requests.get(url).json()

total_vacancies = response["found"]
print(f"Всего вакансий по запросу '{query}': {total_vacancies}")