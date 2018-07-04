from flask import Blueprint, g, request, jsonify, send_file, abort, Response, make_response, redirect, url_for

# Import the database object from the main app module
from cbserver import cbserver, celery
#from celery.result import GroupResult

import bisect
from natsort import natsorted
from operator import itemgetter

from cbserver.tasks import extract_image, import_library_files
#from cbserver.mod_lib.tasks import long_task
from cbserver.mod_lib.extractimages import ComicImageExtracter
from cbserver.models import Series, Issue, User # issues_list, series_list, series_list_by_id, issues_list_by_series, series_get_by_seriesid, issue_update_by_id, issues_get_by_issueid, series_update_or_create, Device, sync, synced,
from cbserver.models.database import db_session, init_db, reset_db
from cbserver.models.gcd_database import gcd_db_session, G_Issues, G_Series, G_Publisher, G_Story, G_Brand, G_Language
from cbserver.mod_lib.cbfile import CBFile
from cbserver.mod_lib.cvfetch import CVFetch
from cbserver.mod_lib.cbcache import CBCache
from cbserver.mod_lib import CBLibrary
import time

from celery import group

from cbserver.mod_comic import ImageGetter
from cbserver.mod_devices import SBDevices
import json
import io
import re
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

@mod_api.route('/library/covers/issues', methods=['POST', 'GET'])
def get_issue_covers():
    if request.method == 'POST':
        issue_set = db_session.query(Issue).all()
        sizes = ['small', 'tiny', 'thumb']
        covers=[issue.id for issue in issue_set]
        #[extract_image(id, sizes, 'series_cover', True) for id in covers]
        job = group(extract_image.s(id, sizes, 'issue_cover', True) for id in covers)
        result = job.apply_async()
        result.save()
        return jsonify({}), 202, {'Location': url_for('api.get_issue_covers',
                                                _external=True,
                                                _scheme='https',
                                                 task=result.id)}

    if request.method == 'GET':
        taskid = request.args.get('task', None)
        task = celery.GroupResult.restore(taskid)
        if task is not None:
            results={}
            results['total'] = len(task.results)
            results['processed'] = task.completed_count()
            results['failed'] = task.failed()
            results['waiting'] = task.waiting()
            results['successful'] = task.successful()
            return jsonify(results)
        else:
            return 'Task already completed.'

@mod_api.route('/library/covers/series', methods=['POST', 'GET'])
def get_series_covers():
    if request.method == 'POST':
        series_set = db_session.query(Series).all()
        sizes = ['small', 'tiny', 'thumb']
        covers=[series.id for series in series_set]
        #[extract_image(id, sizes, 'series_cover', True) for id in covers]
        job = group(extract_image.s(id, sizes, 'series_cover', True) for id in covers)
        result = job.apply_async()
        result.save()
        return jsonify({}), 202, {'Location': url_for('api.get_series_covers',
                                                _external=True,
                                                _scheme='https',
                                                 task=result.id)}

    if request.method == 'GET':
        taskid = request.args.get('task', None)
        task = celery.GroupResult.restore(taskid)
        if task is not None:
            results={}
            results['total'] = len(task.results)
            results['processed'] = task.completed_count()
            results['failed'] = task.failed()
            results['waiting'] = task.waiting()
            results['successful'] = task.successful()
            return jsonify(results)
        else:
            return 'Task already completed.'

@mod_api.route('/library/merge/series', methods=['POST'])
def merge_series():
    if request.method == 'POST':
        toid = request.args.get('toid', None)
        fromid = request.args.get('fromid', None)
        to_series = db_session.query(Series).filter(Series.id==toid).first()
        from_series = db_session.query(Series).filter(Series.id==fromid).first()
        #issue = db_session.query(Issue).join(Issue.series).filter(Issue.series_id==self.id).first() or False
        print(to_series.issues)
        print(from_series.issues)
        for issue in from_series.issues:
            issue.series_id=toid
        db_session.delete(from_series)
        db_session.commit()
        db_session.flush()
    return 'done'
    #return jsonify(series_covers, issue_covers)

@mod_api.route('/library/import', methods=['GET', 'POST'])
#@jwt_required
def mod_scan_library_files():
    if request.method == 'POST':
        task = import_library_files.apply_async()
        return jsonify({}), 202, {'Location': url_for('api.mod_scan_library_files',
                                            _external=True,
                                            _scheme='https',
                                             task=task.id)}
    if request.method == 'GET':
        taskid = request.args.get('task', None)
        task = celery.AsyncResult(taskid)
        if task is not None:
            #print(task.__dict__.items())
            return jsonify(task.info, task.state)
    return jsonify(task)

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
    if request.method == 'POST':
        return redirect(url_for('api.mod_series_list', _scheme='https', _external=True))
    series = db_session.query(Series).limit(request.args.get('limit', 2500)).all()

    response=[]
    print(series)
    for row in series:
        response.append({
            'description': row.description,
            'id': row.id,
            'name': row.name,
            'year': row.year
        })
    if request.method == 'GET':
        #return jsonify(natsorted(response, key=itemgetter(*['name'])))
        return jsonify(response)



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
        return redirect(url_for('api.api_error_text', _scheme='https', _external=True))
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
                return redirect(url_for('api.api_error_text', _scheme='https', _external=True))
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
        pages = ImageGetter(id=id, pagenum=0)
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

