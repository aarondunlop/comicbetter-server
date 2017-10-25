# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from .main import Base
from app import db
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from flask import request
import json

import bcrypt

class User(Base):
    __tablename__ = 'user'
    username = Column(db.String(64))
    name = Column(db.String(200))
    password = Column(db.String(200))
    number = Column(db.Integer)
    date = Column(db.Integer)
    description = Column(db.String(500))

    def __init__(self, *args, **kwargs):
        self.kwargs=kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return "User(id='%s')" % self.id

    def update_or_create(self):
        user = db.session.query(User).filter_by(username=self.username).first() or False
        if not user:
            user = User()
            db.session.add(user)
        print(self.kwargs)
        for key, value in self.kwargs.items():
            print(key, value)
            newvalue=str(value[0]) if isinstance(value, list) else str(value)
            setattr(user, key, newvalue)
        try:
            db.session.add(user)
            db.session.commit()
            db.session.flush()
        except:
            db.session.rollback()
            raise
        return 'ok'

    def update_password(self):
        user = db.session.query(User).filter_by(username=self.username).first() or False
        if not user:
            user=User()
        user.password=bcrypt.hashpw(self.password.encode('utf8'), bcrypt.gensalt())
        try:
            db.session.add(user)
            db.session.commit()
            db.session.flush()
        except:
            db.session.rollback()
            raise
        return 'ok'

    def verify_password(self):
        user = db.session.query(User).filter_by(name=self.name).first() or False
        hashedPassword = bcrypt.hashpw(self.password.encode('utf8'), bcrypt.gensalt())
        if bcrypt.checkpw(self.password.encode('utf8'), hashedPassword):
            return True
        return False

    def get_user_by_id(self):
        user = db.session.query(User).filter_by(id=self.id).first()
        return user

    def get_user_list(self):
        users=''
        diff=int(self.limit)*int(self.page)
        users = db.session.query(User).limit(self.limit).offset(diff).all()
        return users

    def getserieslist(self):
        users=''
        diff=int(self.limit)*int(self.page)
        users = db.session.query(User).filter(User.series_id == self.series_id).limit(self.limit).offset(diff).all()
        return users
