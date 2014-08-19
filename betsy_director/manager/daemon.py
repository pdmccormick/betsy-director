import logging
import argparse

from .ifdev import IfDevice
from .web import run_webapp

log = logging.getLogger(__name__)

class ManagerDaemon(object):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-I", "--ifdev", type=str, nargs=1, help="Tile connected interface"
    )

    def __init__(self):
        self.ifdev = None

    def run(self, args):
        p = self.parser.parse_args(args)

        if p.ifdev is None:
            self.parser.error("Must specify an interface to listen for tiles on!")

        try:
            self.ifdev = IfDevice(p.ifdev[0])
        except Exception as e:
            log.exception("Error initializing interface")
            return -1

        log.info("using interface %r", self.ifdev)

        run_webapp(self)

        return 0

