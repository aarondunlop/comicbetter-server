import yaml
import json
import requests
import os
import sys
from pathlib import Path, PurePosixPath
from cbserver.models.database import db_session
from sqlalchemy import exc
from datetime import datetime
#from .cvfetch import CVFetch

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
        return {
            'issue_cover': self.issuecoverpath,
            'series_cover': self.seriescoverpath,
            'issue_cache': self.issuecoverpath,
            'series_cache': self.seriescoverpath,
            'issue_page': self.issuepath,
            'series_page': self.seriespath
        }.get(self.imagetype)

    def get_image_path_by_size(self):
        basepath = (os.path.splitext(self.dest_path)[0] + '_' + self.size + os.path.splitext(self.dest_path)[1])

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
        self.make_dest_path()
        try:
            im = Image.open(self.source_path)
            im.thumbnail(dimensions, Image.ANTIALIAS)
            im.save(dest_filename, "JPEG")
            return dest_filename
        except IOError as e:
            print(e)
            pass

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
