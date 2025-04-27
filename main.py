import requests
import json
import csv
import time
from collections import defaultdict


def load_requirements(vacancy_name):
    filename = f"data/json-requirements/{vacancy_name}.json"
    with open(filename, 'r', encoding='utf-8') as f:
        requirements = json.load(f)
    keywords_list = []
    for category, keywords in requirements.items():
        for keyword in keywords:
            keywords_list.append((category, keyword.lower()))
    return keywords_list


def fetch_vacancies(vacancy_name):
    base_url = 'https://api.hh.ru/vacancies'
    headers = {'User-Agent': 'Mozilla/5.0'}
    page = 0
    vacancies = []
    while True:
        params = {
            'text': vacancy_name,
            'area': 113,
            'per_page': 50,
            'page': page
        }
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code != 200:
            break
        data = response.json()
        vacancies.extend(data['items'])
        if page >= data['pages'] - 1:
            break
        page += 1
        time.sleep(0.5)
    return vacancies


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


def main():
    vacancy_name = input("Введите название вакансии: ")
    keywords_list = load_requirements(vacancy_name)
    vacancies = fetch_vacancies(vacancy_name)
    counts = defaultdict(int)
    total = 0

    for vacancy in vacancies:
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