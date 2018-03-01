from flask import Blueprint, g, request, jsonify, send_file, abort, Response, make_response, redirect, url_for

# Import the database object from the main app module
from cbserver import cbserver

from cbserver.mod_lib.tasks import CoverTasks, LibraryTasks
#from cbserver.mod_lib.tasks import long_task
from cbserver.mod_lib.extractimages import ComicImageExtracter
from cbserver.models import Series, Issue, User # issues_list, series_list, series_list_by_id, issues_list_by_series, series_get_by_seriesid, issue_update_by_id, issues_get_by_issueid, series_update_or_create, Device, sync, synced,
from cbserver.models.database import db_session, init_db, reset_db
from cbserver.mod_lib.cbfile import CBFile
from cbserver.mod_lib.cvfetch import CVFetch
from cbserver.mod_lib.cbcache import CBCache
from cbserver.mod_lib import CBLibrary
import time

from cbserver.mod_comic import ImageGetter
from cbserver.mod_devices import SBDevices
import json
import io
from config import SBConfig

mod_api = Blueprint('api', __name__, url_prefix='/api')

error_text=None

#JWT stuff
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, jwt_refresh_token_required,
    create_refresh_token
)
cbserver.config['JWT_SECRET_KEY'] = SBConfig.get_jwt_secret()
jwt = JWTManager(cbserver)

@cbserver.route('/getfqdn', methods=['GET'])
def get_servername():
    fqdn = SBConfig.get_fqdn()
    return fqdn

@mod_api.route('/init', methods=['POST'])
def cb_init():
    data = request
    username = request.get_json()['username']
    password = request.get_json()['password']
    init_db()
    user = User(name=username, password=password)
    user.update_password()
    db_session.add(user)
    db_session.flush()
    db_session.commit()
    return jsonify('done')


@mod_api.route('/library/covers/issues', methods=['POST'])
def extract_issue_covers():
    issue_covers = CoverTasks().extract_issues()
    return jsonify(issue_covers)

@mod_api.route('/library/covers/series', methods=['POST'])
def extract_series_covers():
    series_covers = CoverTasks().extract_series()
    return jsonify(series_covers)

@mod_api.route('/library/covers/all', methods=['POST'])
def extract_all_covers():
    series_covers = CoverTasks().extract_series()
    issue_covers = CoverTasks().extract_issues()
    return jsonify(series_covers, issue_covers)

@mod_api.route('/library/import', methods=['GET', 'POST'])
#@jwt_required
def mod_scan_library_files():
    if request.method == 'GET':
        result = LibraryTasks().import_library_files()
        return 'done'
    return jsonify('Make sure method is GET')

@mod_api.route('/cache/reset', methods=['POST'])
def clear_cache():
    response = CBCache().nuke()
    return jsonify(response)

@mod_api.route('/reset', methods=['POST'])
def cb_reset():
    reset_db()
    return jsonify('done')

@mod_api.route('/password', methods=['POST'])
def password_set(**kwargs):
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    user=User(username=username, password=password)
    user.update_or_create()
    user.update_password()
    return(username)

