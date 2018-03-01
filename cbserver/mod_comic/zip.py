import zipfile
from config import SBConfig
from pathlib import Path, PurePosixPath
import os.path
import shutil
import logging
from .utils import CBUtils
logger = logging.getLogger(__name__)

class SBZip(object):
    def __init__(self, filename, id=None):
        self.fp = zipfile.ZipFile(filename, 'r')
        self.id = id

    def listpages(self):
        pagelist = self.fp.infolist()
        result = CBUtils(pagelist=pagelist).listpages()
        return result

    def extract(self):
        pagelist = self.fp.infolist()
        result = CBUtils(pagelist=pagelist, archiveinstance=self).extractpages()
