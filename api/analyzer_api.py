import json
import pytest
import requests

from pprint import pprint

from flask import Blueprint, Flask, Response, abort, request, jsonify
from data import db_session

from models.users import User

from handlers.work_with_analyzer import work_with_analyzer_bp

BASE_URL = 'http://localhost:8080/'

analyzer_api = Blueprint('analyzer_api', __name__)


@analyzer_api.route('/api/analyzer/<int:q_id>', methods=['GET'])
def get_query_result(q_id):
    """ Получение ответа по id. """
    ...


@analyzer_api.route('/api/analyzer', methods=['POST'])
def send_query():
    """ Запрос анализатору. """
    q_data = request.get_json()
    vacancy_query = q_data['vacancy_query']
    vacancy_template = q_data['vacancy_template'] + '.json'
    quantity = q_data['quantity']

    print(vacancy_query, vacancy_template, quantity)
    response = requests.post(
        f"{BASE_URL}/analyzer",
        json={
            "query": vacancy_query,
            "template": vacancy_template,
            "quantity": quantity
        }
    )

    return 'Query is completed!'
