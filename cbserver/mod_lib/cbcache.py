import yaml
import json
import requests
import os
from shutil import rmtree
from os import scandir, walk, path

import sys
from cbserver.models.database import db_session
from sqlalchemy import exc
from datetime import datetime

from cbserver.models import Issue, Publisher, Series

from config import SBConfig
apikey = SBConfig.get_api_key()
libfolder = SBConfig.get_lib_path()
folder=""

import logging
logger = logging.getLogger(__name__)

class CBCache(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def nuke(self):
        readpath = SBConfig.get_read_path()
        cachepath = SBConfig.get_image_path()
        if path.isdir(readpath):
            rmtree(readpath)
        if path.isdir(cachepath):
            rmtree(cachepath)
        issues = db_session.query(Issue).all()
        series = db_session.query(Series).all()
        image_sizes = ['image_icon', 'image_large', 'image_medium', 'image_small', 'image_super', 'image_thumb', 'image_tiny']
        for issue in issues:
            for image in image_sizes:
                setattr(issue, image, None)
        for series in series:
            for image in image_sizes:
                setattr(series, image, None)
        db_session.flush()
        db_session.commit()
        return (readpath, cachepath)
