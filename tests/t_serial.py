import unittest
import StringIO
from mock import patch, call, Mock, MagicMock
import src.log

import src.transport
import src.serial
from tests.sert import sert


transport_ary = []
sleep_counter = 0
ser = None
tport = MagicMock(autospec=src.transport.Transport)


def fake_sleep(secs):
    global sleep_counter
    sleep_counter += 1
    if sleep_counter == 100:
        transport_ary.append(ord('Z'))
    if sleep_counter > 1000:
        raise Exception('fake_sleep was called too many times')


def is_config(dct):
    return sorted(dct.keys()) == ['mode', 'parity', 'timeout', 'watchars']


def is_cmds(dct):
    return sorted(dct.keys()) == ['help', 'quit', 'receive', 'send chars', 'send file', 'set', 'show']


def is_const_dct(dct):
    return sorted(dct.keys()) == ['mode', 'parity']


def is_log(mod):
    return mod.__name__ == 'src.log'



class Base(unittest.TestCase):

    def setUp(self):
        global ser
        global sleep_counter
        sleep_counter = 0
        del transport_ary[:]
        tport.reset_mock()
        tport.peek = Mock(return_value = transport_ary)
        tport.read = Mock(return_value = transport_ary)
        tport.read_bytes = Mock(return_value = transport_ary)
        ser = src.serial.Serial(tport)



class TestToChars(Base):

    def test_should_return_string(self):
        assert ser._to_chars([65, 66, 67]) == 'ABC'



class TestReceiveFile(Base):

    def test_should_use_timeout(self):
        ser.config['mode'].value = 1 # timeout
        ser.receive_file_timeout = Mock()

        ser.receive_file('abc.txt')

        sert(ser.receive_file_timeout).called_once_with('abc.txt')


    def test_should_use_watchars(self):
        ser.config['mode'].value = 2 # watchars
        ser.receive_file_watchars = Mock()

        ser.receive_file('abc.txt')

        sert(ser.receive_file_watchars).called_once_with('abc.txt')


    @patch('src.log.e')
    def test_should_handle_invalid_mode(self, mock_log):
        ser.config['mode'].value = -1 # invalid

        ser.receive_file('abc.txt')

        sert(mock_log).called_once_with('Invalid mode -1')



class TestReceiveFileWatchar(Base):

    @patch('time.sleep', side_effect=fake_sleep)
    def test_should_wait_for_chars_to_exist_in_buffer(self, mock_sleep):
        assert len(transport_ary) == 0
        transport_ary.append(65)
        transport_ary.append(66)
        transport_ary.append(ord('Z'))
        ser._write_file = Mock()
        assert sleep_counter == 0

        ser.receive_file_watchars('abc.txt', 'ZZ')

        assert sleep_counter == 100
        assert transport_ary == [65, 66, ord('Z'), ord('Z')]
        sert(ser._write_file).called_with('abc.txt', [65, 66])


    @patch('time.sleep', side_effect=fake_sleep)
    def test_should_write_file_when_chars_exist_in_buffer(self, mock_sleep):
        assert len(transport_ary) == 0
        transport_ary.append(65)
        transport_ary.append(ord('Z'))
        transport_ary.append(ord('Z'))
        ser._write_file = Mock()
        assert sleep_counter == 0

        ser.receive_file_watchars('abc.txt', 'ZZ')

        assert sleep_counter == 0
        sert(ser._write_file).called_with('abc.txt', [65])


    @patch('time.sleep', side_effect=fake_sleep)
    def test_should_use_default_watchar_value(self, mock_sleep):
        assert len(transport_ary) == 0
        transport_ary.append(65)
        transport_ary.append(ord('Z'))
        transport_ary.append(ord('Z'))
        ser._write_file = Mock()
        assert sleep_counter == 0

        ser.receive_file_watchars('abc.txt')

        assert sleep_counter == 0
        sert(ser._write_file).called_with('abc.txt', [65])


    @patch('time.sleep', side_effect=fake_sleep)
    def test_should_use_config_watchar_value(self, mock_sleep):
        ser.config['watchars'].value = 'XYZ'
        assert len(transport_ary) == 0
        transport_ary.append(65)
        transport_ary.append(66)
        transport_ary.append(ord('X'))
        transport_ary.append(ord('Y'))
        ser._write_file = Mock()
        assert sleep_counter == 0

        ser.receive_file_watchars('abc.txt')

        assert sleep_counter == 100
        assert transport_ary == [65, 66, ord('X'), ord('Y'), ord('Z')]
        sert(ser._write_file).called_with('abc.txt', [65, 66])



class TestTimeout(Base):

    @patch('time.sleep', side_effect=fake_sleep)
    def test_should_use_specified_timeout_value(self, mock_sleep):
        transport_ary.append(65)
        transport_ary.append(66)
        ser._write_file = Mock()
        sert(mock_sleep).not_called()

        ser.receive_file_timeout('abc.txt', 25)

        sert(mock_sleep).called_with(25)
        sert(ser._write_file).called_with('abc.txt', [65, 66])


    @patch('time.sleep', side_effect=fake_sleep)
    def test_should_use_default_timeout_value(self, mock_sleep):
        transport_ary.append(65)
        transport_ary.append(66)
        ser._write_file = Mock()
        sert(mock_sleep).not_called()

        ser.receive_file_timeout('abc.txt', None)

        sert(mock_sleep).called_with(10)
        sert(ser._write_file).called_with('abc.txt', [65, 66])



