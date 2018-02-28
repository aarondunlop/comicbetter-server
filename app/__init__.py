from __future__ import absolute_import, unicode_literals
# Import flask and template operators
from flask import Flask, g, render_template, request, make_response
import logging
import random
from sqlalchemy import create_engine
import time

from celery import Celery

# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from logging.handlers import RotatingFileHandler
from cbserver.models.database import db_session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from cbserver.models.database import Session
# Define the WSGI application object
cbserver = Flask(__name__)

# Configurations
cbserver.config.from_object('config.FlaskConfig')
cbserver.config.setdefault('MAKO_TRANSLATE_EXCEPTIONS', False)
cbserver.config.setdefault('WEBPACK_MANIFEST_PATH', './build/manifest.json')
# Define the database object which is imported
# by modules and controllers


#Celery configs
cbserver.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
cbserver.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(cbserver.name, broker=cbserver.config['CELERY_BROKER_URL'])
celery.conf.update(cbserver.config)

@cbserver.before_request
def create_session():
    g.session = Session()
#def log_request_info():
    #cbserver.logger.debug('Request Headers: %s', request.headers)
    #cbserver.logger.debug('Request Method: %s', request.method)
    #cbserver.logger.debug('Request Body: %s', request.get_data())
    #cbserver.logger.debug('Request: %s', request)
    #return request
    #if False is True:

@cbserver.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@cbserver.after_request
def log_response_info(response):
    #cbserver.logger.debug('Response Headers: %s', response.headers)
    #cbserver.logger.debug('Response Body: %s', response.data.decode('utf-8'))
    #cbserver.logger.debug('Response Status: %s', response.status)
    #cbserver.logger.debug('Response: %s', response)
    return response

@cbserver.errorhandler(500)
def internal_error(exception):
    cbserver.logger.error(exception)
    return make_response('server error', 500)

@cbserver.errorhandler(400)
def handle_bad_request(e):
    cbserver.logger.info('Bad request', e)
    return make_response('bad request', 400)

#if cbserver.debug is not True:
#    import logging
#    from logging.handlers import RotatingFileHandler
#    file_handler = RotatingFileHandler('var/log/server.log', maxBytes=1024 * 1024 * 100, backupCount=20)
#    file_handler.setLevel(logging.ERROR)
#    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#    file_handler.setFormatter(formatter)
#    cbserver.logger.addHandler(file_handler)

# Import a module / component using its blueprint handler variable (mod_auth)
#from cbserver.mod_auth.controllers import mod_auth as auth_module
#from cbserver.mod_lib.controllers import mod_lib as lib_module
#from cbserver.mod_comic.controllers import mod_comic as comic_module
from cbserver.mod_api.controllers import mod_api as api_module

# Register blueprint(s)
#cbserver.register_blueprint(auth_module)
#cbserver.register_blueprint(lib_module)
cbserver.register_blueprint(api_module)
#cbserver.register_blueprint(comic_module)
# cbserver.register_blueprint(xyz_module)
# ..

# Build the database:
# This will create the database file using SQLAlchemy
#db.create_all()
