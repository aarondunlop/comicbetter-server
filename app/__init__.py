# Import flask and template operators
from flask import Flask, render_template

import sys

# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open('/var/log/comicbetter/server.log', "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass

sys.stdout = Logger()

# Define the WSGI application object
app = Flask(__name__)
#app.run('0.0.0.0', debug=True, port=8082, ssl_context='adhoc')

# Configurations
app.config.from_object('config.FlaskConfig')
app.config.setdefault('MAKO_TRANSLATE_EXCEPTIONS', False)
app.config.setdefault('WEBPACK_MANIFEST_PATH', './build/manifest.json')

print(app.config)

# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)
#Session = sessionmaker(bind=engine)
#session = Session()

# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

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
db.create_all()
