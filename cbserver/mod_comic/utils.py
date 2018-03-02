import mimetypes
from pathlib import Path, PurePosixPath
from config import SBConfig
import shutil

class CBUtils(object):
    def __init__(self, **kwargs):
        self.kwargs=kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def filter(self):
        result = mimetypes.guess_type(self.filename)
        if result and result[0] and 'image' in result[0]:
            return True
        return False

    def listpages(self):
        result = []
        for file in self.pagelist:
            filter_result = CBUtils(filename=file.filename).filter()
            self.filename = file.filename
            #There's a lot that can go wrong here - this just checks mimetype by ***FILENAME*** May revisit.
            if self.filter():
                result.append(file)
        pagelist = [PurePosixPath(file.filename).name for file in result]
        return pagelist

    def extractpages(self):
        outpath=SBConfig.get_read_path()  + '/' + str(self.archiveinstance.id) + '/'
        for file in self.pagelist:
            self.filename=file.filename
            if True: #self.filter():
                outputpath = (outpath + PurePosixPath(file.filename).name)
                try:
                    with self.archiveinstance.fp.open(file) as temp, open(outputpath, 'wb') as f:
                        shutil.copyfileobj(temp, f)
                except Exception as e:
                    print(e)
