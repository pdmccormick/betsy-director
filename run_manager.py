#!/usr/bin/env python

import gevent.monkey
gevent.monkey.patch_all()

import os
import sys
import subprocess
import logging

from betsy_director.manager.daemon import ManagerDaemon

logging.basicConfig(format='%(name)s:%(levelname)s %(message)s', level=logging.INFO)
log = logging.getLogger("")

def check_environment():
    """ Check the environment to ensure a smooth ride when running the manager. """

    # Check if root
    if os.getuid() == 0:
        log.critical("Running as root, bypassing further environment checks (this should work, but beware of the security implications of doing so!)")
        return True

    # Check if this Python binary lives on an eCryptFS filesystem
    output = subprocess.check_output([ 'df', '-T', sys.executable ])
    if 'ecryptfs' in output:
        log.critical("The current Python executable %s appears to live on an eCryptFS filesystem, which does not correctly support file capabilities for executables. Please try using a virtualenv built on a non-eCryptFS filesystem instead.", sys.executable)
        return False

    # Check if we have the `getcap` binary installed
    try:
        output = subprocess.check_output([ 'which', 'getcap' ])
    except subprocess.CalledProcessError:
        log.critical("Cannot find the `getcap` executable, you must installation the relevant packages (on Debian/Ubuntu, try `apt-get install libcap2-bin`)")
        return False

    # Check if this Python binary has the correct capabilities
    magic_caps = "cap_net_raw+eip"
    output = subprocess.check_output([ 'getcap', sys.executable ]).strip()
    if magic_caps not in output:
        current_cap = "" if output == "" else output.rsplit('=', 1)[1].strip()
        log.critical("The current Python executable %s does not have the correct capabilities (got `%s`, need `%s`). Please run the following:\n\n\tsudo setcap %s %s\n",
            sys.executable,
            current_cap, magic_caps,
            magic_caps, sys.executable)
        return False

    return True

if __name__ == '__main__':
    if not check_environment():
        if os.environ.get('IGNORE_FAILED_CHECK', None) in [ '1', 'true', 'yes' ]:
            log.warning("Ignoring failed check and continuing anyways (are you sure this is what you want?)")
        else:
            log.critical("Checks failed, aborting. If you know what you're doing, you can bypass this behaviour by setting the environment variable `IGNORE_FAILED_CHECK` to 1.")
            sys.exit(-1)

    d = ManagerDaemon()
    sys.exit(d.run(sys.argv[1:]))

