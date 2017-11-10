# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db
from .main import Base
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

class Publisher(Base):
    cvid = Column(db.String(15))
    cvurl = Column(db.String(200))
    name = Column(db.String(200))
    desc = Column(db.String(500))
    logo = Column(db.String(255))
    series_id = Column(Integer, ForeignKey('series.id'))
    series = relationship("Series")

    def __str__(self):
        return self.name

    def __init__(self, **kwargs):
        self.kwargs=kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def update_or_create_by_cvid(self):
        publisher = db.session.query(Publisher).filter_by(cvid=self.cvid).first() or False
        #print(publisher.cvid, publisher.id, id, publisher.description)
        if not publisher:
            publisher = Publisher()
        db.session.add(publisher)
        for key, value in self.kwargs.items():
            newvalue=str(value[0]) if isinstance(value, list) else str(value)
            setattr(publisher, key, newvalue)

        if self.commit:
            try:
                db.session.commit()
                db.session.flush()
            except:
                db.session.rollback()
                raise