@mod_api.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username:
        return jsonify({"msg": "Missing username parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400

    user=User(username=username, password=password)
    if not user.verify_password():
        return jsonify({"msg": "Bad username or password"}), 401
    ret = {
        'access_token': create_access_token(identity=username),
        'refresh_token': create_refresh_token(identity=username)
    }
    return jsonify(ret), 200

@mod_api.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    ret = {
        'access_token': create_access_token(identity=current_user)
    }
    return jsonify(ret), 200

@mod_api.route('/series', methods=['GET', 'POST'])
#@jwt_required
def mod_series_list():
    series=Series(limit = request.args.get('limit', 2500), page=request.args.get('page', 0))
    if request.method == 'GET':
        return jsonify(series.getlist())

@mod_api.route('/series/cover/<int:id>', methods=['GET', 'POST'])
#This will look up the DB record to see if a cover is specified. If not, it will return the one extracted
#from the comic. Params list will list all covers, and param numbers will specify one to be returned.
##@jwt_required
def api_series_return_covers(id):
    global error_text, error_status
    series = db_session.query(Series).filter(Series.id==id).first()
    if series == None:
        error_text = 'Series with that ID does not exist.'
        error_status = 404
        return redirect(url_for('api.api_error_text'))
    imagesize = request.args.get('size')
    if imagesize not in SBConfig.get_image_sizes():
        return jsonify("Please provide a valid size. Options are: " + str(SBConfig.get_image_sizes()))
    coverlist = request.args.get('list')
    if request.method == 'GET' and coverlist is not None: #Return JSON list of covers.
        return (jsonify('please use list attribute.'))
    elif request.method == 'GET' and coverlist is None and imagesize is not None: #Return actual cover, in requested size.
        file = ImageGetter(id=id, size=imagesize, model=series, imagetype='series_cover').get_cover()
        try:
            if file:
                return send_file(
                    file,
                )
            else:
                error_text = 'File could not be extracted. Review logs.'
                error_status = 404
                return redirect(url_for('api.api_error_text'))
        except:
            return 'ok'
            abort(500)

@mod_api.route('/error_text', methods=['GET', 'POST'])
#@jwt_required
def api_error_text():
    global error_text
    if error_text is not None:
        error_text = str(error_text)
    else:
        error_text = ''
    return Response(error_text, status=error_status, mimetype='application/text')

@mod_api.route('/issue/series/<int:id>', methods=['GET', 'POST'])
#@jwt_required
def mod_issues_list_by_series(id):
    print(id, 'loading')
    issues=Issue(limit = request.args.get('limit', 2500), page=request.args.get('page', 0), series_id=id)
    if request.method == 'GET':
        values=['name', 'description', 'id', 'number']
        #issuesjson = [dict(list(zip(values, [row.name, row.description if row.name and row.description else None, row.id, row.number]))) for row in issues.getserieslist()]
        #issuesjson = [dict(list(zip(values, []))) for row in issues.getserieslist()]
        issuesjson = [dict({ key: value for key, value in list(row.__dict__.items()) if not key == "_sa_instance_state" }) for row in issues.getserieslist()]
        return jsonify(issuesjson)
    return('ok')

@mod_api.route('/issue/cover/<int:id>', methods=['GET', 'POST'])
#This will look up the DB record to see if a cover is specified. If not, it will return the one extracted
#from the comic. Params list will list all covers, and param numbers will specify one to be returned.
##@jwt_required
def api_issue_return_covers(id):
    issue=Issue(id=id).find_by_id()
    imagesize = request.args.get('size')
    if imagesize not in SBConfig.get_image_sizes():
        return jsonify("Please provide a valid size. Options are: " + str(SBConfig.get_image_sizes()))
    coverlist = request.args.get('list')
    if request.method == 'GET' and coverlist is not None: #Return JSON list of covers.
        return(jsonify('done'))
    elif request.method == 'GET' and coverlist is None and imagesize is not None: #Return actual cover, in requested size.
        covers = ImageGetter(id=id, size=imagesize, model=issue, imagetype='issue_cover')
        file = covers.get_cover()
        try:
            return send_file(
                file,
            )
        except:
            return jsonify('ok')

@mod_api.route('/issue/image/<int:id>', methods=['GET', 'POST'])
#@jwt_required
def mod_issue_images(id):
    if request.method == 'GET' and not request.args.get('page'):
        pages = ImageGetter(id=id)
        result = pages.get_issue_pages()
        return jsonify(result)
    if request.method == 'GET' and request.args.get('page'):
        page = ImageGetter(id=id, pagenum=int(request.args.get('page', 1)))
        file = page.read_page()
        try:
            return send_file(
                file,
            )
        except:
            return jsonify('ok')
    return 'ok'

@mod_api.route('/cv/search/series', methods=['POST'])
#@jwt_required
def mod_cv_find_series():
    cvid = request.args.get('cvid') if request.args.get('cvid') else None
    print(request.data)
    name = request.get_json()['name'] if request.get_json()['name'] else None
    if request.method == 'POST':
        series = CVFetch(cvid=cvid, name=name).process_cv_get_series_by_name()
    return jsonify(series)

@mod_api.route('/cv/issue/covers/<int:id>', methods=['GET', 'POST'])
#@jwt_required
def mod_cv_get_issue_covers(id):
    if request.method == 'POST' or request.method == 'GET':
        comic = ImageGetter(id=id, imagetype='issue_cover', size=request.args.get('size'))
        result = comic.fetch_cv_covers()
    return jsonify('done')

@mod_api.route('/cv/series/covers/<int:id>', methods=['GET', 'POST']) #Used to grab covers for local series.
#@jwt_required
def mod_cv_get_series_covers(id):
    if request.method == 'POST' or request.method == 'GET':
        comic = ImageGetter(id=id, imagetype='series_cover', size=request.args.get('size'))
        result = comic.fetch_cv_covers()
        return 'ok'

@mod_api.route('/cv/series', methods=['GET'])
#@jwt_required
def mod_get_cv_series_by_cvid():
    cvid = request.args.get('cvid') if request.args.get('cvid') else None
    if request.method == 'GET':
        series = CVFetch(cvid=cvid).fetch_cv_series_record()
        #db_session.commit()
         #jsonify(process_cv_get_series_details_by_id(series_id, cvid))
        return jsonify(series)

@mod_api.route('/cv/series/covers', methods=['GET']) #Used to grab covers for remote series - used in series matching.
#@jwt_required
def mod_get_cover_by_cvid():
    cvid = request.args.get('cvid') if request.args.get('cvid') else None
    if request.method == 'GET':
        file = CVFetch(cvid=cvid).fetch_cv_series_cover_by_cvid()
        try:
            if file:
                return send_file(
                    file,
                )
            else:
                error_text = 'File could not be extracted. Review logs.'
                error_status = 404
                return redirect(url_for('api.api_error_text'))
        except:
            return 'ok'
            abort(500)

@mod_api.route('/issues', methods=['GET', 'POST'])
#@jwt_required
def mod_issue_list():
    if request.method == 'GET':
        issues = Issue(limit = request.args.get('limit', 2500), page=request.args.get('page', 0)).getlist()
        try:
            if issues:
                response = issues
            else:
                response = 'ok'
        except:
            response = 'ok'
        return jsonify(response)

@mod_api.route('/cv/issue/<int:issue_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_scan_library_cv_issue_cvid(issue_id):
    cvid = request.args.get('cvid') if request.args.get('cvid') else None
    #if cvid == None:
    #    return jsonify('Ensure the series has a CVID set.')
    if request.method == 'POST':
        issue = db_session.query(Issue).filter(Issue.id==issue_id).first()
        issue.cvid = issue.series.cvid
        print(issue.cvid)
        issue = CVFetch(model=issue, imagetype='issue_cover').fetch_record()
        return jsonify('done')

@mod_api.route('/cv/series/<int:series_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_scan_library_cv_series_cvid(series_id):
    cvid = request.args.get('cvid') if request.args.get('cvid') else None
    if request.method == 'POST':
        series = db_session.query(Series).filter(Series.id==series_id).first()
        series = CVFetch(model=series, imagetype='series_cover').fetch_record()
        #db_session.commit()
         #jsonify(process_cv_get_series_details_by_id(series_id, cvid))
        return jsonify('done')

#Ensure cvid is set.
@mod_api.route('/series/<int:series_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_series_update_by_id(series_id):
    if request.method == 'POST':
        cvid = int(request.args.get('cvid'))
        print(cvid)
        series = Series(cvid=cvid, id=series_id).update_or_create()
        db_session.commit()
        db_session.flush()
        print(series.cvid)
        return jsonify(series.id)
    if request.method == 'GET':
        series = Series(id=series_id).get_json_by_id()
        return jsonify(series)

@mod_api.route('/series/issues/<int:series_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_series_manage_issues(series_id):
    if request.method == 'POST':
        cvid = request.args.get('cvid') if request.args.get('cvid') else None
        series = db_session.query(Series).filter_by(id = series_id).first()
        for issue in series.issues:
            record = CVFetch(model=issue, imagetype='issue_cover').fetch_record()
        db_session.commit()
        db_session.flush()

        return jsonify('done')
    if request.method == 'GET':
        return redirect(url_for('api.mod_issues_list_by_series', id=series_id))



@mod_api.route('/issue/<int:issue_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_issues_update_by_id(issue_id):
    if request.method == 'POST':
        issue = Issue(id=issue_id).find_by_id()
        issue = db_session.query(Issue).filter(Issue.id==issue_id).first()
        if issue is not None:
            issue
        else:
            issue = Issue()
        for key, value in request.args.items():
            newvalue=value[0] if isinstance(value, list) else value
            setattr(issue, key, newvalue)
        db_session.commit()


    if request.method == 'GET':
        return jsonify({ key: value for key, value in list(Issue(id=issue_id).find_by_id().__dict__.items()) if not key == "_sa_instance_state" })
#        out = 'covers'
#    if request.method == 'GET' and not request.args.get('cover'):
#        return jsonify(get_issue_covers(issue_id))
#    if request.method == 'GET' and request.args.get('cover'):
#        covernumber = request.args.get('cover', 1)
#        comic = ImageGetter(issue_id)
#        file = comic.read_cover(int(covernumber))
#        return send_file(file)
#    return jsonify(out)

#The stuff below might work, but hasn't been tested and may not be needed.

##@jwt_required
@mod_api.route('/process/library/identify/series/<int:series_id>', methods=['GET', 'POST'])
def mod_scan_library_cv_identify_series(series_id):
    if request.method == 'POST':
        series = CVFetch(id = series_id).process_cv_get_series_cvid_by_id()
        response = jsonify(series)
        return response

@mod_api.route('/process/issue/<int:issue_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_process_issue_by_id(issue_id):
    if request.method == 'GET':
        return jsonify(process_issue_by_id(issue_id))

@mod_api.route('/devices/', methods=['GET', 'POST'])
#@jwt_required
def api_devices():
    device = Device()
    if request.method == 'POST':
        return jsonify(device.update_or_create())
    if request.method == 'GET':
        return jsonify(device.get_all())

@mod_api.route('/devices/<int:id>', methods=['GET', 'POST'])
#@jwt_required
def api_device_details(id):
    device = Device(id=id, **request.args)
    if request.method == 'POST':
        return jsonify(device.update_or_create())
    if request.method == 'GET':
        return jsonify(device.get_all())



@mod_api.route('/device/sync/<int:id>', methods=['GET', 'POST'])
#@jwt_required
def api_device_sync(id):
    add = request.args.get('add').split(",") if request.args.get('add') else None
    remove = request.args.get('remove').split(",") if request.args.get('remove') else None
    if request.method == 'POST':
        return jsonify(sync(id, add, remove))
    if request.method == 'GET':
        return jsonify(synced(id))
