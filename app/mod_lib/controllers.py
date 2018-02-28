# Import flask dependencies
from flask import Flask, Blueprint, request, render_template, flash, g, session, redirect, url_for, jsonify
from flask_mako import MakoTemplates, render_template
from plim import preprocessor

from sqlalchemy import *
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Import the database object from the main app module
from app import db, app

from cbserver.mod_lib import libconf, libfolder

# Import module forms
from cbserver.mod_lib.forms import *
from cbserver.mod_lib.extractimages import ComicImageExtracter

# Import utils
from cbserver.mod_lib.parse_names.util import scancomics

# Import module models (i.e. User)
#from cbserver.mod_lib.models import *

from cbserver.mod_lib.parse_names.comicimporter import MetadataImporter
from cbserver.mod_lib.parse_names.fnameparser import extract as extractname

import json
import logging

logger = logging.getLogger(__name__)

mako = MakoTemplates(app)
cbserver.config['MAKO_PREPROCESSOR'] = preprocessor

# Define the blueprint: 'auth', set its url prefix: cbserver.url/auth
mod_lib = Blueprint('lib', __name__, url_prefix='/lib')

# Set the route and accepted methods
@mod_lib.route('/comic/info/<int:id>', methods=['GET', 'POST'])
def comicinfo(id):
    comicquery = db.session.query(Issue).filter_by(id=id).first()
    return render_template('lib/info.mako', issue=comicquery, app_name=cbserver.config['SITE_NAME'])

# Set the route and accepted methods
@mod_lib.route('/comic/list', methods=['GET', 'POST'])
def comiclist():
    #issues = db.session.query(Issue.cover, Issue.name, Issue.number, Issue.filepath).all()
    issues = db.session.query(Issue).all()
    values=['cover', 'name', 'issue', 'path', 'series_name', 'id']
    #Create JSON object for ui grid
    #comics=([('cover', row.cover), ('name', row.name), ('issue', row.), ('path', row.path) for row in issues])
    comics = json.dumps([dict(list(zip(values, [row.cover, row.name, row.number, row.filepath, row.series.name if row.series and row.series.name else None, row.id]))) for row in issues])

    #comics = json.dumps([dict(zip(values, row)) for row in issues])
    if request.method == 'GET':
        values=['name']
        #resultset = [dict(zip(values, row)) for row in comics]
        resultset=[]
    #for comic in issues:
        #importer = MetadataImporter()
        #comicdict=extractname(str(comic.name))
        #importer.import_comic_files(comic.name, issue_series, issue_number, issue_year)
        #importer.import_issue_files(issuedict[0], issuedict[1], issuedict[2])
    return render_template('lib/list.mako', issues=comics, app_name=cbserver.config['SITE_NAME'])
    #return render_template('lib/list.mako', app_name=cbserver.config['SITE_NAME'])

# Set the route and accepted methods
@mod_lib.route('/parse/full', methods=['GET', 'POST'])
def mod_lib_parse_full():
    comics = db.session.query(Issue)
    for comic in comics:
        importer = MetadataImporter()
        importer.import_comic_files(comic.id, 'full')
    #return render_template('lib/scan.mako', app_name=cbserver.config['SITE_NAME'])
    return redirect(url_for('lib.comiclist'))
    #return redirect(url_for('lib.comicnames'))

# Set the route and accepted methods
@mod_lib.route('/comic/issue/cvid', methods=['GET', 'POST'])
def mod_lib_issue_cvid():
    ids = request.args.get('id')
    #if request.method == 'GET':
        #comic = db.session.query(Issue.filter_by(id=id).first()
        #importer = MetadataImporter()
        #importer.find_issue_id(id)
        #return render_template('lib/scan.mako', app_name=cbserver.config['SITE_NAME'])
        #return redirect(url_for('lib.comiclist'))
        #return redirect(url_for('lib.comicnames'))
    #if request.method == 'POST':
    return redirect(url_for('lib.comiclist'))

