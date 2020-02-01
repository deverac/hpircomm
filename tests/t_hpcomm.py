import unittest
from mock import patch, call, Mock, MagicMock, DEFAULT
import StringIO

import src.log
import src.transport
import src.hpcomm

from tests.sert import sert, TAttrBag

EXIT_OK = 0
EXIT_ERR = 1

class TestReadHistoryFile(unittest.TestCase):

    @patch('readline.read_history_file')
    def test_should_read_history_file(self, mock_file):
        filename = 'abc.txt'

        src.hpcomm.read_history_file(filename)

        sert(mock_file).called_once_with(filename)


    @patch('readline.read_history_file')
    def test_should_handle_read_error(self, mock_file):
        filename = 'abc.txt'
        mock_file.side_effect=IOError('bad thing')

        src.hpcomm.read_history_file(filename)

        sert(mock_file).called_once_with(filename)



class TestWriteHistoryFile(unittest.TestCase):

    @patch('readline.write_history_file')
    def test_should_write_history_file(self, mock_file):
        filename = 'abc.txt'

        src.hpcomm.write_history_file(filename)

        sert(mock_file).called_once_with(filename)


    @patch('readline.write_history_file')
    def test_should_handle_write_error(self, mock_file):
        filename = 'abc.txt'
        mock_file.side_effect=IOError('bad thing')

        src.hpcomm.write_history_file(filename)

        sert(mock_file).called_once_with(filename)



def targs(**kwargs):
    default_dct = { 'init': None, 'showinit': True, 'wavprefix': None, 'framerate': 14400, 'sensitivity': 0.11, 'log': 5 }
    default_dct.update(kwargs)
    return TAttrBag(**default_dct)



class TestLooper(unittest.TestCase):

    @patch('src.hpcomm.readline')
    @patch('src.dispatcher.Dispatcher')
    def test_should_start_transport(self, mock_disp, mock_readline):
        hpc = src.hpcomm.HpComm()

        res = hpc.looper(targs())

        sert(mock_disp, 'start_transport').called_once()
        sert(res).to_equal(EXIT_OK)


    @patch('src.hpcomm.readline')
    @patch('src.dispatcher.Dispatcher')
    def test_should_stop_transport(self, mock_disp, mock_readline):
        hpc = src.hpcomm.HpComm()

        hpc.looper(targs())

        sert(mock_disp, 'stop_transport').called_once()


    @patch('src.hpcomm.read_history_file')
    @patch('src.dispatcher.Dispatcher')
    def test_should_read_history(self, mock_disp, mock_read_hist):
        hpc = src.hpcomm.HpComm()

        hpc.looper(targs())

        sert(mock_read_hist).called_once_with('.hpirhist')


    @patch('src.hpcomm.readline', new=Mock())
    @patch('src.hpcomm.write_history_file')
    @patch('src.dispatcher.Dispatcher')
    def test_should_write_history(self, mock_disp, mock_write_hist):
        hpc = src.hpcomm.HpComm()

        hpc.looper(targs())

        sert(mock_write_hist).called_once_with('.hpirhist')


    @patch('src.hpcomm.readline', new=Mock())
    @patch('src.dispatcher.Dispatcher')
    @patch('src.hpcomm.log')
    def test_should_set_log_level(self, mock_log, mock_disp):
        hpc = src.hpcomm.HpComm()

        hpc.looper(targs())

        sert(mock_log.set_log_level).called_once_with(5)


    @patch('src.hpcomm.readline', new=Mock())
    @patch('src.dispatcher.Dispatcher')
    @patch('src.hpcomm.log')
    @patch('sys.stdout', new_callable=StringIO.StringIO) # Mock 'print'
    def test_should_print_stacktrace(self, mock_print, mock_log, mock_disp):
        mock_disp.return_value.is_trace_on_error.return_value = True
        mock_disp.return_value.is_done.side_effect = [False, True]
        mock_disp.return_value.read_and_exec.side_effect = KeyboardInterrupt
        hpc = src.hpcomm.HpComm()

        res = hpc.looper(targs())

        sert(mock_print.getvalue().split()[-1]).to_equal('KeyboardInterrupt')
        sert(res).to_equal(EXIT_ERR)


    @patch('src.hpcomm.readline', new=Mock())
    @patch('src.dispatcher.Dispatcher')
    @patch('src.hpcomm.log')
    def test_should_exit_on_error(self, mock_log, mock_disp):
        mock_disp.return_value.is_trace_on_error.return_value = False
        mock_disp.return_value.is_exit_on_error.return_value = True
        mock_disp.return_value.is_done.side_effect = [False, True]
        mock_disp.return_value.read_and_exec.side_effect = KeyboardInterrupt
        hpc = src.hpcomm.HpComm()

        res = hpc.looper(targs())

        sert(mock_disp, 'force_done').called_once()
        sert(res).to_equal(EXIT_ERR)


    @patch('src.hpcomm.readline', new=Mock())
    @patch('src.dispatcher.Dispatcher')
    @patch('src.hpcomm.log')
    def test_should_exit_after_two_keyboardinterrupt(self, mock_log, mock_disp):
        d = mock_disp.return_value
        d.is_trace_on_error.return_value = False
        d.is_exit_on_error.return_value = False
        d.is_done.side_effect = [False, False, True]
        d.read_and_exec.side_effect = KeyboardInterrupt
        hpc = src.hpcomm.HpComm()

        res = hpc.looper(targs())

        sert(mock_disp, 'force_done').called_once()
        sert(res).to_equal(EXIT_ERR)


    @patch('src.hpcomm.readline', new=Mock())
    @patch('src.dispatcher.Dispatcher')
    @patch('src.hpcomm.log')
    def test_should_reset_except_count(self, mock_log, mock_disp):
        d = mock_disp.return_value
        d.is_trace_on_error.return_value = False
        d.is_exit_on_error.return_value = False
        d.is_done.side_effect = [False, False, False, False, False, False, False, True]
        d.read_and_exec.side_effect = [KeyboardInterrupt, '', KeyboardInterrupt, '', KeyboardInterrupt, '']
        hpc = src.hpcomm.HpComm()

        res = hpc.looper(targs())

        sert(res).to_equal(EXIT_OK)


    @patch('src.hpcomm.read_history_file')
    @patch('src.hpcomm.log')
    @patch('sys.stdout', new_callable=StringIO.StringIO) # Mock 'print'
    def test_should_handle_exception(self, mock_print, mock_log, mock_hist):
        mock_hist.side_effect = IOError('bad thing')
        hpc = src.hpcomm.HpComm()

        res = hpc.looper(targs())

        sert(mock_print.getvalue().split('\n')[-3]).to_equal('IOError: bad thing')
        sert(res).to_equal(EXIT_ERR)
