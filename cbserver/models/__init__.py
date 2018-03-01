from .arc import *
from .character import *
from .comicpages import *
from .creator import *
from .issue import Issue
from .libraryfolders import *
from .publisher import *
from .series import *
from .settings import *
from .team import *
from .device import Device
from .user import User
import json

def issues_list():
    issues = db.session.query(Issue).all()
    values=['cover', 'name', 'issue', 'path', 'series_name', 'id']
    comics = [dict(list(zip(values, [row.cover, row.name, row.number, row.filepath, row.series.name if row.series and row.series.name else None, row.id]))) for row in issues]
    return comics

def series_list(limit, page):
    series = db.session.query(Series)[(limit * page):page].all()
    values=['name', 'description', 'id']
    series = [dict(list(zip(values, [row.name, row.description if row.name and row.description else None, row.id]))) for row in series]
    return series

def series_list_by_id(series_id):
    series = db.session.query(Series).filter(Series.id==series_id).all()
    values=['name', 'description', 'id']
    series = [dict(list(zip(values, [row.name, row.description if row.name and row.description else None, row.id]))) for row in series]
    return series

def issues_list_by_series(series_id):
    issues = db.session.query(Issue).filter(Issue.series_id==series_id).all()
    #values=['cover', 'name', 'issue', 'path', 'series_name', 'id']
    #comics = json.dumps([dict(zip(values, [row.cover, row.name, row.number, row.filepath, row.series.name if row.series and row.series.name else None, row.id])) for row in issues])
    return issues

def get_all_issues():
    return db.session.query(Issue)

def issues_get_by_filename(filename):
    return db.session.query(Issue).filter_by(filepath=filename).first() or False

def issues_get_by_issueid(issue_id):
    issue = db.session.query(Issue).filter_by(id=issue_id).first()
    return issue

def series_get_by_seriesid(series_id):
    return db.session.query(Series).filter_by(id=series_id).first() or False

def issue_match_or_create(filename, filepath):
    #issue = db.session.query(Issue).filter_by(filename=filename.decode('utf8', 'ignore')).first() or False
    issue = db.session.query(Issue).filter_by(filename=filename).first() or False

    if not issue:
        #issue = Issue(filename=filename.decode('utf8', 'ignore'), filepath=filepath)
        issue = Issue(filename=filename, filepath=filepath)
        db.session.add(issue)
        #db.session.flush()
        db.session.commit()
    return issue

def series_match_or_save(series_name, force):
    matching_series = db.session.query(Series).filter_by(name=series_name).first()
    if not matching_series or force:
        matching_series = Series(name=series_name)
        db.session.add(matching_series)
        db.session.flush()
        db.session.commit()

def issue_update_by_id(issue, **kwargs):
    try:
        for key, value in kwargs.items():
            newvalue=value[0] if isinstance(value, list) else value
            setattr(issue, key, newvalue)
        db.session.commit()
        db.session.flush()
    except:
        db.session.rollback()
        raise
    return 'ok'

def series_get_from_cvid(cvid, **kwargs):
    series = db.session.query(Series).filter_by(cvid=cvid).first() or False
    return series

def series_update_or_create(series_id, **kwargs):
    series = db.session.query(Series).filter_by(id=series_id).first() or False
    if not series:
        series = Series(id=series_id)
    for key, value in kwargs.items():
        newvalue=value[0] if isinstance(value, list) else value
        setattr(series, key, newvalue)
    try:
        db.session.commit()
        db.session.flush()
    except:
        db.session.rollback()
        raise
    return 'ok'

def publisher_get_from_cvid(cvid, **kwargs):
    publisher = db.session.query(Publisher).filter_by(id=cvid).first() or False
    return publisher

def publisher_get_by_publisherid(series_id):
    return db.session.query(Publisher).filter_by(id=publisher_id).first() or False

def publisher_update_or_create(id, **kwargs):
    publisher = db.session.query(Publisher).filter_by(id=id).first() or False
    if not publisher:
        publisher = Publisher(id=id, **kwargs)
        db.session.add(publisher)
    try:
        db.session.commit()
        db.session.flush()
    except:
        db.session.rollback()
        raise
    return 'ok'

def issue_get_from_cvid(cvid, **kwargs):
    issue = db.session.query(Issue).filter_by(id=cvid).first() or False
    return issue

def issue_get_by_issueid(issue_id):
    return db.session.query(Issue).filter_by(id=issue_id).first() or False

def issue_update_or_create(id=None, **kwargs):
    issue = db.session.query(Issue).filter_by(id=id).first() or False
    if not issue:
        issue = Issue(id=id, **kwargs)
    for key, value in kwargs.items():
        setattr(issue, key, value)
    db.session.commit()
    db.session.flush()

    try:
        db.session.commit()
        db.session.flush()
    except:
        db.session.rollback()
        raise
    return 'ok'

#def issue_get_file(id):
#    issue = db.session.query(Issue).filter_by(id=id).first()
#    return issue.filepath, issue.filename

def sync(id, add, remove):
    device = db.session.query(Device).filter(Device.id==id).first()
    if add:
        for id in add:
            issue = db.session.query(Issue).filter(Issue.id==id).first()
            device.issues.append(issue)
    if remove:
        for id in remove:
            issue = db.session.query(Issue).filter(Issue.id==id).first()
            device.issues.remove(issue)
    try:
        db.session.commit()
        db.session.flush()
    except:
        db.session.rollback()
        raise
    return device.id

def synced(id):
    device = db.session.query(Device).filter(Device.id==id).first()
    return [d.id for d in device.issues]
