import os
from config import SBConfig
from .sevenz import SevenZFile
from .tar import SBTar
from .rar import SBRar
from .zip import SBZip

from app.models import Issue #, issue_get_file
from app.models import Series #, series_get_file

from app.mod_lib import CBFile

import logging
logger = logging.getLogger(__name__)

class ImageGetter(object):
    def __init__(self, **kwargs):
        self.id=''
        self.filepath=''
        self.filetype=''
        self.pages=[]
        self.size=''
        self.covername=''
        self.model=''
        self.covers=''
        self.imagepath=SBConfig.get_image_path()
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.readpath=SBConfig.get_read_path() + '/' + str(self.id) + '/'
        self.seriespath=SBConfig.get_image_path() + '/' + 'series/pages/' + str(self.id) + '/'
        self.issuepath=SBConfig.get_image_path() + '/' + 'issues/pages/' + str(self.id) + '/'
        self.seriescoverpath=SBConfig.get_image_path() + '/' + 'series/covers/' + str(self.id) + '/'
        self.issuecoverpath=SBConfig.get_image_path() + '/' + 'issues/covers/' + str(self.id) + '/'

    def get_size(issue, id, size):
        #covers = ImageGetter(id=id, size=size)
        covers.issue=self.issue
        file = covers.get_issue_cover()
        return file

    def get_cover(self):
        #Flow - check if cover exists in DB. If so, check if file still exists. If so, return it. If not, extract
        #Comic page 1(0) and return that.
        converted_size = ('image_' + str(self.size))
        sized_cover = getattr(self.issue, converted_size)
        if sized_cover: #Ensure everything exists before final checks.
            verify_cover = CBFile(dest_path=sized_cover, id=self.id, size=self.size)
            verify_cover_exists = verify_cover.verify_file_present()
        if sized_cover is not None and verify_cover_exists is True:
            filepath = sized_cover
            return filepath
        elif sized_cover is None or verify_cover_exists is False:
                filepath = self.extract_issue_cover() #This checks to make sure it doesn't exist first, returns path.
                resized_cover = CBFile(source_path=filepath, dest_path=self.issuecoverpath, size=self.size)
                resized_cover.get_resized_filename() #just getting filename.
                thumbnail = resized_cover.copy_and_resize() #Saving file.
                setattr(self.issue, converted_size, thumbnail) #Saves to the correct cover attribute.
                self.issue.issue_commit()
                return thumbnail

    def make_covers_local(self):
        for img in self.covers:
            if img['size'] == 'small' or img['size'] == 'thumb':
                self.download_file_name = getattr(self.issue, 'image_' + img['size'])
                self.download_file(self.download_file_name, img['path'])
        return self.covers

    def get_issue_covers(self):
        issuepath=SBConfig.get_image_path() + 'issues/covers/' + str(id)
        sizes=['small','large','medium','icon','tiny','thumb','super']
        self.covers=[{'size': size, 'path': self.issuecoverpath + '/' + self.covername + '_' + self.size + '.jpg'} for size in sizes]
        return self.covers

    def extract_issue_cover(self):
        #This gets called when no covers exist, or when the existing one is overridden.
        #Gets the first comic page from file.
        self.pagenum = 0 #The API may start at 1 but pagenum starts at 0. Careful.
        source = self.read_page() #Grabs the first file/page.
        #dest_base=(self.issuecoverpath) #Using page0 to denote that the cover is extracted.
        cbmover = CBFile(source_path=source, issue=self.issue, dest_path=self.issuecoverpath, id=self.id, size=self.size)
        result = cbmover.move_image()
        return result

    def fetch_series_cover(self):
        for root, dirs, files in os.walk(self.seriescoverpath):
            file = [(self.seriescoverpath + filename) for filename in files if self.size in filename][0]
            return file

    def fetch_issue_cover(self):
        #Flow - check if cover exists in DB. If so, return that file. If not, return first file in covers dir that
        #matches size. If none exist, extract a cover from the file, save it as 'firstpage'
        #page = ImageGetter(id=id, pagenum=int(request.args.get('page', 1)))
        for root, dirs, files in os.walk(self.issuecoverpath):
            return [(self.issuecoverpath + filename) for filename in files if self.size in filename][0]

    def fetch_series_cover(self):
        for root, dirs, files in os.walk(self.seriescoverpath):
            file = [(self.seriescoverpath + filename) for filename in files if self.size in filename][0]
            return file

    def list_issue_covers(self):
        return self.list_images(self.issuecoverpath)

    def list_series_covers(self):
        return self.list_images(self.seriescoverpath)

    def get_issue_pages(self):
        issue = Issue(id=self.id)
        issue = issue.find_by_id()
        self.filepath=issue.filepath
        self.pages = self.list_extractor()
        return sorted(self.pages)

    def read_page(self):
        CBFile(dest_path=self.readpath).make_dest_path() #Make sure dir exists.
        issue = Issue(id=self.id).find_by_id()
        self.filepath=issue.filepath
        #app.logger.debug('filepath is', self.filepath)
        self.pages = self.list_extractor()
        self.pagenum = self.pagenum if self.pagenum < len(self.pages) else (len(self.pages) - 1)
        self.comicextractor()
        result = self.readpath + sorted(self.pages)[int(self.pagenum)]
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
        #Zip at least leaves dirs in the list, this messes with successive operations.
        #Pull empty dirs out. Need to catch edge case where an archive contains more
        #than one comic - it'll still work but it would be an unordered mess.
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
