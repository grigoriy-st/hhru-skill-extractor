import requests
import json
import csv
import time
from collections import defaultdict
from pprint import pprint


def load_requirements(vacancy_name):
    filename = f"data/json-requirements/{vacancy_name}.json"
    with open(filename, 'r', encoding='utf-8') as f:
        requirements = json.load(f)
    keywords_list = []
    for category, keywords in requirements.items():
        for keyword in keywords:
            keywords_list.append((category, keyword.lower()))
    return keywords_list


def fetch_vacancies(vacancy_name, vacancy_count=False):
    base_url = 'https://api.hh.ru/vacancies'
    headers = {'User-Agent': 'Mozilla/5.0'}
    page = 0
    vacancies = []

    while True:
        params = {
            'text': vacancy_name,
            'per_page': 50,
            'page': page
        }
        response = requests.get(base_url, params=params, headers=headers)

        if response.status_code != 200:
            break

        data = response.json()
        vacancies.extend(data['items'])

        # Прерываем цикл, если достигли нужного количества или конца страниц
        if vacancy_count and len(vacancies) >= vacancy_count:
            vacancies = vacancies[:vacancy_count]  # Отсекаем лишние
            break

        if page >= data['pages'] - 1:
            break

        page += 1
        time.sleep(0.5)

    return vacancies  # Возвращаем результат в любом случае


def get_vacancy_details(vacancy_id):
    url = f'https://api.hh.ru/vacancies/{vacancy_id}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None


def parse_vacancy_details(details):
    text = []
    if 'description' in details:
        text.append(details['description'])
    if 'key_skills' in details:
        skills = [skill['name'] for skill in details['key_skills']]
        text.extend(skills)
    return ' '.join(text).lower()


def count_keywords(text, keywords_list):
    found = set()
    text_lower = text.lower()
    for category, keyword in keywords_list:
        if keyword in text_lower:
            found.add((category, keyword))
    return found


def get_all_vacancy_count(query_string) -> int:
    """ Возращает общее кол-во вакансий по запросу. """
    url = f"https://api.hh.ru/vacancies?text={query_string}"
    response = requests.get(url).json()

    total_vacancies = response["found"]
    return total_vacancies


def main():
    vacancy_name = input("Введите название вакансии: ")
    total_vac_count = get_all_vacancy_count(vacancy_name)

    print(
        f'Общее количество вакансий по запросу {vacancy_name}: ' +
        f'{total_vac_count}'
    )
    vac_count = input("Сколько вакансий вы хотите обработать?[all]: ")
    vac_count = False if vac_count.isalpha() else int(vac_count)

    keywords_list = load_requirements(vacancy_name)
    vacancies = fetch_vacancies(vacancy_name, vac_count)
    counts = defaultdict(int)
    total = 0

    # pprint(vacancies)
    for vacancy in vacancies[:vac_count - 1]:
        vacancy_id = vacancy['id']
        details = get_vacancy_details(vacancy_id)
        if not details:
            continue
        text = parse_vacancy_details(details)
        found = count_keywords(text, keywords_list)
        for key in found:
            counts[key] += 1
        total += 1
        print(f"Обработано вакансий: {total}", end='\r')
        time.sleep(0.1)

    grouped = defaultdict(list)
    for (category, keyword), count in counts.items():
        grouped[category].append((keyword, count))

    for category in grouped:
        grouped[category].sort(key=lambda x: -x[1])

    with open(f'data/csv-responces/{vacancy_name}_stats.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for category, keywords in grouped.items():
            writer.writerow([category])
            for keyword, count in keywords:
                writer.writerow([keyword, count])

    print(f"\nРезультаты сохранены в data/csv-responces/{vacancy_name}_stats.csv")


if __name__ == "__main__":
    main()