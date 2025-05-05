import logging
import requests

from flask import (
    Flask, Blueprint, 
    request,
    flash, redirect, render_template, url_for,
    get_flashed_messages, jsonify
)
from data import db_session
from models.users import User

API_KEY = 'f3a0fe3a-b07e-4840-a1da-06f18b2ddf13' 

logging.basicConfig(level=logging.INFO)
work_with_users_bp = Blueprint('work_with_users', __name__)


@work_with_users_bp.route('/users_show/<int:user_id>')
def get_user_page_with_map(user_id):
    """Отображение страницы с местоположением пользователя."""
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    db_sess.close()

    if not user:
        flash(f"Нет такого пользователя с id = {user_id}")
        return redirect(url_for('work_with_users.get_user_list'))

    if not user.city_from:
        flash(f"У пользователя {user.name} {user.surname} не указан родной город")
        return redirect(url_for('work_with_users.get_user_list'))

    coords, error = get_map(user.city_from)
    if error:
        flash(f"Не удалось найти координаты для города {user.city_from}")
        return redirect(url_for('work_with_users.get_user_list'))

    return render_template('personal_page.html', user=user)


@work_with_users_bp.route('/user_list')
def get_user_list():
    """Отображение списка пользователей."""

    messages = get_flashed_messages()
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    db_sess.close()
    return render_template('user_list.html', users=users, messages=messages)


def get_map(address):
    """Получение координат по адресу через Яндекс.Геокодер."""

    GEOCODER_API_KEY = '8013b162-6b42-4997-9691-77b7074026e0'
    STATIC_MAP_API_KEY = 'f3a0fe3a-b07e-4840-a1da-06f18b2ddf13'

    WIDTH, HEIGHT = 600, 450

    place_name = address.strip()

    if not place_name:
        return "Error: Вы ничего не ввели.", 400
        exit()

    geocoder_url = (
        f'https://geocode-maps.yandex.ru/1.x/'
        f'?apikey={GEOCODER_API_KEY}&geocode={place_name}&format=json'
    )

    geo_response = requests.get(geocoder_url)

    if geo_response.status_code != 200:
        return "Error: Ошибка геокодирования:", geo_response.status_code
        exit()

    try:
        geo_json = geo_response.json()
        geo_object = geo_json["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        pos = geo_object["Point"]["pos"]
        name = geo_object["name"]
        longitude, latitude = pos.split()  # Получение координат
    except (IndexError, KeyError, ValueError):
        return "Error: Не удалось найти координаты по введённому адресу.", 400
        exit()

    # Запрос для получения карты
    map_url = (
        f'https://static-maps.yandex.ru/1.x/'
        f'?ll={longitude},{latitude}'
        f'&z=6&l=map&size={WIDTH},{HEIGHT}'
        f'&pt={longitude},{latitude},pm2rdm'
        f'&apikey={STATIC_MAP_API_KEY}'
    )

    map_response = requests.get(map_url)

    if map_response.status_code == 200:
        file_name = "static/imgs/map_image.png"

        # Каждый запрос на получение карты
        # обновляет одну и ту же картинку
        with open(file_name, "wb") as f:
            f.write(map_response.content)
        return 1, False
    else:
        return "Error: Ошибка при загрузке карты:", map_response.status_code
