import os
import logging
import argparse

from .ifdev import IfDevice
from .web import run_webapp
from .gridmap import Gridmap

log = logging.getLogger(__name__)

class ManagerDaemon(object):
    FILENAME_GRIDMAP = "gridmap.json"

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-I", "--ifdev", type=str, nargs=1, help="Tile connected interface")
    parser.add_argument(
        "-D", "--data", type=str, nargs='?', help="Data directory path")

    def __init__(self):
        self.ifdev = None
        self.data_path = None
        self.gridmap = None

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

        log.info("using interface `%s`", self.ifdev.name)
        log.info("using data path %s", self.data_path)

        self.gridmap = Gridmap()
        self.gridmap.savefile = os.path.join(self.data_path, self.FILENAME_GRIDMAP)
        if os.path.exists(self.gridmap.savefile):
            with open(self.gridmap.savefile, 'r') as fobj:
                self.gridmap.load(fobj)

        run_webapp(self)

        return 0

