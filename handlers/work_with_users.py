import logging
import requests

from flask import (
    Flask, Blueprint, 
    request,
    flash, redirect, render_template, url_for,
    get_flashed_messages, jsonify
)
from flask_login import current_user

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


@work_with_users_bp.route('/dashboard')
def get_dashbord_page():
    if not current_user.is_authenticated:
        message = ('Чтобы просматривать историю запросов,<br>'
                  'необходимо войти или зарегистрироваться',
                  'error')
        flash(message)
        return redirect('/login')
    return render_template('dashboard.html')
