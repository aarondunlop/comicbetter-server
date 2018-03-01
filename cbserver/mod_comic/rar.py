import rarfile
from config import SBConfig
import os.path
import shutil
import logging
from pathlib import Path, PurePosixPath
from .utils import CBUtils
logger = logging.getLogger(__name__)

class SBRar(object):
    def __init__(self, **kwargs):
        self.kwargs=kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.fp = rarfile.RarFile(self.filename, 'r')

    def listpages(self):
        pagelist = self.fp.infolist()
        result = CBUtils(pagelist=pagelist).listpages()
        return result

    def extract(self):
        pagelist = self.fp.infolist()
        result = CBUtils(pagelist=pagelist, archiveinstance=self).extractpages()