@mod_api.route('/search/series', methods=['POST'])
#@jwt_required
#Todo, language support - set _en
def mod_search_series():
    content = request.get_json(silent=True)
    if request.method == 'POST':
        response=[]
        name = content.get("name", None)
        id = int(request.args.get("id", default=None))
        if id:
            series = db_session.query(Series).filter(Series.id==id).first()
            name = content.get("name", series.name)
            number=len(series.issues)
            year=content.get("year", None)
            #print(number, series.name, id)
            if not year:
                year=series.year if series.year else '%'
            g_series = gcd_db_session.query(G_Series).join(G_Language).filter(
                G_Series.name.contains(name),
                G_Series.year_began.like(year),
                G_Language.code == 'en'
            ).all()
            sortedlist = natsorted(series.issues, key=lambda k: k.filename)
            print(len(sortedlist))
            sl = []
            for issue in sortedlist:
                num = ''.join(re.findall(r"\D(\d{3})\D", issue.filename))
                sl.append(issue.filepath)
                #print(issue.filepath)
            s = set()
            #duplicates = set(x for x in sl if x in s or s.add(x))
            return jsonify([dict({ key: value for key, value in list(row.__dict__.items()) if not key == "_sa_instance_state" }) for row in g_series])
            #return jsonify([dict({ key: value for key, value in list(row.__dict__.items()) if not key == "_sa_instance_state" }) for row in series.issues])
            #newlist = natsorted(sl)
            #print(len(newlist) != len(set(sortedlist)))
            #print(len(duplicates))
            #print(duplicates)
            return jsonify(g_series)


        elif name:
            g_series = gcd_db_session.query(G_Series).filter(G_Series.name.contains(name)).all()
        else:
            return 'No results found, or Name unset.'
        #issue = db_session.query(Issue).filter(Issue.id==issue_id).first()
        for row in g_series:
            response.append({
                'id': row.id,
                'name': row.name,
                #'year': year_began
            })
        #G_Issues, G_Series, G_Publisher, G_Story, G_Brand
        #Address = Base.classes.address
        #parsedseries=[dict({ key: value for key, value in list(row.__dict__.items()) if not key == "_sa_instance_state" }) for row in series]
    return jsonify(len(response))


@mod_api.route('/cv/search/series', methods=['POST'])
#@jwt_required
def mod_cv_find_series():
    cvid = request.args.get('cvid') if request.args.get('cvid') else None
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
                return redirect(url_for('api.api_error_text', _scheme='https', _external=True))
        except:
            return 'ok'
            abort(500)

@mod_api.route('/issues', methods=['GET', 'POST'])
#@jwt_required
def mod_issue_list():
    if request.method == 'GET':
        issues = Issue(limit = request.args.get('limit', 2500), page=request.args.get('page', 0)).getlist()
        issues = ({ key: value for key, value in list(Issue(id=issue_id).find_by_id().__dict__.items()) if not key == "_sa_instance_state" })

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

@mod_api.route('/cv/series/issues/<int:series_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_cv_get_series_issues(series_id):
    if request.method == 'POST':
        #series = db_session.query(Series).filter_by(id=series_id).first()
        series = db_session.query(Series).filter_by(id = series_id).first()
        issues = db_session.query(Issue).order_by(Issue.number.asc()).filter(Issue.series_id == series_id).all()
        records = CVFetch(model=series, issues=issues).process_cv_get_issue_details()
        #issues = db_session.query(Issue).order_by(Issue.number.asc()).filter(Issue.series_id == series_id).all()
        #for issue in issues:
            #print(issue.number)
        #    if issue.number < 2:
        #        record = CVFetch(model=issue).process_cv_get_issue_details()
        #s.query(Child).join(Parent, Child.parent).filter(Child.name == 'Xavier').filter(Parent.name == 'Chris')

        #for issue in series.issues:
            #record = CVFetch(model=issue, imagetype='issue_cover').fetch_record()
        #    print(issue)
        #db_session.commit()
        #db_session.flush()

        return jsonify('done')
    if request.method == 'GET':
        return redirect(url_for('api.mod_issues_list_by_series', _scheme='https', _external=True, id=series_id))

#Ensure cvid is set.
@mod_api.route('/series/<int:series_id>', methods=['GET', 'POST'])
#@jwt_required
def mod_series_update_by_id(series_id):
    if request.method == 'POST':
        cvid = int(request.args.get('cvid'))
        series = Series(cvid=cvid, id=series_id).update_or_create()
        db_session.commit()
        db_session.flush()
        return jsonify(series.id)
    if request.method == 'GET':
        series = db_session.query(Series).filter(Series.id==series_id).first()
        if series:
            return jsonify({ key: value for key, value in series.__dict__.items() if not key == "_sa_instance_state"})
        else:
            return abort(404)

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
        return redirect(url_for('api.mod_issues_list_by_series', _scheme='https', _external=True, id=series_id))

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
