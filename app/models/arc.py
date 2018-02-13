# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app.models.database import Base, db_session
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

issuearcs = Table('issuearcs', Base.metadata,
    Column('arcs_id', Integer, ForeignKey('arc.id')),
    Column('issue_id', Integer, ForeignKey('issue.id'))
)

class Arc(Base):
    __tablename__ = 'arc'
    id = Column(Integer, primary_key=True)
    #series = relationship("Issue", secondary=seriesarcs,back_populates="arcs")
    issues = relationship("Issue", secondary=issuearcs,back_populates="arcs")
    cvid = Column(String(15))
    cvurl = Column(String(200))
    name = Column(String(200))
    desc = Column(String(500))
    image = Column(String(255))

    def __str__(self):
        return self.name
