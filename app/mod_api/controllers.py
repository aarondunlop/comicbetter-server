# Import flask dependencies
#from flask import Flask, Blueprint, request, render_template, flash, g, session, redirect, url_for
#from plim import preprocessor
from flask import Blueprint, request, jsonify, send_file, abort

#from bluemonk.models.hotel import Hotel

# Import the database object from the main app module
from app import db, app
from app.mod_lib.extractimages import *
from app.models import issues_list, series_list, series_list_by_id, issues_list_by_series, series_get_by_seriesid, issue_update_by_id, issues_get_by_issueid, series_update_or_create, Device, sync, synced, Series, Issue
from app.mod_lib import scan_library_path, process_series_by_issue_id, process_cv_get_series_cvid_by_id, process_cv_get_series_details_by_id, process_cv_get_issue_details_by_id, process_cv_get_issue_covers, process_cv_get_series_covers, get_issue_covers, get_series_covers
from app.mod_comic import ImageGetter
from app.mod_devices import SBDevices
mod_api = Blueprint('api', __name__, url_prefix='/api')
import json
from config import SBConfig

#Auth
import pyrebase
from flask_jwt import JWT, jwt_required

firebaseconfig = SBConfig.get_firebase_conf()

firebase = pyrebase.initialize_app(firebaseconfig)
auth = firebase.auth()

class FBUser(object):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return "User(id='%s')" % self.id

def verify(username, password):
    if not (username and password):
        return False
    if auth.get(username) == password:
        return FBUser(id=123)

def identity(payload):
    user_id = payload['identity']
    return {"user_id": user_id}

jwt = JWT(app, verify, identity)

@mod_api.route('/auth', methods=['POST'])
#@jwt_required()
def mod_auth():
    print(request.json)
    return 'ok'
    #user = auth.sign_in_with_email_and_password('testing@tuxbiker.com', 'testing')
    #user2 = auth.get_account_info(user['idToken'])
    #print(user)
    #print(user2)
    #return jsonify(user)


@mod_api.route('/issues', methods=['GET', 'POST'])
def mod_issue_list():
    if request.method == 'GET':
        return jsonify(issues_list())

@mod_api.route('/issue/series/<int:id>', methods=['GET', 'POST'])
def mod_issues_list_by_series(id):
    issues=Issue(limit = request.args.get('limit', 5), page=request.args.get('page', 0), series_id=id)
    if request.method == 'GET':
        values=['name', 'description', 'id']
        issuesjson = [dict(list(zip(values, [row.name, row.description if row.name and row.description else None, row.id]))) for row in issues.getserieslist()]
        print(issuesjson)
        return jsonify(issuesjson)

        #return jsonify(issues_list_by_series(series_id))
        #return jsonify({ key: value for key, value in issues_list_by_series(series_id).__dict__.items() if not key == "_sa_instance_state" })
        #x = { key: value for key, value in issue for issue in issues_list_by_series(series_id)}
        #x = issues_list_by_series(series_id)
        #key, value in issue for issue in issues_list_by_series(series_id)
        return 'ok'

@mod_api.route('/issue/<int:issue_id>', methods=['GET', 'POST'])
def mod_issues_update_by_id(issue_id):
    if request.method == 'POST':
        issue = issues_get_by_issueid(issue_id)
        #print('thing is', issue_update_by_id(issue, **request.args))
        #return jsonify({ key: value for key, value in issue_update_by_id(issue, **request.args).__dict__.items() if not key == "_sa_instance_state" })
        return jsonify('saved')
    if request.method == 'GET':
        return jsonify({ key: value for key, value in list(issues_get_by_issueid(issue_id).__dict__.items()) if not key == "_sa_instance_state" })
#        out = 'covers'
#    if request.method == 'GET' and not request.args.get('cover'):
#        return jsonify(get_issue_covers(issue_id))
#    if request.method == 'GET' and request.args.get('cover'):
#        covernumber = request.args.get('cover', 1)
#        comic = ImageGetter(issue_id)
#        file = comic.read_cover(int(covernumber))
#        return send_file(file)
#    return jsonify(out)


@mod_api.route('/series', methods=['GET', 'POST'])
def mod_series_list():
    series=Series(limit = request.args.get('limit', 2500), page=request.args.get('page', 0))
    if request.method == 'GET':
        return jsonify(series.getlist())

#This sets the series ID + other factors. Usually tag cvid=x in the URI.
@mod_api.route('/series/<int:series_id>', methods=['GET', 'POST'])
def mod_series_update_by_id(series_id):
    if request.method == 'POST':
        series = series_get_by_seriesid(series_id).id
        return jsonify(series_update_or_create(series, **request.args))
    if request.method == 'GET':
        #return jsonify(series_get_by_seriesid(series_id))
        return jsonify({ key: value for key, value in list(series_get_by_seriesid(series_id).__dict__.items()) if not key == "_sa_instance_state" })

