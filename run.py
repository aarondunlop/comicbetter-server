# Run a test server.
import logging
from app import app
from logging.handlers import RotatingFileHandler

if __name__ == '__main__':
    handler = RotatingFileHandler('./var/server.log', backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=58008, debug=False)
