# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from cbserver.models.database import Base, db_session
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

# Define a User model
class LibraryFolders(Base):

    __tablename__ = 'library'
    id = Column(Integer, primary_key=True)
    # Identification Data: email & password
    #folder    = Column(String(128),  nullable=False)

    # New instance instantiation procedure
    def __init__(self, folder):

        self.folder    = folder

    def __repr__(self):
        return '<Folder %r>' % (self.folder)
