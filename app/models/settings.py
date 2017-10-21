# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db
from .main import Base
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

class Settings(Base):
    api_key = Column(db.String(40))
    library_path = Column(db.String(128))
    image_path = Column(db.String(128))
    def __str__(self):
        return "Settings"

