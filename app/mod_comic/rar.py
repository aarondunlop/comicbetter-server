import rarfile
from config import SBConfig
import os.path
import logging
logger = logging.getLogger(__name__)

class SBRar(object):
    def __init__(self, **kwargs):
        self.kwargs=kwargs
        for key, value in kwargs.items():
            print(key, value)
            setattr(self, key, value)
        self.fp = rarfile.RarFile(self.filename, 'r')
        print(self.fp)


    def listpages(self):
        namelist = self.fp.namelist()
        print(namelist)
        return namelist

    def extract(self):
        outpath=SBConfig.get_read_path() + str(self.id) + '/'
        self.fp.extractall(path=outpath)
