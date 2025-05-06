import os
import csv
import json
import time
import logging
import requests

from collections import defaultdict
from pprint import pprint

from werkzeug.utils import secure_filename
from typing import Optional, Dict, Any  # Для аннотаций

from flask import (
    Flask, Blueprint,
    request,
    flash, redirect, render_template, url_for,
    get_flashed_messages, jsonify, Response, session
)

from data import db_session
from models.users import User

work_with_analyzer_bp = Blueprint('work_with_analyzer', __name__)

@work_with_analyzer_bp.route('/analyzer', methods=['POST', 'GET'])
def get_analyzer_page():
    """Отображение страницы с анализатором."""
    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        # Обработка данных формы
        template_data = {
            "vacancy_query": form_data.get('vacancy_query', ''),
            "quantity": int(form_data.get('quantity', 100)),
            "vacancy_template": form_data.get('template', ''),
        }
        
        vacancy_name = template_data['vacancy_query']
        vacancy_template = template_data['vacancy_template']
        vac_count = template_data['quantity']
        
        # Получаем список ключевых слов
        keywords_list = load_requirements(vacancy_template)
        vacancies = fetch_vacancies(vacancy_name, vac_count)
        
        # Анализируем вакансии
        counts = defaultdict(int)
        for vacancy in vacancies[:vac_count]:
            vacancy_id = vacancy['id']
            details = get_vacancy_details(vacancy_id)
            if not details:
                continue
                
            text = parse_vacancy_details(details)
            found = count_keywords(text, keywords_list)
            
            for key in found:
                counts[key] += 1
        
        # Группируем результаты по категориям
        grouped = defaultdict(list)
        for (category, keyword), count in counts.items():
            grouped[category].append((keyword, count))
        
        # Сортируем по убыванию частоты
        for category in grouped:
            grouped[category].sort(key=lambda x: -x[1])
        
        # Сохраняем в CSV
        filename = f'{vacancy_name}_stats.csv'
        os.makedirs('data/csv-responses', exist_ok=True)
        csv_path = os.path.join('data/csv-responses', filename)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for category, keywords in grouped.items():
                writer.writerow([category])
                for keyword, count in keywords:
                    writer.writerow([keyword, count])
        
        # Сохраняем данные в сессии для отображения на странице результатов
        session['analysis_results'] = {
            'vacancy_name': vacancy_name,
            'csv_path': csv_path,
            'results': grouped,
            'total_vacancies': len(vacancies)
        }
        
        # Перенаправляем на страницу с результатами
        return redirect(url_for('work_with_analyzer.show_results'))
    
    # GET запрос - отображаем форму
    job_templates = os.listdir('data/json-requirements')
    return render_template('analyzer.html', job_templates=job_templates)

@work_with_analyzer_bp.route('/results')
def show_results():
    """Страница с результатами анализа."""
    if 'analysis_results' not in session:
        return redirect(url_for('work_with_analyzer.get_analyzer_page'))
    
    results = session['analysis_results']
    return render_template('results.html', results=results)

def load_requirements(vacancy_name):
    """ Выгрузка требований из json-файла. """
    print('-'*10, vacancy_name)
    filename = f"data/json-requirements/{vacancy_name}"
    with open(filename, 'r', encoding='utf-8') as f:
        requirements = json.load(f)

    keywords_list = []
    for category, keywords in requirements.items():
        for keyword in keywords:
            keywords_list.append((category, keyword.lower()))
    return keywords_list


def fetch_vacancies(vacancy_name, vacancy_count=0) -> list:
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

@work_with_analyzer_bp.route('/create_requirements_template', methods=['POST', 'GET'])
def create_requirements_template():
    if request.method == 'POST':

        form_data = request.form.to_dict()
        pprint(form_data)  # Для отладки
        
        # Создаем структуру для JSON
        template_data = {
            "template_name": form_data.get('template_name', ''),
        }
        
        # Обрабатываем категории
        categories = {}
        for key, value in form_data.items():
            if key.startswith('categories['):
                # Извлекаем ID категории и тип поля (name/skills)
                parts = key.split('[')
                category_id = parts[1].split(']')[0]
                field_type = parts[2].split(']')[0]
                
                if category_id not in categories:
                    categories[category_id] = {}
                
                categories[category_id][field_type] = value
        
        # Добавляем категории в template_data
        for category in categories.values():
            skills = [skill.strip() for skill in category['skills'].split('\n') if skill.strip()]
            template_data[category['name']] = skills
        
        # Сохраняем в файл
        templates_dir = 'data/json-requirements'
        os.makedirs(templates_dir, exist_ok=True)
        
        filename = secure_filename(f"{template_data['template_name']}.json")
        filepath = os.path.join(templates_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=4)
            flash('Шаблон успешно сохранен!', 'success')
        except Exception as e:
            flash(f'Ошибка при сохранении: {str(e)}', 'error')

        flash(f'Шаблон {template_data["template_name"]} успешно сохранён!') 
        return redirect(url_for('work_with_analyzer.create_requirements_template'))

    message = get_flashed_messages()
    return render_template('create_requirements_template.html', message=message)

@work_with_analyzer_bp.route('/progress')
def progress():
    def generate():
        # Здесь реализуйте логику отправки событий
        for i in range(100):
            yield f"data: {i}\n\n"
            time.sleep(0.1)
    
    return Response(generate(), mimetype='text/event-stream')