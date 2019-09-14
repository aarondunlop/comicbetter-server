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
        outpath, filename = CBUtils(pagenum=self.pagenum, pagelist=pagelist, archiveinstance=self).getpaths()
        try:
            with self.fp.open(filename) as temp, open(outpath, 'wb') as f: #This actually gets obj from archive.
                shutil.copyfileobj(temp, f)
        except Exception as e:
            print(e)
        return outpath
