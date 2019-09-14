import mimetypes
from pathlib import Path, PurePosixPath
from config import SBConfig
import shutil
from natsort import natsorted

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

    def filenamepagelist(self): #This is to return the full path.
        result = []
        for file in self.pagelist:
            filter_result = CBUtils(filename=file.filename).filter()
            self.filename = file.filename
            #There's a lot that can go wrong here - this just checks mimetype by ***FILENAME*** May revisit.
            if self.filter():
                result.append(file)
        nativepagelist = [file.filename for file in result]
        return nativepagelist

    def listpages(self):
        pagelist = [PurePosixPath(file).name for file in self.filenamepagelist()]
        return pagelist

    def getpaths(self):
        result = []
        self.readpath = SBConfig.get_read_path()
        filename = self.filenamepagelist()[self.pagenum]
        outpath=self.readpath  + '/' + str(self.archiveinstance.id) + '/'
        fullpath = (outpath + PurePosixPath(filename).name)
        return fullpath, filename
        #print(outputpath, self.fileobj)

    def extractpages(self):
        outpath=SBConfig.get_read_path()  + '/' + str(self.archiveinstance.id) + '/'
        for file in self.pagelist:
            self.filename=file.filename
            if self.filter():
                outputpath = (outpath + PurePosixPath(file.filename).name)
                try:
                    with self.archiveinstance.fp.open(file) as temp, open(outputpath, 'wb') as f:
                        shutil.copyfileobj(temp, f)
                except Exception as e:
                    print(e)
