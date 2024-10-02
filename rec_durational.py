#!/usr/bin/env python3

"""Create continuous recordings with a set duration.

The soundfile module (https://python-soundfile.readthedocs.io/)
has to be installed!

"""

"""Adapted from these example files

- https://github.com/spatialaudio/python-sounddevice/blob/master/examples/rec_unlimited.py
- https://github.com/spatialaudio/python-sounddevice/blob/master/examples/asyncio_coroutines.py

"""

import argparse
import sys

import sounddevice as sd
import soundfile as sf
import numpy as np  # Make sure NumPy is loaded before it is used in the callback

import datetime
from datetime import datetime

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    'filename', nargs='?', metavar='FILENAME',
    help='audio file to store recording to')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-r', '--samplerate', type=int, default=48000, help='sampling rate')
parser.add_argument(
    '-c', '--channels', type=int, default=1, help='number of input channels')
parser.add_argument(
    '-t', '--subtype', type=str, default="PCM_24", help='sound file subtype (e.g. "PCM_24")')
parser.add_argument(
    '-dur', '--duration', type=int, default=60, help='duration of segments")')
args = parser.parse_args(remaining)

frames = args.samplerate * args.duration


def record_unlimited():
    idx = 0
    buffer = np.empty((frames, args.channels), dtype='float32')

    def callback(indata, frame_count, time, status):
        """This is called (from a separate thread) for each audio block."""

        nonlocal idx
        
        if status:
            print(status, file=sys.stderr)


        remainder = len(buffer) - idx
        print(idx, remainder, frame_count, len(buffer), buffer.shape)
        if remainder == 0:
            write_file(buffer)
            idx = 0

        indata = indata[:remainder]
        buffer[idx:idx + len(indata)] = indata
        idx += len(indata)

    with sd.InputStream(samplerate=args.samplerate, device=args.device,
                        channels=args.channels, callback=callback, blocksize=0):
        
        print('#' * 80)
        print('press Ctrl+C to kill the recording process')
        print('#' * 80)

        while True:
            x = 0

def write_file(buffer): 
    # schedule the next call first
    print('writing')

    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info['default_samplerate'])
    if args.filename is None:
        date_format="%Y%m%d-%H%M%S"
        timestamp = datetime.now().strftime(date_format)
        filename = '' + timestamp + '.wav'

    sf.write(filename, buffer, samplerate=args.samplerate, subtype=args.subtype)

try:
    record_unlimited()
except KeyboardInterrupt:
    print('\nRecording finished.')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))