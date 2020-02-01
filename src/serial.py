import sys
import time
import util

import log

from util import ConfigVal as CV
from util import CmdVal as Cmd


C = {
    'parity': {'none': 0, 'odd': 1, 'even': 2, 'mark': 3, 'space': 4},
    'mode': {'timeout': 1, 'watchars': 2 },
}


serial_cmds = {
    'send chars': Cmd('Send text', 'TEXT'),
    'send file':  Cmd('Send file', 'FILE'),
    'help':       Cmd('Show help', '[TEXT]'),
    'quit':       Cmd('Quit serial protocol'), # Handled by dispatcher.py.
    'receive':    Cmd('Receive data and save to file', 'FILE'),
    'set':        Cmd('Set config value', 'NAME VAL'),
    'show':       Cmd('Show config values', '[NAME]'),
}


class Serial:

    def __init__(self, transport):
        self.transport = transport
        self.config = {
            'parity':   CV(C['parity']['none'], int, 'Parity'),
            'timeout':  CV(10, int, 'Receive data until given time has elapsed'),
            'watchars': CV('ZZ', str, 'Receive data until given chars are received'),
            'mode':     CV(C['mode']['timeout'], int, 'Receive mode'),
        }


    def _to_chars(self, bytes):
        return ''.join([chr(b) for b in bytes])


    def receive_file(self, filename):
        mode = self.config['mode'].value
        if mode == C['mode']['timeout']:
            self.receive_file_timeout(filename)
        elif mode == C['mode']['watchars']:
            self.receive_file_watchars(filename)
        else:
            log.e('Invalid mode {}'.format(mode))


    def receive_file_watchars(self, filename, watchars=None):
        if not watchars:
            watchars = self.config['watchars'].value
        lenw = len(watchars)
        log.i('Watching for ' + watchars)
        while True:
            pos = self._to_chars(self.transport.peek()).find(watchars)
            if pos >= 0:
                chars = self.transport.read_bytes(pos + lenw)[:-lenw]
                break
            else:
                time.sleep(0.5)
        self._write_file(filename, chars)


    def receive_file_timeout(self, filename, timeout=None):
        if not timeout:
            timeout = self.config['timeout'].value
        log.i('Waiting for ' + str(timeout) + ' seconds')
        time.sleep(timeout)
        self._write_file(filename, self.transport.read())


    def send_chars(self, chars):
        log.i('Sending chars: {}'.format(chars))
        if len(chars) > 255:
            log.w("Text length exceeds calc's buffer size (255 chars).")
        parity_bytes = util.set_parity(bytearray(chars), int(self.config['parity'].value))
        self.transport.write_bytes(parity_bytes)


    def send_file(self, filename):
        log.i('Sending file: {}'.format(filename))
        if filename == 'STDIN':
            self.send_chars(sys.stdin.read())
        else:
            f = open(filename, 'r')
            chars = f.read()
            f.close()
            self.send_chars(chars)


    def help(self, line=''):
        util.show_help(log, line, serial_cmds, self.config, C)


    def show_config(self, line=''):
        util.show_config(self.config, C, log, line)


    def set_config(self, line):
        util.set_config(line, self.config, C, log)


    def _write_file(self, filename, bytes):
        if filename == 'STDOUT':
            print(self._to_chars(bytes))
        else:
            f = open(filename, 'w')
            f.write(bytearray(bytes))
            f.close()
            log.i('Wrote file ' + filename)
