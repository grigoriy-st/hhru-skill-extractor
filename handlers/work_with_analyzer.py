import json
import time
import logging
import requests

from collections import defaultdict
from pprint import pprint

from typing import Optional, Dict, Any  # Для аннотаций

from flask import (
    Flask, Blueprint,
    request,
    flash, redirect, render_template, url_for,
    get_flashed_messages, jsonify
)

from data import db_session
from models.users import User

work_with_analyzer_bp = Blueprint('work_with_ analyzer', __name__)

@work_with_analyzer_bp.route('/analyzer', methods=['POST', 'GET'])
def get_analyzer_page():
    """ Отображение страницы с анализатором. """
    if request.method == 'POST':
        ...
    return render_template('analyzer.html')

def load_requirements(vacancy_name):
    """ Выгрузка требований из json-файла. """

    filename = f"data/json-requirements/{vacancy_name}.json"
    with open(filename, 'r', encoding='utf-8') as f:
        requirements = json.load(f)

    keywords_list = []
    for category, keywords in requirements.items():
        for keyword in keywords:
            keywords_list.append((category, keyword.lower()))
    return keywords_list


def fetch_vacancies(vacancy_name, vacancy_count=False) -> list:
    """ Парсинг всех вакансий. """
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


def get_vacancy_details(vacancy_id) -> Optional[Dict[str, Any]]:
    """ Парсинг данных с одной вакансии. """
    url = f'https://api.hh.ru/vacancies/{vacancy_id}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None


def parse_vacancy_details(details) -> str:
    """ Парсинг текста с одной вакансии. """

    text = []
    if 'description' in details:
        text.append(details['description'])
    if 'key_skills' in details:
        skills = [skill['name'] for skill in details['key_skills']]
        text.extend(skills)
    return ' '.join(text).lower()


def count_keywords(text, keywords_list) -> set:
    """ Счётчик требований из вакансии на основе списка ключевых слов. """

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
