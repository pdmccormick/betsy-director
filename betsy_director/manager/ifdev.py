import errno
import fcntl
import socket
import struct
import logging

from netaddr import EUI

log = logging.getLogger(__name__)

class IfDevice(object):
    fmt     = struct.Struct('256s')
    u32_fmt = struct.Struct('=I')

    SIOCGIFINDEX    = 0x8933
    SIOCGIFHWADDR   = 0x8927
    SIOCGIFNETMASK  = 0x891B
    SIOCGIFBRDADDR  = 0x8919
    SIOCGIFADDR     = 0x8915

    def __init__(self, ifname):
        self.name = ifname
        self.packed_name = self.fmt.pack(self.name[:15])
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            self.ifindex = self.u32_fmt.unpack(self._ioctl(self.SIOCGIFINDEX)[16:20])[0]
        except IOError as e:
            if e.errno == errno.ENODEV:
                raise IOError("Could not find Ethernet device `%s`" % (ifname,))

            raise

        mac_bin = self._ioctl(self.SIOCGIFHWADDR)[18:24]
        mac_str = ("%02x" * 6) % tuple(map(ord, mac_bin))
        self.mac = EUI(mac_str)

        self.netmask = self._ioctl_inet_ntoa(self.SIOCGIFNETMASK, 20)
        self.broadcast = self._ioctl_inet_ntoa(self.SIOCGIFBRDADDR, 20)
        self.addr = self._ioctl_inet_ntoa(self.SIOCGIFADDR, 20)

    def __del__(self):
        self.sock.close()

    def _ioctl(self, req):
        return fcntl.ioctl(self.sock.fileno(), req, self.packed_name)

    def _ioctl_inet_ntoa(self, req, base):
        try:
            raw = self._ioctl(req)
        except IOError as e:
            if e.errno == errno.EADDRNOTAVAIL:
                return None

            raise

        return socket.inet_ntoa(raw[base:base + 4])

    def __unicode__(self):
        return u"name=%s addr=%s netmask=%s broadcast=%s mac=%s" % (self.name, self.addr, self.netmask, self.broadcast, self.mac)

    def __repr__(self):
        return u"<IfDevice %s>" % (self,)

if __name__ == '__main__':
    import sys
    ifdev = IfDevice(sys.argv[1])
    print(ifdev)

