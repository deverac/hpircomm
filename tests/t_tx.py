import unittest
from mock import patch, call, Mock, MagicMock, DEFAULT
import struct

import src.Tx

from tests.sert import sert


mock_txpa = None
tx = None

pa_callback = None
sleep_counter = 0
wav_output = []



class F:

    def sleep(self, secs):
        global sleep_counter
        sleep_counter += 1
        if sleep_counter > 1000:
            raise Exception('fake_sleep was called too many times')


    def time(self):
        return 123


def fake_is_active():
    """Simulate playing wav data by calling callback"""
    in_data = []
    frame_count = 20000
    time_info = 0
    status = 0

    (data, result) = pa_callback(in_data, frame_count, time_info, status)
    wav_output.append(data)
    return (result + 1) % 2


def fake_open(**kwargs):
    """Save the callback function"""
    global pa_callback
    pa_callback = kwargs['stream_callback']
    return DEFAULT


def default_cfg(config):
    names = ['samp_width', 'chan', 'framerate', 'quiet_init', 'wav_file']
    dct = {}
    for name in names:
        dct[name] = None
    for name in names:
        if name in config:
            dct[name] = config[name]
    return dct


def get_mock_stream():
    return mock_txpa.get_instance.return_value.open.return_value



class Base(unittest.TestCase):

    def setUp(self):
        del wav_output[:] # clear list
        self.init_tx({})


    @patch('src.Tx.pa')
    def init_tx(self, config, mock_srctxpa):
        global mock_txpa
        global tx

        mock_txpa = mock_srctxpa
        mock_txpa.get_instance.return_value.open = MagicMock(side_effect=fake_open)
        mock_txpa.get_instance.return_value.open.return_value.is_active = fake_is_active

        cfg = default_cfg(config)
        samp_width = cfg['samp_width'] or 2
        chan = cfg['chan'] or 1
        framerate = cfg['framerate'] or 14400
        quiet_init = cfg['quiet_init'] or True
        wav_file = cfg['wav_file']
        tx = src.Tx.Tx(samp_width, chan, framerate, quiet_init, wav_file)



class TestWriteBytes(Base):

    def test_should_ignore_writes_after_all_done(self):
        tx.run()
        tx.all_done()
        sert(get_mock_stream().start_stream).called_once()

        tx.write_bytes([65])

        sert(get_mock_stream().start_stream).called_once()


    def test_should_open_and_close_stream(self):
        tx.run()
        stream = get_mock_stream()
        sert(stream.start_stream).called_once()
        sert(stream.stop_stream).called_once()

        tx.write_bytes([65])

        sert(stream.start_stream).called_twice()
        sert(stream.stop_stream).called_twice()


    @patch('src.Tx.time', new=F())
    def test_should_update_start_time(self):
        tx.run()
        sert(tx.started_at).to_equal(0)

        tx.write_bytes([65])

        sert(tx.started_at).to_equal(123)


    @patch('src.Tx.time', new=F())
    def test_should_record_session(self):
        tx.run()
        tx.record_session = True
        sert(len(tx.session_buffer)).to_equal(0)

        tx.write_bytes([65])

        sert(len(tx.session_buffer)).to_equal(5120)

        tx.write_bytes([66])

        sert(len(tx.session_buffer)).to_equal(10240)


    @patch('src.Tx.time', new=F())
    def test_should_output_wav_data(self):
        tx.run()
        sert(len(wav_output)).to_equal(0)

        tx.write_bytes([65])
        #print wav_output
        sert(len(wav_output)).to_equal(2)
        sert(len(wav_output[0])).to_equal(5120)
        sert(len(wav_output[1])).to_equal(0)


    @patch('src.Tx.time', new=F())
    def test_should_encode_one(self):
        tx.run()
        tx.write_bytes([1])
        dat = struct.unpack('<'+str(len(tx.wavdat)/2)+'h', tx.wavdat)

        bits = []
        i = 0
        last = 60
        step = 6
        for i in range(0, last, step):
            bits.append(dat[i:i+step])
        tail = dat[last:]

        sert(bits[0]).to_equal((0,0,0,0,0,0))
        sert(bits[1]).to_equal((32767,0,0,0,0,0))
        sert(bits[2]).to_equal((0,0,0,0,0,0))
        sert(bits[3]).to_equal((32767,0,0,0,0,0))
        sert(bits[4]).to_equal((32767,0,0,0,0,0))
        sert(bits[5]).to_equal((32767,0,0,0,0,0))
        sert(bits[6]).to_equal((32767,0,0,0,0,0))
        sert(bits[7]).to_equal((32767,0,0,0,0,0))
        sert(bits[8]).to_equal((32767,0,0,0,0,0))
        sert(bits[9]).to_equal((32767,0,0,0,0,0))

        assert tail == (0,) * 2500


    @patch('src.Tx.time', new=F())
    def test_should_encode_zero(self):
        tx.run()
        tx.write_bytes([0])
        dat = struct.unpack('<'+str(len(tx.wavdat)/2)+'h', tx.wavdat)

        bits = []
        i = 0
        last = 60
        step = 6
        for i in range(0, last, step):
            bits.append(dat[i:i+step])
        tail = dat[last:]

        sert(bits[0]).to_equal((0,0,0,0,0,0))
        sert(bits[1]).to_equal((32767,0,0,0,0,0))
        sert(bits[2]).to_equal((32767,0,0,0,0,0))
        sert(bits[3]).to_equal((32767,0,0,0,0,0))
        sert(bits[4]).to_equal((32767,0,0,0,0,0))
        sert(bits[5]).to_equal((32767,0,0,0,0,0))
        sert(bits[6]).to_equal((32767,0,0,0,0,0))
        sert(bits[7]).to_equal((32767,0,0,0,0,0))
        sert(bits[8]).to_equal((32767,0,0,0,0,0))
        sert(bits[9]).to_equal((32767,0,0,0,0,0))

        assert tail == (0,) * 2500



