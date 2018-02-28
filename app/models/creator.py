# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.

from cbserver.models.database import Base, db_session
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

issuecreators = Table('issuecreators', Base.metadata,
    Column('creators_id', Integer, ForeignKey('creator.id')),
    Column('issue_id', Integer, ForeignKey('issue.id'))
)

class Creator(Base):
    __tablename__ = 'creator'
    id = Column(Integer, primary_key=True)
    issues = relationship("Issue", secondary=issuecreators,back_populates="creators")
    cvid = Column(String(15))
    cvurl = Column(String(200))
    name = Column(String(200))
    desc = Column(String(500))
    image = Column(String(255))

    def __str__(self):
        return self.name
