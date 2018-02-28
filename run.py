# Run a test server.
import logging
from app import cbserver
from logging.handlers import RotatingFileHandler

if __name__ == '__main__':
    formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler = RotatingFileHandler('/var/log/comicbetter/server.log', maxBytes=10000000, backupCount=5)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    cbserver.logger.setLevel(logging.DEBUG)
    cbserver.logger.addHandler(handler)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    cbserver.run(host='0.0.0.0', port=58008, debug=True)
