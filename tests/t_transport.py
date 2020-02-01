import unittest
import re
from mock import patch, call, Mock, MagicMock, DEFAULT

import src.transport as transport
from tests.sert import sert


mock_tx = None
mock_rx = None
tport = None



class TestInit(unittest.TestCase):

    @patch('src.Rx.Rx')
    @patch('src.Tx.Tx')
    def test_should_init_quietly(self, mock_tx, mock_rx):
        quiet_init = True
        wav_prefix = None
        framerate = None
        rxsens = None

        t = transport.Transport(quiet_init, wav_prefix, framerate, rxsens)

        sert(mock_rx).called_once_with(2, 1, 44100, True, None, 0.11)
        sert(mock_tx).called_once_with(2, 1, 44100, True, None)


    @patch('src.Rx.Rx')
    @patch('src.Tx.Tx')
    def test_should_init_noisily(self, mock_tx, mock_rx):
        quiet_init = False
        wav_prefix = None
        framerate = None
        rxsens = None

        t = transport.Transport(quiet_init, wav_prefix, framerate, rxsens)

        sert(mock_rx).called_once_with(2, 1, 44100, False, None, 0.11)
        sert(mock_tx).called_once_with(2, 1, 44100, False, None)


    @patch('src.Rx.Rx')
    @patch('src.Tx.Tx')
    def test_should_init_wav_file(self, mock_tx, mock_rx):
        quiet_init = None
        wav_prefix = 'pfx'
        framerate = None
        rxsens = None

        t = transport.Transport(quiet_init, wav_prefix, framerate, rxsens)

        sert(mock_rx).called_once_with(2, 1, 44100, False, 'pfx_rx.wav', 0.11)
        sert(mock_tx).called_once_with(2, 1, 44100, False, 'pfx_tx.wav')


    @patch('src.Rx.Rx')
    @patch('src.Tx.Tx')
    def test_should_init_framerate(self, mock_tx, mock_rx):
        quiet_init = None
        wav_prefix = None
        framerate = 22050
        rxsens = None

        t = transport.Transport(quiet_init, wav_prefix, framerate, rxsens)

        sert(mock_rx).called_once_with(2, 1, 22050, False, None, 0.11)
        sert(mock_tx).called_once_with(2, 1, 22050, False, None)


    @patch('src.Rx.Rx')
    @patch('src.Tx.Tx')
    def test_should_init_rxsensitivity(self, mock_tx, mock_rx):
        quiet_init = None
        wav_prefix = None
        framerate = None
        rxsens = 0.04

        t = transport.Transport(quiet_init, wav_prefix, framerate, rxsens)

        sert(mock_rx).called_once_with(2, 1, 44100, False, None, 0.04)
        sert(mock_tx).called_once_with(2, 1, 44100, False, None)



class Base(unittest.TestCase):

    @patch('src.Rx.Rx')
    @patch('src.Tx.Tx')
    def setUp(self, mock_txtx, mock_rxrx):
        global mock_tx
        global mock_rx
        global tport
        mock_rx = mock_rxrx
        mock_tx = mock_txtx
        tport = transport.Transport(True, None, None, None)



class TestStartIt(Base):

    def test_should_start(self):
        sert(mock_rx, 'run').not_called()
        sert(mock_tx, 'run').not_called()

        tport.start_it()

        sert(mock_rx, 'run').called_once()
        sert(mock_tx, 'run').called_once()



class TestStopIt(Base):

    def test_should_start(self):
        sert(mock_rx, 'all_done').not_called()
        sert(mock_tx, 'all_done').not_called()

        tport.stop_it()

        sert(mock_rx, 'all_done').called_once()
        sert(mock_tx, 'all_done').called_once()



class TestSetWavPrefix(Base):

    def test_should_set_wav_prefix(self):

        tport.set_wav_prefix('abc')

        sert(mock_rx, 'set_wav_filename').called_once_with('abc_rx.wav')
        sert(mock_tx, 'set_wav_filename').called_once_with('abc_tx.wav')


    def test_should_strip_whitespace(self):
        tport.set_wav_prefix('  abc  ')
        sert(mock_rx, 'set_wav_filename').called_with('abc_rx.wav')
        sert(mock_tx, 'set_wav_filename').called_with('abc_tx.wav')


    def test_should_squash_invalid_chars(self):
        for i in range(0, 256):
            if re.match('[a-zA-Z0-9\-]', chr(i)):
                continue
            pfx = 'f{}{}'.format(chr(i), i)
            exp = 'f_{}'.format(i)
            tport.set_wav_prefix(pfx)

            sert(mock_rx, 'set_wav_filename').called_with('{}_rx.wav'.format(exp))
            sert(mock_tx, 'set_wav_filename').called_with('{}_tx.wav'.format(exp))


    def test_should_call_with_none(self):
        tport.set_wav_prefix('NoNe')
        sert(mock_rx, 'set_wav_filename').called_with(None)
        sert(mock_tx, 'set_wav_filename').called_with(None)


    def test_should_handle_empty_val(self):
        tport.set_wav_prefix('')
        sert(mock_rx, 'set_wav_filename').called_with(None)
        sert(mock_tx, 'set_wav_filename').called_with(None)



class TestPeekBytes(Base):

    def test_should_peek(self):
        sert(mock_rx, 'peek_bytes').not_called()

        tport.peek()

        sert(mock_rx, 'peek_bytes').called_once_with(9223372036854775807)


    def test_should_peek_byte(self):
        sert(mock_rx, 'peek_bytes').not_called()

        tport.peek_byte()

        sert(mock_rx, 'peek_bytes').called_once_with(1)


    def test_should_peek_bytes(self):
        sert(mock_rx, 'peek_bytes').not_called()

        tport.peek_bytes(4)

        sert(mock_rx, 'peek_bytes').called_once_with(4)



class TestReadBytes(Base):

    def test_should_read(self):
        sert(mock_rx, 'read_bytes').not_called()

        tport.read()

        sert(mock_rx, 'read_bytes').called_once_with(9223372036854775807)


    def test_should_read_byte(self):
        sert(mock_rx, 'read_bytes').not_called()

        tport.read_byte()

        sert(mock_rx, 'read_bytes').called_once_with(1)


    def test_should_read_bytes(self):
        sert(mock_rx, 'read_bytes').not_called()

        tport.read_bytes(4)

        sert(mock_rx, 'read_bytes').called_once_with(4)


    def test_should_read_bytes(self):
        sert(mock_rx, 'read_bytes').not_called()

        tport.clear_buffer()

        sert(mock_rx, 'read_bytes').called_once_with(9223372036854775807)



class TestWriteBytes(Base):

    def test_should_write_byte(self):
        sert(mock_tx, 'write_bytes').not_called()

        tport.write_byte(65)

        sert(mock_tx, 'write_bytes').called_once_with([65])


    def test_should_write_bytes(self):
        sert(mock_tx, 'write_bytes').not_called()

        tport.write_bytes([65, 66])

        sert(mock_tx, 'write_bytes').called_once_with([65, 66])
