import tarfile
from config import SBConfig
import os.path
import shutil
from pathlib import Path, PurePosixPath
import logging
logger = logging.getLogger(__name__)

class SBTar(object):
    def __init__(self, filename, id=None):
        self.fp = tarfile.TarFile(filename, 'r')
        self.id = id

    def listpages(self):
        pagelist = self.fp.infolist()
        #We don't want to extract all (security risks) and we don't want nested archives. Edge cases need dealing with
        #on the client side. Strip hidden files and directories from the path.
        result = []
        for file in pagelist:
            if file.filename.startswith('.') or file.isdir() or file.filename.startswith('_'):
                continue
            else:
                result.append(file)
        pagelist = [PurePosixPath(file.filename).name for file in result]
        return pagelist

    def extract(self):
        outpath=SBConfig.get_read_path()  + '/' + str(self.id) + '/'
        pagelist = self.fp.infolist()
        for file in pagelist:
            if file.filename.startswith('.') or file.isdir() or file.filename.startswith('_'):
                continue
            else:
                outputpath = (outpath + PurePosixPath(file.filename).name)
                try:
                    with self.fp.open(file) as temp, open(outputpath, 'wb') as f:
                        shutil.copyfileobj(temp, f)
                except Exception as e:
                    print(e)
