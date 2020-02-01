import unittest
from mock import patch, call, Mock, MagicMock, DEFAULT
import struct

import src.Rx

from tests.sert import sert

sleep_counter = 0
mock_rxpa = None
rx = None
wav_data = []

pa_callback = None


def default_cfg(config):
    names = ['samp_width', 'chan', 'framerate', 'quiet_init', 'wav_file', 'sensitivity']
    dct = {}
    for name in names:
        dct[name] = None
    for name in names:
        if name in config:
            dct[name] = config[name]
    return dct


def fake_start(mockt):
    mock_threading = mockt
    def fake_thread_launch():
        lst = mock_threading.Thread.call_args_list
        if len(lst) > 0:
            (args, dct) = lst[0]
            fn = dct['target']
            fn()
        else:
            raise Exception('call_args_list length is zero')
    return fake_thread_launch


def fake_open(**kwargs):
    """Save the callback function"""
    global pa_callback
    pa_callback = kwargs['stream_callback']
    return DEFAULT


def get_mock_stream():
    return mock_rxpa.get_instance.return_value.open.return_value



class F:

    def sleep(self, secs):
        global sleep_counter
        rx.is_started = True
        if sleep_counter < len(wav_data):
            dat = wav_data[sleep_counter]
            in_data = struct.pack('<'+str(len(dat))+'h', *dat)
            frame_count = len(dat)
            time_info = 0
            status = 0
            pa_callback(in_data, frame_count, time_info, status)
        else:
            rx.all_done()
        sleep_counter += 1
        if sleep_counter > 1000:
            raise Exception('fake_sleep was called too many times')



class Base(unittest.TestCase):

    def setUp(self):
        del wav_data[:] # clear list
        self.init_rx({})


    @patch('src.Rx.pa')
    def init_rx(self, config, mock_srcrxpa):
        global mock_rxpa
        global rx
        global sleep_counter

        sleep_counter = 0

        mock_rxpa = mock_srcrxpa
        mock_rxpa.get_instance.return_value.open = MagicMock(side_effect=fake_open)

        cfg = default_cfg(config)
        samp_width = cfg['samp_width'] or 2
        chan = cfg['chan'] or 1
        framerate = cfg['framerate'] or 14400
        quiet_init = cfg['quiet_init'] or True
        wav_file = cfg['wav_file']
        sensitivity = cfg['sensitivity'] or 0.11
        rx = src.Rx.Rx(samp_width, chan, framerate, quiet_init, wav_file, sensitivity)



class TestMaxShort(Base):

    def test_max_short(self):
        sert(src.Rx.MAX_SHORT).to_equal(32767)



class TestStartRx(Base):

    # A poor test, but helps with code-coverage metrics.
    def test_should_not_alter_stream_after_starting(self):
        rx.is_started = True
        rx.stream = 'a_val'

        rx._start_rx()

        sert(rx.stream).to_equal('a_val')



class TestAllDone(Base):

    def test_should_write_file_only_once(self):
        self.init_rx({'wav_file' : 'file.wav'})
        rx.is_started = True
        rx.write_wav = Mock()
        rx.thread = Mock()
        rx.all_done()
        sert(rx.write_wav).called_once()

        rx.all_done()

        sert(rx.write_wav).called_once()


    def test_should_save_session_when_wav_file_is_given(self):
        self.init_rx({'wav_file' : 'file.wav'})
        rx.is_started = True
        rx.session_buffer = [33, 44]
        rx.write_wav = Mock()
        rx.thread = Mock()
        sert(rx.write_wav).not_called()

        rx.all_done()

        sert(rx.write_wav).called_once_with('file.wav', bytearray([33, 44]))


    def test_should_join_thread(self):
        self.init_rx({})
        rx.is_started = True
        rx.thread = Mock()
        sert(rx.thread.join).not_called()

        rx.all_done()

        sert(rx.thread.join).called_once()



class TestSetWavFilename(Base):

    def test_should_clear_session_buffer(self):
        filename = None
        rx.session_buffer = [33, 44]

        rx.set_wav_filename(filename)

        sert(rx.session_buffer).to_equal([])


    def test_should_set_wav_file(self):
        filename = 'abc.wav'
        sert(rx.wav_file).to_equal(None)

        rx.set_wav_filename(filename)

        sert(rx.wav_file).to_equal(filename)


    def test_should_set_record_session(self):
        filename = 'abc.wav'
        sert(rx.record_session).is_false()

        rx.set_wav_filename(filename)

        sert(rx.record_session).is_true()


    def test_should_clear_record_session(self):
        filename = None
        rx.record_session = True

        rx.set_wav_filename(filename)

        sert(rx.record_session).is_false()


    @patch('wave.open')
    def test_should_save_session_buffer(self, mock_open):
        wavdat = [33, 44]
        filename = None
        rx.session_buffer = wavdat
        rx.wav_file = 'abc.txt'

        rx.set_wav_filename(filename)

        sert(mock_open).called_once()
        sert(mock_open).called_with('abc.txt', 'wb')
        sert(mock_open.return_value.writeframes).called_with(bytearray(wavdat))
        sert(mock_open.return_value.close).called_once()



