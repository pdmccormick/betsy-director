import json
import logging
from collections import OrderedDict

from netaddr import IPAddress, EUI

from ..serializer import JsonSerializer

log = logging.getLogger(__name__)

class GridmapEntry(object):
    def __init__(self, serial, mac, tile_ip, xstart, ystart, xend, yend):
        self.serial = int(serial)
        self.mac = EUI(mac)
        self.tile_ip = IPAddress(tile_ip)
        self.xstart = int(xstart)
        self.ystart = int(ystart)
        self.xend = int(xend)
        self.yend = int(yend)

    def to_object(self):
        data = OrderedDict([
            ( "serial", self.serial ),
            ( "mac", self.mac ),
            ( "tile_ip", self.tile_ip ),
            ( "xstart", self.xstart ),
            ( "ystart", self.ystart ),
            ( "xend", self.xend ),
            ( "yend", self.yend ),
        ])
        return data

    @property
    def cropbox(self):
        return (self.xstart, self.ystart, self.xend, self.yend)

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return u"serial=%d mac=%s tile_ip=%s cropbox=%d,%d,%d,%d" %\
            (self.serial, self.mac, self.tile_ip,
            self.xstart, self.ystart, self.xend, self.yend)

    def __repr__(self):
        return u"<GridmapEntry %s>" % (self,)

class Gridmap(object):
    def __init__(self):
        self.savefile = None

        self.entries = []
        self.mac2entry = {}
        self.serial2entry = {}
        self.tile_ip2entry = {}

        self.size = (-1, -1)

    def clear(self):
        self.entries = []
        self.mac2entry.clear()
        self.serial2entry.clear()
        self.tile_ip2entry.clear()

    def load(self, fobj):
        self.clear()

        data = json.load(fobj)
        for row in data:
            entry = GridmapEntry(**row)
            self.add_entry(entry)

        max_x = max([ entry.xend for entry in self.entries ])
        max_y = max([ entry.yend for entry in self.entries ])
        self.size = (max_x, max_y)

        log.info("loaded map: %d tile%s, pixel size %d*%d",
            len(self.entries), "s" if len(self.entries) > 1 else "",
            self.size[0], self.size[1])

    def add_entry(self, entry):
        self.entries.append(entry)

        self.mac2entry[entry.mac] = entry
        self.serial2entry[entry.serial] = entry
        self.tile_ip2entry[entry.tile_ip] = entry

    def save(self):
        with open(self.savefile, 'w') as fobj:
            fobj.write(self.to_json())

    def to_json(self):
        data = {
            "gridmap": self.entries,
            "display_size": self.size,
        }
        return JsonSerializer.dumps(data)

