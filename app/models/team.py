# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db
from .main import Base
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from .character import characterteams

issueteams = Table('issueteams', Base.metadata,
    Column('teams_id', Integer, ForeignKey('team.id')),
    Column('issue_id', Integer, ForeignKey('issue.id'))
)

class Team(Base):
    issues = relationship("Issue", secondary=issueteams,back_populates="teams")
    characters = relationship("Character", secondary=characterteams,back_populates="")
    cvid = Column(db.String(15))
    cvurl = Column(db.String(200))
    name = Column(db.String(200))
    desc = Column(db.String(500))
    image = Column(db.String(255))

    def __str__(self):
        return self.name
