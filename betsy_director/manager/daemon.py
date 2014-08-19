import os
import socket
import logging
import argparse

from ..protocol import Protocol

from .ifdev import IfDevice
from .web import run_webapp
from .gridmap import Gridmap
from .blaster import Blaster

log = logging.getLogger(__name__)

class ManagerDaemon(object):
    FILENAME_GRIDMAP = "gridmap.json"

    DEFAULT_WEB = "127.0.0.1:8080"

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-I", "--ifdev", type=str, nargs=1, help="Tile connected interface")
    parser.add_argument(
        "-D", "--data", type=str, nargs='?', help="Data directory path")
    parser.add_argument(
        "-W", "--web", type=str, nargs='?', help="Web server listening `host:port`, defaults to `127.0.0.1:8080`")

    def __init__(self):
        self.ifdev = None
        self.data_path = None
        self.gridmap = None
        self.blaster = None
        self.sock = None
        self.web_bind = self.DEFAULT_WEB

    def run(self, args):
        p = self.parser.parse_args(args)

        if p.ifdev is None:
            self.parser.error("Must specify an interface to listen for tiles on!")

        try:
            self.ifdev = IfDevice(p.ifdev[0])
        except Exception as e:
            log.exception("Error initializing interface")
            return -1

        if p.data is None:
            # if   __file__  is betsy-director/betsy_director/manager/daemon.py
            # then data_path is betsy-director/data
            self.data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        else:
            self.data_path = p.data

        if p.web is not None:
            self.web_bind = p.web

        log.info("using interface `%s`", self.ifdev.name)
        log.info("using data path %s", self.data_path)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((str(self.ifdev.addr), Protocol.UDP_PORT))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.gridmap = Gridmap()
        self.gridmap.savefile = os.path.join(self.data_path, self.FILENAME_GRIDMAP)
        if os.path.exists(self.gridmap.savefile):
            with open(self.gridmap.savefile, 'r') as fobj:
                self.gridmap.load(fobj)

        self.blaster = Blaster(self.sock, self.ifdev, self.gridmap)

        host, port = self.web_bind.split(":", 1)
        port = int(port)
        run_webapp(self, host=host, port=port)

        return 0

