import os
from config import SBConfig
from .sevenz import SevenZFile
from .tar import SBTar
from .rar import SBRar
from .zip import SBZip

from time import sleep
import magic

from natsort import natsorted

from shutil import rmtree

from cbserver.models import Issue #, issue_get_file
from cbserver.models import Series #, series_get_file

from cbserver.models.database import db_session
from cbserver.mod_lib import CBFile, CVFetch

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

    def clean_extracted_comic(self):
        exists = False
        exists = os.path.isdir(self.readpath)
        sleep_time = 10
        num_retries = 5
        if self.readpath and exists:
            for x in range(0, num_retries):
                try:
                    rm_error = None
                    rmtree(self.readpath)
                except Exception as rm_error:
                    logging.error(e, exc_info=True)
                    pass
                if rm_error:
                    print(self.readpath, 'cannot be deleted, retrying.')
                    sleep(sleep_time)  # wait before trying to fetch the data again
                    sleep_time *= 2  # Implement your backoff algorithm here i.e. exponential backoff
                else:
                    break

    def get_size(issue, id, size):
        #covers = ImageGetter(id=id, size=size)
        covers.issue=self.issue
        file = covers.get_issue_cover()
        return file

    def fetch_cv_covers(self):
        #Flow - check if cover exists in DB. If so, check if file still exists. If so, return it. If not, call cvfetch to
        #download it. Todo, list each dir, run posixpath to get stem, and compare each option against array.
        #This will prevent repeat downloads/hammering their API.
        self.dest_path = CBFile(imagetype=self.imagetype, id=self.id).path_getter()
        if self.imagetype is 'series_cover':
            self.model = db_session.query(Series).filter(Series.id==self.id).first()
        elif self.imagetype is 'issue_cover':
            self.model = db_session.query(Issue).filter(Issue.id==self.id).first()
        covers = CVFetch(model=self.model, dest_path=self.dest_path, size=self.size, imagetype = self.imagetype).fetch_covers()
        db_session.commit()

    def get_cover(self):
        #Flow - check if cover exists in DB. If so, check if file still exists. If so, return it. If not, extract
        #first Comic page and return that. Todo, unit testing/input validation.
        CBFile(imagetype=self.imagetype, id=self.id).path_getter()
        converted_size = ('image_' + str(self.size)) #Get the model attribute name for the lookup
        sized_cover = getattr(self.model, converted_size) #This is the value of the model attribute for the right version.
        if sized_cover: #Ensure everything exists before final checks.
            verify_cover = CBFile(dest_path=sized_cover, id=self.id, size=self.size)
            verify_cover_exists = verify_cover.verify_file_present()
        if sized_cover is not None and verify_cover_exists is True:
            filepath = sized_cover
            return filepath
        elif sized_cover is None or verify_cover_exists is False:
            #If this is for the series, we need to find the first issue of that series and do all these steps
            #on that instead.
            if self.imagetype == 'series_cover':
                issue = db_session.query(Issue).join(Issue.series).filter(Issue.series_id==self.id).first() or False
                if issue: #It's possible that a series won't have any local issues.
                    series_cover = ImageGetter(id=issue.id, size=self.size, model=issue, imagetype='issue_cover').get_cover()
                    self.filepath = issue.filepath
                    self.destpath = self.seriescoverpath
                    #filepath = series_cover.extract_issue_cover() #This checks to make sure it doesn't exist first, returns path.
                else:
                    return False
            elif self.imagetype == 'issue_cover':
                #filepath = self.extract_issue_cover() #This checks to make sure it doesn't exist first, returns path.
                self.filepath = self.model.filepath
                self.destpath = self.issuecoverpath
            try:
                #resized_cover = CBFile(source_path=self.filepath, dest_path=self.destpath, size=self.size)
                self.pagenum=0
                CBFile(dest_path=self.readpath).make_dest_path()
                archive = self.get_archive_object_by_mimetype() #Requires filepath to be set.
                archivename = archive.extract()
                extracted_image = CBFile(source_path=archive.extract(), dest_path=self.destpath, size=self.size)
                extracted_image.move_image()
                extracted_image.get_resized_filename() #just getting filename.
                thumbnail = extracted_image.copy_and_resize() #Saving file.
                setattr(self.model, converted_size, thumbnail) #Saves to the correct cover attribute.
                db_session.commit()
                return thumbnail
                return self.model
            except Exception as e:
                logging.error(e, exc_info=True)

    def extract_issue_cover(self):
        #This gets called when no covers exist, or when the existing one is overridden.
        #Gets the first comic page from file.
        self.pagenum = 0 #The API may start at 1 but pagenum starts at 0. Careful.
        source = self.read_page() #Grabs the first file/page.
        cbmover = CBFile(source_path=source, issue=self.model, dest_path=self.issuecoverpath, id=self.id, size=self.size)
        result = cbmover.move_image()
        return result

    def read_page(self):
        CBFile(dest_path=self.readpath).make_dest_path() #Make sure dir exists.
        issue = Issue(id=self.id).find_by_id()
        self.filepath=issue.filepath
        self.pages = self.list_extractor()
        self.pagenum = self.pagenum if self.pagenum < len(self.pages) else (len(self.pages) - 1)
        self.comic_extractor()
        result = self.readpath + natsorted(self.pages)[int(self.pagenum)]
        return self.readpath + natsorted(self.pages)[int(self.pagenum)]

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
        issue = Issue(id=self.id).find_by_id()
        self.filepath=issue.filepath
        self.pages = self.list_extractor()
        return sorted(self.pages)

    def list_extractor(self):
        archive = self.get_archive_object_by_mimetype()
        result = archive.listpages()
        #Zip at least leaves dirs in the list, this messes with successive operations.
        #Pull empty dirs out. Need to catch edge case where an archive contains more
        #than one comic - it'll still work but it would be an unordered mess.
        return result

    def get_archive_object_by_mimetype(self):
        mimetype = magic.from_file(self.filepath, mime=True)
        if mimetype == 'application/x-tar':
            archive = SBTar(filename=self.filepath, id=self.id, pagenum=self.pagenum)
        elif mimetype == 'application/x-rar':
            archive = SBRar(filename=self.filepath, id=self.id, pagenum=self.pagenum)
        elif mimetype == 'application/zip':
            archive = SBZip(filename=self.filepath, id=self.id, pagenum=self.pagenum)
        else:
            archive = False
        return archive

    def comic_extractor(self):
        self.page = self.get_archive_object_by_mimetype()
        try:
            result = self.extract_and_return_page_filename(self.page)
        except:
            result = 'None'
        return result

    def extract_and_return_page_filename(self, page):
        filename = self.readpath + natsorted(self.pages)[int(self.pagenum)]
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
