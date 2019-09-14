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
        outpath, filename = CBUtils(pagenum=self.pagenum, pagelist=pagelist, archiveinstance=self).getpaths()
        try:
            with self.fp.extractfile(filename) as temp, open(outpath, 'wb') as f: #This actually gets obj from archive.
                shutil.copyfileobj(temp, f)
        except Exception as e:
            print(e)
        return outpath            
