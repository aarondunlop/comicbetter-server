import yaml
import json
import requests
import os
import sys
from pathlib import Path, PurePosixPath
from cbserver.models.database import db_session
from sqlalchemy import exc
from datetime import datetime

from .cbfile import CBFile

from PIL import Image

from cbserver.models import Issue, Publisher, Series #, issues_list, series_list, series_list_by_id, issues_list_by_series, get_all_issues, issues_get_by_filename, issues_get_by_issueid, series_match_or_save, issue_match_or_create, issue_update_by_id, series_update_or_create, series_get_by_seriesid, publisher_update_or_create, publisher_get_from_cvid, series_get_from_cvid, issue_update_or_create, issue_get_by_issueid
from cbserver.mod_lib.comicimporter import CVWrapper
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

class CVFetch(object):
    def __init__(self, **kwargs):
        self.filepath=''
        self.pages=[]
        self.size=''
        self.model=''
        self.covername=''
        self.issue=''
        self.covers={}
        #self.imagepath=SBConfig.get_image_path()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def fetch_cv_series_record(self):
        details = CVWrapper(cvid=self.cvid).get_series_details()
        response={}
        response['image_thumb'] = str(details['image']['thumb_url'])
        response['name'] = str(details['name'])
        response['start_year'] = str(details['start_year'])
        response['id'] = str(details['id'])
        return response

    def fetch_cv_series_cover_by_cvid(self):
        image = CVWrapper(cvid=self.cvid).get_series_details()
        self.url = str(image['image']['thumb_url'])
        self.dest_path = CBFile(imagetype='series_cache', id='cache').path_getter()
        self.filename = self.dest_path + PurePosixPath(self.url).name
        self.download_file()
        return self.filename

    def process_cv_get_issue_details_by_id(self): #This is unused for now.
        issue=issue_get_by_issueid(issue_id)
        importer = CVWrapper()
        issue.cvid = importer.get_issue_cvid_by_number(issue)
        if isinstance(issue.cvid, int):
            details = importer.get_issue_details(issue)
            issue_update_or_create(issue_id,
                image_small=details['image']['small_url'],
                image_large=details['image']['screen_large_url'],
                image_medium=details['image']['medium_url'],
                image_icon=details['image']['icon_url'],
                image_tiny=details['image']['tiny_url'],
                image_thumb=details['image']['thumb_url'],
                image_super=details['image']['super_url'],
                name=details['name'],
                date=details['cover_date'],
                description=details['description'])
            #process_cv_get_images(issue.id)
            return 'ok'
        else:
            return issue.cvid #This will be the error message

    def get_cv_size_paths(self): #This creates JSON with all the possible file sizes. Do we need this? It's not used now.
        self.covers={}
        sizes=['small','large','medium','icon','tiny','thumb','super']
        self.covers = {size: {'path': (self.dest_path + size)} for size in sizes}

    def get_cv_size_urls(self):
        self.covers['small']['url'] = self.details['image']['small_url']
        self.covers['large']['url'] = self.details['image']['small_url']
        self.covers['medium']['url']= self.details['image']['small_url']
        self.covers['icon']['url']= self.details['image']['small_url']
        self.covers['tiny']['url']= self.details['image']['small_url']
        self.covers['thumb']['url']= self.details['image']['small_url']
        self.covers['super']['url']= self.details['image']['small_url']

    def fetch_covers(self):
        #images = (image for image in details['image'] if image not in 'image_tags')
        #for image in images:
        importer = CVWrapper(model=self.model, cvid=self.cvid)

        if self.imagetype is 'series_cover':
            details = importer.get_series_details()
        elif self.imagetype is 'issue_cover':
            details = importer.get_issue_details()
        self.details = details
        self.get_cv_size_paths()
        self.get_cv_size_urls()

        for size, keys in self.covers.items():
            if self.size == size or self.size == 'all':
                self.url = keys['url']
                if self.url.find('/'):
                    filename = self.dest_path + self.url.rsplit('/', 1)[1]
                    fileext = PurePosixPath(filename).suffix
                    self.filename = self.dest_path + (str(PurePosixPath(filename).stem) + '_' + str(size)) + fileext
                self.download_file()
                converted_size = ('image_' + str(size))
                setattr(self.model, converted_size, self.filename)
        return self.covers

    def fetch_record(self):
        importer = CVWrapper(model=self.model, cvid=self.model.cvid)
        if self.imagetype is 'issue_cover':
            self.model.cvid = importer.get_issue_cvid_by_number() #This gets the issue CVID via the Series CVID.
            details = importer.get_issue_details()
            coverted_cover_date = datetime.strptime(str(details['cover_date']), '%Y-%M-%d')
            self.model.date=coverted_cover_date
            self.model.description=str(details['description'])
            self.model.name=str(details['name'])
        elif self.imagetype is 'series_cover':
            details = importer.get_series_details()
            self.model.cvurl=str(details['api_detail_url'])
            self.model.description=str(details['description'])
        elif self.imagetype is 'issue':
            details = importer.get_issue_details()
            self.model.description=str(details['description'])
            self.model.name=str(details['name'])
        #publisher = db_session.query(Publisher).filter(Publisher.id==details['publisher']['id']).first()
        #if publisher is not None:
        #    publisher.name = details['publisher']['name']
        #else:
        #    publisher = Publisher(cvid=details['publisher']['id'], name=details['publisher']['name'], commit=True)
        #self.model.name=details['name'],
        #self.model.year=str(details['year'])

        try:
            db_session.commit()
        except:
            import sys, traceback
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
            traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)
        return details, self.model

    def download_file(self):#url, filename, force=False):
        headers = {'User-Agent': 'SomethingBetter v0.1.1'}
        i = requests.get(self.url, headers=headers)
        CBFile(dest_path=self.dest_path).make_dest_path()
        with open(self.filename, 'wb') as f:
            f.write(i.content)

    def get_cv_issue_covers(self):#id, force=False):
        model = db_session.query(Issue).filter(Issue.id==self.id).first()

        #self.download_file(self.dest_path)

        #issue=db_session.queryissue_get_by_issueid(id)
        #covers=get_issue_covers(id)
        #make_covers_local(issue, covers, force)
        #return covers
        return 'ok'

    def get_cv_series_covers(id, force=False):
        model = db_session.query(Series).filter(Series.id==id).first()

        #self.download_file(self.dest_path)

        #series=series_get_by_seriesid(id)
        #covers=get_series_covers(id)
        #make_covers_local(series, covers, force)
        return 'ok'

    def process_cv_get_series_cvid_by_id(self):
        series = db_session.query(Series).filter_by(id = self.id).first()
        importer = CVWrapper(name=series.name)
        series_matches = importer.find_series_matches(series)
        return series_matches

    def process_cv_get_series_by_name(self):
        importer = CVWrapper(name=self.name)
        series_matches = importer.find_series_matches()
        print(series_matches)
        return series_matches

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
