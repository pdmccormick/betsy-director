import base64
import logging

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import requests
from flask import Flask, Response, render_template, request
from flask.ext.socketio import SocketIO, emit

log = logging.getLogger(__name__)
app = Flask(__name__)

class DirectorSocketIO(SocketIO):
    def __init__(self, app, **kwargs):
        super(DirectorSocketIO, self).__init__(app, **kwargs)

        self.manager = None
        self.num_clients = 0

    def start_background(self, manager):
        self.manager = manager

        # TODO: Start listening for manager activity and `self.emit` it

    def client_connect(self):
        log.info("client connect %r", request)

        self.num_clients += 1

        emit('clients', { 'num_clients': self.num_clients })

    def client_disconnect(self):
        log.info("client disconnect %r", request)

        self.num_clients -= 1
        if self.num_clients < 0:
            self.num_clients = 0

        emit('clients', { 'num_clients': self.num_clients })

socketio = DirectorSocketIO(app)

def run_webapp(manager, host=None, port=None, debug=True):
    socketio.start_background(manager)
    app.debug = debug
    socketio.run(app, host=host, port=port)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gridmap')
def gridmap():
    if request.method == 'GET':
        return Response(socketio.manager.gridmap.to_json(), mimetype='application/json')

@app.route('/frame', methods=[ 'POST' ])
def frame():
    settings = {}

    postscaler = request.form.get('postscaler') or request.args.get('postscaler')
    try:
        if postscaler is not None:
            postscaler = float(postscaler)
            if not (0.0 <= postscaler <= 100.0):
                raise ValueError("Out of range")

            settings['postscaler'] = postscaler
    except ValueError:
        log.error("Invalid postscaler value `%s` (must be a float between 0 and 100 inclusive)", postscaler)

    gamma = request.form.get('gamma') or request.args.get('gamma')
    try:
        if gamma is not None:
            gamma = float(gamma)
            settings['gamma'] = gamma
    except ValueError:
        log.error("Invalid gamma value `%s` (must be a float)", gamma)

    image = request.files.get('image')
    image_base64 = request.form.get('image_base64')
    url = request.form.get('url') or request.args.get('url')
    fobj = None

    if image is not None:
        fobj = image
    elif image_base64 is not None:
        fobj = StringIO(base64.b64decode(image_base64))
    elif url is not None:
        log.info("loading image URL %s", url)
        img_data = requests.get(url).content
        fobj = StringIO(img_data)

    if fobj is not None:
        socketio.manager.blaster.blast_frame(fobj, settings)

    fobj.close()

    return "done"

# SocketIO endpoints
@socketio.on('connect', namespace='/events')
def events_connect():
    socketio.client_connect()

@socketio.on('disconnect', namespace='/events')
def events_disconnect():
    socketio.client_disconnect()

