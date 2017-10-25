import rarfile
from config import SBConfig
import os.path
import logging
logger = logging.getLogger(__name__)

class SBRar(object):
    def __init__(self, filename, id=None):
        self.fp = rarfile.RarFile(filename, 'r')
        self.id = id

    def listpages(self):
        return self.fp.namelist()

    def extract(self):
        outpath=SBConfig.get_read_path() + str(self.id) + '/'
        self.fp.extractall(path=outpath)
