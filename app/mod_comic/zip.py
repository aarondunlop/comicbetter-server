import zipfile
from config import SBConfig
from pathlib import Path, PurePosixPath
import os.path
import shutil
import logging
logger = logging.getLogger(__name__)

class SBZip(object):
    def __init__(self, filename, id=None):
        self.fp = zipfile.ZipFile(filename, 'r')
        self.id = id

    def listpages(self):
        pagelist = self.fp.namelist()
        #We don't want to extract all (security risks) and we don't want nested archives. Edge cases need dealing with
        #on the client side. Strip hidden files and directories from the path.
        for file in list(pagelist):
            if file.endswith('/') or file.startswith('.'):
                pagelist.remove(file)
        pagelist = [PurePosixPath(file).name for file in pagelist]
        return pagelist

    def extract(self):
        outpath=SBConfig.get_read_path()  + '/' + str(self.id) + '/'
        pagelist = self.fp.infolist()
        for file in pagelist:
            if file.filename.endswith('/') or file.filename.startswith('.'):
                continue
            else:
                outputpath = (outpath + PurePosixPath(file.filename).name)
                try:
                    with self.fp.open(file) as temp, open(outputpath, 'wb') as f:
                        shutil.copyfileobj(temp, f)
                except Exception as e:
                    print(e)
