import py7zlib
import logging
logger = logging.getLogger(__name__)

class SevenZFile(object):
    @classmethod
    def is_7zfile(cls, filepath):
        is7z = False
        fp = None
        try:
            fp = open(filepath, 'rb')
            archive = py7zlib.Archive7z(fp)
            n = len(archive.getnames())
            is7z = True
        finally:
            if fp:
                fp.close()
        return is7z

    def __init__(self, filepath):
        fp = open(filepath, 'rb')
        self.archive = py7zlib.Archive7z(fp)

    def extractall(self, path):
        for name in self.archive.getnames():
            outfilename = os.path.join(path, name)
            outdir = os.path.dirname(outfilename)
            outfile = open(outfilename, 'wb')
            outfile.write(self.archive.getmember(name).read())
            outfile.close()
