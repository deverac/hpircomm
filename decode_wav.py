import argparse
import wave
import struct

import src.Rx


def get_parser():
    parser = argparse.ArgumentParser(description='Extracts data encoded in WAVFILE')
    parser.add_argument('wavfile', action="store", metavar='WAVFILE', help='WAV file to read')
    parser.add_argument('--calibrate', action="store_true", help='Compute sensitivity')
    parser.add_argument('--sensitivity', action="store", metavar='FLOAT', help='Rx sensitivity [0.0 - 1.0]', type=float)
    parser.add_argument('--showinit', action="store_true", help='Show PyAudio initialization')
    parser.add_argument('--filter', action="store_true", help='Write filtered wav')
    parser.add_argument('--echo', action="store_true", help='Echo decoded data')
    parser.add_argument('--info', action="store_true", help='Display wav info')
    return parser


def compute_sens(bufr, framerate):
    # Pick a point that is about halfway between tho noise floor and
    # the max value.

    # The first half-second may have transients, so ignore it.
    scalar_ignore = int(framerate / 2)

    working = bufr[scalar_ignore:]
    max_val = max(working)
    num_buckets = 32 # 32 is arbitrary.
    bucket_size = max_val / num_buckets

    buckets = []
    for i in range(num_buckets):
        buckets.append(0)

    for w in working:
        if w < 0:
            w = 0
        ind = w / bucket_size
        if ind == num_buckets:
            ind -= 1
        buckets[ind] += 1

    floor_ind = 0
    for i in range(0, num_buckets-1):
        p = (buckets[i+1] + 1) / float(buckets[i] + 1) # Add 1 to avoid zeros.
        if p < 0.0001: # 0.0001 is arbitrary
            floor_ind = i

    bot_ind = floor_ind + 1
    top_ind = num_buckets - 1
    aa = (bucket_size * (top_ind - bot_ind)) / 2
    MAX_SHORT = ((2**16) / 2) - 1
    bb = float(aa) / MAX_SHORT
    return bb


def to_samp(binf, num):
    return struct.unpack('<'+str(num)+'h', binf)


parsed_args = get_parser().parse_args()

wf = wave.open(parsed_args.wavfile, 'rb')
num_frames = wf.getnframes()
frames = wf.readframes(num_frames)
framerate = wf.getframerate()
samp_width = wf.getsampwidth()
num_channels = wf.getnchannels()
wf.close()

if parsed_args.info:
    print 'Num frames: {}'.format(num_frames)
    print 'Framerate: {}'.format(framerate)
    print 'Duration (sec): {}'.format(num_frames / float(framerate))

if framerate != 44100:
    print 'WARN: Framerate is not 44100. Actual: {}'.format(framerate)

if samp_width != 2:
    print 'WARN: Sample width is not 2. Actual: {}'.format(samp_width)

if num_channels != 1:
    print 'ERROR: Number of channels is not 1. Actual: {}'.format(num_channels)
    exit(0)

if parsed_args.sensitivity and parsed_args.calibrate:
    print "ERROR: 'sensitivity' cannot be used with 'calibrate'"
    exit(0)

sens = None

if parsed_args.sensitivity:
    if (parsed_args.sensitivity < 0) or (parsed_args.sensitivity > 1):
        print "ERROR: 'sensitivity' must be >= 0 and <= 1."
        exit(0)
    sens = parsed_args.sensitivity

if parsed_args.calibrate or (sens is None):
    sens = compute_sens(to_samp(frames, num_frames), framerate)
    print ('sensitivity = %.2f'% sens)

rx = src.Rx.Rx(samp_width, num_channels, framerate, parsed_args.showinit, parsed_args.wavfile, sens)

bufr = rx._to_samples(frames, num_frames)

filt_bufr = rx._filtered(bufr, sens)

# Must call protected method _decode_buffer() to
# decode wav data. The return value is not used.
samples_read = rx._decode_buffer(filt_bufr)
bytes = rx.peek_bytes(len(rx.char_buf))
if parsed_args.echo:
    print [chr(b) for b in bytes]

if parsed_args.filter:
    filtfile = 'filt_'+parsed_args.wavfile
    bin = struct.pack('<'+str(len(filt_bufr))+'h', *filt_bufr)
    rx.write_wav(filtfile, bin)
    print 'Wrote {}'.format(filtfile)

outfile = parsed_args.wavfile + '.bin'
f = open(outfile, 'wb')
f.write(bytearray(bytes))
f.close()
print 'Wrote {}'.format(outfile)
