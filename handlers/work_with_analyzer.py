import os
import csv
import json
import time
# import logging
import sqlite3
import requests

from random  import uniform
from collections import defaultdict
from pprint import pprint

from werkzeug.utils import secure_filename
from typing import Optional, Tuple, Dict, List,  Any  # Для аннотаций

from flask import (
    Blueprint, Response,
    request, session, current_app,
    flash, redirect, render_template, url_for,
    send_from_directory, stream_with_context,
    get_flashed_messages,
)

from data import db_session
from models.users import User

work_with_analyzer_bp = Blueprint('work_with_analyzer', __name__)


from flask import (
    Response, json,
    request, session,
    stream_with_context, redirect, url_for, render_template
)
from collections import defaultdict
from datetime import datetime


@work_with_analyzer_bp.route('/analyzer', methods=['POST', 'GET'])
def get_analyzer_page():
    """Обработчик анализа вакансий с поддержкой прогресс-бара"""

    if request.method == 'POST':
        send_query()

    if request.method == 'GET':
        try:
            job_templates = []

            for f in os.listdir('data/json-requirements'):
                if f.endswith('.json'):
                    job_templates.append(f)

            
            con = sqlite3.connect('db/database.sqlite')
            cursor = con.cursor()
            cursor.execute("SELECT id, title FROM cities")
            regions = cursor.fetchall()
            con.close()
            return render_template('analyzer.html',
                                   job_templates=job_templates,
                                   regions=regions)
        except Exception as e:
            return str(e), 500

    # Обработка AJAX-запроса с прогресс-баром
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        def generate():
            try:
                form_data = request.form.to_dict()
                vacancy_name = form_data.get('vacancy_query', '').strip()
                vacancy_template = form_data.get('vacancy_template', '').strip()
                city_id = form_data.get('city', 0)
                vac_count = min(9999, int(form_data.get('quantity', 50)))

                if not all([vacancy_name, vacancy_template, vac_count > 0]):
                    raise ValueError("Неверные параметры запроса")

                yield ''

                # Этап 1: Загрузка шаблона (10%)
                yield json.dumps({
                    'progress': 10,
                    'message': 'Загрузка шаблона требований...'
                }) + '\n'

                keywords_list = load_requirements(vacancy_template)

                # Этап 2: Поиск вакансий (20%)
                yield json.dumps({
                    'progress': 20,
                    'message': 'Поиск вакансий...'
                }) + '\n'

                vacancies, status = fetch_vacancies(vacancy_name, city_id,  vac_count)
                print(vacancies)
                if not vacancies:
                    raise ValueError("Не найдено вакансий по запросу")

                total_to_process = min(vac_count, len(vacancies))

                # Этап 3: Анализ вакансий (20-90%)
                counts = defaultdict(int)
                for i, vacancy in enumerate(vacancies[:total_to_process]):
                    progress = 20 + int((i / total_to_process) * 60)
                    yield json.dumps({
                        'progress': progress,
                        'message': f'Анализ вакансии {i+1}/{total_to_process}'
                    }) + '\n'

                    details = get_vacancy_details(vacancy['id'])
                    if details:
                        text = parse_vacancy_details(details)
                        found = count_keywords(text, keywords_list)
                        for key in found:
                            counts[key] += 1
                time.sleep(1)
                # Этап 4: Обработка результатов (90-100%)
                yield json.dumps({
                    'progress': 80,
                    'message': 'Обработка результатов...'
                }) + '\n'

                grouped = process_results(counts)

                time.sleep(1)
                # Этап 5: Сохранение (90-100%)
                yield json.dumps({
                    'progress': 90,
                    'message': 'Сохранение результатов...'
                }) + '\n'
                
                csv_path = save_results(vacancy_name, grouped, total_to_process)

                time.sleep(1)
                yield json.dumps({
                    'progress': 100,
                    'message': 'Последние штрихи!',
                }) + '\n'
                
                time.sleep(2)
                yield json.dumps({
                    'progress': 100,
                    'message': 'Анализ завершен!',
                    'redirect': url_for('work_with_analyzer.show_results')
                }) + '\n'

                time.sleep(1)

            except Exception as e:
                yield json.dumps({
                    'error': str(e),
                    'progress': 0,
                    'message': f'Ошибка: {str(e), type(e)}'
                }) + '\n'

        return Response(stream_with_context(generate()), mimetype='text/event-stream')


