# Run a test server.
from app import app
app.run(host='0.0.0.0', port=58008, debug=True)
#app.run('0.0.0.0', debug=True, port=8082, ssl_context='adhoc')
