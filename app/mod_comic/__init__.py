import os
from config import SBConfig
from .sevenz import SevenZFile
from .tar import SBTar
from .rar import SBRar
from .zip import SBZip

from app.models import Issue #, issue_get_file
from app.models import Series #, series_get_file

import logging
logger = logging.getLogger(__name__)

class ImageGetter(object):
    def __init__(self, **kwargs):
        self.filepath=''
        self.pages=[]
        self.imagepath=SBConfig.get_image_path()
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.readpath=SBConfig.get_read_path() + '/' + str(self.id) + '/'
        self.seriespath=SBConfig.get_image_path() + '/' + 'series/pages/' + str(self.id) + '/'
        self.issuepath=SBConfig.get_image_path() + '/' + 'issues/pages/' + str(self.id) + '/'
        self.seriescoverpath=SBConfig.get_image_path() + '/' + 'series/covers/' + str(self.id) + '/'
        self.issuecoverpath=SBConfig.get_image_path() + '/' + 'issues/covers/' + str(self.id) + '/'

    def get_issue_cover(self):
        for root, dirs, files in os.walk(self.issuecoverpath):
            return [(self.issuecoverpath + filename) for filename in files if self.size in filename][0]

    def get_series_cover(self):
        for root, dirs, files in os.walk(self.seriescoverpath):
            print('there')
            print((self.seriescoverpath))
            print(self)
            print((root, dirs, files))
            file = [(self.seriescoverpath + filename) for filename in files if self.size in filename][0]
            print(file)
            return file

    def list_issue_covers(self):
        return self.list_images(self.issuecoverpath)

    def list_series_covers(self):
        return self.list_images(self.seriescoverpath)

    def check_cover_exists(self):
        if os.path.exists(filename):
            return True
        return False

    def get_issue_pages(self):
        issue = Issue(id=self.id)
        issue = issue.find_by_id()
        print(issue.id)
        self.filepath=issue.filepath
        print(self.filepath)
        self.pages = self.list_extractor()
        return sorted(self.pages)

    def read_page(self):
        issue = Issue(id=self.id)
        issue = issue.find_by_id()
        self.filepath=issue.filepath
        print('filepath is', self.filepath)
        self.pages = self.list_extractor()
        self.pagenum = self.pagenum if self.pagenum < len(self.pages) else (len(self.pages) - 1)
        self.comicextractor()
        result = self.readpath + sorted(self.pages)[int(self.pagenum)]
        print(result)
        return self.readpath + sorted(self.pages)[int(self.pagenum)]

    def list_extractor(self):
        extension = os.path.splitext(self.filepath)[1]
        if extension == '.cbt':
            archive = SBTar(self.filepath)
            result = archive.listpages()
        elif extension == '.cbr':
            archive = SBRar(filename=self.filepath)
            result = archive.listpages()
        elif extension == '.cbz':
            archive = SBZip(self.filepath)
            result = archive.listpages()
        else:
            result = ''
            print(archive, result)
        return result

    def comicextractor(self):
        result = ''
        extension = os.path.splitext(self.filepath)[1]
        if extension == '.cbt':
            self.page = SBTar(filename=self.filepath, id=self.id)
        elif extension == '.cbr':
            self.page = SBRar(filename=self.filepath, id=self.id)
        elif extension == '.cbz':
            self.page = SBZip(filename=self.filepath, id=self.id)
        try:
            result = self.check_exists(self.page)
        except:
            result = 'None'
        return result

    def check_exists(self, page):
        filename = self.readpath + sorted(self.pages)[int(self.pagenum)]
        print(filename)
        if not os.path.exists(filename):
            self.page.extract()
        return True

    def list_images(self, filepath):
        try:
            files = os.listdir(filepath)
            for filename in files:
                ext = os.path.splitext(filename)[-1].lower()
                extensions = ['.jpeg', '.jpg', '.png']
                if ext in extensions:
                    filelist.append(filename)
            return filelist
        except:
            return False
#.cb7 7z
#.cba ACE
#.cbr RAR
#.cbt TAR
#.cbz ZIP
