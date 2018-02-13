import yaml
import json
import requests
import os
import sys
from pathlib import Path, PurePosixPath

from PIL import Image

from app.models import Issue, Publisher, Series, issues_list, series_list, series_list_by_id, issues_list_by_series, get_all_issues, issues_get_by_filename, issues_get_by_issueid, series_match_or_save, issue_match_or_create, issue_update_by_id, series_update_or_create, series_get_by_seriesid, publisher_update_or_create, publisher_get_from_cvid, series_get_from_cvid, issue_update_or_create, issue_get_by_issueid
from app.mod_lib.parse_names.comicimporter import MetadataImporter
from config import SBConfig

from app.mod_lib.parse_names.fnameparser import extract as extractname
from app.mod_lib.parse_names.util import remove_special_characters

from config import SBConfig
apikey = SBConfig.get_api_key()
libfolder = SBConfig.get_lib_path()
folder=""

import logging
from os import scandir, walk

logger = logging.getLogger(__name__)

class CBFile(object):
    #This seems overkill, but want to add child/parent classes, unit testing, abstract MIME detection, etc.
    #May remove after fleshing API out.
    def __init__(self, **kwargs):
        self.source_path=''
        self.dest_base=''
        self.dest_path=''
        self.dest_name=''
        self.source_size=''
        self.imagepath=SBConfig.get_image_path()
        self.filetype=''
        self.image_type=''
        self.id = ''
        self.image_sizes=SBConfig.get_image_sizes()
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.readpath=SBConfig.get_read_path() + '/' + str(self.id) + '/'
        self.seriespath=SBConfig.get_image_path() + '/' + 'series/pages/' + str(self.id) + '/'
        self.issuepath=SBConfig.get_image_path() + '/' + 'issues/pages/' + str(self.id) + '/'
        self.seriescoverpath=SBConfig.get_image_path() + '/' + 'series/covers/' + str(self.id) + '/'
        self.issuecoverpath=SBConfig.get_image_path() + '/' + 'issues/covers/' + str(self.id) + '/'

    def path_getter(self):
        print(self.imagetype)
        return {
            'issue_cover': self.seriescoverpath,
            'series_cover': self.issuecoverpath,
            'issue_page': self.issuepath,
            'series_page': self.seriespath
        }.get(self.imagetype)    # 9 is default if x not found

    def get_image_path_by_size(self):
        basepath = (os.path.splitext(self.dest_path)[0] + '_' + self.size + os.path.splitext(self.dest_path)[1])

    def get_size_array(self): #This creates JSON with all the possible file sizes. Do we need this? It's not used now.
        sizes=['small','large','medium','icon','tiny','thumb','super']
        covers=[{'size': size, 'path': self.dest_path + '/' + size} for size in sizes]

    def verify_file_present(self):
        size = self.get_image_path_by_size()
        return os.path.isfile(self.dest_path)

    def get_image_type(self):
        try:
            with Image.open(self.source_path) as im:
                self.filetype = im.format
        except IOError as e:
            print(e)
            pass

    def get_image_size(self):
        try:
            with Image.open(self.source_path) as im:
                self.source_size = im.size
        except IOError as e:
            print(e)
            pass

    def copy_and_resize(self):
        dest_filename = self.get_resized_filename()
        dimensions=(self.image_sizes[self.size]['width'], self.image_sizes[self.size]['height'])
        print(self.image_sizes[self.size])
        #size =
        print('at copy and resize. source: ' + str(self.source_path) + 'dest: '+ self.dest_path)
        self.make_dest_path()
        try:
            im = Image.open(self.source_path)
            im.thumbnail(dimensions, Image.ANTIALIAS)
            im.save(dest_filename, "JPEG")
            return dest_filename
        except IOError:
            print('cannot create thumbnail for ' + infile)


    def get_resized_filename(self):
        fileext = PurePosixPath(self.source_path).suffix
        filename = (str(PurePosixPath(self.source_path).stem) + '_' + str(self.size))
        dest_file = self.dest_path + filename + fileext
        return dest_file

    def move_image(self):
        self.make_dest_path()
        result = self.link_image()
        return result

    def link_image(self):
        dest_file = (self.dest_path + PurePosixPath(self.source_path).name)
        try:
            if not os.path.isfile(dest_file):
                os.link(self.source_path, dest_file)
            return dest_file

        except IOError as e:
            print(e)
            pass

    def make_dest_path(self):
        if not os.path.exists(self.dest_path):
            try:
                os.makedirs(self.dest_path)
            except:
                raise

    def make_source_path(self):
        if not os.path.exists(self.issuecoverpath):
            try:
                os.makedirs(self.issuecoverpath)
            except:
                raise