class TestWriteFile(Base):

    @patch('sys.stdout', new_callable=StringIO.StringIO) # Mock 'print'
    def test_should_write_to_stdout(self, mock_print):
        self.assertEqual(mock_print.getvalue(), '')

        ser._write_file('STDOUT', [ord('A')])

        self.assertEqual(mock_print.getvalue(), 'A\n')


    @patch('__builtin__.open')
    def test_should_write_to_file(self, mock_open):
        sert(mock_open).not_called()

        ser._write_file('abc.txt', [66])

        sert(mock_open).called_with('abc.txt', 'w')
        sert(mock_open, 'write').called_with(bytearray([66]))
        sert(mock_open, 'close').called_once()



class TestSendChars(Base):

    def test_should_write_data_with_no_parity(self):
        ser.config['parity'].value = 0
        sert(tport.write_bytes).not_called()

        ser.send_chars('ABC')

        sert(tport.write_bytes).called_with([ord('A'), ord('B'), ord('C')])


    def test_should_write_data_with_parity_odd_parity(self):
        ser.config['parity'].value = 1
        sert(tport.write_bytes).not_called()

        ser.send_chars('ABC')

        sert(tport.write_bytes).called_with([ord('A')|0x80, ord('B')|0x80, ord('C')])


    def test_should_write_data_with_parity_even_parity(self):
        ser.config['parity'].value = 2
        sert(tport.write_bytes).not_called()

        ser.send_chars('ABC')

        sert(tport.write_bytes).called_with([ord('A'), ord('B'), ord('C')|0x80])


    def test_should_write_data_with_parity_mark_parity(self):
        ser.config['parity'].value = 3
        sert(tport.write_bytes).not_called()

        ser.send_chars('ABC')

        sert(tport.write_bytes).called_with([ord('A')|0x80, ord('B')|0x80, ord('C')|0x80])


    def test_should_write_data_with_parity_space_parity(self):
        ser.config['parity'].value = 4
        sert(tport.write_bytes).not_called()

        ser.send_chars('AB' + chr(ord('C')|0x80))

        sert(tport.write_bytes).called_with([ord('A'), ord('B'), ord('C')])


    @patch('src.log.w')
    def test_should_warn_when_big_buffer(self, mock_log):
        buf_ok = [65] * 255
        buf_too_big = [65] * 256

        ser.send_chars(buf_ok)

        sert(mock_log).not_called()

        ser.send_chars(buf_too_big)

        sert(mock_log).called_once_with("Text length exceeds calc's buffer size (255 chars).")



class TestSendFile(Base):

    @patch('sys.stdin')
    def test_should_write_to_stdout(self, mock_stdin):
        mock_stdin.read = Mock(return_value='abc')
        ser.send_chars = Mock()

        ser.send_file('STDIN')

        sert(ser.send_chars).called_with('abc')


    @patch('__builtin__.open')
    def test_should_write_to_file(self, mock_open):
        mock_open.return_value.read.return_value = 'xyz'
        ser.send_chars = Mock()
        sert(mock_open).not_called()

        ser.send_file('abc.txt')

        sert(mock_open).called_with('abc.txt', 'r')
        sert(mock_open, 'read').called_once()
        sert(mock_open, 'close').called_once()
        sert(ser.send_chars).called_with('xyz')



class TestHelp(Base):

    @patch('src.util.show_help')
    def test_should_call_help(self, mock_util):
        ser.help('abc')

        sert(mock_util).called_once()
        rgs = mock_util.call_args.args
        sert(len(rgs)).to_equal(5)
        sert(      is_log(rgs[0])).is_true()
        sert(             rgs[1]).to_equal('abc')
        sert(     is_cmds(rgs[2])).is_true()
        sert(   is_config(rgs[3])).is_true()
        sert(is_const_dct(rgs[4])).is_true()



class TestShowConfig(Base):

    @patch('src.util.show_config')
    def test_should_call_show_config(self, mock_util):
        ser.show_config('abc')

        sert(mock_util).called_once()
        rgs = mock_util.call_args.args
        sert(len(rgs)).to_equal(4)
        sert(   is_config(rgs[0])).is_true()
        sert(is_const_dct(rgs[1])).is_true()
        sert(      is_log(rgs[2])).is_true()
        sert(             rgs[3]).to_equal('abc')



class TestSetConfig(Base):

    @patch('src.util.set_config')
    def test_should_call_set_config(self, mock_util):
        ser.set_config('abc def')

        sert(mock_util).called_once()
        rgs = mock_util.call_args.args
        sert(             rgs[0]).to_equal('abc def')
        sert(   is_config(rgs[1])).is_true()
        sert(is_const_dct(rgs[2])).is_true()
        sert(      is_log(rgs[3])).is_true()
