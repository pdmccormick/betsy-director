#!/usr/bin/env python

import gevent.monkey
gevent.monkey.patch_all()

import sys
import logging

from betsy_director.manager import ManagerDaemon

logging.basicConfig(format='%(name)s %(levelname)s:%(message)s', level=logging.INFO)

if __name__ == '__main__':
    d = ManagerDaemon()
    sys.exit(d.run(sys.argv[1:]))

