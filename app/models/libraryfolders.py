# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db
from .main import Base
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

# Define a User model
class LibraryFolders(Base):

    __tablename__ = 'library'

    # Identification Data: email & password
    #folder    = Column(db.String(128),  nullable=False)

    # New instance instantiation procedure
    def __init__(self, folder):

        self.folder    = folder

    def __repr__(self):
        return '<Folder %r>' % (self.folder)
