# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.

from app.models.database import Base, db_session
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

# Define ComicPages model
class ComicPages(Base):

    __tablename__ = 'comicpages'
    id = Column(Integer, primary_key=True)
    # Identification Data: email & password
    name    = Column(String(128),  nullable=False)
    page    = Column(Integer)
    comicid = Column(Integer)

    # New instance instantiation procedure
    def __init__(self, name, page, comicid):

        self.name = name
        self.page = page
        self.comicid = comicid

    def __repr__(self):
        return '<Comic %r>' % (self.name)
