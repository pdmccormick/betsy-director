import sys
import socket
import select
from time import sleep
from struct import Struct
from collections import namedtuple

from crc32 import crc32
from protocol import chunk, Protocol

FlashXmitProgress = namedtuple('FlashXmitProgress', 'num total offs block_len block_crc32')

class FlashWrite(object):
    BLOCK_SIZE  = 1024

    CMD_FLASHWRITE = "flashwrite {name} 0x{crc32:08x} {offs};"
    RESPONSE_BAD_MEMORY = "bad-memory;"

    def __init__(self, sock):
        self.sock = sock

        self.name = None
        self.data = None
        self.data_crc32 = None
        self.blocks_and_crc32 = None

    def load_blob(self, name, data):
        self.name = name
        self.data = data
        self.data_crc32 = crc32(data)
        self.blocks_and_crc32 = [ (blk, crc32(blk)) for blk in chunk(self.data, self.BLOCK_SIZE) ]

    def send_to(self, ip):
        offs = 0
        num = 0
        total = len(self.blocks_and_crc32)

        for block, block_crc32 in self.blocks_and_crc32:
            block_len = len(block)

            bufs = [ self.CMD_FLASHWRITE.format(name=self.name, crc32=block_crc32, offs=offs) + block ]
            Protocol.sendto(self.sock, ip, bufs)

            pkt, addr = sock.recvfrom(1500)
            bufs = Protocol.unpack(pkt)

            if bufs[0].startswith(self.RESPONSE_BAD_MEMORY):
                bad = bufs[0][len(self.RESPONSE_BAD_MEMORY):]
                diffs = [ (i,a,b) for (i,(a,b)) in enumerate(zip(block, bad)) if a != b ]
                raise IOError("Bad memory at offset %d: diffs %s" % (offs, diffs))

            yield FlashXmitProgress(num, total, offs, block_len, block_crc32)

            num += 1
            offs += block_len

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "usage: %s tile_ip flash_name file_path" % (sys.argv[0],)
        sys.exit(-1)

    tile_ip, flash_name, file_path = sys.argv[1:4]

    print "sending `%s` (%s)" % (flash_name, file_path)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fw = FlashWrite(sock)
    with open(file_path, 'rb') as fobj:
        blob = fobj.read()
        fw.load_blob(flash_name, blob)
        try:
            for progress in fw.send_to(tile_ip):
                percent = (progress.num + 1.0) / progress.total * 100
                line = "\rFlashing %s... %.1f%%" % (tile_ip, percent)
                sys.stdout.write(line)
                sys.stdout.flush()
        except:
            raise
        finally:
            print ""

