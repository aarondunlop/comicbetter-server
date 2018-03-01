import tarfile
from config import SBConfig
import os.path
import shutil
from pathlib import Path, PurePosixPath
import logging
from .utils import CBUtils
logger = logging.getLogger(__name__)

class SBTar(object):
    def __init__(self, filename, id=None):
        self.fp = tarfile.TarFile(filename, 'r')
        self.id = id

    def listpages(self):
        pagelist = self.fp.infolist()
        result = CBUtils(pagelist=pagelist).listpages()
        return result

    def extract(self):
        pagelist = self.fp.infolist()
        result = CBUtils(pagelist=pagelist, archiveinstance=self).extractpages()
