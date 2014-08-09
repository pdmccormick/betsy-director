from struct import Struct

def chunk(data, stride):
    return [ data[i:i + stride] for i in range(0, len(data), stride) ]

class Protocol(object):
    UDP_PORT            = 48757 # ==0xBE75
    MAGIC_ICMP_SIZE     = 183   # ==0xB7
    FRAME_CHUNK_SIZE    = 1024

    fmt_header  = Struct("<HH") # len, seq
    fmt_buf     = Struct("<H")  # len, data[len]

    @classmethod
    def pack(cls, seq, bufs):
        packed_bufs = "".join([ (cls.fmt_buf.pack(len(b)) + b) for b in bufs ])
        pkt_len = cls.fmt_header.size + len(packed_bufs)
        return cls.fmt_header.pack(pkt_len, seq) + packed_bufs

    @classmethod
    def unpack(cls, pkt):
        pkt_len, seq = cls.fmt_header.unpack(pkt[0:cls.fmt_header.size])
        pkt = pkt[cls.fmt_header.size:]

        bufs = []

        while len(pkt) > 0:
            buf_len, = cls.fmt_buf.unpack(pkt[0:cls.fmt_buf.size])
            pkt = pkt[cls.fmt_buf.size:]
            bufs.append(pkt[:buf_len])
            pkt = pkt[buf_len:]

        return bufs

    @classmethod
    def sendto(cls, sock, ip, bufs, seq=0):
        sock.sendto(cls.pack(seq, bufs), (ip, cls.UDP_PORT))

    @classmethod
    def push_dpc_frame(cls, sendto, frame, seq=1):
        for p in chunk(frame, self.FRAME_CHUNK_SIZE):
            bufs = [ "dpc data %d;%s" % (offs, p) ]
            sendto(cls.pack(seq, bufs))
            offs += len(p)
            seq += 1

        return seq

    @classmethod
    def push_dpc_upload(cls, sendto, seq=0):
        bufs = [ "dpc upload" ]
        sendto(Protocol.pack(seq, bufs))

        return seq + 1

def push_frame(sock, dest, frame, seq=0):
    sendto = lambda buf: sock.sendto(buf, dest)

    seq = Protocol.push_dpc_frame(sendto, frame, seq)
    Protocol.push_dpc_upload(sendto, seq)

