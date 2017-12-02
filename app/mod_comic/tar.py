import tarfile
from config import SBConfig
import os.path
import logging
logger = logging.getLogger(__name__)

class SBTar(object):
    def __init__(self, filename, id=None):
        self.fp = tarfile.TarFile(filename, 'r')
        self.id = id

    def listpages(self):
        return self.fp.getnames()

    def extract(self):
        outpath=SBConfig.get_read_path()  + '/' + str(self.id) + '/'
        self.fp.extractall(path=outpath)
