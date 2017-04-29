from flask import Flask
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
from ethereum import slogging

import v0_1


log = slogging.get_logger('node.api')


class APIServer:

    def __init__(self, address, port, raidex_node):
        self.address = address
        self.port = port
        self.raidex_node = raidex_node
        self.app = Flask('Raidex Api')
        CORS(self.app)

    def start(self):
        log.info('Start api at port {}'.format(self.port))
        # build blueprints for desired rest versions:
        bbp_v0_1 = v0_1.build_blueprint(self.raidex_node)
        self.app.register_blueprint(bbp_v0_1)
        # run the rest-server
        rest_server = WSGIServer((self.address, self.port), self.app)
        rest_server.start()
