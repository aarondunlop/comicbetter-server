# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from .main import Base
from app import db
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

issuearcs = Table('issuearcs', Base.metadata,
    Column('arcs_id', Integer, ForeignKey('arc.id')),
    Column('issue_id', Integer, ForeignKey('issue.id'))
)

class Arc(Base):
    #series = relationship("Issue", secondary=seriesarcs,back_populates="arcs")
    issues = relationship("Issue", secondary=issuearcs,back_populates="arcs")
    cvid = Column(db.String(15))
    cvurl = Column(db.String(200))
    name = Column(db.String(200))
    desc = Column(db.String(500))
    image = Column(db.String(255))

    def __str__(self):
        return self.name