class TestPeekBytes(Base):

    def test_should_peek_bytes(self):
        rx.char_buf = ['a', 'b', 'c']

        b = rx.peek_bytes(2)

        sert(b).to_equal(['a', 'b'])
        sert(rx.char_buf).to_equal(['a', 'b', 'c'])



class TestReadBytes(Base):

    def test_should_read_bytes(self):
        rx.char_buf = ['a', 'b', 'c']

        b = rx.read_bytes(2)

        sert(b).to_equal(['a', 'b'])
        sert(rx.char_buf).to_equal(['c'])



class TestRun(Base):

    @patch('src.Rx.threading')
    def test_should_start_thread(self, mock_threading):
        sert(mock_threading.Thread, 'start').not_called()

        rx.run()

        sert(mock_threading.Thread, 'start').called_once()


    @patch('src.Rx.threading')
    def test_should_start_thread_only_once(self, mock_threading):
        sert(mock_threading.Thread, 'start').not_called()
        rx.run()
        sert(mock_threading.Thread, 'start').called_once()

        rx.run()

        sert(mock_threading.Thread, 'start').called_once()


    @patch('src.Rx.time', new=F())
    @patch('src.Rx.threading')
    def test_should_start_stop_close_stream(self, mock_threading):
        mock_threading.Thread.return_value.start = fake_start(mock_threading)
        stream = get_mock_stream()
        sert(stream.start_stream).not_called()
        sert(stream.stop_stream).not_called()
        sert(stream.close).not_called()

        rx.run()

        sert(stream.start_stream).called_once()
        sert(stream.stop_stream).called_once()
        sert(stream.close).called_once()


    @patch('src.Rx.time', new=F())
    @patch('src.Rx.threading')
    def test_should_decode_zero(self, mock_threading):
        samps = [0,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                0,0,0,0,0,0,
                0,0,0,0,0,0,
                ]
        wav_data.append(samps)
        mock_threading.Thread.return_value.start = fake_start(mock_threading)

        rx.run()

        bytes = rx.peek_bytes(1000)
        sert(len(bytes)).to_equal(1)
        sert(bytes).to_equal([0])


    @patch('src.Rx.time', new=F())
    @patch('src.Rx.threading')
    def test_should_decode_one(self, mock_threading):
        samps = [0,0,0,0,0,0,
                32767,0,0,0,0,0,
                0,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                0,0,0,0,0,0,
                0,0,0,0,0,0,
                ]
        wav_data.append(samps)
        mock_threading.Thread.return_value.start = fake_start(mock_threading)

        rx.run()

        bytes = rx.peek_bytes(1000)
        sert(len(bytes)).to_equal(1)
        sert(bytes).to_equal([1])


    @patch('src.Rx.time', new=F())
    @patch('src.Rx.threading')
    def test_should_ignore_edge_outside_frame(self, mock_threading):
        samps = [0,0,0,0,0,0,
                32767,0,0,0,0,0,
                0,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                32767,0,0,0,0,0,
                0,0,0,0,0,9000, # ignore
                0,0,0,0,0,0,
                ]
        wav_data.append(samps)
        mock_threading.Thread.return_value.start = fake_start(mock_threading)

        rx.run()

        bytes = rx.peek_bytes(1000)
        sert(len(bytes)).to_equal(1)
        sert(bytes).to_equal([1])


    @patch('src.Rx.time', new=F())
    @patch('src.Rx.threading')
    def test_should_record_session(self, mock_threading):
        wav_data.append([0x65])
        wav_data.append([0x67])
        mock_threading.Thread.return_value.start = fake_start(mock_threading)
        rx.record_session = True

        rx.run()

        sert(rx.session_buffer).to_equal(['\x65', '\x00', '\x67', '\x00'])



class TestWriteWav(Base):

    @patch('src.Rx.wave')
    def test_should_write_wave_file(self, mock_wave):
        sert(mock_wave.open).not_called()
        sert(mock_wave.open, 'setparams').not_called()
        sert(mock_wave.open, 'writeframes').not_called()
        sert(mock_wave.open, 'close').not_called()

        rx.write_wav('abc.wav', [15, 23, 41])

        sert(mock_wave.open).called_with('abc.wav', 'wb')
        sert(mock_wave.open, 'setparams').called_with((1, 2, 14400, 0, 'NONE', 'not compressed'))
        sert(mock_wave.open, 'writeframes').called_with([15, 23, 41])
        sert(mock_wave.open, 'close').called_once()
