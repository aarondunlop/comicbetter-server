# Import flask dependencies
from flask import Flask, Blueprint, request, render_template, flash, g, session, redirect, url_for
from flask_mako import MakoTemplates, render_template
from plim import preprocessor

# Import the database object from the main app module
from app import db, app
from app.mod_lib.extractimages import *
from app.models.main import *

mako = MakoTemplates(app)
app.config['MAKO_PREPROCESSOR'] = preprocessor

mod_comic = Blueprint('comic', __name__, url_prefix='/comic')

# Set the route and accepted methods
@mod_comic.route('/read/<int:id>/<int:page>', methods=['GET', 'POST'])
def mod_comic_read(id, page):
    images=[]
    #comics = db.session.query(Comics).filter_by(id=id).first()
    comic = ComicImageExtracter(id)
    pages=comic.extract_comic()
    images = ['/static/comics/' + str(id) + '/' + page for page in pages]
    return render_template('comic/read.mako', app_name=app.config['SITE_NAME'], images=images)


@mod_comic.route('/list', methods=['GET', 'POST'])
def mod_comic_list():
    issues = db.session.query(Issue).all()
    for issue in issues:
        print issue
    return render_template('comic/list.mako', app_name=app.config['SITE_NAME'], issues=issues)
