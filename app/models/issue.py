# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from .main import Base
from app import db
from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from .arc import issuearcs
from .character import issuecharacters
from .creator import issuecreators
from .team import issueteams
from .device import deviceissues

from flask import request
import json

from .series import Series

from sqlalchemy.inspection import inspect

class Serializer(object):

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]

class Issue(Base, Serializer):
    __tablename__ = 'issue'
    #series = relationship("Series", secondary=issueseries,back_populates="issues")
    series_id = Column(Integer, ForeignKey('series.id'))
    series = relationship("Series", back_populates="issues")
    arcs = relationship("Arc", secondary=issuearcs,back_populates="issues")
    characters = relationship("Character", secondary=issuecharacters,back_populates="issues")
    creators = relationship("Creator", secondary=issuecreators,back_populates="issues")
    teams = relationship("Team", secondary=issueteams,back_populates="issues")
    cvid = Column(db.String(15))
    cvurl = Column(db.String(200))
    #series = db.ForeignKey(Series, on_delete=db.CASCADE)
    name = Column(db.String(200))
    number = Column(db.Integer)
    date = Column(db.Integer)
    description = Column(db.String(500))
    #arcs = db.ManyToManyField(Arc)
    #characters = db.ManyToManyField(Character)
    #creators = db.ManyToManyField(Creator)
    #teams = db.ManyToManyField(Team)
    file = Column(db.String(255))
    cover = Column(db.String(255))
    image_large = Column(db.String(255))
    image_icon = Column(db.String(255))
    image_medium = Column(db.String(255))
    image_tiny = Column(db.String(255))
    image_small = Column(db.String(255))
    image_thumb = Column(db.String(255))
    image_screen = Column(db.String(255))
    image_super = Column(db.String(255))
    filepath    = Column(db.String(128),  nullable=False)
    filename    = Column(db.String(128))
    devices = relationship(
    "Device",
    secondary=deviceissues,
    back_populates="issues")

    def __init__(self, **kwargs):
        self.kwargs=kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def serialize(self):
        d = Serializer.serialize(self)
        return d

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]

    def get_file(self):
        issue = db.session.query(Issue).filter_by(id=self.id).first()
        return issue.filename

    def get_filepath(self):
        issue = db.session.query(Issue).filter_by(id=self.id).first()
        return issue.filepath

    def get_abfilepath(self):
        issue = db.session.query(Issue).filter_by(id=self.id).first()
        output = issue.filepath + '/' + issue.filename
        return output

    def getlist(self):
        issues=''
        diff=int(self.limit)*int(self.page)
        issues = db.session.query(Issue).limit(self.limit).offset(diff).all()
        #values=['name', 'description', 'id']
        #issues = [dict(zip(values, [row.name, row.description if row.name and row.description else None, row.id])) for row in issues]
        return issues

    def getserieslist(self):
        issues=''
        diff=int(self.limit)*int(self.page)
        issues = db.session.query(Issue).filter(Issue.series_id == self.series_id).limit(self.limit).offset(diff).all()
        #values=['name', 'description', 'id']
        #issues = [dict(zip(values, [row.name, row.description if row.name and row.description else None, row.id])) for row in issues]
        return issues

    def find_by_id(self):
        issue = db.session.query(Issue).filter_by(id=self.id).first() or False
        return issue

    def issue_find_by_path_or_id(self):
        if self.id:
            issue = db.session.query(Issue).filter_by(id=self.id).first() or False
        elif self.name:
            issue = db.session.query(Issue).filter_by(filepath=self.filepath).first() or False
        return issue

    def issue_commit(self):
        try:
            db.session.commit()
            db.session.flush()
        except:
            db.session.rollback()
            raise

    def process_issue_by_id(issue):
        #issue = issues_get_by_issueid(issue_id)
        extracted = extractname(issue.filename)
        series_name = extracted[0]
        issue.number = extracted[1]
        issue.date = extracted[2]
        series = Series(series_name = series_name, force = False)
        issue.series = series.id
        #issue_update_by_id(issue, number = number, date = date, series_id = series.id)
        #issue_update_by_id(issue)
        #return series_name, number, date

    def update_or_create(self):
        if self.id:
            issue = db.session.query(Issue).filter_by(id=self.id).first() or False
        elif self.filepath:
            issue = db.session.query(Issue).filter_by(filepath=self.filepath).first() or False
        if not issue:
            issue = Issue(filepath=self.filepath)
            db.session.add(issue)
        for key, value in self.kwargs.items():
            newvalue=str(value[0]) if isinstance(value, list) else str(value)
            setattr(issue, key, newvalue)
        try:
            db.session.commit()
            db.session.flush()
        except:
            db.session.rollback()
            raise
        return issue


    def match_or_save(self):
        matching_issue = db.session.query(Issue).filter_by(name=self.issue_name).first()
        if not matching_issue or self.force:
            matching_issue = Issue(name=self.issue_name)
            db.session.add(matching_issue)
            db.session.commit()
            db.session.flush()
        return matching_issue
