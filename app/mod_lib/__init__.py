import os
import yaml
import json
import requests
import logging

from app.models import Issue, issues_list, series_list, series_list_by_id, issues_list_by_series, get_all_issues, issues_get_by_filename, issues_get_by_issueid, series_match_or_save, issue_match_or_create, issue_update_by_id, series_update_or_create, series_get_by_seriesid, publisher_update_or_create, publisher_get_from_cvid, series_get_from_cvid, issue_update_or_create, issue_get_by_issueid
from app.mod_lib.parse_names.comicimporter import MetadataImporter
from config import SBConfig

from app.mod_lib.parse_names.fnameparser import extract as extractname
from app.mod_lib.parse_names.util import remove_special_characters

from config import SBConfig
apikey = SBConfig.get_api_key()
libfolder = SBConfig.get_lib_path()
folder=""

def scan_library_path():
    comicfilelist = [(file, os.path.join(root,file)) for folder in libfolder for root, dir, files in os.walk(folder) for file in files]
    for comic, filename in comicfilelist:
        ext = os.path.splitext(filename)[-1].lower()
        extensions = ['.jpeg', '.jpg', '.cbr', '.cbt', '.cbz']
        if ext in extensions:
            issue = issue_match_or_create(comic, os.path.dirname(filename))
            process_issue_by_id(issue.id)
    return 'done'

def process_issue_by_id(issue_id):
    issue = issues_get_by_issueid(issue_id)
    extracted = extractname(issue.filename)
    series_name = extracted[0]
    number = extracted[1]
    date = extracted[2]
    series = series_match_or_save(series_name, False)
    issue_update_by_id(issue, number = number, date = date, series_id = series.id)
    #issue_update_by_id(issue)
    #return series_name, number, date

def process_series_by_issue_id(issue_id, force):
    issue = issues_get_by_issueid(issue_id)
    extracted = extractname(issue.filename)
    series_name = remove_special_characters(extracted[0])
    series = series_match_or_save(series_name, force)
    return str(series)

#def process_library_files():
#    comics = get_all_issues()
#    for comic in comics:
#        importer = MetadataImporter()
#        series_name, series_number, series_date = importer.import_comic_records(comic.id, 'basic')
#        match_or_save(series_name, series_number, series_date)
#    return 'ok'

def process_library_cv_issue():
    comics = db.session.query(Issue)
    for comic in comics:
        importer = MetadataImporter()
        importer.import_comic_records(comic, 'cv')
        import_issue_details
    return 'ok'

def process_cv_series_by_id(series_id):
    series = series_get_by_seriesid(series_id)
    print(series.cvid)
    importer = MetadataImporter()
    #importer.import_issue_details(series)
    return 'ok'

def process_cv_get_series_cvid_by_id(series_id):
    series = series_get_by_seriesid(series_id)
    importer = MetadataImporter()
    series_matches = importer.find_series_matches(series)
    importer.import_issue_details(series)
    #cvid = find_issue_id(series.id)
    return 'ok'

def process_cv_get_series_details_by_id(series_id):
    series = series_get_by_seriesid(series_id)
    importer = MetadataImporter()
    details = importer.get_series_details(series)['results']
    publisher = publisher_get_from_cvid(details['publisher']['id'])
    #publisher_update_or_create(pubid, name=publisher['name'])
    series = series_update_or_create(series_id,
        image_small=details['image']['small_url'],
        image_large=details['image']['screen_large_url'],
        image_medium=details['image']['medium_url'],
        image_icon=details['image']['icon_url'],
        image_tiny=details['image']['tiny_url'],
        image_thumb=details['image']['thumb_url'],
        image_super=details['image']['super_url'],
        name=details['name'],
        description=details['description'])
    return 'ok'

def process_cv_get_publisher_details_by_id(issue_id):
    publisher = publisher_get_publisher_by_issueid(issue_id)

def process_cv_get_issue_details_by_id(issue_id):
    issue=issue_get_by_issueid(issue_id)
    importer = MetadataImporter()
    issue.cvid = importer.get_issue_cvid_by_number(issue)
    if isinstance(issue.cvid, int):
        details = importer.get_issue_details(issue)
        issue_update_or_create(issue_id,
            image_small=details['image']['small_url'],
            image_large=details['image']['screen_large_url'],
            image_medium=details['image']['medium_url'],
            image_icon=details['image']['icon_url'],
            image_tiny=details['image']['tiny_url'],
            image_thumb=details['image']['thumb_url'],
            image_super=details['image']['super_url'],
            name=details['name'],
            date=details['cover_date'],
            description=details['description'])
        #process_cv_get_images(issue.id)
        return 'ok'
    else:
        return issue.cvid #This will be the error message

def process_cv_get_issue_covers(id, force=False):
    issue=issue_get_by_issueid(id)
    covers=get_issue_covers(id)
    print(('issue', issue, 'covers', covers, 'force', force))
    make_covers_local(issue, covers, force)
    print(('issue', issue, 'covers', covers, 'force', force))
    #return covers
    return 'ok'

def process_cv_get_series_covers(id, force=False):
    series=series_get_by_seriesid(id)
    covers=get_series_covers(id)
    make_covers_local(series, covers, force)
    return covers

def get_series_covers(id):
    seriespath=SBConfig.get_image_path() + 'series/covers/' + str(id)
    sizes=['small','large','medium','icon','tiny','thumb','super']
    covers=[{'size': size, 'path': seriespath + '/' + size + '.jpg'} for size in sizes]
    return covers

def get_issue_covers(id):
    issuepath=SBConfig.get_image_path() + 'issues/covers/' + str(id)
    sizes=['small','large','medium','icon','tiny','thumb','super']
    covers=[{'size': size, 'path': issuepath + '/' + size + '.jpg'} for size in sizes]
    return covers

def make_covers_local(record, covers, force=False):
    print(record)
    for img in covers:
        print(img)
        if img['size'] == 'small' or img['size'] == 'thumb':
            download_file(getattr(record, 'image_' + img['size']), img['path'], force)
            print(img)
    return covers

def download_file(url, filename, force=False):
    headers = {'User-Agent': 'SomethingBetter v0.1.1'}
    i = requests.get(url, headers=headers)
    make_path(filename)
    with open(filename, 'wb') as f:
        f.write(i.content)

def make_path(filename):
    filepath = os.path.dirname(filename)
    if not os.path.exists(filepath):
        try:
            os.makedirs(filepath)
        except:
            raise