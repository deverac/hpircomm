import re
import sys

import Rx
import Tx


def _check_prefix(pfx):
    if pfx:
        s = pfx.strip()
        if s.lower() != 'none':
            return s
    return None


def _file(pfx, sfx):
    if pfx:
        mod_pfx = re.sub('[^a-zA-Z0-9\-]', '_', pfx)
        return mod_pfx + sfx
    return None


def _rx_file(pfx):
    return _file(pfx, '_rx.wav')


def _tx_file(pfx):
    return _file(pfx, '_tx.wav')


# For some reason, recording in stereo and then ignoring the left
# channel (which is completely blank) results in the right channel
# being about twice as loud as recording only the right channel (mono).
# I do not know why this is.
# Interestingly, recording in stereo and then 'Mix Stero Down To Mono'
# in Audacity results in a mono track that is half as loud.

class Transport(object):

    def __init__(self, show_init, wav_prefix, framerate, rx_sensitivity):
        sh_init = show_init or False
        frate = framerate or 44100
        rx_sens = rx_sensitivity or 0.11
        sample_width = 2
        channels = 1
        self.rx = Rx.Rx(sample_width, channels, frate, sh_init, _rx_file(wav_prefix), rx_sens)
        self.tx = Tx.Tx(sample_width, channels, frate, sh_init, _tx_file(wav_prefix))


    def start_it(self):
        self.rx.run()
        self.tx.run()


    def stop_it(self):
        self.tx.all_done()
        self.rx.all_done()


    def set_wav_prefix(self, wav_prefix):
        prefix = _check_prefix(wav_prefix)
        self.rx.set_wav_filename(_rx_file(prefix))
        self.tx.set_wav_filename(_tx_file(prefix))


    def peek_bytes(self, n):
        return self.rx.peek_bytes(n)


    def peek_byte(self):
        return self.peek_bytes(1)


    def peek(self):
        return self.peek_bytes(sys.maxsize)


    def read_bytes(self, n):
        return self.rx.read_bytes(n)


    def read_byte(self):
        return self.read_bytes(1)


    def read(self):
        return self.read_bytes(sys.maxsize)


    def clear_buffer(self):
        _ = self.read()


    def write_bytes(self, bytes):
        self.tx.write_bytes(bytes)


    def write_byte(self, byte):
        self.write_bytes([byte])
