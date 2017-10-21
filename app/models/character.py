# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db
from .main import Base
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

issuecharacters = Table('issuecharacters', Base.metadata,
    Column('characters_id', Integer, ForeignKey('character.id')),
    Column('issue_id', Integer, ForeignKey('issue.id'))
)

characterteams = Table('characterteams', Base.metadata,
    Column('characters_id', Integer, ForeignKey('character.id')),
    Column('teams_id', Integer, ForeignKey('team.id'))
)

class Character(Base):
    issues = relationship("Issue", secondary=issuecharacters,back_populates="characters")
    teams = relationship("Team", secondary=characterteams,back_populates="characters")
    cvid = Column(db.String(15))
    cvurl = Column(db.String(200))
    name = Column(db.String(200))
    desc = Column(db.String(500))
    #teams = db.ManyToManyField(Team)
    image = Column(db.String(255))

    def __str__(self):
        return self.name