@mod_api.route('/process/issue/<int:issue_id>', methods=['GET', 'POST'])
def mod_process_issue_by_id():
    if request.method == 'GET':
        return jsonify(process_issue_by_id(issue_id))

@mod_api.route('/process/series/issue/<int:issue_id>', methods=['GET', 'POST'])
def mod_process_issue_series(issue_id):
    if request.method == 'GET':
        force = False
        if request.args.get('force'):
            force = True if request.args.get('force').lower() == 'true' else False
        return jsonify(process_series_by_issue_id(issue_id, force))

@mod_api.route('/process/library/files', methods=['GET', 'POST'])
def mod_scan_library_files():
    if request.method == 'GET':
        return jsonify(scan_library_path())

@mod_api.route('/process/library/cv/series/cvid/<int:series_id>', methods=['GET', 'POST'])
def mod_scan_library_cv_series(series_id):
    if request.method == 'GET':
        return jsonify(process_cv_get_series_cvid_by_id(series_id))

@mod_api.route('/process/library/cv/series/<int:series_id>', methods=['GET', 'POST'])
def mod_scan_library_cv_series_cvid(series_id):
    if request.method == 'POST':
         process_cv_get_series_details_by_id(series_id)
    return jsonify('ok')

@mod_api.route('/process/library/cv/issue/<int:issue_id>', methods=['GET', 'POST'])
def mod_scan_library_cv_issue_cvid(issue_id):
    if request.method == 'POST':
         process_cv_get_issue_details_by_id(issue_id)
    if request.method == 'GET':
         process_cv_get_issue_details_by_id(issue_id)
    return jsonify('ok')

@mod_api.route('/devices/', methods=['GET', 'POST'])
def api_devices():
    device = Device()
    if request.method == 'POST':
        return jsonify(device.update_or_create())
    if request.method == 'GET':
        return jsonify(device.get_all())

@mod_api.route('/devices/<int:id>', methods=['GET', 'POST'])
def api_device_details(id):
    device = Device(id=id, **request.args)
    if request.method == 'POST':
        return jsonify(device.update_or_create())
    if request.method == 'GET':
        return jsonify(device.get_all())

@mod_api.route('/device/sync/<int:id>', methods=['GET', 'POST'])
def api_device_sync(id):
    add = request.args.get('add').split(",") if request.args.get('add') else None
    remove = request.args.get('remove').split(",") if request.args.get('remove') else None
    if request.method == 'POST':
        return jsonify(sync(id, add, remove))
    if request.method == 'GET':
        return jsonify(synced(id))

@mod_api.route('/issue/cover/<int:id>', methods=['GET', 'POST'])
def api_issue_return_covers(id):
    if request.method == 'GET' and request.args.get('size'):
        covers = ImageGetter(id=id, size=request.args.get('size'))
        file = covers.get_issue_cover()
        if file:
            return send_file(file)
        else:
            abort(404)

    if request.method == 'GET' and not request.args.get('size'):
        covers = ImageGetter(id=id)
        coverlist = covers.list_issue_covers()
        if coverlist:
            return jsonify(coverlist)
        else:
            return jsonify()

@mod_api.route('/series/cover/<int:id>', methods=['GET', 'POST'])
def api_series_return_covers(id):
    print(id)
    if request.method == 'GET' and request.args.get('size'):
        covers = ImageGetter(id=id, size=request.args.get('size'))
        file = covers.get_series_cover()
        print('ok')
        print(file)
        if file:
            return send_file(file)
        else:
            abort(404)

    if request.method == 'GET' and not request.args.get('size'):
        covers = ImageGetter(id=id)
        coverlist = covers.list_issue_covers()
        return jsonify(coverlist)

@mod_api.route('/issue/image/<int:id>', methods=['GET', 'POST'])
def mod_issue_images(id):
    if request.method == 'GET' and not request.args.get('page'):
        pages = ImageGetter(id=id)
        return jsonify(pages.get_issue_pages())
    if request.method == 'GET' and request.args.get('page'):
        page = ImageGetter(id=id, pagenum=int(request.args.get('page', 1)))
        file = page.read_page()
        return send_file(file)
    return 'ok'

@mod_api.route('/process/library/cv/issue/covers/<int:id>', methods=['GET', 'POST'])
def mod_cv_get_issue_covers(id):
    if request.method == 'POST' or request.method == 'GET':
        #print 'this works.'
        return(process_cv_get_issue_covers(id))

@mod_api.route('/process/library/cv/series/covers/<int:id>', methods=['GET', 'POST'])
def mod_cv_get_series_covers(id):
    if request.method == 'POST' or request.method == 'GET':
        process_cv_get_series_covers(id)
        return 'ok'