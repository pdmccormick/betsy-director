import logging

from flask import Flask, render_template, request
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

# SocketIO endpoints
@socketio.on('connect', namespace='/events')
def events_connect():
    socketio.client_connect()

@socketio.on('disconnect', namespace='/events')
def events_disconnect():
    socketio.client_disconnect()

