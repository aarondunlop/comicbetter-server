# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db
from .main import Base
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

class Publisher(Base):
    cvid = Column(db.String(15))
    cvurl = Column(db.String(200))
    name = Column(db.String(200))
    desc = Column(db.String(500))
    logo = Column(db.String(255))
    series_id = Column(Integer, ForeignKey('series.id'))
    series = relationship("Series")

    def __str__(self):
        return self.name
