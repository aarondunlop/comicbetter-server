import re,sys,os,yaml,os.path
from cbserver.models import Issue
from PIL import Image
from app import db
import logging

logger = logging.getLogger(__name__)

from config import SBConfig
apikey = SBConfig.get_api_key()
libfolder = SBConfig.get_lib_path()

from os import scandir, walk

class CVWrapper(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def scantree(self, path):
        extensions = ['.jpeg', '.jpg', '.cbr', '.cbt', '.cbz']
        for entry in os.scandir(path):
            if not entry.name.startswith('.') and entry.is_dir(follow_symlinks=False):
                yield from self.scantree(entry.path)
            else:
              ext = os.path.splitext(entry.name)[-1].lower()
              if not entry.name.startswith('.') and ext in extensions:
                  yield entry

    def scan_library_path(self):
        comicfilelist = [(os.path.basename(entry.path), entry.path) for entry in self.scantree(libfolder)]
        print(comicfilelist)
        for filename, filepath in comicfilelist:
            series, extracted = self.process_series_by_filename(filename)
            issue=Issue(filename=filename, filepath=filepath, number=extracted[1])
            issue=issue.update_or_create()
            series.issues.append(issue)

        db_session.commit()
        db_session.flush()
        return 'comicfilelist'

    def process_series_by_filename(self):
        #issue = issues_get_by_issueid(issue_id)
        extracted = extractname(self.filename)
        series_name = remove_special_characters(extracted[0])
        series = db_session.query(Series).filter_by(name=series_name).first()
        if not series:
            series = Series(name=series_name)
            db_session.add(series)
        db_session.flush()
        return series, extracted
