# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from flask import request

# Define a base model for other database tables to inherit
class Base(db.Model):

    __abstract__  = True
    id      = Column(db.Integer, primary_key=True)
    created = Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated = Column(db.DateTime, default=datetime.utcnow, nullable=False)
