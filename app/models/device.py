# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from .main import Base
from app import db
from datetime import datetime
from json import dumps

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

deviceissues = Table('deviceissues', Base.metadata,
    Column('issue_id', Integer, ForeignKey('issue.id')),
    Column('device_id', Integer, ForeignKey('device.id'))
)

class Device(Base):
    __tablename__ = 'device'
    name = Column(db.String(200))
    last_seen = Column(db.Integer)
    description = Column(db.String(500))
    issues = relationship(
    "Issue",
    secondary=deviceissues,
    back_populates="devices")

    def __init__(self, **kwargs):
        self.kwargs=kwargs
        for key, value in kwargs.items():
            if key == 'issues':
                setattr(self, 'issue_id', value)
            else:
                setattr(self, key, value)

    def update_or_create(self):
        device = db.session.query(Device).filter_by(id=self.id).first() or False
        if not device:
            device = Device()
        db.session.add(device)
        for key, value in self.kwargs.items():
            newvalue=str(value[0]) if isinstance(value, list) else str(value)
            setattr(device, key, newvalue)

        try:
            db.session.commit()
            db.session.flush()
        except:
            db.session.rollback()
            raise
        return 'ok'

    def get(cls):
        return db.session.query(Device).filter(id=self.id)

    def get_all(cls):
        devices = db.session.query(Device).all()
        values=['id', 'name', 'last_seen', 'description']
        return ([dict(list(zip(values, [row.id, row.name, row.last_seen, row.description]))) for row in devices])

    def sync(self, issues):
        device = db.session.query(Device).filter(Device.id==self.id).first()
        return self.id

    def synced(self):
        device = db.session.query(Device).filter(Device.id==self.id).first()
        return device.issues
