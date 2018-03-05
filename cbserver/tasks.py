from cbserver import celery
from celery import group
from cbserver.models import Arc, Character, Creator, Team, Publisher, Series, Issue, Settings
from cbserver.models.database import db_session
from cbserver.mod_comic import ImageGetter
from cbserver.mod_lib import CBLibrary
from config import SBConfig
import os

libfolder = SBConfig.get_lib_path()
#logger = get_task_logger(__name__)

@celery.task(bind=True)
def import_library_files(self):
    comicfilelist = [(os.path.basename(entry.path), entry.path) for entry in CBLibrary().scantree(libfolder)]
    total = len(comicfilelist)
    self.update_state(state='PROGRESS',
                  meta={'current': 0, 'total': total})
    for index, (filename, filepath) in enumerate(comicfilelist):
        percentage = 100 * float(index)/float(total)
        series, extracted = CBLibrary(filename=filename).process_series_by_filename()
        issue=Issue(filename=filename, filepath=filepath, number=extracted[1])
        issue=issue.update_or_create()
        series.issues.append(issue)
        self.update_state(state='PROGRESS',
                      meta={'current': index, 'total': total, 'message': filename})
    db_session.commit()
    db_session.flush()
    return {'current': 100, 'total': 100, 'status': 'Task completed!'}

@celery.task(bind=True)
def extract_image(self, id, sizes, imagetype, remove):
#def extract_image(id, sizes, imagetype, remove):
    if imagetype == 'series_cover':
        model = db_session.query(Series).filter(Series.id==id).first()
    elif imagetype == 'issue_cover':
        model = db_session.query(Issue).filter(Issue.id==id).first()
    for size in sizes:
        file = ImageGetter(id=id, size=size, model=model, imagetype=imagetype)
        file.get_cover()
    if remove is True:
        file.clean_extracted_comic()
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': model.id}