# Given an ID passed as a param, scrapes the CV API and presents most likely hits. User clicks to select, pops the current id param, and re-iterates.
@mod_lib.route('/comic/series', methods=['GET', 'POST'])
def mod_lib_get_series_id():
    id = ''
    if request.args.get('issueid'):
        id = request.args.get('issueid').split(",")
        id = id.pop(0)
        importer = MetadataImporter()
    if request.args.get('cvid'):
        series_cvid = request.args.get('cvid')
    result=''

    if request.method == 'GET' and id:
        result = importer.find_series_matches(id=id)
        #newresult = importer.set_series_cvid(id, result
        #return render_template('lib/scan.mako', app_name=cbserver.config['SITE_NAME'])
        #return redirect(url_for('lib.comiclist'))
        #return redirect(url_for('lib.comicnames'))
    if request.method == 'POST':
        #result = importer.set_series_cvid(id, series_cvid)
        #return redirect(url_for('lib.comiclist'))
    #return render_template('lib/seriesmatch.mako', comics=result, id=id, app_name=cbserver.config['SITE_NAME'])
    #return render_template('lib/seriesmatch.mako', comics=result, id=id, app_name=cbserver.config['SITE_NAME'])
    return jsonify(result)

# Set the route and accepted methods
@mod_lib.route('/parse/basic', methods=['GET', 'POST'])
def mod_lib_parse_basic():
    ids = ''
    if request.args.get('issueid'):
        ids = request.args.get('issueid').split(",")
        importer = MetadataImporter()
    result=''

    if request.method == 'GET' and ids:
        for id in ids:
            importer.import_comic_records(id, 'basic')
    return redirect(url_for('lib.comiclist'))

# Set the route and accepted methods
@mod_lib.route('/parse/scan', methods=['GET', 'POST'])
def mod_lib_parse_scan():
    importer = MetadataImporter()
    for folder in libfolder:
        scancomics(folder)
        #comic = ComicImageExtracter(comicpath=folder, comicname=comicname)
        #comic.extract_comic()
    #return render_template('lib/scan.mako', app_name=cbserver.config['SITE_NAME'])
    return redirect(url_for('lib.comiclist'))

# Set the route and accepted methods
@mod_lib.route('/image/cover/<int:id>', methods=['GET', 'POST'])
def mod_lib_get_covers(id):
    #if request.args.get('url'):

    if request.method == 'GET':
        issue = db.session.query(Issue).filter_by(id=id).first()
        importer = MetadataImporter()
        importer.import_issue_covers(issue)
        #icon_url, medium_url, tiny_url,small_url, thumb_url,screen_url,super_url

    #elif request.method == 'POST':
    #    issue = db.session.query(Issue).filter_by(id=id).first()

    #return render_template('lib/image.mako', issue=issue, app_name=cbserver.config['SITE_NAME'])
    return redirect(url_for('lib.comiclist'))

# Set the route and accepted methods
@mod_lib.route('/cvscan', methods=['GET', 'POST'])
def mod_lib_cvscan():
    comics = db.session.query(Issue)
    #comics = db.session.query(Issue).all()
    #folders = db.session.query(LibraryFolders).all()
    for comic in comics:
        importer = MetadataImporter()
        importer.import_comic_files(comic, 'cv')
    return render_template('lib/scan.mako', app_name=cbserver.config['SITE_NAME'])
    #return redirect(url_for('lib.comicnames'))

# Set the route and accepted methods
@mod_lib.route('/match', methods=['GET', 'POST'])
def mod_lib_match():
    form = MatchLibraryForm(request.form)
    form.filepath.data='/Users/aaron/comics/the.flintstones/The\ Flintstones\ 001\ \(2016\)\ \(6\ covers\)\ \(digital\)\ \    (Son\ of\ Ultron-Empire\).cbr'
    match=''
    matches=[]
    if form.query.data and form.filepath.data:
        match = matchcomics(query=form.query.data, filepath=form.filepath.data)
        matches=[ (i, match[0][i]) for i, x in enumerate(match[0])]
    matches.insert(0,(0, 'None'))
    form.series.choices = matches
    form.year.choices = matches
    form.issue.choices = matches
    #try:
    return render_template('lib/match.mako', app_name=cbserver.config['SITE_NAME'], form=form, match=match)
    #except:
    #    return redirect(url_for('base.mod_lib_match'))

# Set the route and accepted methods
@mod_lib.route('/config', methods=['GET', 'POST'])
def mod_lib_config():
    form = ConfigLibraryForm(request.form)
    if request.method == 'GET':
        form.librarypath.data=libconf['library']['path']
        return render_template('lib/config.mako', app_name=cbserver.config['SITE_NAME'], form=form)
    if request.method == 'POST':# and form.validate():
        libconf['library']['path']=str(form.librarypath.data)
        updateconf(libconf)
    return render_template('lib/config.mako', app_name=cbserver.config['SITE_NAME'], form=form)
