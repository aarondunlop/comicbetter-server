# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.

from cbserver.models.database import Base, db_session
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from .character import characterteams

issueteams = Table('issueteams', Base.metadata,
    Column('teams_id', Integer, ForeignKey('team.id')),
    Column('issue_id', Integer, ForeignKey('issue.id'))
)

class Team(Base):
    __tablename__ = 'team'
    id = Column(Integer, primary_key=True)
    issues = relationship("Issue", secondary=issueteams,back_populates="teams")
    characters = relationship("Character", secondary=characterteams,back_populates="")
    cvid = Column(String(15))
    cvurl = Column(String(200))
    name = Column(String(200))
    desc = Column(String(500))
    image = Column(String(255))

    def __str__(self):
        return self.name
