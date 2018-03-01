from cbserver import celery
from cbserver.models import Arc, Character, Creator, Team, Publisher, Series, Issue, Settings
from cbserver.models.database import db_session
from cbserver.mod_comic import ImageGetter
from cbserver.mod_lib import CBLibrary

class CoverTasks(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    #@celery.task
    def extract_series(self):
        series_set = db_session.query(Series).all()
        response=[]
        for series in series_set:
            print(series.name)
            response.append(series.id)
            for size in ['small', 'tiny', 'thumb']:
                print(series.id, size)
                file = ImageGetter(id=series.id, size=size, model=series, imagetype='series_cover').get_cover()

        return response

    #@celery.task
    def extract_issues(self):
        issue_set = db_session.query(Issue).all()
        response=[]
        for issue in issue_set:
            print(issue.name)
            response.append(issue.id)
        return response

class LibraryTasks(object):
    def __init(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def import_library_files(self):
        library = CBLibrary().import_library_files()
        return 'ok'

class CacheTasks(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)



@celery.task()
def add_together(a, b):
    return a + b
