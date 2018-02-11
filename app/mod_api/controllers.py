from flask import Blueprint, request, jsonify, send_file, abort

# Import the database object from the main app module
from app import db, app
from app.mod_lib.extractimages import ComicImageExtracter
from app.models import issues_list, series_list, series_list_by_id, issues_list_by_series, series_get_by_seriesid, issue_update_by_id, issues_get_by_issueid, series_update_or_create, Device, sync, synced, Series, Issue, User
from app.mod_lib import CBFile, scan_library_path, process_cv_get_series_cvid_by_id, process_cv_get_series_details_by_id, process_cv_get_issue_details_by_id, process_cv_get_issue_covers, process_cv_get_series_covers, get_series_covers
from app.mod_comic import ImageGetter
from app.mod_devices import SBDevices
import json
import io
from config import SBConfig

mod_api = Blueprint('api', __name__, url_prefix='/api')

#JWT stuff
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, jwt_refresh_token_required,
    create_refresh_token
)
app.config['JWT_SECRET_KEY'] = SBConfig.get_jwt_secret()
jwt = JWTManager(app)

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
#@jwt_required
def api_series_return_covers(id):
    app.logger.info(id)
    if request.method == 'GET' and request.args.get('size'):
        covers = ImageGetter(id=id, size=request.args.get('size'))
        file = covers.get_series_cover()
        app.logger.info('ok')
        app.logger.info(file)
        if file:
            return send_file(file)
        else:
            abort(404)

    if request.method == 'GET' and not request.args.get('size'):
        covers = ImageGetter(id=id)
        coverlist = covers.list_issue_covers()
        return jsonify(coverlist)


@mod_api.route('/issue/series/<int:id>', methods=['GET', 'POST'])
#@jwt_required
def mod_issues_list_by_series(id):
    issues=Issue(limit = request.args.get('limit', 2500), page=request.args.get('page', 0), series_id=id)
    if request.method == 'GET':
        values=['name', 'description', 'id']
        issuesjson = [dict(list(zip(values, [row.name, row.description if row.name and row.description else None, row.id]))) for row in issues.getserieslist()]
        return jsonify(issuesjson)

        #return jsonify(issues_list_by_series(series_id))
        #return jsonify({ key: value for key, value in issues_list_by_series(series_id).__dict__.items() if not key == "_sa_instance_state" })
        #x = { key: value for key, value in issue for issue in issues_list_by_series(series_id)}
        #x = issues_list_by_series(series_id)
        #key, value in issue for issue in issues_list_by_series(series_id)
        return 'ok'

@mod_api.route('/issue/cover/<int:id>', methods=['GET', 'POST'])
#This will look up the DB record to see if a cover is specified. If not, it will return the one extracted
#from the comic. Params list will list all covers, and param numbers will specify one to be returned.
##@jwt_required
def api_issue_return_covers(id):
    issue=Issue(id=id).find_by_id()
    imagesize = request.args.get('size')
    coverlist = request.args.get('list')
    issuepath=SBConfig.get_image_path() + 'issues/covers/' + str(id)

    if request.method == 'GET' and coverlist is not None: #Return JSON list of covers.
        return(jsonify('done'))
    elif request.method == 'GET' and coverlist is None and imagesize is not None: #Return actual cover, in requested size.
        covers = ImageGetter(id=id, size=imagesize, issue=issue, imagetype='ImageGetterissue')
        file = covers.get_cover()
        return send_file(
            file,
        )

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
        return send_file(
            file,
        )
    return 'ok'

##@jwt_required
@mod_api.route('/process/library/identify/series/<int:series_id>', methods=['GET', 'POST'])
def mod_scan_library_cv_identify_series(series_id):
    if request.method == 'POST':
        response = jsonify(process_cv_get_series_cvid_by_id(series_id))
        return response

#The stuff below might work, but hasn't been tested and may not be needed.





@mod_api.route('/issues', methods=['GET', 'POST'])
#@jwt_required
def mod_issue_list():
    if request.method == 'GET':
        return jsonify(issues_list())




@mod_api.route('/issue/<int:issue_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_issues_update_by_id(issue_id):
    if request.method == 'POST':
        issue = issues_get_by_issueid(issue_id)
        #app.logger.info('thing is', issue_update_by_id(issue, **request.args))
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


#This sets the series ID + other factors. Tag cvid=x in the URI.
@mod_api.route('/series/<int:series_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_series_update_by_id(series_id):
    if request.method == 'POST':
        series = series_get_by_seriesid(series_id).id
        return jsonify(series_update_or_create(series, **request.args))
    if request.method == 'GET':
        #return jsonify(series_get_by_seriesid(series_id))
        return jsonify({ key: value for key, value in list(series_get_by_seriesid(series_id).__dict__.items()) if not key == "_sa_instance_state" })

@mod_api.route('/process/issue/<int:issue_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_process_issue_by_id(issue_id):
    if request.method == 'GET':
        return jsonify(process_issue_by_id(issue_id))

@mod_api.route('/process/series/issue/<int:issue_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_process_issue_series(issue_id):
    if request.method == 'GET':
        force = False
        if request.args.get('force'):
            force = True if request.args.get('force').lower() == 'true' else False
        return jsonify(process_series_by_issue_id(issue_id, force))

@mod_api.route('/process/library/files', methods=['GET', 'POST'])
#@jwt_required
def mod_scan_library_files():
    if request.method == 'GET':
        result = scan_library_path()
        return 'done'
    return jsonify('Make sure method is GET')

#@mod_api.route('/process/library/cv/series/cvid/<int:series_id>', methods=['GET', 'POST'])
#def mod_scan_library_cv_series(series_id):#
    #if request.method == 'POST':
        #return jsonify(process_cv_get_series_cvid_by_id(series_id, cvid))
#        series = Series(cvid=cvid, id=series_id)#
        #return jsonify(process_cv_get_issue_details_by_id(series_id, cvid))



@mod_api.route('/process/library/cv/series/<int:series_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_scan_library_cv_series_cvid(series_id):
    cvid = request.args.get('cvid') if request.args.get('cvid') else None
    if request.method == 'POST':
         jsonify(process_cv_get_series_details_by_id(series_id, cvid))
    return jsonify('ok')

@mod_api.route('/process/library/cv/issue/<int:issue_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_scan_library_cv_issue_cvid(issue_id):
    if request.method == 'POST':
         process_cv_get_issue_details_by_id(issue_id)
    if request.method == 'GET':
         process_cv_get_issue_details_by_id(issue_id)
    return jsonify('ok')

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



@mod_api.route('/process/library/cv/issue/covers/<int:id>', methods=['GET', 'POST'])
#@jwt_required
def mod_cv_get_issue_covers(id):
    if request.method == 'POST' or request.method == 'GET':
        return(process_cv_get_issue_covers(id))

@mod_api.route('/process/library/cv/series/covers/<int:id>', methods=['GET', 'POST'])
#@jwt_required
def mod_cv_get_series_covers(id):
    if request.method == 'POST' or request.method == 'GET':
        process_cv_get_series_covers(id)
        return 'ok'
