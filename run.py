# Run a test server.
import logging
from app import app
#app.run('0.0.0.0', debug=True, port=8082, ssl_context='adhoc')

def setup_logger():
    # create logger
    logger = logging.getLogger('project')
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel('DEBUG')

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

if __name__ == '__main__':
     setup_logger()
     app.run(host='0.0.0.0', port=58008, debug=True)
