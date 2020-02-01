import sys
import unittest
from mock import patch, Mock

import src.pa as pa
from tests.sert import sert


STDIN = 0  # Not used
STDOUT = 1 # Not used
STDERR = 2
DEVNULL = 3

fileno = [3, 8, 9, 22] # Arbitrary


def fake_dup(index):
    return fileno[index]


def fake_dup2(fileno_num, fileno_index):
    fileno[fileno_index] = fileno_num


def fake_open(fileno_num, mode):
    return fileno[fileno_num]


def fake_pyaudio():
    if fileno[STDERR] == 9:
        sys.stderr.write('Initiating PyAudio')


# Use global vars to improve readability
mock_pyaud = None
mock_stderr = None
mock_os = None



class TestPa(unittest.TestCase):

    def setUp(self):
        global mock_pyaud
        global mock_stderr
        global mock_os
        patch1 = patch('src.pa.pyaudio')
        patch2 = patch('sys.stderr')
        patch3 = patch('src.pa.os')
        mock_pyaud  = patch1.start()
        mock_stderr = patch2.start()
        mock_os     = patch3.start()
        self.addCleanup(patch1.stop)
        self.addCleanup(patch2.stop)
        self.addCleanup(patch3.stop)

        mock_pyaud.PyAudio = fake_pyaudio
        mock_stderr.fileno = Mock(return_value=STDERR)
        mock_os.devnull = DEVNULL
        mock_os.open = fake_open
        mock_os.dup = fake_dup
        mock_os.dup2 = fake_dup2
        mock_os.close = Mock()


    def test_should_silence_stderr(self):
        sert(mock_stderr.write).not_called()
        sert(mock_os.close).not_called()

        pa.get_instance(False)

        sert(mock_stderr.write).not_called()
        sert(mock_os.close).called_twice()
        sert(mock_os.close).first_call_called_with(fileno[DEVNULL])
        sert(mock_os.close).second_call_called_with(fileno[STDERR])


    def test_should_write_to_stderr(self):
        sert(mock_stderr.write).not_called()

        pa.get_instance(True)

        sert(mock_stderr.write).called_with('Initiating PyAudio')