class TestAllDone(Base):

    def test_should_close_stream(self):
        tx.run()
        mock_stream = get_mock_stream()
        sert(mock_stream.close).not_called()

        tx.all_done()

        sert(mock_stream.close).called_once()


    def test_should_close_stream_once(self):
        tx.run()
        tx.all_done()
        sert(get_mock_stream().close).called_once()

        tx.all_done()

        sert(get_mock_stream().close).called_once()


    def test_should_save_session_when_wav_file_is_given(self):
        self.init_tx({'wav_file' : 'file.wav'})
        tx.session_buffer = [33, 44]
        tx.write_wav = Mock()
        tx.run()
        sert(tx.write_wav).not_called()

        tx.all_done()

        sert(tx.write_wav).called_once_with('file.wav', bytearray([33, 44]))



class TestSetWavFilename(Base):

    def test_should_clear_session_buffer(self):
        filename = None
        tx.session_buffer = [33, 44]

        tx.set_wav_filename(filename)

        sert(tx.session_buffer).to_equal([])


    def test_should_set_wav_file(self):
        filename = 'abc.wav'
        sert(tx.wav_file).to_equal(None)

        tx.set_wav_filename(filename)

        sert(tx.wav_file).to_equal(filename)


    def test_should_set_record_session(self):
        filename = 'abc.wav'
        sert(tx.record_session).is_false()

        tx.set_wav_filename(filename)

        sert(tx.record_session).is_true()


    def test_should_clear_record_session(self):
        filename = None
        tx.record_session = True

        tx.set_wav_filename(filename)

        sert(tx.record_session).is_false()


    @patch('wave.open')
    def test_should_save_session_buffer(self, mock_open):
        wavdat = [33, 44]
        filename = None
        tx.session_buffer = wavdat
        tx.wav_file = 'abc.txt'

        tx.set_wav_filename(filename)

        sert(mock_open).called_once()
        sert(mock_open).called_with('abc.txt', 'wb')
        sert(mock_open.return_value.writeframes).called_with(bytearray(wavdat))
        sert(mock_open.return_value.close).called_once()



class TestRun(Base):

    def test_should_start(self):
        sert(tx.is_started).is_false()

        tx.run()

        sert(tx.is_started).is_true()


    @patch('src.Tx.now')
    def test_should_record_start_time_when_wav_file(self, mock_now):
        mock_now.return_value = 120
        self.init_tx({'wav_file' : 'file.wav'})
        sert(tx.started_at).to_equal(0)

        tx.run()

        sert(tx.started_at).to_equal(120)



    def test_should_open_pyaudio(self):
        mock_pa = mock_txpa.get_instance
        sert(mock_pa, 'open').not_called()

        tx.run()

        sert(mock_pa, 'open').called_once()


    def test_should_run_once(self):
        mock_pa = mock_txpa.get_instance
        tx.run()
        sert(mock_pa, 'open').called_once()

        tx.run()

        sert(mock_pa, 'open').called_once()



class TestWriteWav(Base):

    @patch('src.Tx.wave')
    def test_should_write_wave_file(self, mock_wave):
        sert(mock_wave.open).not_called()
        sert(mock_wave.open, 'setparams').not_called()
        sert(mock_wave.open, 'writeframes').not_called()
        sert(mock_wave.open, 'close').not_called()

        tx.write_wav('abc.txt', [15, 23, 41])

        sert(mock_wave.open).called_with('abc.txt', 'wb')
        sert(mock_wave.open, 'setparams').called_with((1, 2, 14400, 0, 'NONE', 'not compressed'))
        sert(mock_wave.open, 'writeframes').called_with([15, 23, 41])
        sert(mock_wave.open, 'close').called_once()



class TestNow(Base):

    def test_now(self):
        t1 = src.Tx.now()
        t2 = src.Tx.now()
        assert t2 > t1



class TestPadSilence(Base):

    @patch('src.Tx.time')
    def test_pad(self, mock_time):
        now_ms = 11
        mock_time.time.return_value = now_ms
        start_time = now_ms - 5
        frame_rate = 14400
        sample_width = 2
        channels = 1

        pad = src.Tx.pad_silence(start_time, channels, frame_rate, sample_width)

        assert pad ==  (5 * 14400 * 2) * [0]
