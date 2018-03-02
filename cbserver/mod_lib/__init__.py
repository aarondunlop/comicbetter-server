import yaml
import json
import requests
import os
import sys
from pathlib import Path, PurePosixPath
from cbserver.models.database import db_session
from sqlalchemy import exc
from datetime import datetime

from natsort import natsorted, ns

from PIL import Image

from cbserver.models import Issue, Publisher, Series #, issues_list, series_list, series_list_by_id, issues_list_by_series, get_all_issues, issues_get_by_filename, issues_get_by_issueid, series_match_or_save, issue_match_or_create, issue_update_by_id, series_update_or_create, series_get_by_seriesid, publisher_update_or_create, publisher_get_from_cvid, series_get_from_cvid, issue_update_or_create, issue_get_by_issueid
from cbserver.mod_lib.comicimporter import CVWrapper
from cbserver.mod_lib.cbfile import CBFile
from cbserver.mod_lib.cvfetch import CVFetch
from config import SBConfig

from cbserver.mod_lib.parse_names.fnameparser import extract as extractname
from cbserver.mod_lib.parse_names.util import remove_special_characters

from config import SBConfig
apikey = SBConfig.get_api_key()
libfolder = SBConfig.get_lib_path()
folder=""

import logging
from os import scandir, walk

logger = logging.getLogger(__name__)

class CBLibrary(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def scantree(self, path):
        extensions = ['.cbr', '.cbt', '.cbz']
        for entry in os.scandir(path):
            if not entry.name.startswith('.') and entry.is_dir(follow_symlinks=False):
                self.path=entry.path
                yield from self.scantree(entry.path)
            else:
              ext = os.path.splitext(entry.name)[-1].lower()
              if ext in extensions and not entry.name.startswith('.'):
                  yield entry

    def process_series_by_filename(self):
        #issue = issues_get_by_issueid(issue_id)
        extracted = extractname(self.filename)
        series_name = remove_special_characters(extracted[0])
        series = db_session.query(Series).filter_by(name=series_name).first()
        year = int(extracted[2]) if extracted[2] else None
        if not series:
            series = Series(name=series_name, year=year)
            db_session.add(series)
        db_session.flush()
        return series, extracted

    def import_library_files(self):
        comicfilelist = [(os.path.basename(entry.path), entry.path) for entry in self.scantree()]
        for self.filename, self.filepath in natsorted(comicfilelist, alg=ns.IGNORECASE):
            series, extracted = self.process_series_by_filename()
            issue=Issue(filename=self.filename, filepath=self.filepath, number=extracted[1], year=extracted[2])
            issue=issue.update_or_create()
            series.issues.append(issue)
            db_session.flush()

        db_session.commit()
        db_session.flush()
        return 'comicfilelist'

#def process_library_files():
#    comics = get_all_issues()
#    for comic in comics:
#        importer = CVWrapper()
#        series_name, series_number, series_date = importer.import_comic_records(comic.id, 'basic')
#        match_or_save(series_name, series_number, series_date)
#    return 'ok'

def process_library_cv_issue():
    comics = db_session.query(Issue)
    for comic in comics:
        importer = CVWrapper()
        importer.import_comic_records(comic, 'cv')
        import_issue_details
    return 'ok'

def process_cv_series_by_id(series_id):
    series = series_get_by_seriesid(series_id)
    importer = CVWrapper()
    #importer.import_issue_details(series)
    return 'ok'

def process_cv_get_publisher_details_by_id(issue_id):
    publisher = publisher_get_publisher_by_issueid(issue_id)

def get_series_covers(id):
    seriespath=SBConfig.get_image_path() + 'series/covers/' + str(id)
    sizes=['small','large','medium','icon','tiny','thumb','super']
    covers=[{'size': size, 'path': seriespath + '/' + size + '.jpg'} for size in sizes]
    return covers

def download_file(url, filename, force=False):
    headers = {'User-Agent': 'SomethingBetter v0.1.1'}
    i = requests.get(url, headers=headers)
    make_path(filename)
    with open(filename, 'wb') as f:
        f.write(i.content)

def make_path(filename):
    filepath = os.path.dirname(filename)
    if not os.path.exists(filepath):
        try:
            os.makedirs(filepath)
        except:
            raise