def send_query():
    """ POST-обработка запроса. """
    try:
        form_data = request.form.to_dict()
        vacancy_name = form_data['vacancy_query']
        vacancy_template = form_data['vacancy_template']
        city_id = from_data['city']
        vac_count = form_data['quantity']

        if vac_count == 'all':  # Процерка на обработку всех вакансий
            vacancy_count = min(2000, get_all_vacancy_count(vacancy_name))
        else:
            vacancy_count = min(2000, int(vac_count))


        keywords_list = load_requirements(vacancy_template)
        vacancies, status = fetch_vacancies(vacancy_name, city_id, vac_count)
        if not status:
            print('Error:')

        vacancies_id_for_print = []

        counts = defaultdict(int)
        for vacancy in vacancies[:vac_count]:
            details = get_vacancy_details(vacancy['id'])
            vacancies_id_for_print.append(vacancy['id'])

            if details:
                text = parse_vacancy_details(details)
                found = count_keywords(text, keywords_list)
                for key in found:
                    counts[key] += 1
        print(vacancies_id_for_print)
        grouped = process_results(counts)
        csv_path = save_results(vacancy_name, grouped,
                                len(vacancies[:vac_count]))

        session['analysis_results'] = {
            'vacancy_name': vacancy_name,
            'csv_path': csv_path,
            'results': grouped,
            'total_vacancies': len(vacancies[:vac_count]),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

        return redirect(url_for('work_with_analyzer.show_results'))

    except Exception as e:
        return str(e), 500


def fetch_vacancies(vacancy_name, area_id=1, vacancy_count=0):
    """ Парсинг всех вакансий. """

    # Огрраничения hh,ru API
    MAX_PER_PAGE = 10
    MAX_PAGE = 199
    REQUEST_DELAY = 10
    MAX_RETRIES = 3
    # TIMEOUT = 10
    MAX_TOTAL_PAGE = 2000

    base_url = 'https://api.hh.ru/vacancies'
    headers = {'User-Agent': 'Mozilla/5.0'}
    page = 0
    retry_count = 0
    processed_count = 0
    vacancies = []
    
    while processed_count < vacancy_count:
        try:
            params = {
                'text': vacancy_name,
                'area': area_id,
                'per_page': 50,
                'page': page,
                'only_with_salary': False  # Для получения большего количества результатов
            }
            response = requests.get(base_url, params=params, headers=headers)

            if response.status_code != 200:
                return None, False

            data = response.json()
            vacancies.extend(data['items'])

            # Прерываем цикл, если достигли нужного количества или конца страниц
            if vacancy_count and len(vacancies) >= vacancy_count:
                vacancies = vacancies[:vacancy_count]
                break

            if page >= data['pages'] - 1:
                break

            delay = REQUEST_DELAY + uniform(8, 10)
            time.sleep(delay)

            page += 1
            retry_count = 0

        except (requests.exceptions.RequestException, ValueError) as e:
            retry_count += 1
            if retry_count >= MAX_RETRIES:
                return None, False

            wait_time = main(30, 2 ** retry_count) + uniform(0, 1)
            time.sleep(wait_time)
            continue

    return vacancies, True


def process_results(counts):
    """Группировка и сортировка результатов"""
    grouped = defaultdict(list)
    for (category, keyword), count in counts.items():
        grouped[category].append((keyword, count))

    for category in grouped:
        grouped[category].sort(key=lambda x: -x[1])

    return grouped


def save_results(vacancy_name, grouped_data, total_vacancies):
    """Сохранение результатов в CSV"""
    os.makedirs('data/csv-responses', exist_ok=True)
    safe_name = ''.join(c if c.isalnum() else '_' for c in vacancy_name)
    filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    csv_path = f"data/csv-responses/{filename}"

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Категория', 'Навык', 'Количество', 'Всего вакансий', total_vacancies])
        for category, keywords in grouped_data.items():
            for keyword, count in keywords:
                writer.writerow([category, keyword, count])

    return csv_path


def load_requirements(vacancy_name):
    """ Выгрузка требований из json-файла. """

    # print('-'*10, vacancy_name)
    # print("This is vac", vacancy_name)
    # print(os.path())
    filename = f"data/json-requirements/{vacancy_name}"
    with open(filename, 'r', encoding='utf-8') as f:
        requirements = json.load(f)

    keywords_list = []
    for category, keywords in requirements.items():
        for keyword in keywords:
            keywords_list.append((category, keyword.lower()))
    return keywords_list




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


@work_with_analyzer_bp.route('/results')
def show_results():
    """Страница с результатами анализа."""
    if 'analysis_results' not in session:
        return redirect(url_for('work_with_analyzer.get_analyzer_page'))

    results = session['analysis_results']
    return render_template('results.html', results=results)


@work_with_analyzer_bp.route('/create_requirements_template',
                             methods=['POST', 'GET'])
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
            skills = []
            for skill in category['skills'].split('\n'):
                if skill.strip():
                    skills.append(skill.strip())

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
        for i in range(100):
            yield f"data: {i}\n\n"
            time.sleep(0.1)

    return Response(generate(), mimetype='text/event-stream')


@work_with_analyzer_bp.route('/download-csv/<filename>')
def download_csv(filename):
    """Скачивание CSV-файла."""

    try:
        # Убедимся, что filename содержит только имя файла
        safe_filename = os.path.basename(filename)
        directory = os.path.join(current_app.root_path, 'data', 'csv-responses')
        return send_from_directory(
            directory=directory,
            path=safe_filename,
            as_attachment=True,
            mimetype='text/csv'
        )
    except FileNotFoundError:
        flash("Файл не найден", "error")
        return redirect(url_for('work_with_analyzer.show_results'))
