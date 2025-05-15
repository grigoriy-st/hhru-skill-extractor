from flask_restful import Resource, reqparse
from flask import request, jsonify
from collections import defaultdict
from handlers.work_with_analyzer import (
    fetch_vacancies,
    get_vacancy_details,
    parse_vacancy_details,
    count_keywords,
    load_requirements,
    process_results,
    save_results
)

parser = reqparse.RequestParser()
parser.add_argument('vacancy_query', type=str, required=True)
parser.add_argument('vacancy_template', type=str, required=True)
parser.add_argument('quantity', type=int, default=50)

class VacancyList(Resource):
    def get(self):
        """GET /api/vacancies?query=Python&count=10"""
        query = request.args.get('query', '')
        count = min(50, int(request.args.get('count', 50)))
        vacancies = fetch_vacancies(query, count)
        return jsonify(vacancies[:count])

class AnalyzeVacancy(Resource):
    def post(self):
        """POST /api/analyzer"""
        args = parser.parse_args()
        keywords_list = load_requirements(args['vacancy_template'] + '.json')
        vacancies = fetch_vacancies(args['vacancy_query'], args['quantity'])
        
        counts = defaultdict(int)
        for vacancy in vacancies:
            details = get_vacancy_details(vacancy['id'])
            if details:
                text = parse_vacancy_details(details)
                found = count_keywords(text, keywords_list)
                for key in found:
                    counts[key] += 1

        grouped = process_results(counts)
        csv_path = save_results(args['vacancy_query'], grouped, len(vacancies))
        
        return {
            'status': 'success',
            'csv_path': csv_path,
            'results': grouped
        }, 200