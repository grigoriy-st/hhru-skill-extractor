import datetime
import sqlalchemy
from sqlalchemy.orm import relationship
from data import db_session
from data.db_session import SqlAlchemyBase
from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, 
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    age = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, 
                              index=True, unique=True, nullable=True)
    position = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    speciality = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    
    address = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    # news = relationship("News", back_populates='user')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f'{self.name}, {self.surname}, id={self.id}'

    def to_dict(self, only=None):
        """Преобразует объект в словарь."""
        result = {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'email': self.email,
        }
        if only:
            return {key: result[key] for key in only if key in result}
        return result
