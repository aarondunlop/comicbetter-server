# Import flask and template operators
from flask import Flask, g, render_template, request, make_response
import logging
from sqlalchemy import create_engine


# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from logging.handlers import RotatingFileHandler
from app.models.database import db_session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.models.database import Session
# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config.FlaskConfig')
app.config.setdefault('MAKO_TRANSLATE_EXCEPTIONS', False)
app.config.setdefault('WEBPACK_MANIFEST_PATH', './build/manifest.json')
# Define the database object which is imported
# by modules and controllers

#db = SQLAlchemy(app)

#Session = sessionmaker(bind=engine)
#session = Session()

@app.before_request
def create_session():
    g.session = Session()
#def log_request_info():
    #app.logger.debug('Request Headers: %s', request.headers)
    #app.logger.debug('Request Method: %s', request.method)
    #app.logger.debug('Request Body: %s', request.get_data())
    #app.logger.debug('Request: %s', request)
    #return request
    #if False is True:

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.after_request
def log_response_info(response):
    #app.logger.debug('Response Headers: %s', response.headers)
    #app.logger.debug('Response Body: %s', response.data.decode('utf-8'))
    #app.logger.debug('Response Status: %s', response.status)
    #app.logger.debug('Response: %s', response)
    return response

@app.errorhandler(500)
def internal_error(exception):
    app.logger.error(exception)
    return make_response('server error', 500)

@app.errorhandler(400)
def handle_bad_request(e):
    app.logger.info('Bad request', e)
    return make_response('bad request', 400)

#if app.debug is not True:
#    import logging
#    from logging.handlers import RotatingFileHandler
#    file_handler = RotatingFileHandler('var/log/server.log', maxBytes=1024 * 1024 * 100, backupCount=20)
#    file_handler.setLevel(logging.ERROR)
#    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#    file_handler.setFormatter(formatter)
#    app.logger.addHandler(file_handler)

# Import a module / component using its blueprint handler variable (mod_auth)
#from app.mod_auth.controllers import mod_auth as auth_module
#from app.mod_lib.controllers import mod_lib as lib_module
#from app.mod_comic.controllers import mod_comic as comic_module
from app.mod_api.controllers import mod_api as api_module

# Register blueprint(s)
#app.register_blueprint(auth_module)
#app.register_blueprint(lib_module)
app.register_blueprint(api_module)
#app.register_blueprint(comic_module)
# app.register_blueprint(xyz_module)
# ..

# Build the database:
# This will create the database file using SQLAlchemy
#db.create_all()
