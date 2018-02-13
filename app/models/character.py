# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.

from app.models.database import Base, db_session
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey, String
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
    __tablename__ = 'character'
    id = Column(Integer, primary_key=True)
    issues = relationship("Issue", secondary=issuecharacters,back_populates="characters")
    teams = relationship("Team", secondary=characterteams,back_populates="characters")
    cvid = Column(String(15))
    cvurl = Column(String(200))
    name = Column(String(200))
    desc = Column(String(500))
    #teams = ManyToManyField(Team)
    image = Column(String(255))

    def __str__(self):
        return self.name
