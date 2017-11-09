# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db
from .main import Base
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

class Series(Base):
    #issues = relationship("Issue", secondary=issueseries,back_populates="series")
    issues = relationship("Issue", back_populates="series")
    cvid = Column(db.String(15))
    cvurl = Column(db.String(200))
    image_small = Column(db.String(200))
    image_large = Column(db.String(200))
    image_medium = Column(db.String(200))
    image_icon = Column(db.String(200))
    image_tiny = Column(db.String(200))
    image_thumb = Column(db.String(200))
    image_super = Column(db.String(200))
    name = Column(db.String(200))
    #publishers = Column(Integer, ForeignKey('publisher.id'))
    #publishers = relationship("Publisher", secondary=pubassociation, back_populates="series")
    #publisher_id = Column(Integer, ForeignKey('publisher.id'))
    #publisher = relationship("Publisher")
    #id = Column(Integer, primary_key=True)
    #publisher = db.ForeignKey(Publisher, on_delete=db.CASCADE, null=True)
    year = Column(db.Integer)
    description = Column(db.String(500))

    def __init__(self, **kwargs):
        self.kwargs=kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return self.name

    def issue_numerical_order_set(self):
        return self.issue_set.all().order_by('number')

    class Meta:
        verbose_name_plural = "Series"

    def series_get_file(self):
        series = db.session.query(Series).filter_by(id=self.id).first()
        return series.filename

    def series_get_filepath(self):
        series = db.session.query(Series).filter_by(id=self.id).first()
        return series.filepath

    def series_get_abfilepath(self):
        series = db.session.query(Series).filter_by(id=self.id).first()
        return series.filepath + '/' + series.filename

    def series_match_or_save(self):
        matching_series = db.session.query(Series).filter_by(name=self.series_name).first()
        if not matching_series or force:
            matching_series = Series(name=series_name)
            db.session.add(matching_series)
            db.session.commit()
            db.session.flush()
        return matching_series

    def getlist(self):
        series=''
        diff=int(self.limit)*int(self.page)
        series = db.session.query(Series).limit(self.limit).offset(diff).all()
        values=['name', 'description', 'id']
        series = [dict(list(zip(values, [row.name, row.description if row.name and row.description else None, row.id]))) for row in series]
        return series
