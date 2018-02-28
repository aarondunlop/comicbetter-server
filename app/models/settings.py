# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.

from cbserver.models.database import Base, db_session
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    api_key = Column(String(40))
    library_path = Column(String(128))
    image_path = Column(String(128))
    def __str__(self):
        return "Settings"
