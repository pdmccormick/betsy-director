"""
Display an animated sequence of images on a single tile.

Use like this:

    python seqblast.py $TILE_IP frame_{0}.png 1 120

which will display images frame_1.png, frame_2.png, ..., up to frame_120.png
consecutively in a repeating loop at the default rate of 30 frames per second.
"""

import sys
import socket
import argparse
from time import time, sleep

from PIL import Image

from betsy_director.imaging import ProcessedImage
from betsy_director.protocol import push_frame

def parse_args(options):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tile_ip", type=str, nargs=1, help="Tile IP address")
    parser.add_argument(
        "image_file_fmt", type=str, nargs=1, help="Image filename to display (Python string `format` style, ex: ``file-{0].png``)")
    parser.add_argument(
        "start", type=int, nargs='?', help="Filename start range (inclusive)", default=1)
    parser.add_argument(
        "end", type=int, nargs='?', help="Filename end range (inclusive)", default=1)
    parser.add_argument(
        "-P", "--postscaler", type=float, nargs=1, help="Postscaler value between 0.0 and 100.0")
    parser.add_argument(
        "-G", "--gamma", type=float, nargs=1, help="Gamma exponent (default %.1f)" % (options['gamma'],))
    parser.add_argument(
        "-F", "--fps", type=float, nargs=1, help="Frames per second", default=[ 30.0 ])

    p = parser.parse_args()

    options['tile_ip'] = p.tile_ip[0]
    options['image_file_fmt'] = p.image_file_fmt[0]
    options['start'] = p.start
    options['end'] = p.end

    if p.gamma:
        options['gamma'] = p.gamma[0]

    if p.postscaler:
        options['postscaler'] = p.postscaler[0]

    if p.fps:
        options['fps'] = p.fps[0]

def image_stream(image_file_fmt, start, end, postscaler, gamma, repeat=True):
    frames = []
    size = (18, 18)

    for k in range(start, end + 1):
        image_file = image_file_fmt.format(k)

        fobj = open(image_file, 'rb')
        img = Image.open(fobj)
        if img.size != size:
            img = img.resize(size, resample=Image.ANTIALIAS)

        pimg = ProcessedImage(img, postscaler / 100.0, gamma)
        pimg.process()
        raw_bytes = pimg.crop2raw_bytes(0, 0, size[0], size[1])

        yield raw_bytes
        frames.append(raw_bytes)

    # If repeating, we've already done the work!
    while repeat:
        for frame in frames:
            yield frame

    del frames

if __name__ == '__main__':
    options = {
        'postscaler': 100,
        'gamma': 2.4,
        'image_file_fmt': None,
        'tile_ip': None,
        'start': None,
        'end': None,
        'fps': None,
    }
    parse_args(options)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    period = 1.0 / options['fps']

    # Repeat is ON for any >1 sequence of images
    repeat = (options['start'] != options['end'])

    start = None
    for frame in image_stream(
            options['image_file_fmt'],
            options['start'],
            options['end'],
            options['postscaler'],
            options['gamma'],
            repeat):

        push_frame(sock, options['tile_ip'], frame)

        end = time()
        if start is None:
            # No compensation on first iteration
            start = end

        # Aim for a steady and correct intra-frame period by taking local
        # processing time into account
        sleep(period - (end - start))
        start = time()

