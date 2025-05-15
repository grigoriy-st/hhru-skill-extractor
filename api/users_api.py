import json
import pytest
import requests

BASE_URL = 'http://localhost:8080/api/users'

from flask import Blueprint, Flask, Response, abort, request, jsonify
from data import db_session

from models.users import User

users_api = Blueprint('users_api', __name__)


@users_api.route('/api/users', methods=['GET'])
def get_all_users():
    """ Выдача всех пользователей. """

    db_ss = db_session.create_session()
    users = db_ss.query(User).all()

    users_list = []
    for user in users:
        users_list.append({
            'id': user.id,
            'name': user.name,
            'surname': user.surname,
            'position': user.position,
            'speciality': user.speciality,
            'email': user.email,
            'city_from': user.city_from
        })
    response_data = json.dumps({
        'status': 'all users have been recieved', 
        'jobs': users_list})
    return Response(response_data, mimetype='application/json')


@users_api.route('/api/users/<int:id>', methods=['GET'])
def get_info_to_one_user_by_id(id):
    """ Прсомотр информации по одному пользователю. """

    db_ss = db_session.create_session()
    user = db_ss.query(User).filter(User.id == id).first()
    db_ss.close()

    if not user:
        return jsonify({'error': 'user was not found'}), 400

    response_of_user = {
        'id': user.id,
        'name': user.name,
        'surname': user.surname,
        'position': user.position,
        'speciality': user.speciality,
        'email': user.email,
        'city_from': user.city_from,
    }
    return jsonify({'user': response_of_user})


@users_api.route('/api/users/add', methods=['POST'])
def add_user():
    """ Добавление пользователя. """
    data = request.get_json()

    necуssary_fields = [
        'id',
        'surname',
        'name',
        'age',
        'address',
        'position',
        'speciality',
        'email',
        'password',
        'city_from',
    ]

    if 'id' not in data.keys() or 'password' not in data.keys():
        return jsonify({'error': 'missing user id or password'}), 400

    for field in data.keys():
        if field not in necуssary_fields:
            return jsonify({'error': 'field not in necessary fields'})


    user_id = data['id']

    db_ss = db_session.create_session()
    user = db_ss.query(User).filter(User.id == user_id).first()

    if user:
        return jsonify({'error': 'user with this id was found'})
    
    new_user = User()

    for field in data.keys():
        if field not in necуssary_fields:
            db_ss.close()
            return jsonify({'error': 'field not in necessary fields'})
        else:
            setattr(new_user, field, data[field])

    try:
        new_user.set_password(data['password'])
        db_ss.add(new_user)
    finally:
        db_ss.commit()
        db_ss.close()

    return jsonify({'user': "is added"})


@users_api.route('/api/users/delete', methods=['DELETE', 'POST'])
def delete_user():
    """ Удаление пользователя. """
    data = request.get_json()

    if 'id' not in data.keys():
        return jsonify({'error': 'missing id'}), 400

    user_id = data['id']
    try:
        db_ss = db_session.create_session()
        user = db_ss.query(User).filter(User.id == user_id).first()

        if not user:
            db_ss.close()
            return jsonify({'error': 'user was not found'}), 400

        db_ss.delete(user)
    finally:
        db_ss.commit()
        db_ss.close()

    return jsonify({'user': 'is deleted'}), 200


@users_api.route('/api/users/edit', methods=['PUT', 'POST'])
def edit_user():
    """ Редактирование пользователя. """

    data = request.get_json()

    necуssary_fields = [
        'id',
        'surname',
        'name',
        'age',
        'position',
        'speciality',
        'email',
        'city_from',
    ]

    if 'id' not in data.keys():
        return jsonify({'error': 'missing user id or password'}), 400

    for field in data.keys():
        if field not in necуssary_fields:
            return jsonify({'error': 'field not in necessary fields'}), 400

    user_id = data['id']

    db_ss = db_session.create_session()
    user = db_ss.query(User).filter(User.id == user_id).first()

    for field in data.keys():
        if field == 'password':
            user.set_password(data['password'])
        else:
            setattr(user, field, data[field])

    db_ss.commit()
    db_ss.close()

    return jsonify({'user': 'updated successfully'})
