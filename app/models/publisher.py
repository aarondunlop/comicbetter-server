# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.

from cbserver.models.database import Base, db_session
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

class Publisher(Base):
    __tablename__ = 'publisher'
    id = Column(Integer, primary_key=True)
    cvid = Column(String(15))
    cvurl = Column(String(200))
    name = Column(String(200))
    desc = Column(String(500))
    logo = Column(String(255))
    series_id = Column(Integer, ForeignKey('series.id'))
    series = relationship("Series")

    def __str__(self):
        return self.name

    def __init__(self, **kwargs):
        self.kwargs=kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def update_or_create_by_cvid(self):
        publisher = db_session.query(Publisher).filter_by(cvid=self.cvid).first() or False
        if not publisher:
            publisher = Publisher()
        db_session.add(publisher)
        for key, value in self.kwargs.items():
            newvalue=str(value[0]) if isinstance(value, list) else str(value)
            setattr(publisher, key, newvalue)

        if self.commit:
            try:
                db_session.commit()
                db_session.flush()
            except:
                db_session.rollback()
                raise
