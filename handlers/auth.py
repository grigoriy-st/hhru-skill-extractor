from flask import Blueprint, render_template, redirect, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from data import db_session
from models.users import User
from forms.LoginForm import LoginForm
from forms.user import RegisterForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/user_list")
        return render_template("login.html", message="Error", form=form)
    return render_template('login.html', title='Authorization', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    print(1)
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', form=form, message="Пароли не совпадают")

        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', form=form, message="Такой пользователь уже есть")

        user = User(
            email=form.email.data,
            surname=form.surname.data,
            name=form.name.data,
            age=form.age.data,
            position=form.position.data,
            speciality=form.speciality.data,
            address=form.address.data,
        )
        user.hashed_password = generate_password_hash(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return render_template('register.html', form=form, message="The user has been added")

    return render_template('register.html', form=form)