class CVFetch(object):
    def __init__(self, **kwargs):
        self.filepath=''
        self.pages=[]
        self.size=''
        self.covername=''
        self.issue=''
        self.covers=''
        self.imagepath=SBConfig.get_image_path()
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.readpath=SBConfig.get_read_path() + '/' + str(self.id) + '/'
        self.seriespath=SBConfig.get_image_path() + '/' + 'series/pages/' + str(self.id) + '/'
        self.issuepath=SBConfig.get_image_path() + '/' + 'issues/pages/' + str(self.id) + '/'
        self.seriescoverpath=SBConfig.get_image_path() + '/' + 'series/covers/' + str(self.id) + '/'
        self.issuecoverpath=SBConfig.get_image_path() + '/' + 'issues/covers/' + str(self.id) + '/'

    def make_path():
        if not os.path.exists(self.issuecoverpath):
            try:
                os.makedirs(self.issuecoverpath)
            except:
                raise

    def download_file(url, filename, force=False):
        headers = {'User-Agent': 'SomethingBetter v0.1.1'}
        i = requests.get(url, headers=headers)
        self.make_path()
        with open(filename, 'wb') as f:
            f.write(i.content)



def scantree(path):
    extensions = ['.jpeg', '.jpg', '.cbr', '.cbt', '.cbz']
    for entry in os.scandir(path):
        if not entry.name.startswith('.') and entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path)
        else:
          ext = os.path.splitext(entry.name)[-1].lower()
          if not entry.name.startswith('.') and ext in extensions:
              yield entry

def scan_library_path():
    comicfilelist = [(os.path.basename(entry.path), entry.path) for entry in scantree(libfolder)]

    for filename, filepath in comicfilelist:
        series, extracted = process_series_by_filename(filename)
        issue=Issue(filename=filename, filepath=filepath, series_id=series.id, number=extracted[1])
        issue=issue.update_or_create()

    db_session.commit()
    db_session.flush()
    return 'comicfilelist'

def process_series_by_filename(filename, force=False):
    #issue = issues_get_by_issueid(issue_id)
    extracted = extractname(filename)
    series_name = remove_special_characters(extracted[0])
    #series = series_match_or_save(series_name, force)
    series = Series(series_name=series_name, force=False)
    series=series.match_or_save()
    return series, extracted

#def process_library_files():
#    comics = get_all_issues()
#    for comic in comics:
#        importer = MetadataImporter()
#        series_name, series_number, series_date = importer.import_comic_records(comic.id, 'basic')
#        match_or_save(series_name, series_number, series_date)
#    return 'ok'

def process_library_cv_issue():
    comics = db_session.query(Issue)
    for comic in comics:
        importer = MetadataImporter()
        importer.import_comic_records(comic, 'cv')
        import_issue_details
    return 'ok'

def process_cv_series_by_id(series_id):
    series = series_get_by_seriesid(series_id)
    importer = MetadataImporter()
    #importer.import_issue_details(series)
    return 'ok'

def process_cv_get_series_cvid_by_id(series_id):
    series = series_get_by_seriesid(series_id)
    importer = MetadataImporter()
    series_matches = importer.find_series_matches(series)
    #importer.import_issue_details(series)
    #cvid = find_issue_id(series.id)
    return series_matches

def process_cv_get_series_details_by_id(series_id, cvid):
    series = series_get_by_seriesid(series_id)
    if not series.cvid:
        series.cvid=cvid
    importer = MetadataImporter()
    details = importer.get_series_details(series)['results']

    publisher=Publisher(cvid=details['publisher']['id'], name=details['publisher']['name'], commit=True)
    publisher.update_or_create_by_cvid()
    series = series_update_or_create(series_id,
        image_small=details['image']['small_url'],
        image_large=details['image']['screen_large_url'],
        image_medium=details['image']['medium_url'],
        image_icon=details['image']['icon_url'],
        image_tiny=details['image']['tiny_url'],
        image_thumb=details['image']['thumb_url'],
        image_super=details['image']['super_url'],
        name=details['name'],
        description=details['description'])
    return 'ok'

def process_cv_get_publisher_details_by_id(issue_id):
    publisher = publisher_get_publisher_by_issueid(issue_id)

def process_cv_get_issue_details_by_id(issue_id):
    issue=issue_get_by_issueid(issue_id)
    importer = MetadataImporter()
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

def process_cv_get_issue_covers(id, force=False):
    issue=issue_get_by_issueid(id)
    covers=get_issue_covers(id)
    make_covers_local(issue, covers, force)
    #return covers
    return 'ok'

def process_cv_get_series_covers(id, force=False):
    series=series_get_by_seriesid(id)
    covers=get_series_covers(id)
    make_covers_local(series, covers, force)
    return covers

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
