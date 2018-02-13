import os
import yaml

with open("/etc/comicbetter/flask.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

class FlaskConfig(object):

    # Define the application directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Define the database - we are working with
    # SQLite for this example
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, cfg['sqlite']['name'])
    DATABASE_CONNECT_OPTIONS = {}

    # Application threads. A common general assumption is
    # using 2 per available processor cores - to handle
    # incoming requests using one and performing background
    # operations using the other.
    THREADS_PER_PAGE = 2

    # Enable protection agains *Cross-site Request Forgery (CSRF)*
    CSRF_ENABLED     = True

    # Use a secure, unique and absolutely secret key for
    # signing the data.
    CSRF_SESSION_KEY = cfg['flask']['csrf']

    # Secret key for signing cookies
    SECRET_KEY = cfg['flask']['secret']
    SALT = cfg['flask']['salt']

    SITE_NAME=cfg['app']['name']

    # Statement for enabling the development environment
    DEBUG = cfg['app']['debug']

class SBConfig(object):
    with open('/etc/comicbetter/config.yml', 'r') as ymlfile:
        sbcfg = yaml.load(ymlfile)

    @staticmethod
    def cfg():
       with open('/etc/comicbetter/config.yml', 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
       return cfg

    @staticmethod
    def get_lib_path():
        return SBConfig.cfg()['directories']['comics']

    @staticmethod
    def get_db_config():
        value = ('sqlite:///' + SBConfig.cfg()['db']['sqlite']['path'])
        print(value)
        return ('sqlite:///' + str(SBConfig.cfg()['db']['sqlite']['path']))

    @staticmethod
    def get_image_path():
        return SBConfig.cfg()['directories']['images']

    @staticmethod
    def get_read_path():
        return SBConfig.cfg()['directories']['read']

    @staticmethod
    def get_api_key():
        return SBConfig.cfg()['comicvine']['apikey']

    @staticmethod
    def get_image_sizes():
        image_formats = SBConfig.cfg()['image_formats']
        return image_formats

    @staticmethod
    def update_cfg(confdict):
        try:
            with open("config.yml", 'w') as outfile:
                yaml.dump(confdict, outfile, default_flow_style=False)
            outfile.close()
        finally:
            print('done')

    @staticmethod
    def get_cfg():
        try:
            with open("config.yml", 'r') as outfile:
                yaml.load(confdict, outfile, default_flow_style=False)
            outfile.close()
        finally:
            print('done')

    @staticmethod
    def get_firebase_conf():
        return SBConfig.cfg()['firebase']

    @staticmethod
    def get_jwt_secret():
        return SBConfig.cfg()['jwt']['secret']
