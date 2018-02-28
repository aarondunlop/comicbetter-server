# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.

from cbserver.models.database import Base, db_session
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

class Series(Base):
    __tablename__ = 'series'
    id = Column(Integer, primary_key=True)
    #issues = relationship("Issue", secondary=issueseries,back_populates="series")
    issues = relationship("Issue", back_populates="series")
    cvid = Column(Integer)
    cvurl = Column(String(200))
    image_small = Column(String(200))
    image_large = Column(String(200))
    image_medium = Column(String(200))
    image_icon = Column(String(200))
    image_tiny = Column(String(200))
    image_thumb = Column(String(200))
    image_super = Column(String(200))
    name = Column(String(200))
    #publishers = Column(Integer, ForeignKey('publisher.id'))
    #publishers = relationship("Publisher", secondary=pubassociation, back_populates="series")
    #publisher_id = Column(Integer, ForeignKey('publisher.id'))
    #publisher = relationship("Publisher")
    #id = Column(Integer, primary_key=True)
    #publisher = ForeignKey(Publisher, on_delete=CASCADE, null=True)
    year = Column(Integer)
    description = Column(String(500))

    def __init__(self, **kwargs):
        self.kwargs=kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return self.name

    def get_first_issue(self):
        series = db_session.query(Series).filter(id == id).first()
        issues = db_session.query(Issue).filter(Issue.series_id == self.series_id).all()
        return issues

    def get_json_by_id(self):
        series = db_session.query(Series).filter_by(id=self.id).first() or False
        seriesJson = ({ key: value for key, value in list(series.__dict__.items()) if not key == "_sa_instance_state" })
        return seriesJson

    def issue_numerical_order_set(self):
        return self.issue_set.all().order_by('number')

    class Meta:
        verbose_name_plural = "Series"

    def series_get_file(self):
        series = db_session.query(Series).filter_by(id=self.id).first()
        return series.filename

    def series_get_filepath(self):
        series = db_session.query(Series).filter_by(id=self.id).first()
        return series.filepath

    def series_get_abfilepath(self):
        series = db_session.query(Series).filter_by(id=self.id).first()
        return series.filepath + '/' + series.filename

    def match_or_save(self):
        matching_series = db_session.query(Series).filter_by(name=self.name).first()
        if not matching_series:
            matching_series = Series(name=self.name)
            db_session.add(matching_series)
            db_session.flush()
        return matching_series

    def getlist(self):
        series=''
        diff=int(self.limit)*int(self.page)
        series = db_session.query(Series).limit(self.limit).offset(diff).all()
        values=['name', 'description', 'id', 'year']
        series = [dict(list(zip(values, [row.name, row.description if row.name and row.description else None, row.id, row.year]))) for row in series]
        return series

    def update_or_create(self):
        series = db_session.query(Series).filter_by(id=self.id).first() or False
        if not series:
            series = Series(id=self.id)
            db_session.add(series)
        for key, value in self.kwargs.items():
            newvalue=value[0] if isinstance(value, list) else value
            setattr(series, key, newvalue)
        return series
